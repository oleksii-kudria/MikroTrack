from __future__ import annotations

import unittest

from app.api.main import _arp_flag, _device_state, _dhcp_flag
from app.collector import get_arp_entries, get_dhcp_leases
from app.device_builder import build_devices


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
        self.assertEqual(_dhcp_flag(True, {"dynamic": True}), "D")
        self.assertEqual(_dhcp_flag(True, {"dynamic": False}), "S")
        self.assertIsNone(_dhcp_flag(False, {}))

    def test_arp_flag_matrix(self) -> None:
        self.assertEqual(_arp_flag(True, {"dynamic": True, "complete": True}), "DC")
        self.assertEqual(_arp_flag(True, {"dynamic": True, "complete": False}), "D")
        self.assertEqual(_arp_flag(True, {"dynamic": False, "complete": True}), "SC")
        self.assertEqual(_arp_flag(True, {"dynamic": False, "complete": False}), "S")
        self.assertEqual(_arp_flag(True, {"complete": True}), "SC")
        self.assertIsNone(_arp_flag(False, {"dynamic": False, "complete": False}))

    def test_device_state_uses_arp_status_as_source_of_truth(self) -> None:
        self.assertEqual(_device_state({"arp_status": "failed"}), "offline")
        self.assertEqual(_device_state({"arp_status": "reachable"}), "online")
        self.assertEqual(_device_state({"arp_status": "probe"}), "unknown")
        self.assertEqual(_device_state({"arp_status": "stale"}), "unknown")

    def test_device_state_fallback_for_missing_arp_status(self) -> None:
        self.assertEqual(_device_state({"dhcp_status": "bound"}), "unknown")
        self.assertEqual(_device_state({}), "offline")

    def test_device_state_handles_invalid_or_disabled_entries(self) -> None:
        self.assertEqual(
            _device_state({"arp_status": "reachable", "arp_flags": {"invalid": True}}),
            "offline",
        )
        self.assertEqual(
            _device_state({"arp_status": "reachable", "arp_flags": {"disabled": True}}),
            "offline",
        )


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
        self.assertTrue(leases[0]["has_dhcp_lease"])
        self.assertTrue(leases[0]["dhcp_is_dynamic"])
        self.assertFalse(leases[1]["dhcp_is_dynamic"])

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
        self.assertTrue(arp_entries[0]["has_arp_entry"])

    def test_builder_does_not_fake_dhcp_for_arp_only_device(self) -> None:
        devices = build_devices(
            dhcp=[],
            arp=[
                {
                    "mac_address": "AA",
                    "ip_address": "192.168.88.20",
                    "status": "reachable",
                    "dynamic": True,
                    "complete": True,
                }
            ],
        )

        self.assertEqual(len(devices), 1)
        self.assertFalse(devices[0]["has_dhcp_lease"])
        self.assertIsNone(devices[0]["dhcp_is_dynamic"])
        self.assertEqual(devices[0]["dhcp_flags"], {})
        self.assertTrue(devices[0]["has_arp_entry"])

    def test_builder_marks_no_arp_for_dhcp_only_device(self) -> None:
        devices = build_devices(
            dhcp=[
                {
                    "mac_address": "AA",
                    "ip_address": "192.168.88.10",
                    "status": "bound",
                    "dynamic": False,
                    "has_dhcp_lease": True,
                }
            ],
            arp=[],
        )

        self.assertEqual(len(devices), 1)
        self.assertFalse(devices[0]["has_arp_entry"])

    def test_builder_keeps_non_link_local_dhcp_as_primary(self) -> None:
        devices = build_devices(
            dhcp=[
                {
                    "mac_address": "AA",
                    "ip_address": "192.168.88.10",
                    "status": "bound",
                    "dynamic": True,
                }
            ],
            arp=[
                {
                    "mac_address": "AA",
                    "ip_address": "169.254.10.5",
                    "status": "reachable",
                    "dynamic": True,
                    "complete": True,
                }
            ],
        )

        self.assertEqual(devices[0]["ip_address"], "192.168.88.10")

    def test_builder_prefers_non_failed_non_link_local_arp(self) -> None:
        devices = build_devices(
            dhcp=[],
            arp=[
                {"mac_address": "AA", "ip_address": "169.254.10.5", "status": "reachable", "dynamic": True},
                {"mac_address": "AA", "ip_address": "192.168.88.11", "status": "stale", "dynamic": True},
                {"mac_address": "AA", "ip_address": "192.168.88.12", "status": "failed", "dynamic": True},
            ],
        )

        self.assertEqual(devices[0]["ip_address"], "192.168.88.11")
        self.assertEqual(devices[0]["arp_status"], "stale")
        self.assertEqual(len(devices[0]["arp_secondary"]), 2)

    def test_builder_does_not_use_failed_arp_as_primary_ip(self) -> None:
        devices = build_devices(
            dhcp=[],
            arp=[
                {"mac_address": "AA", "ip_address": "192.168.88.12", "status": "failed", "dynamic": True},
                {"mac_address": "AA", "ip_address": "169.254.10.5", "status": "failed", "dynamic": True},
            ],
        )

        self.assertEqual(devices[0]["ip_address"], "")
        self.assertEqual(devices[0]["arp_status"], "failed")


if __name__ == "__main__":
    unittest.main()
