from __future__ import annotations

from copy import deepcopy

from web.ui_regression import (
    apply_display_mode,
    apply_filters,
    build_summary,
    cycle_direction,
    sort_items,
    validate_contract_fields,
)


def _device(mac: str, **overrides):
    base = {
        "mac": mac,
        "ip": "192.168.88.10",
        "hostname": f"host-{mac[-2:]}",
        "status": "online",
        "state_changed_at": "2026-04-10T10:00:00+00:00",
        "online_since": "2026-04-10T10:00:00+00:00",
        "idle_since": None,
        "offline_since": None,
        "entity_type": "client",
        "interface_name": None,
        "flags": {"has_arp_entry": True, "bridge_host_present": False, "arp_flag": "", "dhcp_flag": "D"},
        "last_known_ip": "192.168.88.10",
        "last_known_hostname": "known-host",
        "ip_is_stale": False,
        "hostname_is_stale": False,
        "data_is_stale": False,
    }
    base.update(overrides)
    return base


def test_default_sorting_respects_status_order_and_unknown_alphabetical_only():
    items = [
        _device("AA:01", status="unknown", hostname="zulu", online_since=None, idle_since=None, offline_since=None),
        _device("AA:02", status="online", online_since="2026-04-10T11:00:00+00:00"),
        _device("AA:03", status="offline", offline_since="2026-04-10T09:00:00+00:00", online_since=None),
        _device("AA:04", status="idle", idle_since="2026-04-10T10:30:00+00:00", online_since="2026-04-10T09:00:00+00:00"),
        _device("AA:05", status="unknown", hostname="alpha", state_changed_at="2026-04-11T00:00:00+00:00"),
    ]

    sorted_items = sort_items(items)
    assert [row["status"] for row in sorted_items] == ["online", "idle", "offline", "unknown", "unknown"]
    assert [row["hostname"] for row in sorted_items[-2:]] == ["alpha", "zulu"]


def test_explicit_single_column_sorting_and_direction_cycle():
    items = [
        _device("AA:01", hostname="beta", ip="192.168.88.25", status="idle", idle_since="2026-04-10T10:10:00+00:00"),
        _device("AA:02", hostname="alpha", ip="192.168.88.2", status="online", online_since="2026-04-10T10:20:00+00:00"),
        _device("AA:03", hostname="gamma", ip="192.168.88.15", status="offline", offline_since="2026-04-10T10:05:00+00:00", online_since=None),
    ]

    assert [row["hostname"] for row in sort_items(items, sort_key="hostname", direction="asc")] == ["alpha", "beta", "gamma"]
    assert [row["hostname"] for row in sort_items(items, sort_key="hostname", direction="desc")] == ["gamma", "beta", "alpha"]

    assert [row["ip"] for row in sort_items(items, sort_key="ip", direction="asc")] == ["192.168.88.2", "192.168.88.15", "192.168.88.25"]
    assert [row["status"] for row in sort_items(items, sort_key="status", direction="desc")] == ["offline", "idle", "online"]
    assert [row["mac"] for row in sort_items(items, sort_key="session", direction="asc")] == ["AA:02", "AA:01", "AA:03"]

    assert cycle_direction(None) == "asc"
    assert cycle_direction("asc") == "desc"
    assert cycle_direction("desc") is None


def test_mode_end_vs_all_and_summary_scope():
    bridge = _device("AA:10", status="online", flags={"has_arp_entry": False, "bridge_host_present": True, "arp_flag": "", "dhcp_flag": ""})
    complete = _device("AA:11", status="idle", flags={"has_arp_entry": True, "bridge_host_present": False, "arp_flag": "DC", "dhcp_flag": ""}, idle_since="2026-04-10T10:11:00+00:00")
    interface = _device("AA:12", status="online", entity_type="interface")
    unknown = _device("AA:13", status="unknown", online_since=None, idle_since=None, offline_since=None)
    regular = _device("AA:14", status="offline", offline_since="2026-04-10T10:12:00+00:00", online_since=None)
    items = [bridge, complete, interface, unknown, regular]

    all_items = apply_display_mode(items, mode="all")
    end_items = apply_display_mode(items, mode="end_devices")

    assert len(all_items) == 5
    assert [row["mac"] for row in end_items] == ["AA:14"]
    assert build_summary(all_items)["total"] == 5
    assert build_summary(end_items)["total"] == 1


def test_filters_only_affect_rows_and_clear_restores_rows():
    items = [
        _device("AA:20", status="online"),
        _device("AA:21", status="idle", idle_since="2026-04-10T10:33:00+00:00"),
        _device("AA:22", status="offline", offline_since="2026-04-10T10:34:00+00:00", online_since=None),
    ]

    mode_items = apply_display_mode(items, mode="all")
    summary_before = build_summary(mode_items)

    filtered = apply_filters(mode_items, status_filter="online")
    assert [row["mac"] for row in filtered] == ["AA:20"]
    assert build_summary(mode_items) == summary_before

    cleared = apply_filters(mode_items, status_filter=None)
    assert len(cleared) == 3


def test_unknown_visibility_and_sorting_without_time_fallback():
    items = [
        _device("AA:30", status="unknown", hostname="charlie", state_changed_at="2026-04-11T12:00:00+00:00"),
        _device("AA:31", status="unknown", hostname="bravo", state_changed_at="2026-04-09T12:00:00+00:00"),
        _device("AA:32", status="online", online_since="2026-04-10T12:00:00+00:00"),
    ]

    assert [row["status"] for row in apply_display_mode(items, mode="end_devices")] == ["online"]
    assert len(apply_display_mode(items, mode="all")) == 3

    sorted_items = sort_items(items)
    assert [row["hostname"] for row in sorted_items[-2:]] == ["bravo", "charlie"]


def test_empty_and_null_values_are_handled_deterministically():
    items = [
        _device("AA:40", hostname="", ip="", status="online", online_since=None, state_changed_at="2026-04-10T10:01:00+00:00"),
        _device("AA:41", hostname="alpha", ip="192.168.88.2", status="online", online_since=None, state_changed_at="2026-04-10T10:02:00+00:00"),
        _device("AA:42", hostname="bravo", ip=None, status="idle", idle_since=None, state_changed_at="2026-04-10T10:03:00+00:00"),
    ]

    ip_sorted = sort_items(items, sort_key="ip", direction="asc")
    assert [row["mac"] for row in ip_sorted] == ["AA:41", "AA:40", "AA:42"]

    name_sorted = sort_items(items, sort_key="hostname", direction="asc")
    assert [row["mac"] for row in name_sorted] == ["AA:41", "AA:42", "AA:40"]


def test_contract_assumptions_are_validated_for_required_fields():
    item = _device("AA:50")
    assert validate_contract_fields(item)

    broken = deepcopy(item)
    broken.pop("state_changed_at")
    assert not validate_contract_fields(broken)
