from __future__ import annotations

import unittest

from app.api.main import _arp_flag, _device_state, _dhcp_flag
from app.collector import get_arp_entries, get_bridge_hosts, get_dhcp_leases, get_interface_macs
from app.device_builder import _is_random_mac, build_devices


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
        self.assertEqual(_device_state({"arp_status": "probe"}), "online")
        self.assertEqual(_device_state({"arp_status": "stale"}), "idle")
        self.assertEqual(_device_state({"arp_status": "permanent", "bridge_host_present": True}), "online")
        self.assertEqual(_device_state({"arp_status": "permanent"}), "unknown")

    def test_device_state_fallback_for_missing_arp_status(self) -> None:
        self.assertEqual(_device_state({"dhcp_status": "bound"}), "unknown")
        self.assertEqual(_device_state({"bridge_host_present": True}), "online")
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

    def test_collector_parses_bridge_hosts(self) -> None:
        client = _FakeClient(
            {
                "/interface/bridge/host": [
                    {"mac-address": "AA", "interface": "bridge1", "last-seen": "12s"},
                ]
            }
        )
        bridge_hosts = get_bridge_hosts(client)
        self.assertEqual(bridge_hosts[0]["mac_address"], "AA")
        self.assertEqual(bridge_hosts[0]["interface"], "bridge1")
        self.assertEqual(bridge_hosts[0]["bridge_host_last_seen"], "12s")
        self.assertTrue(bridge_hosts[0]["bridge_host_present"])

    def test_collector_parses_interface_macs(self) -> None:
        client = _FakeClient(
            {
                "/interface": [{"name": "ether1", "mac-address": "AA"}],
                "/interface/bridge": [{"name": "bridge1", "mac-address": "BB"}],
                "/interface/vlan": [{"name": "vlan10", "mac-address": "CC"}],
                "/interface/wireless": [{"name": "wlan1", "mac-address": "DD"}],
            }
        )
        interface_macs = get_interface_macs(client)
        self.assertEqual(len(interface_macs), 4)
        self.assertEqual(interface_macs[0]["mac_address"], "AA")

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

    def test_builder_exposes_arp_state_for_permanent_records(self) -> None:
        devices = build_devices(
            dhcp=[],
            arp=[
                {"mac_address": "AA", "ip_address": "192.168.88.12", "status": "permanent", "dynamic": False},
            ],
        )

        self.assertEqual(devices[0]["arp_status"], "permanent")
        self.assertEqual(devices[0]["arp_state"], "unknown")
        self.assertIn("PERM", devices[0]["badges"])

    def test_builder_promotes_permanent_to_online_when_bridge_host_present(self) -> None:
        devices = build_devices(
            dhcp=[],
            arp=[
                {"mac_address": "AA", "ip_address": "192.168.88.12", "status": "permanent", "dynamic": False},
            ],
            bridge_hosts=[
                {"mac_address": "AA", "interface": "bridge1", "bridge_host_last_seen": "5s", "bridge_host_present": True}
            ],
        )
        self.assertEqual(devices[0]["arp_state"], "online")
        self.assertTrue(devices[0]["bridge_host_present"])
        self.assertIn("bridge_host", devices[0]["source"])
        self.assertIn("PERM", devices[0]["badges"])

    def test_builder_adds_bridge_badge_for_bridge_only_device(self) -> None:
        devices = build_devices(
            dhcp=[],
            arp=[],
            bridge_hosts=[
                {"mac_address": "AA", "interface": "bridge1", "bridge_host_last_seen": "5s", "bridge_host_present": True}
            ],
        )

        self.assertTrue(devices[0]["bridge_host_present"])
        self.assertFalse(devices[0]["has_arp_entry"])
        self.assertFalse(devices[0]["has_dhcp_lease"])
        self.assertIn("BRIDGE", devices[0]["badges"])

    def test_builder_does_not_add_bridge_badge_when_arp_or_dhcp_exists(self) -> None:
        with_arp = build_devices(
            dhcp=[],
            arp=[{"mac_address": "AA", "ip_address": "192.168.88.10", "status": "reachable", "dynamic": True}],
            bridge_hosts=[
                {"mac_address": "AA", "interface": "bridge1", "bridge_host_last_seen": "5s", "bridge_host_present": True}
            ],
        )
        with_dhcp = build_devices(
            dhcp=[{"mac_address": "BB", "ip_address": "192.168.88.11", "status": "bound", "dynamic": True}],
            arp=[],
            bridge_hosts=[
                {"mac_address": "BB", "interface": "bridge1", "bridge_host_last_seen": "5s", "bridge_host_present": True}
            ],
        )

        self.assertNotIn("BRIDGE", with_arp[0]["badges"])
        self.assertNotIn("BRIDGE", with_dhcp[0]["badges"])

    def test_builder_marks_interface_entity_and_name(self) -> None:
        devices = build_devices(
            dhcp=[],
            arp=[{"mac_address": "AA", "ip_address": "192.168.88.12", "status": "reachable", "dynamic": False}],
            interface_macs=[{"mac_address": "AA", "interface_name": "ether3"}],
        )

        self.assertEqual(devices[0]["entity_type"], "interface")
        self.assertEqual(devices[0]["interface_name"], "ether3")
        self.assertIn("INTERFACE", devices[0]["badges"])

    def test_random_mac_detection_uses_locally_administered_bit(self) -> None:
        self.assertTrue(_is_random_mac("02:11:22:33:44:55"))
        self.assertTrue(_is_random_mac("da:11:22:33:44:55"))
        self.assertFalse(_is_random_mac("00:11:22:33:44:55"))
        self.assertFalse(_is_random_mac("invalid"))

    def test_builder_uses_random_badge_with_highest_priority(self) -> None:
        devices = build_devices(
            dhcp=[
                {
                    "mac_address": "02:11:22:33:44:55",
                    "ip_address": "192.168.88.10",
                    "status": "bound",
                    "dynamic": False,
                }
            ],
            arp=[
                {
                    "mac_address": "02:11:22:33:44:55",
                    "ip_address": "192.168.88.10",
                    "status": "permanent",
                    "dynamic": False,
                    "complete": False,
                }
            ],
        )

        self.assertIn("RANDOM", devices[0]["badges"])
        self.assertNotIn("PERM", devices[0]["badges"])


if __name__ == "__main__":
    unittest.main()
