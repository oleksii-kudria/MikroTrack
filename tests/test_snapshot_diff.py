from __future__ import annotations

import json
import logging
import tempfile
import unittest
from pathlib import Path

from app.persistence import configure_persistence, process_snapshot_diff


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


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
