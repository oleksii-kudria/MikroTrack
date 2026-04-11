from __future__ import annotations

import logging

from app.persistence import _index_devices_by_mac


def test_index_devices_by_mac_supports_mac_address_field() -> None:
    devices = [{"mac_address": "aa:bb:cc:dd:ee:01", "ip_address": "192.168.88.10"}]

    indexed = _index_devices_by_mac(devices)

    assert "AA:BB:CC:DD:EE:01" in indexed
    assert indexed["AA:BB:CC:DD:EE:01"]["ip_address"] == "192.168.88.10"


def test_index_devices_by_mac_supports_legacy_mac_field() -> None:
    devices = [{"mac": "aa:bb:cc:dd:ee:02", "host_name": "legacy-host"}]

    indexed = _index_devices_by_mac(devices)

    assert "AA:BB:CC:DD:EE:02" in indexed
    assert indexed["AA:BB:CC:DD:EE:02"]["host_name"] == "legacy-host"


def test_index_devices_by_mac_prefers_mac_address_when_both_present() -> None:
    devices = [
        {
            "mac_address": "aa:bb:cc:dd:ee:03",
            "mac": "ff:ff:ff:ff:ff:ff",
            "ip_address": "192.168.88.33",
        }
    ]

    indexed = _index_devices_by_mac(devices)

    assert "AA:BB:CC:DD:EE:03" in indexed
    assert "FF:FF:FF:FF:FF:FF" not in indexed


def test_index_devices_by_mac_logs_warning_when_mac_missing(caplog) -> None:
    caplog.set_level(logging.WARNING, logger="mikrotrack")

    indexed = _index_devices_by_mac([{"ip_address": "192.168.88.50"}])

    assert indexed == {}
    assert "persistence: skipping device without MAC key" in caplog.text
