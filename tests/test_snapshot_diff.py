from __future__ import annotations

import json
import logging
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from app.persistence import _make_json_safe, configure_persistence, process_snapshot_diff, save_snapshot


class SnapshotDiffTests(unittest.TestCase):
    def test_make_json_safe_normalizes_complex_values(self) -> None:
        class CustomObject:
            def __str__(self) -> str:
                return "custom-value"

        payload = {
            "dt": datetime(2026, 4, 10, 12, 30, 45),
            "set_value": {"a", "b"},
            "tuple_value": ("x", "y"),
            "bytes_value": b"hello",
            "nested": [{"raw": b"\xff", "custom": CustomObject()}],
        }

        safe = _make_json_safe(payload)

        self.assertEqual(safe["dt"], "2026-04-10T12:30:45")
        self.assertIsInstance(safe["set_value"], list)
        self.assertCountEqual(safe["set_value"], ["a", "b"])
        self.assertEqual(safe["tuple_value"], ["x", "y"])
        self.assertEqual(safe["bytes_value"], "hello")
        self.assertEqual(safe["nested"][0]["raw"], "b'\\xff'")
        self.assertEqual(safe["nested"][0]["custom"], "custom-value")

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

    def test_extended_diff_field_change_contains_required_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "2026-04-05T23-10-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:99",
                            "ip_address": "192.168.88.10",
                            "host_name": "old-host",
                            "source": ["dhcp", "arp"],
                            "fused_state": "online",
                            "dhcp_flags": {"dynamic": True},
                            "arp_flags": {"dynamic": True},
                            "dhcp_comment": "old-dhcp",
                            "arp_comment": "old-arp",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            configure_persistence(tmp, retention_days=7)
            events = process_snapshot_diff(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:99",
                        "ip_address": "192.168.88.11",
                        "host_name": "new-host",
                        "source": ["arp"],
                        "fused_state": "offline",
                        "dhcp_flags": {"dynamic": False},
                        "arp_flags": {"dynamic": False},
                        "dhcp_comment": "",
                        "arp_comment": "new-arp",
                    }
                ]
            )

        field_changes = [event for event in events if event.get("event_type") == "FIELD_CHANGE"]
        self.assertTrue(field_changes)

        by_field = {str(event["field_name"]): event for event in field_changes}
        self.assertEqual(by_field["state"]["previous_value"], "online")
        self.assertEqual(by_field["state"]["current_value"], "offline")
        self.assertEqual(by_field["ip_address"]["previous_value"], "192.168.88.10")
        self.assertEqual(by_field["ip_address"]["current_value"], "192.168.88.11")
        self.assertEqual(by_field["dhcp_presence"]["previous_value"], True)
        self.assertEqual(by_field["dhcp_presence"]["current_value"], False)
        self.assertEqual(by_field["source"]["previous_value"], "arp+dhcp")
        self.assertEqual(by_field["source"]["current_value"], "arp")
        self.assertEqual(by_field["dhcp_comment"]["previous_value"], "old-dhcp")
        self.assertIsNone(by_field["dhcp_comment"]["current_value"])
        self.assertTrue(all(event.get("device_mac") == "AA:AA:AA:AA:AA:99" for event in field_changes))

    def test_extended_diff_no_field_change_events_when_snapshot_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            device = {
                "mac_address": "AA:AA:AA:AA:AA:98",
                "ip_address": "192.168.88.10",
                "host_name": "same-host",
                "source": ["dhcp", "arp"],
                "fused_state": "online",
                "dhcp_flags": {"dynamic": True},
                "arp_flags": {"dynamic": True},
                "dhcp_comment": "same",
                "arp_comment": "same",
            }
            Path(tmp, "2026-04-05T23-10-00.json").write_text(json.dumps([device]), encoding="utf-8")
            configure_persistence(tmp, retention_days=7)
            events = process_snapshot_diff([dict(device)])

        field_changes = [event for event in events if event.get("event_type") == "FIELD_CHANGE"]
        self.assertEqual(field_changes, [])

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

    def test_diff_persists_events_with_non_json_python_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "2026-04-05T23-10-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:13",
                            "arp_flags": {"complete": True},
                            "source": ["arp"],
                        }
                    ]
                ),
                encoding="utf-8",
            )
            configure_persistence(tmp, retention_days=7)
            current = [
                {
                    "mac_address": "AA:AA:AA:AA:AA:13",
                    "arp_flags": {"complete": True, "labels": {"seen", "test"}},
                    "source": ["arp"],
                }
            ]

            events = process_snapshot_diff(current)

            events_path = Path(tmp) / "events.jsonl"
            persisted_events = [
                json.loads(line)
                for line in events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            self.assertTrue(events)
            self.assertTrue(events_path.exists())
            field_change = next(event for event in persisted_events if event.get("field_name") == "arp_flags")
            labels = field_change["current_value"]["labels"]
            self.assertIsInstance(labels, list)
            self.assertCountEqual(labels, ["seen", "test"])

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
        self.assertEqual(by_type["arp_state_changed"]["new_state"], "idle")

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

    def test_diff_treats_idle_timeout_as_offline_before_reconnect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "2026-04-05T23-10-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:22",
                            "ip_address": "192.168.88.82",
                            "source": ["arp"],
                            "arp_status": "stale",
                            "fused_state": "idle",
                            "state_changed_at": "2026-04-08T10:30:00+00:00",
                            "idle_since": "2026-04-08T10:30:00+00:00",
                            "online_since": "2026-04-08T10:00:00+00:00",
                            "offline_since": None,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            configure_persistence(tmp, retention_days=7, idle_timeout_seconds=900)

            with patch("app.persistence.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime.fromisoformat("2026-04-08T10:50:00+00:00")
                mock_datetime.fromisoformat.side_effect = datetime.fromisoformat

                events = process_snapshot_diff(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:22",
                            "ip_address": "192.168.88.82",
                            "source": ["arp", "bridge_host"],
                            "arp_status": "stale",
                            "fused_state": "online",
                            "bridge_host_present": True,
                        }
                    ]
                )

        by_type = {event["event_type"]: event for event in events}
        self.assertEqual(by_type["arp_state_changed"]["old_state"], "offline")
        self.assertEqual(by_type["arp_state_changed"]["new_state"], "online")
        self.assertEqual(by_type["state_changed"]["old_state"], "offline")
        self.assertEqual(by_type["state_changed"]["new_state"], "online")
        self.assertEqual(by_type["session_started"]["event_type"], "session_started")

    def test_diff_uses_fused_state_for_state_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "2026-04-05T23-10-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:31",
                            "ip_address": "192.168.88.91",
                            "source": ["arp"],
                            "arp_status": "delay",
                            "fused_state": "online",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            configure_persistence(tmp, retention_days=7)

            events = process_snapshot_diff(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:31",
                        "ip_address": "192.168.88.91",
                        "source": ["arp"],
                        "arp_status": "reachable",
                        "fused_state": "online",
                    }
                ]
            )

        event_types = [event["event_type"] for event in events]
        self.assertIn("arp_status_changed", event_types)
        self.assertNotIn("arp_state_changed", event_types)
        self.assertNotIn("state_changed", event_types)

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

    def test_save_snapshot_updates_last_change_when_arp_type_changes_without_state_transition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:4A",
                            "ip_address": "192.168.88.74",
                            "source": ["arp"],
                            "arp_status": "reachable",
                            "arp_state": "online",
                            "arp_type": "dynamic",
                            "state_changed_at": "2026-04-08T10:00:00+00:00",
                            "online_since": "2026-04-08T10:00:00+00:00",
                            "offline_since": None,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            save_snapshot(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:4A",
                        "ip_address": "192.168.88.74",
                        "source": ["arp"],
                        "arp_status": "reachable",
                        "arp_state": "online",
                        "arp_type": "static",
                    }
                ]
            )
            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertNotEqual(snapshot["state_changed_at"], "2026-04-08T10:00:00+00:00")
        self.assertEqual(snapshot["online_since"], "2026-04-08T10:00:00+00:00")
        self.assertIsNone(snapshot["offline_since"])

    def test_save_snapshot_updates_last_change_when_comment_or_badges_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:4B",
                            "ip_address": "192.168.88.75",
                            "source": ["dhcp", "arp"],
                            "arp_status": "reachable",
                            "arp_state": "online",
                            "arp_comment": "",
                            "badges": [],
                            "state_changed_at": "2026-04-08T11:00:00+00:00",
                            "online_since": "2026-04-08T11:00:00+00:00",
                            "offline_since": None,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            save_snapshot(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:4B",
                        "ip_address": "192.168.88.75",
                        "source": ["dhcp", "arp"],
                        "arp_status": "reachable",
                        "arp_state": "online",
                        "arp_comment": "manual",
                        "badges": ["STATIC"],
                    }
                ]
            )
            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertNotEqual(snapshot["state_changed_at"], "2026-04-08T11:00:00+00:00")
        self.assertEqual(snapshot["online_since"], "2026-04-08T11:00:00+00:00")
        self.assertIsNone(snapshot["offline_since"])

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

    def test_save_snapshot_online_restarts_session_when_offline_since_exists(self) -> None:
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

        self.assertNotEqual(snapshot["state_changed_at"], "2026-04-08T16:03:00+00:00")
        self.assertEqual(snapshot["online_since"], snapshot["state_changed_at"])
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

    def test_save_snapshot_unknown_with_presence_evidence_preserves_last_change_on_source_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
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

    def test_save_snapshot_bridge_host_loss_downgrades_online_to_idle_and_emits_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:4A",
                            "ip_address": "192.168.88.74",
                            "source": ["dhcp", "arp", "bridge_host"],
                            "arp_status": "permanent",
                            "arp_state": "online",
                            "fused_state": "online",
                            "bridge_host_present": True,
                            "state_changed_at": "2026-04-08T15:00:00+00:00",
                            "online_since": "2026-04-08T15:00:00+00:00",
                            "idle_since": None,
                            "offline_since": None,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            save_snapshot(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:4A",
                        "ip_address": "192.168.88.74",
                        "source": ["dhcp", "arp"],
                        "arp_status": "permanent",
                        "arp_state": "unknown",
                        "fused_state": "unknown",
                        "bridge_host_present": False,
                    }
                ]
            )
            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]
            events = [
                json.loads(line)
                for line in (Path(tmp) / "events.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        self.assertEqual(snapshot["fused_state"], "idle")
        self.assertEqual(snapshot["arp_state"], "idle")
        self.assertEqual(snapshot["online_since"], "2026-04-08T15:00:00+00:00")
        self.assertIsNotNone(snapshot["idle_since"])
        self.assertIsNone(snapshot["offline_since"])

        by_type = {event["event_type"]: event for event in events}
        self.assertEqual(by_type["state_changed"]["old_state"], "online")
        self.assertEqual(by_type["state_changed"]["new_state"], "idle")
        self.assertIn("device_idle", by_type)

    def test_save_snapshot_bridge_host_reconnect_forces_online_and_clears_idle_since(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7, idle_timeout_seconds=900)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:4B",
                            "ip_address": "192.168.88.75",
                            "source": ["arp"],
                            "arp_status": "stale",
                            "arp_state": "idle",
                            "fused_state": "idle",
                            "bridge_host_present": False,
                            "state_changed_at": "2026-04-08T15:10:00+00:00",
                            "online_since": "2026-04-08T15:00:00+00:00",
                            "idle_since": "2026-04-08T15:10:00+00:00",
                            "offline_since": None,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            with patch("app.persistence._iso_timestamp", return_value="2026-04-08T15:20:00+00:00"):
                save_snapshot(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:4B",
                            "ip_address": "192.168.88.75",
                            "source": ["arp", "bridge_host"],
                            "arp_status": "stale",
                            "arp_state": "idle",
                            "fused_state": "idle",
                            "bridge_host_present": True,
                        }
                    ]
                )

            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertEqual(snapshot["fused_state"], "online")
        self.assertEqual(snapshot["arp_state"], "online")
        self.assertEqual(snapshot["state_changed_at"], "2026-04-08T15:20:00+00:00")
        self.assertEqual(snapshot["online_since"], "2026-04-08T15:00:00+00:00")
        self.assertIsNone(snapshot["idle_since"])
        self.assertIsNone(snapshot["offline_since"])

    def test_save_snapshot_bridge_host_reconnect_after_idle_timeout_starts_new_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7, idle_timeout_seconds=900)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:4C",
                            "ip_address": "192.168.88.76",
                            "source": ["arp"],
                            "arp_status": "stale",
                            "arp_state": "idle",
                            "fused_state": "idle",
                            "bridge_host_present": False,
                            "state_changed_at": "2026-04-08T15:10:00+00:00",
                            "online_since": "2026-04-08T15:00:00+00:00",
                            "idle_since": "2026-04-08T15:10:00+00:00",
                            "offline_since": None,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            with patch("app.persistence._iso_timestamp", return_value="2026-04-08T15:30:00+00:00"):
                save_snapshot(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:4C",
                            "ip_address": "192.168.88.76",
                            "source": ["arp", "bridge_host"],
                            "arp_status": "stale",
                            "arp_state": "idle",
                            "fused_state": "idle",
                            "bridge_host_present": True,
                        }
                    ]
                )

            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertEqual(snapshot["fused_state"], "online")
        self.assertEqual(snapshot["arp_state"], "online")
        self.assertEqual(snapshot["state_changed_at"], "2026-04-08T15:30:00+00:00")
        self.assertEqual(snapshot["online_since"], "2026-04-08T15:30:00+00:00")
        self.assertIsNone(snapshot["idle_since"])
        self.assertIsNone(snapshot["offline_since"])

    def test_save_snapshot_preserves_identity_for_mac_with_different_letter_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:50",
                            "ip_address": "192.168.88.50",
                            "source": ["arp"],
                            "arp_status": "reachable",
                            "arp_state": "online",
                            "state_changed_at": "2026-04-08T10:00:00+00:00",
                            "online_since": "2026-04-08T10:00:00+00:00",
                            "offline_since": None,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            save_snapshot(
                [
                    {
                        "mac_address": "aa:aa:aa:aa:aa:50",
                        "ip_address": "192.168.88.50",
                        "source": ["dhcp", "arp"],
                        "arp_status": "reachable",
                        "arp_state": "online",
                    }
                ]
            )
            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertEqual(snapshot["state_changed_at"], "2026-04-08T10:00:00+00:00")
        self.assertEqual(snapshot["online_since"], "2026-04-08T10:00:00+00:00")
        self.assertIsNone(snapshot["offline_since"])

    def test_save_snapshot_unchanged_online_initializes_missing_session_timestamps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:45",
                            "ip_address": "192.168.88.45",
                            "source": ["dhcp", "arp", "bridge_host"],
                            "arp_status": "reachable",
                            "arp_state": "online",
                            "state_changed_at": None,
                            "online_since": None,
                            "offline_since": None,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            save_snapshot(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:45",
                        "ip_address": "192.168.88.45",
                        "source": ["dhcp", "arp", "bridge_host"],
                        "arp_status": "reachable",
                        "arp_state": "online",
                        "bridge_host_present": True,
                    }
                ]
            )
            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertIsNotNone(snapshot["state_changed_at"])
        self.assertIsNotNone(snapshot["online_since"])
        self.assertIsNone(snapshot["offline_since"])

    def test_save_snapshot_unchanged_offline_initializes_missing_session_timestamps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:46",
                            "ip_address": "192.168.88.46",
                            "source": ["dhcp", "arp", "bridge_host"],
                            "arp_status": "failed",
                            "arp_state": "offline",
                            "state_changed_at": None,
                            "online_since": None,
                            "offline_since": None,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            save_snapshot(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:46",
                        "ip_address": "192.168.88.46",
                        "source": ["dhcp", "arp", "bridge_host"],
                        "arp_status": "failed",
                        "arp_state": "offline",
                        "bridge_host_present": False,
                    }
                ]
            )
            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertIsNotNone(snapshot["state_changed_at"])
        self.assertIsNotNone(snapshot["offline_since"])
        self.assertIsNone(snapshot["online_since"])

    def test_save_snapshot_offline_to_online_resets_session_timestamps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "B0:E4:5C:FD:BB:98",
                            "ip_address": "192.168.88.98",
                            "source": ["arp"],
                            "arp_status": "failed",
                            "arp_state": "offline",
                            "state_changed_at": "2026-04-08T10:00:00+00:00",
                            "online_since": None,
                            "offline_since": "2026-04-08T10:00:00+00:00",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            save_snapshot(
                [
                    {
                        "mac_address": "B0:E4:5C:FD:BB:98",
                        "ip_address": "192.168.88.98",
                        "source": ["arp"],
                        "arp_status": "reachable",
                        "arp_state": "online",
                        # stale value that must not be preserved on real transition
                        "offline_since": "2026-04-08T10:00:00+00:00",
                    }
                ]
            )
            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertIsNotNone(snapshot["state_changed_at"])
        self.assertEqual(snapshot["online_since"], snapshot["state_changed_at"])
        self.assertIsNone(snapshot["offline_since"])

    def test_save_snapshot_offline_since_forces_previous_effective_offline_on_reconnect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "B0:E4:5C:FD:BB:99",
                            "ip_address": "192.168.88.99",
                            "source": ["arp"],
                            # stale derived state from old session
                            "arp_status": "stale",
                            "arp_state": "idle",
                            "state_changed_at": "2026-04-08T10:00:00+00:00",
                            "online_since": "2026-04-08T09:00:00+00:00",
                            "idle_since": "2026-04-08T09:45:00+00:00",
                            # explicit marker that previous session is already offline
                            "offline_since": "2026-04-08T10:00:00+00:00",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertLogs("mikrotrack", level="INFO") as logs:
                save_snapshot(
                    [
                        {
                            "mac_address": "B0:E4:5C:FD:BB:99",
                            "ip_address": "192.168.88.99",
                            "source": ["arp"],
                            "arp_status": "reachable",
                            "arp_state": "online",
                        }
                    ]
                )
            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        output = "\n".join(logs.output)
        self.assertIn("treating previous effective state as offline", output)
        self.assertIn("starting new online session", output)
        self.assertIn("Session timer reset", output)
        self.assertEqual(snapshot["online_since"], snapshot["state_changed_at"])
        self.assertIsNone(snapshot["idle_since"])
        self.assertIsNone(snapshot["offline_since"])

    def test_save_snapshot_perm_reconnect_uses_offline_since_as_single_source_of_truth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "B0:E4:5C:FD:BB:9A",
                            "ip_address": "192.168.88.101",
                            "source": ["arp"],
                            "arp_status": "permanent",
                            "arp_state": "permanent",
                            "bridge_host_present": False,
                            "state_changed_at": "2026-04-08T10:00:00+00:00",
                            # stale leaked value from an old online session
                            "online_since": "2026-04-08T12:00:00+00:00",
                            "idle_since": "2026-04-08T12:00:00+00:00",
                            # true session boundary marker from the most recent disconnect
                            "offline_since": "2026-04-08T10:30:00+00:00",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertLogs("mikrotrack", level="INFO") as logs:
                save_snapshot(
                    [
                        {
                            "mac_address": "B0:E4:5C:FD:BB:9A",
                            "ip_address": "192.168.88.101",
                            "source": ["arp"],
                            "arp_status": "reachable",
                            "arp_state": "online",
                        }
                    ]
                )
            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]


        output = "\n".join(logs.output)
        self.assertIn("treating previous effective state as offline", output)
        self.assertIn("starting new online session", output)
        self.assertIn("Session timer reset", output)
        self.assertEqual(snapshot["arp_state"], "online")
        self.assertEqual(snapshot["online_since"], snapshot["state_changed_at"])
        self.assertIsNone(snapshot["idle_since"])
        self.assertIsNone(snapshot["offline_since"])

    def test_save_snapshot_bridge_host_reconnect_after_offline_starts_new_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "B0:E4:5C:FD:BB:A0",
                            "ip_address": "192.168.88.100",
                            "source": ["arp"],
                            "arp_status": "failed",
                            "arp_state": "offline",
                            "bridge_host_present": False,
                            "state_changed_at": "2026-04-08T10:00:00+00:00",
                            "online_since": None,
                            "idle_since": None,
                            "offline_since": "2026-04-08T10:00:00+00:00",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            save_snapshot(
                [
                    {
                        "mac_address": "B0:E4:5C:FD:BB:A0",
                        "ip_address": "192.168.88.100",
                        "source": ["arp", "bridge_host"],
                        "arp_status": "unknown",
                        "arp_state": "online",
                        "bridge_host_present": True,
                    }
                ]
            )
            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertEqual(snapshot["fused_state"], "online")
        self.assertTrue(snapshot["bridge_host_present"])
        self.assertEqual(snapshot["online_since"], snapshot["state_changed_at"])
        self.assertIsNone(snapshot["idle_since"])
        self.assertIsNone(snapshot["offline_since"])

    def test_save_snapshot_online_to_offline_resets_session_timestamps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:47",
                            "ip_address": "192.168.88.47",
                            "source": ["arp"],
                            "arp_status": "reachable",
                            "arp_state": "online",
                            "state_changed_at": "2026-04-08T10:00:00+00:00",
                            "online_since": "2026-04-08T10:00:00+00:00",
                            "offline_since": None,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            save_snapshot(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:47",
                        "ip_address": "192.168.88.47",
                        "source": ["arp"],
                        "arp_status": "failed",
                        "arp_state": "offline",
                        # stale value that must not be preserved on real transition
                        "online_since": "2026-04-08T10:00:00+00:00",
                    }
                ]
            )
            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertIsNotNone(snapshot["state_changed_at"])
        self.assertEqual(snapshot["offline_since"], snapshot["state_changed_at"])
        self.assertIsNone(snapshot["online_since"])

    def test_save_snapshot_online_idle_online_manages_idle_since(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:48",
                            "ip_address": "192.168.88.48",
                            "source": ["arp"],
                            "arp_status": "reachable",
                            "arp_state": "online",
                            "state_changed_at": "2026-04-08T10:00:00+00:00",
                            "online_since": "2026-04-08T10:00:00+00:00",
                            "idle_since": None,
                            "offline_since": None,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            save_snapshot(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:48",
                        "ip_address": "192.168.88.48",
                        "source": ["arp"],
                        "arp_status": "stale",
                        "arp_state": "idle",
                    }
                ]
            )
            idle_snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            idle_snapshot = json.loads(idle_snapshot_path.read_text(encoding="utf-8"))[0]

            save_snapshot(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:48",
                        "ip_address": "192.168.88.48",
                        "source": ["arp"],
                        "arp_status": "reachable",
                        "arp_state": "online",
                    }
                ]
            )
            online_snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            online_snapshot = json.loads(online_snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertEqual(idle_snapshot["online_since"], "2026-04-08T10:00:00+00:00")
        self.assertIsNotNone(idle_snapshot["idle_since"])
        self.assertIsNone(idle_snapshot["offline_since"])
        self.assertEqual(online_snapshot["online_since"], "2026-04-08T10:00:00+00:00")
        self.assertIsNone(online_snapshot["idle_since"])
        self.assertIsNone(online_snapshot["offline_since"])

    def test_save_snapshot_idle_timeout_forces_offline_transition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7, idle_timeout_seconds=900)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:49",
                            "ip_address": "192.168.88.49",
                            "source": ["arp"],
                            "arp_status": "stale",
                            "arp_state": "idle",
                            "state_changed_at": "2026-04-08T10:05:00+00:00",
                            "online_since": "2026-04-08T10:00:00+00:00",
                            "idle_since": "2026-04-08T10:05:00+00:00",
                            "offline_since": None,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            with patch("app.persistence._iso_timestamp", return_value="2026-04-08T10:21:00+00:00"):
                save_snapshot(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:49",
                            "ip_address": "192.168.88.49",
                            "source": ["arp"],
                            "arp_status": "stale",
                            "arp_state": "idle",
                        }
                    ]
                )

            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertEqual(snapshot["arp_state"], "offline")
        self.assertEqual(snapshot["state_changed_at"], "2026-04-08T10:21:00+00:00")
        self.assertIsNone(snapshot["online_since"])
        self.assertIsNone(snapshot["idle_since"])
        self.assertEqual(snapshot["offline_since"], "2026-04-08T10:21:00+00:00")

    def test_save_snapshot_idle_timeout_forces_offline_for_permanent_without_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7, idle_timeout_seconds=900)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:59",
                            "ip_address": "192.168.88.59",
                            "source": ["arp"],
                            "arp_status": "stale",
                            "fused_state": "idle",
                            "bridge_host_present": False,
                            "state_changed_at": "2026-04-08T10:05:00+00:00",
                            "online_since": "2026-04-08T10:00:00+00:00",
                            "idle_since": "2026-04-08T10:05:00+00:00",
                            "offline_since": None,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            with patch("app.persistence._iso_timestamp", return_value="2026-04-08T10:21:00+00:00"):
                save_snapshot(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:59",
                            "ip_address": "192.168.88.59",
                            "source": ["arp"],
                            "arp_status": "permanent",
                            "arp_state": "permanent",
                            "fused_state": "unknown",
                            "bridge_host_present": False,
                        }
                    ]
                )

            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertEqual(snapshot["fused_state"], "offline")
        self.assertEqual(snapshot["arp_state"], "offline")
        self.assertEqual(snapshot["state_changed_at"], "2026-04-08T10:21:00+00:00")
        self.assertIsNone(snapshot["online_since"])
        self.assertIsNone(snapshot["idle_since"])
        self.assertEqual(snapshot["offline_since"], "2026-04-08T10:21:00+00:00")

    def test_diff_treats_permanent_as_generic_presence_without_special_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "2026-04-08T10-05-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:5A",
                            "ip_address": "192.168.88.90",
                            "source": ["arp"],
                            "arp_status": "stale",
                            "fused_state": "idle",
                            "bridge_host_present": False,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            configure_persistence(tmp, retention_days=7, idle_timeout_seconds=900)

            events = process_snapshot_diff(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:5A",
                        "ip_address": "192.168.88.90",
                        "source": ["arp"],
                        "arp_status": "permanent",
                        "arp_state": "permanent",
                        "fused_state": "offline",
                        "bridge_host_present": False,
                    }
                ]
            )

        by_type = {event["event_type"]: event for event in events}
        self.assertIn("state_changed", by_type)
        self.assertIn("device_offline", by_type)
        self.assertEqual(by_type["state_changed"]["old_state"], "idle")
        self.assertEqual(by_type["state_changed"]["new_state"], "offline")

    def test_save_snapshot_perm_offline_idle_loop_does_not_reconnect_without_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7, idle_timeout_seconds=900)
            Path(tmp, "2026-04-08T10-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:6A",
                            "ip_address": "192.168.88.106",
                            "source": ["arp"],
                            "arp_status": "permanent",
                            "arp_state": "offline",
                            "fused_state": "offline",
                            "status": "offline",
                            "active": False,
                            "bridge_host_present": False,
                            "state_changed_at": "2026-04-08T10:00:00+00:00",
                            "online_since": None,
                            "idle_since": None,
                            "offline_since": "2026-04-08T10:00:00+00:00",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            with patch("app.persistence._iso_timestamp", return_value="2026-04-08T10:10:00+00:00"):
                save_snapshot(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:6A",
                            "ip_address": "192.168.88.106",
                            "source": ["arp"],
                            "arp_status": "permanent",
                            "arp_state": "offline",
                            "fused_state": "idle",
                            "bridge_host_present": False,
                            "status": "online",
                            "active": True,
                        }
                    ]
                )

            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertEqual(snapshot["fused_state"], "offline")
        self.assertEqual(snapshot["arp_state"], "offline")
        self.assertEqual(snapshot["status"], "offline")
        self.assertFalse(snapshot["active"])
        self.assertEqual(snapshot["offline_since"], "2026-04-08T10:00:00+00:00")
        self.assertIsNone(snapshot["online_since"])

    def test_save_snapshot_perm_offline_reconnects_when_bridge_host_returns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7, idle_timeout_seconds=900)
            Path(tmp, "2026-04-08T10-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:6B",
                            "ip_address": "192.168.88.107",
                            "source": ["arp"],
                            "arp_status": "permanent",
                            "arp_state": "offline",
                            "fused_state": "offline",
                            "bridge_host_present": False,
                            "state_changed_at": "2026-04-08T10:00:00+00:00",
                            "online_since": None,
                            "idle_since": None,
                            "offline_since": "2026-04-08T10:00:00+00:00",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            with patch("app.persistence._iso_timestamp", return_value="2026-04-08T10:15:00+00:00"):
                save_snapshot(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:6B",
                            "ip_address": "192.168.88.107",
                            "source": ["arp", "bridge_host"],
                            "arp_status": "permanent",
                            "arp_state": "idle",
                            "fused_state": "idle",
                            "bridge_host_present": True,
                        }
                    ]
                )

            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertEqual(snapshot["fused_state"], "online")
        self.assertEqual(snapshot["arp_state"], "online")
        self.assertEqual(snapshot["online_since"], "2026-04-08T10:15:00+00:00")
        self.assertIsNone(snapshot["offline_since"])

    def test_save_snapshot_idle_within_timeout_preserves_online_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7, idle_timeout_seconds=900)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:50",
                            "ip_address": "192.168.88.50",
                            "source": ["arp"],
                            "arp_status": "stale",
                            "arp_state": "idle",
                            "state_changed_at": "2026-04-08T10:05:00+00:00",
                            "online_since": "2026-04-08T10:00:00+00:00",
                            "idle_since": "2026-04-08T10:05:00+00:00",
                            "offline_since": None,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            with patch("app.persistence._iso_timestamp", return_value="2026-04-08T10:19:00+00:00"):
                save_snapshot(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:50",
                            "ip_address": "192.168.88.50",
                            "source": ["arp"],
                            "arp_status": "stale",
                            "arp_state": "idle",
                        }
                    ]
                )

            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertEqual(snapshot["arp_state"], "idle")
        self.assertEqual(snapshot["online_since"], "2026-04-08T10:00:00+00:00")
        self.assertEqual(snapshot["idle_since"], "2026-04-08T10:05:00+00:00")
        self.assertIsNone(snapshot["offline_since"])

    def test_save_snapshot_previous_offline_with_idle_probe_stays_offline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7, idle_timeout_seconds=900)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:51",
                            "ip_address": "192.168.88.51",
                            "source": ["arp"],
                            "arp_status": "failed",
                            "arp_state": "offline",
                            "state_changed_at": "2026-04-08T10:21:00+00:00",
                            "online_since": None,
                            "idle_since": None,
                            "offline_since": "2026-04-08T10:21:00+00:00",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            with patch("app.persistence._iso_timestamp", return_value="2026-04-08T10:24:00+00:00"):
                save_snapshot(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:51",
                            "ip_address": "192.168.88.51",
                            "source": ["arp"],
                            "arp_status": "stale",
                            "arp_state": "idle",
                        }
                    ]
                )

            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertEqual(snapshot["arp_state"], "offline")
        self.assertEqual(snapshot["state_changed_at"], "2026-04-08T10:21:00+00:00")
        self.assertIsNone(snapshot["online_since"])
        self.assertIsNone(snapshot["idle_since"])
        self.assertEqual(snapshot["offline_since"], "2026-04-08T10:21:00+00:00")

    def test_save_snapshot_perm_offline_idle_timeout_does_not_restart_offline_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7, idle_timeout_seconds=900)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:6C",
                            "ip_address": "192.168.88.108",
                            "source": ["arp"],
                            "arp_status": "permanent",
                            "arp_state": "idle",
                            "fused_state": "idle",
                            "bridge_host_present": False,
                            "state_changed_at": "2026-04-08T10:00:00+00:00",
                            "online_since": None,
                            "idle_since": None,
                            "offline_since": "2026-04-08T10:00:00+00:00",
                            "last_seen": "2026-04-08T09:20:00+00:00",
                            "last_seen_by_mac": "2026-04-08T09:20:00+00:00",
                            "active": False,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            with patch("app.persistence._iso_timestamp", return_value="2026-04-08T10:30:00+00:00"):
                save_snapshot(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:6C",
                            "ip_address": "192.168.88.108",
                            "source": ["arp"],
                            "arp_status": "permanent",
                            "arp_state": "idle",
                            "fused_state": "idle",
                            "bridge_host_present": False,
                            "active": False,
                        }
                    ]
                )

            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertEqual(snapshot["arp_state"], "offline")
        self.assertEqual(snapshot["fused_state"], "offline")
        self.assertEqual(snapshot["state_changed_at"], "2026-04-08T10:00:00+00:00")
        self.assertEqual(snapshot["offline_since"], "2026-04-08T10:00:00+00:00")

    def test_save_snapshot_preserves_last_known_ip_and_hostname_for_offline_device(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7, idle_timeout_seconds=900)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:7D",
                            "ip_address": "192.168.88.120",
                            "host_name": "iphone",
                            "source": ["dhcp", "arp"],
                            "arp_status": "failed",
                            "arp_state": "offline",
                            "fused_state": "offline",
                            "offline_since": "2026-04-08T10:00:00+00:00",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            save_snapshot(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:7D",
                        "ip_address": "",
                        "host_name": "",
                        "source": ["arp"],
                        "arp_status": "failed",
                        "arp_state": "offline",
                        "fused_state": "offline",
                    }
                ]
            )

            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertEqual(snapshot["ip_address"], "192.168.88.120")
        self.assertEqual(snapshot["host_name"], "iphone")
        self.assertEqual(snapshot["last_known_ip"], "192.168.88.120")
        self.assertEqual(snapshot["last_known_hostname"], "iphone")
        self.assertTrue(snapshot["ip_is_stale"])
        self.assertTrue(snapshot["hostname_is_stale"])
        self.assertTrue(snapshot["data_is_stale"])

    def test_save_snapshot_clears_stale_flags_after_reconnect_with_fresh_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configure_persistence(tmp, retention_days=7, idle_timeout_seconds=900)
            Path(tmp, "2020-01-01T00-00-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:7E",
                            "ip_address": "192.168.88.121",
                            "host_name": "iphone-old",
                            "last_known_ip": "192.168.88.121",
                            "last_known_hostname": "iphone-old",
                            "ip_is_stale": True,
                            "hostname_is_stale": True,
                            "data_is_stale": True,
                            "source": ["arp"],
                            "arp_status": "failed",
                            "arp_state": "offline",
                            "fused_state": "offline",
                            "offline_since": "2026-04-08T10:00:00+00:00",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            save_snapshot(
                [
                    {
                        "mac_address": "AA:AA:AA:AA:AA:7E",
                        "ip_address": "192.168.88.122",
                        "host_name": "iphone-new",
                        "source": ["dhcp", "arp", "bridge_host"],
                        "bridge_host_present": True,
                        "arp_status": "reachable",
                        "arp_state": "online",
                        "fused_state": "online",
                    }
                ]
            )

            snapshot_path = sorted(Path(tmp).glob("*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))[0]

        self.assertFalse(snapshot["ip_is_stale"])
        self.assertFalse(snapshot["hostname_is_stale"])
        self.assertFalse(snapshot["data_is_stale"])
        self.assertEqual(snapshot["last_known_ip"], "192.168.88.122")
        self.assertEqual(snapshot["last_known_hostname"], "iphone-new")

    def test_diff_uses_mac_fallback_and_persists_events_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "2026-04-05T23-10-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac": "6E:7B:C9:CC:5A:81",
                            "source": ["arp"],
                            "fused_state": "online",
                            "arp_state": "online",
                            "arp_status": "reachable",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            configure_persistence(tmp, retention_days=7)
            events = process_snapshot_diff(
                [
                    {
                        "mac": "6E:7B:C9:CC:5A:81",
                        "source": ["arp"],
                        "fused_state": "offline",
                        "arp_state": "offline",
                        "arp_status": "failed",
                    }
                ]
            )

            events_path = Path(tmp) / "events.jsonl"
            self.assertTrue(events_path.exists())
            persisted_events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line]

        self.assertEqual(events, persisted_events)
        self.assertTrue(any(event.get("event_type") == "FIELD_CHANGE" and event.get("field_name") == "state" for event in events))

    def test_diff_prefers_mac_address_when_both_mac_keys_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "2026-04-05T23-10-00.json").write_text(
                json.dumps([{"mac_address": "AA:AA:AA:AA:AA:01", "mac": "BB:BB:BB:BB:BB:02", "ip_address": "192.168.88.10"}]),
                encoding="utf-8",
            )
            configure_persistence(tmp, retention_days=7)
            events = process_snapshot_diff(
                [{"mac_address": "AA:AA:AA:AA:AA:01", "mac": "CC:CC:CC:CC:CC:03", "ip_address": "192.168.88.11"}]
            )

        self.assertTrue(any(event.get("event_type") == "IP_CHANGED" and event.get("mac") == "AA:AA:AA:AA:AA:01" for event in events))

    def test_index_logs_warning_when_device_has_no_mac_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "2026-04-05T23-10-00.json").write_text(
                json.dumps([{"ip_address": "192.168.88.10"}]),
                encoding="utf-8",
            )
            configure_persistence(tmp, retention_days=7)
            with self.assertLogs("mikrotrack", level="WARNING") as logs:
                events = process_snapshot_diff([{"ip_address": "192.168.88.11"}])

        self.assertEqual(events, [])
        self.assertIn("persistence: skipping device without MAC key", "\n".join(logs.output))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
