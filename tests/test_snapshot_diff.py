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
                process_snapshot_diff([])

        output = "\n".join(logs.output)
        self.assertIn("[DIFF_SKIPPED] No previous snapshot found", output)

    def test_diff_events_for_new_changed_and_removed_devices(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            snapshot_path = Path(tmp) / "2026-04-05T23-10-00.json"
            snapshot_path.write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:01",
                            "ip_address": "192.168.88.10",
                            "host_name": "old-host",
                        },
                        {
                            "mac_address": "AA:AA:AA:AA:AA:02",
                            "ip_address": "192.168.88.20",
                            "host_name": "to-be-removed",
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
                },
                {
                    "mac_address": "AA:AA:AA:AA:AA:03",
                    "ip_address": "192.168.88.30",
                    "host_name": "new-device",
                },
            ]

            with self.assertLogs("mikrotrack", level="DEBUG") as logs:
                process_snapshot_diff(current)

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

    def test_diff_error_for_invalid_snapshot_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            snapshot_path = Path(tmp) / "2026-04-05T23-10-00.json"
            snapshot_path.write_text("{\"invalid\": true}", encoding="utf-8")

            configure_persistence(tmp, retention_days=7)
            with self.assertLogs("mikrotrack", level="ERROR") as logs:
                process_snapshot_diff([])

        output = "\n".join(logs.output)
        self.assertIn("[DIFF_ERROR] Failed to process snapshots", output)
        self.assertIn("Recommendation: Verify snapshot format and integrity", output)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
