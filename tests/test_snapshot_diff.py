from __future__ import annotations

import json
import logging
import tempfile
import unittest
from pathlib import Path

from app.persistence import configure_persistence, process_snapshot_diff, save_snapshot


class SnapshotDiffTests(unittest.TestCase):
    def test_diff_skipped_without_previous_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7)
            with self.assertLogs("mikrotrack", level="INFO") as logs:
                events = process_snapshot_diff([])

        output = "\n".join(logs.output)
        self.assertIn("[DIFF_SKIPPED] No previous snapshot found", output)
        self.assertEqual(events, [])

    def test_diff_presence_identity_and_event_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            snapshot_path = Path(tmp) / "2026-04-05T23-10-00.json"
            snapshot_path.write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:01",
                            "ip_address": "192.168.88.10",
                            "host_name": "old-host",
                            "source": ["dhcp", "arp"],
                            "dhcp_flags": {"dynamic": True},
                            "arp_flags": {"dynamic": True, "complete": True},
                        },
                        {
                            "mac_address": "AA:AA:AA:AA:AA:02",
                            "ip_address": "192.168.88.20",
                            "host_name": "to-be-removed",
                            "source": ["dhcp"],
                        },
                    ]
                ),
                encoding="utf-8",
            )

            configure_persistence(tmp, retention_days=7)
            current = [
                {
                    "mac_address": "AA:AA:AA:AA:AA:01",
                    "ip_address": "192.168.88.11",
                    "host_name": "new-host",
                    "source": ["dhcp", "arp"],
                    "dhcp_flags": {"dynamic": True},
                    "arp_flags": {"dynamic": True, "complete": True},
                },
                {
                    "mac_address": "AA:AA:AA:AA:AA:03",
                    "ip_address": "192.168.88.30",
                    "host_name": "new-device",
                    "source": ["arp"],
                },
            ]

            with self.assertLogs("mikrotrack", level="DEBUG") as logs:
                events = process_snapshot_diff(current)

            events_path = Path(tmp) / "events.jsonl"
            persisted_events = [
                json.loads(line)
                for line in events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        output = "\n".join(logs.output)
        self.assertIn("[NEW_DEVICE] New device detected: 192.168.88.30 (AA:AA:AA:AA:AA:03)", output)
        self.assertIn(
            "[IP_CHANGED] Device IP changed: AA:AA:AA:AA:AA:01 192.168.88.10 -> 192.168.88.11",
            output,
        )
        self.assertIn(
            "[HOSTNAME_CHANGED] Hostname changed: AA:AA:AA:AA:AA:01 old-host -> new-host",
            output,
        )
        self.assertIn(
            "[DEVICE_REMOVED] Device disappeared: 192.168.88.20 (AA:AA:AA:AA:AA:02)",
            output,
        )
        self.assertIn("Diff summary:", output)
        self.assertIn("- new: 1", output)
        self.assertIn("- removed: 1", output)
        self.assertIn("- changed: 2", output)

        event_types = [event["event_type"] for event in events]
        self.assertIn("NEW_DEVICE", event_types)
        self.assertIn("IP_CHANGED", event_types)
        self.assertIn("HOSTNAME_CHANGED", event_types)
        self.assertIn("DEVICE_REMOVED", event_types)
        self.assertEqual(events, persisted_events)
        for event in events:
            self.assertIn("timestamp", event)
            self.assertIn("mac", event)

    def test_diff_dhcp_dynamic_and_ip_assignment_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "2026-04-05T23-10-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:10",
                            "ip_address": "192.168.88.50",
                            "source": ["dhcp"],
                            "dhcp_flags": {"dynamic": True},
                        }
                    ]
                ),
                encoding="utf-8",
            )
            configure_persistence(tmp, retention_days=7)
            current = [
                {
                    "mac_address": "AA:AA:AA:AA:AA:10",
                    "ip_address": "192.168.88.50",
                    "source": ["dhcp"],
                    "dhcp_flags": {"dynamic": False},
                }
            ]

            events = process_snapshot_diff(current)

        by_type = {event["event_type"]: event for event in events}
        self.assertEqual(by_type["DHCP_DYNAMIC_CHANGED"]["old_value"], True)
        self.assertEqual(by_type["DHCP_DYNAMIC_CHANGED"]["new_value"], False)
        self.assertEqual(by_type["DEVICE_IP_ASSIGNMENT_CHANGED"]["old_value"], "dynamic")
        self.assertEqual(by_type["DEVICE_IP_ASSIGNMENT_CHANGED"]["new_value"], "static")

    def test_diff_source_changed_when_dhcp_to_arp_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "2026-04-05T23-10-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:11",
                            "ip_address": "192.168.88.60",
                            "source": ["dhcp", "arp"],
                        }
                    ]
                ),
                encoding="utf-8",
            )
            configure_persistence(tmp, retention_days=7)

            events = process_snapshot_diff(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:11",
                        "ip_address": "192.168.88.60",
                        "source": ["arp"],
                    }
                ]
            )

        event_types = [event["event_type"] for event in events]
        self.assertIn("SOURCE_CHANGED", event_types)
        self.assertIn("DHCP_REMOVED", event_types)

    def test_diff_error_for_invalid_snapshot_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            snapshot_path = Path(tmp) / "2026-04-05T23-10-00.json"
            snapshot_path.write_text('{"invalid": true}', encoding="utf-8")

            configure_persistence(tmp, retention_days=7)
            with self.assertLogs("mikrotrack", level="ERROR") as logs:
                events = process_snapshot_diff([])

        output = "\n".join(logs.output)
        self.assertIn("[DIFF_ERROR] Failed to process snapshots", output)
        self.assertIn("Recommendation: Verify snapshot format and integrity", output)
        self.assertEqual(events, [])

    def test_diff_generates_arp_status_and_state_change_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "2026-04-05T23-10-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:12",
                            "ip_address": "192.168.88.70",
                            "source": ["arp"],
                            "arp_status": "reachable",
                            "arp_state": "online",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            configure_persistence(tmp, retention_days=7)

            events = process_snapshot_diff(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:12",
                        "ip_address": "192.168.88.70",
                        "source": ["arp"],
                        "arp_status": "permanent",
                        "arp_state": "permanent",
                    }
                ]
            )

        by_type = {event["event_type"]: event for event in events}
        self.assertEqual(by_type["arp_status_changed"]["old_status"], "reachable")
        self.assertEqual(by_type["arp_status_changed"]["new_status"], "permanent")
        self.assertEqual(by_type["arp_state_changed"]["old_state"], "online")
        self.assertEqual(by_type["arp_state_changed"]["new_state"], "permanent")

    def test_diff_generates_session_started_and_ended_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "2026-04-05T23-10-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:21",
                            "ip_address": "192.168.88.81",
                            "source": ["arp"],
                            "arp_status": "failed",
                            "arp_state": "offline",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            configure_persistence(tmp, retention_days=7)

            started_events = process_snapshot_diff(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:21",
                        "ip_address": "192.168.88.81",
                        "source": ["arp"],
                        "arp_status": "reachable",
                        "arp_state": "online",
                    }
                ]
            )

            Path(tmp, "2026-04-05T23-11-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:21",
                            "ip_address": "192.168.88.81",
                            "source": ["arp"],
                            "arp_status": "reachable",
                            "arp_state": "online",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            ended_events = process_snapshot_diff(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:21",
                        "ip_address": "192.168.88.81",
                        "source": ["arp"],
                        "arp_status": "failed",
                        "arp_state": "offline",
                    }
                ]
            )

        started_by_type = {event["event_type"]: event for event in started_events}
        ended_by_type = {event["event_type"]: event for event in ended_events}

        self.assertEqual(started_by_type["state_changed"]["old_state"], "offline")
        self.assertEqual(started_by_type["state_changed"]["new_state"], "online")
        self.assertEqual(started_by_type["session_started"]["event_type"], "session_started")

        self.assertEqual(ended_by_type["state_changed"]["old_state"], "online")
        self.assertEqual(ended_by_type["state_changed"]["new_state"], "offline")
        self.assertEqual(ended_by_type["session_ended"]["event_type"], "session_ended")

    def test_diff_adds_entity_context_and_interface_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "2026-04-05T23-10-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:20",
                            "ip_address": "192.168.88.80",
                            "source": ["arp"],
                            "entity_type": "client",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            configure_persistence(tmp, retention_days=7)

            events = process_snapshot_diff(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:20",
                        "ip_address": "192.168.88.80",
                        "source": ["arp"],
                        "entity_type": "interface",
                        "interface_name": "ether3",
                    }
                ]
            )

        by_type = {event["event_type"]: event for event in events}
        self.assertEqual(by_type["entity_type_detected"]["new_value"], "interface")
        self.assertEqual(by_type["interface_detected"]["new_value"], "ether3")
        self.assertEqual(by_type["entity_type_detected"]["entity_type"], "interface")
        self.assertEqual(by_type["interface_detected"]["interface_name"], "ether3")

    def test_save_snapshot_keeps_timestamps_when_state_does_not_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7)
            first_device = {
                "mac_address": "AA:AA:AA:AA:AA:40",
                "ip_address": "192.168.88.40",
                "source": ["arp"],
                "arp_status": "reachable",
                "arp_state": "online",
            }
            save_snapshot([first_device])
            first_snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            first_snapshot = json.loads(first_snapshot_path.read_text(encoding="utf-8"))[0]

            self.assertIsNotNone(first_snapshot.get("state_changed_at"))
            self.assertIsNotNone(first_snapshot.get("online_since"))
            self.assertIsNone(first_snapshot.get("offline_since"))

            save_snapshot([first_device])
            second_snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            second_snapshot = json.loads(second_snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertEqual(second_snapshot["state_changed_at"], first_snapshot["state_changed_at"])
        self.assertEqual(second_snapshot["online_since"], first_snapshot["online_since"])
        self.assertIsNone(second_snapshot["offline_since"])

    def test_save_snapshot_keeps_offline_session_timestamps_for_unchanged_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7)
            first_device = {
                "mac_address": "AA:AA:AA:AA:AA:41",
                "ip_address": "192.168.88.41",
                "source": ["arp"],
                "arp_status": "failed",
                "arp_state": "offline",
            }
            save_snapshot([first_device])
            first_snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            first_snapshot = json.loads(first_snapshot_path.read_text(encoding="utf-8"))[0]

            self.assertIsNotNone(first_snapshot.get("state_changed_at"))
            self.assertIsNotNone(first_snapshot.get("offline_since"))
            self.assertIsNone(first_snapshot.get("online_since"))

            save_snapshot([first_device])
            second_snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            second_snapshot = json.loads(second_snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertEqual(second_snapshot["state_changed_at"], first_snapshot["state_changed_at"])
        self.assertEqual(second_snapshot["offline_since"], first_snapshot["offline_since"])
        self.assertIsNone(second_snapshot["online_since"])

    def test_save_snapshot_unchanged_online_clears_stale_offline_since(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7)
            initial_snapshot = [
                {
                    "mac_address": "AA:AA:AA:AA:AA:42",
                    "ip_address": "192.168.88.42",
                    "source": ["arp"],
                    "arp_status": "reachable",
                    "arp_state": "online",
                    "state_changed_at": "2026-04-08T16:03:00+00:00",
                    "online_since": "2026-04-08T16:03:00+00:00",
                    "offline_since": "2026-04-08T15:00:00+00:00",
                }
            ]
            (Path(tmp) / "2020-01-01T00-00-00.json").write_text(json.dumps(initial_snapshot), encoding="utf-8")

            save_snapshot(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:42",
                        "ip_address": "192.168.88.42",
                        "source": ["arp"],
                        "arp_status": "reachable",
                        "arp_state": "online",
                    }
                ]
            )
            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertEqual(snapshot["state_changed_at"], "2026-04-08T16:03:00+00:00")
        self.assertEqual(snapshot["online_since"], "2026-04-08T16:03:00+00:00")
        self.assertIsNone(snapshot["offline_since"])

    def test_save_snapshot_adds_null_timestamps_for_unknown_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7)
            save_snapshot(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:43",
                        "ip_address": "192.168.88.43",
                        "source": ["dhcp"],
                        "arp_status": "unknown",
                        "arp_state": "unknown",
                    }
                ]
            )
            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertIn("state_changed_at", snapshot)
        self.assertIn("online_since", snapshot)
        self.assertIn("offline_since", snapshot)
        self.assertIsNone(snapshot["state_changed_at"])
        self.assertIsNone(snapshot["online_since"])
        self.assertIsNone(snapshot["offline_since"])

    def test_save_snapshot_unknown_with_presence_evidence_keeps_previous_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7)
            Path(tmp, "2026-04-08T16-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:44",
                            "ip_address": "192.168.88.44",
                            "source": ["arp"],
                            "arp_status": "reachable",
                            "arp_state": "online",
                            "state_changed_at": "2026-04-08T15:00:00+00:00",
                            "online_since": "2026-04-08T15:00:00+00:00",
                            "offline_since": None,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            save_snapshot(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:44",
                        "ip_address": "192.168.88.44",
                        "source": ["dhcp", "arp"],
                        "arp_status": "delay",
                        "arp_state": "unknown",
                        "bridge_host_present": False,
                    }
                ]
            )
            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertEqual(snapshot["state_changed_at"], "2026-04-08T15:00:00+00:00")
        self.assertEqual(snapshot["online_since"], "2026-04-08T15:00:00+00:00")
        self.assertIsNone(snapshot["offline_since"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
