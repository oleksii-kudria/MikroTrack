from __future__ import annotations

import unittest

from app.api.main import _arp_flag, _dhcp_flag
from app.collector import get_arp_entries, get_dhcp_leases


class _FakeResource:
    def __init__(self, payload):
        self.payload = payload

    def get(self):
        return self.payload


class _FakeClient:
    def __init__(self, resources):
        self._resources = resources

    def get_resource(self, path):
        return _FakeResource(self._resources[path])


class DeviceFlagRenderingTests(unittest.TestCase):
    def test_dhcp_flag_dynamic_and_static(self) -> None:
        self.assertEqual(_dhcp_flag({"dynamic": True}), "D")
        self.assertEqual(_dhcp_flag({"dynamic": False}), "S")
        self.assertEqual(_dhcp_flag({}), "S")

    def test_arp_flag_matrix(self) -> None:
        self.assertEqual(_arp_flag({"dynamic": True, "complete": True}), "DC")
        self.assertEqual(_arp_flag({"dynamic": True, "complete": False}), "D")
        self.assertEqual(_arp_flag({"dynamic": False, "complete": True}), "SC")
        self.assertEqual(_arp_flag({"dynamic": False, "complete": False}), "S")
        self.assertEqual(_arp_flag({"complete": True}), "SC")


class MikroTikCollectorFlagParsingTests(unittest.TestCase):
    def test_collector_keeps_dhcp_dynamic_flag_from_mikrotik(self) -> None:
        client = _FakeClient(
            {
                "/ip/dhcp-server/lease": [
                    {"address": "192.168.88.10", "mac-address": "AA", "dynamic": "true"},
                    {"address": "192.168.88.11", "mac-address": "BB", "dynamic": "false"},
                ]
            }
        )

        leases = get_dhcp_leases(client)

        self.assertTrue(leases[0]["dynamic"])
        self.assertFalse(leases[1]["dynamic"])

    def test_collector_keeps_arp_dynamic_and_complete_flags(self) -> None:
        client = _FakeClient(
            {
                "/ip/arp": [
                    {"address": "192.168.88.10", "mac-address": "AA", "dynamic": "true", "complete": "true"},
                    {"address": "192.168.88.11", "mac-address": "BB", "dynamic": "false", "complete": "false"},
                ]
            }
        )

        arp_entries = get_arp_entries(client)

        self.assertTrue(arp_entries[0]["dynamic"])
        self.assertTrue(arp_entries[0]["complete"])
        self.assertFalse(arp_entries[1]["dynamic"])
        self.assertFalse(arp_entries[1]["complete"])


if __name__ == "__main__":
    unittest.main()
