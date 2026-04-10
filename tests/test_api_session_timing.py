from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from app.api.main import list_devices


class ApiSessionTimingTests(unittest.TestCase):
    def test_api_uses_snapshot_raw_timestamps_without_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PERSISTENCE_PATH"] = tmp
            Path(tmp, "2026-04-08T10-10-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:30",
                            "ip_address": "192.168.88.30",
                            "source": ["arp"],
                            "arp_status": "reachable",
                            "arp_state": "online",
                            "state_changed_at": "2026-04-08T10:01:00+00:00",
                            "online_since": "2026-04-08T10:00:00+00:00",
                            "idle_since": None,
                            "offline_since": None,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            payload = list_devices()
            item = payload["items"][0]

        self.assertEqual(item["status"], "online")
        self.assertEqual(item["state_changed_at"], "2026-04-08T10:01:00+00:00")
        self.assertEqual(item["online_since"], "2026-04-08T10:00:00+00:00")
        self.assertIsNone(item["idle_since"])
        self.assertIsNone(item["offline_since"])

    def test_idle_keeps_online_since_and_uses_idle_since_for_idle_duration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PERSISTENCE_PATH"] = tmp
            Path(tmp, "2026-04-08T10-10-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:31",
                            "ip_address": "192.168.88.31",
                            "source": ["arp"],
                            "arp_status": "stale",
                            "arp_state": "idle",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            Path(tmp, "events.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "timestamp": "2026-04-08T10:00:00+00:00",
                                "event_type": "state_changed",
                                "mac": "AA:AA:AA:AA:AA:31",
                                "old_state": "offline",
                                "new_state": "online",
                            }
                        ),
                        json.dumps(
                            {
                                "timestamp": "2026-04-08T10:05:00+00:00",
                                "event_type": "state_changed",
                                "mac": "AA:AA:AA:AA:AA:31",
                                "old_state": "online",
                                "new_state": "idle",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            payload = list_devices()
            item = payload["items"][0]

        self.assertEqual(item["status"], "idle")
        self.assertEqual(item["online_since"], "2026-04-08T10:00:00+00:00")
        self.assertEqual(item["idle_since"], "2026-04-08T10:05:00+00:00")
        self.assertEqual(item["state_changed_at"], "2026-04-08T10:05:00+00:00")
        self.assertIsNone(item["offline_since"])
        self.assertIsInstance(item["presence_duration_seconds"], int)
        self.assertIsInstance(item["idle_duration_seconds"], int)
        self.assertGreaterEqual(item["presence_duration_seconds"], item["idle_duration_seconds"])

    def test_offline_sets_offline_since_and_clears_online_since(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PERSISTENCE_PATH"] = tmp
            Path(tmp, "2026-04-08T10-10-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:32",
                            "ip_address": "192.168.88.32",
                            "source": ["arp"],
                            "arp_status": "failed",
                            "arp_state": "offline",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            Path(tmp, "events.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "timestamp": "2026-04-08T10:00:00+00:00",
                                "event_type": "state_changed",
                                "mac": "AA:AA:AA:AA:AA:32",
                                "old_state": "offline",
                                "new_state": "online",
                            }
                        ),
                        json.dumps(
                            {
                                "timestamp": "2026-04-08T10:12:00+00:00",
                                "event_type": "state_changed",
                                "mac": "AA:AA:AA:AA:AA:32",
                                "old_state": "idle",
                                "new_state": "offline",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            payload = list_devices()
            item = payload["items"][0]

        self.assertEqual(item["status"], "offline")
        self.assertIsNone(item["online_since"])
        self.assertIsNone(item["idle_since"])
        self.assertEqual(item["offline_since"], "2026-04-08T10:12:00+00:00")
        self.assertEqual(item["state_changed_at"], "2026-04-08T10:12:00+00:00")
        self.assertIsInstance(item["offline_duration_seconds"], int)
        self.assertIsNone(item["presence_duration_seconds"])
        self.assertEqual(item["elapsed_seconds"], item["offline_duration_seconds"])

    def test_api_does_not_fallback_to_snapshot_time_for_missing_timestamps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PERSISTENCE_PATH"] = tmp
            Path(tmp, "2026-04-08T10-10-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:33",
                            "ip_address": "192.168.88.33",
                            "source": ["arp"],
                            "arp_status": "reachable",
                            "arp_state": "online",
                            "state_changed_at": None,
                            "online_since": None,
                            "idle_since": None,
                            "offline_since": None,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            payload = list_devices()
            item = payload["items"][0]

        self.assertIsNone(item["state_changed_at"])
        self.assertIsNone(item["online_since"])
        self.assertIsNone(item["idle_since"])
        self.assertIsNone(item["offline_since"])
        self.assertIsNone(item["presence_duration_seconds"])

    def test_offline_since_overrides_stale_idle_state_in_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PERSISTENCE_PATH"] = tmp
            Path(tmp, "2026-04-08T10-10-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:34",
                            "ip_address": "192.168.88.34",
                            "source": ["arp"],
                            "arp_status": "stale",
                            "arp_state": "idle",
                            "online_since": None,
                            "idle_since": "2026-04-08T10:08:00+00:00",
                            "offline_since": "2026-04-08T10:10:00+00:00",
                            "state_changed_at": "2026-04-08T10:10:00+00:00",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            payload = list_devices()
            item = payload["items"][0]

        self.assertEqual(item["status"], "offline")
        self.assertEqual(item["flags"]["state"], "offline")
        self.assertFalse(item["active"])
        self.assertEqual(item["offline_since"], "2026-04-08T10:10:00+00:00")
        self.assertIsInstance(item["offline_duration_seconds"], int)

    def test_api_exposes_bridge_host_presence_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PERSISTENCE_PATH"] = tmp
            Path(tmp, "2026-04-08T10-10-00.json").write_text(
                json.dumps(
                    [
                        {
                            "mac_address": "AA:AA:AA:AA:AA:35",
                            "ip_address": "",
                            "source": ["bridge_host"],
                            "arp_status": "unknown",
                            "arp_state": "online",
                            "bridge_host_present": True,
                            "has_arp_entry": False,
                            "has_dhcp_lease": False,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            payload = list_devices()
            item = payload["items"][0]

        self.assertTrue(item["flags"]["bridge_host_present"])
        self.assertFalse(item["flags"]["has_arp_entry"])
        self.assertFalse(item["flags"]["has_dhcp_lease"])


if __name__ == "__main__":
    unittest.main()
