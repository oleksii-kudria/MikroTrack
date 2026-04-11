from __future__ import annotations

import json
from datetime import datetime

from app.persistence import _generate_diff_events, _make_json_safe


BASE_PREVIOUS = {
    "mac_address": "AA:BB:CC:DD:EE:20",
    "ip_address": "192.168.88.20",
    "host_name": "old-host",
    "source": ["dhcp", "arp"],
    "fused_state": "online",
    "arp_status": "reachable",
    "dhcp_flags": {"dynamic": True},
    "arp_flags": {"dynamic": True},
    "dhcp_comment": "old-dhcp",
    "arp_comment": "old-arp",
}


BASE_CURRENT = {
    "mac_address": "AA:BB:CC:DD:EE:20",
    "ip_address": "192.168.88.21",
    "host_name": "new-host",
    "source": ["arp"],
    "fused_state": "offline",
    "arp_status": "failed",
    "dhcp_flags": {"dynamic": False},
    "arp_flags": {"dynamic": False},
    "dhcp_comment": "",
    "arp_comment": "new-arp",
}


def test_extended_diff_generates_field_change_and_state_related_events() -> None:
    events = _generate_diff_events([BASE_PREVIOUS], [BASE_CURRENT])
    by_type = {
        event["event_type"]: event
        for event in events
        if event.get("event_type") != "FIELD_CHANGE"
    }

    assert "IP_CHANGED" in by_type
    assert by_type["IP_CHANGED"]["old_value"] == "192.168.88.20"
    assert by_type["IP_CHANGED"]["new_value"] == "192.168.88.21"

    assert "HOSTNAME_CHANGED" in by_type
    assert by_type["HOSTNAME_CHANGED"]["old_value"] == "old-host"
    assert by_type["HOSTNAME_CHANGED"]["new_value"] == "new-host"

    assert "state_changed" in by_type
    assert by_type["state_changed"]["old_state"] == "online"
    assert by_type["state_changed"]["new_state"] == "offline"

    field_changes = [
        event for event in events if event.get("event_type") == "FIELD_CHANGE"
    ]
    assert field_changes
    state_change = next(
        event for event in field_changes if event["field_name"] == "state"
    )
    assert state_change["previous_value"] == "online"
    assert state_change["current_value"] == "offline"


def test_make_json_safe_keeps_payload_serializable_for_complex_types() -> None:
    payload = {
        "timestamp": datetime(2026, 4, 11, 12, 34, 56),
        "tags": {"a", "b"},
        "coords": (1, 2),
        "raw": b"hello",
        "nested": {"tuple": ("x", b"y")},
    }

    safe_payload = _make_json_safe(payload)
    encoded = json.dumps(safe_payload)

    assert isinstance(encoded, str)
    assert safe_payload["timestamp"] == "2026-04-11T12:34:56"
    assert sorted(safe_payload["tags"]) == ["a", "b"]
    assert safe_payload["coords"] == [1, 2]
    assert safe_payload["raw"] == "hello"
    assert safe_payload["nested"]["tuple"] == ["x", "y"]
