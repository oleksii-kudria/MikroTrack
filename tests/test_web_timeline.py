from __future__ import annotations

import unittest

from web.timeline_utils import group_events, readable_description


class TimelineFormattingTests(unittest.TestCase):
    def test_readable_description_for_assignment_change(self) -> None:
        description = readable_description(
            {
                "event_type": "DEVICE_IP_ASSIGNMENT_CHANGED",
                "old_value": "dynamic",
                "new_value": "static",
            }
        )
        self.assertEqual(description, "DHCP lease changed from dynamic to static")

    def test_readable_description_for_ip_and_source(self) -> None:
        ip_description = readable_description(
            {
                "event_type": "IP_CHANGED",
                "old_value": "192.168.88.10",
                "new_value": "192.168.88.11",
            }
        )
        source_description = readable_description(
            {
                "event_type": "SOURCE_CHANGED",
                "old_value": "dhcp",
                "new_value": "arp",
            }
        )

        self.assertEqual(ip_description, "IP changed from 192.168.88.10 to 192.168.88.11")
        self.assertEqual(source_description, "Source changed from dhcp to arp")

    def test_readable_description_for_arp_status_and_state_changes(self) -> None:
        status_description = readable_description(
            {
                "event_type": "arp_status_changed",
                "old_value": "reachable",
                "new_value": "permanent",
            }
        )
        state_description = readable_description(
            {
                "event_type": "arp_state_changed",
                "old_value": "online",
                "new_value": "idle",
            }
        )

        self.assertEqual(status_description, "ARP status changed from reachable to permanent")
        self.assertEqual(state_description, "ARP state changed from online to idle")

    def test_groups_events_by_mac_and_timestamp_window(self) -> None:
        events = [
            {
                "timestamp": "2026-04-06T10:00:00",
                "event_type": "IP_CHANGED",
                "mac": "AA:AA",
                "old_value": "1",
                "new_value": "2",
            },
            {
                "timestamp": "2026-04-06T10:00:01",
                "event_type": "SOURCE_CHANGED",
                "mac": "AA:AA",
                "old_value": "dhcp",
                "new_value": "arp",
            },
            {
                "timestamp": "2026-04-06T10:00:03",
                "event_type": "DHCP_ADDED",
                "mac": "AA:AA",
            },
            {
                "timestamp": "2026-04-06T10:00:01",
                "event_type": "IP_CHANGED",
                "mac": "BB:BB",
                "old_value": "3",
                "new_value": "4",
            },
        ]

        grouped = group_events(events)

        self.assertEqual(len(grouped), 3)
        first_group = grouped[0]
        self.assertEqual(first_group["mac"], "AA:AA")
        self.assertEqual(len(first_group["events"]), 2)
        self.assertIn("IP changed from 1 to 2", first_group["changes"])
        self.assertIn("Source changed from dhcp to arp", first_group["changes"])


if __name__ == "__main__":
    unittest.main()
