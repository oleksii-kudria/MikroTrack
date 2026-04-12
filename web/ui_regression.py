from __future__ import annotations

from datetime import datetime
from typing import Any

VALID_STATES = {"online", "idle", "offline", "unknown"}
STATUS_GROUP_PRIORITY = {"online": 0, "idle": 1, "offline": 2, "unknown": 3}
STATUS_SORT_PRIORITY = {
    "asc": {"online": 0, "idle": 1, "offline": 2, "unknown": 3},
    "desc": {"offline": 0, "idle": 1, "online": 2, "unknown": 3},
}


def normalize_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text if text and text != "-" else None


def normalize_status(item: dict[str, Any]) -> str:
    state = str(item.get("status") or "").strip().lower()
    return state if state in VALID_STATES else "unknown"


def parse_ts(value: Any) -> datetime | None:
    raw = normalize_text(value)
    if raw is None:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def read_state_timestamp(item: dict[str, Any]) -> datetime | None:
    state = normalize_status(item)
    if state == "unknown":
        return None
    by_state = {
        "online": item.get("online_since"),
        "idle": item.get("idle_since"),
        "offline": item.get("offline_since"),
    }
    return parse_ts(by_state.get(state)) or parse_ts(item.get("state_changed_at"))


def resolve_assignment(item: dict[str, Any]) -> str | None:
    entity_type = str(item.get("entity_type") or "client").strip().lower()
    if entity_type == "interface":
        return "INTERFACE"

    flags = item.get("flags") or {}
    arp_flag = str(flags.get("arp_flag") or "").strip().upper()
    dhcp_flag = str(flags.get("dhcp_flag") or "").strip().upper()
    has_dhcp_lease = bool(dhcp_flag)
    dhcp_is_dynamic = dhcp_flag == "D"
    dhcp_is_static = dhcp_flag == "S"
    arp_is_static = arp_flag.startswith("S")
    bridge_host_present = bool(flags.get("bridge_host_present"))
    bridge_only = not flags.get("has_arp_entry") and not has_dhcp_lease and bridge_host_present

    if arp_is_static:
        return "PERM"
    if has_dhcp_lease and dhcp_is_static:
        return "STATIC"
    if has_dhcp_lease and dhcp_is_dynamic:
        return "DYNAMIC"
    if not has_dhcp_lease and arp_flag == "DC":
        return "COMPLETE"
    if bridge_only:
        return "BRIDGE"
    return None


def apply_display_mode(items: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    if mode == "all":
        return list(items)
    result: list[dict[str, Any]] = []
    for item in items:
        status = normalize_status(item)
        assignment = resolve_assignment(item)
        if status == "unknown":
            continue
        if assignment in {"BRIDGE", "COMPLETE", "INTERFACE"}:
            continue
        result.append(item)
    return result


def apply_filters(
    items: list[dict[str, Any]],
    status_filter: str | None = None,
    assignment_filter: str | None = None,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in items:
        if status_filter and normalize_status(item) != status_filter:
            continue
        if assignment_filter and resolve_assignment(item) != assignment_filter:
            continue
        result.append(item)
    return result


def build_summary(items: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"total": len(items), "online": 0, "idle": 0, "unknown": 0, "offline": 0}
    for item in items:
        summary[normalize_status(item)] += 1
    return summary


def _compare_nullable(left: Any, right: Any, direction: str, cmp_non_null) -> int:
    if left is None and right is None:
        return 0
    if left is None:
        return 1
    if right is None:
        return -1
    return cmp_non_null(left, right) if direction == "asc" else cmp_non_null(right, left)


def _parse_ip_number(value: Any) -> int | None:
    ip_text = normalize_text(value)
    if ip_text is None:
        return None
    parts = ip_text.split(".")
    if len(parts) != 4:
        return None
    try:
        octets = [int(part) for part in parts]
    except ValueError:
        return None
    if any(octet < 0 or octet > 255 for octet in octets):
        return None
    return octets[0] * 256**3 + octets[1] * 256**2 + octets[2] * 256 + octets[3]


def _compare_default(left: dict[str, Any], right: dict[str, Any]) -> int:
    left_status = normalize_status(left)
    right_status = normalize_status(right)
    lp = STATUS_GROUP_PRIORITY[left_status]
    rp = STATUS_GROUP_PRIORITY[right_status]
    if lp != rp:
        return lp - rp

    if left_status == "unknown" and right_status == "unknown":
        left_name = normalize_text(left.get("hostname")) or normalize_text(left.get("mac")) or ""
        right_name = normalize_text(right.get("hostname")) or normalize_text(right.get("mac")) or ""
        if left_name.lower() < right_name.lower():
            return -1
        if left_name.lower() > right_name.lower():
            return 1
        return 0

    left_ts = read_state_timestamp(left)
    right_ts = read_state_timestamp(right)
    return _compare_nullable(
        left_ts, right_ts, "desc", lambda a, b: -1 if a < b else (1 if a > b else 0)
    )


def _compare_sort_key(left: dict[str, Any], right: dict[str, Any], key: str, direction: str) -> int:
    if key == "status":
        pr = STATUS_SORT_PRIORITY[direction]
        ls, rs = normalize_status(left), normalize_status(right)
        if pr[ls] != pr[rs]:
            return pr[ls] - pr[rs]
        return _compare_nullable(
            read_state_timestamp(left),
            read_state_timestamp(right),
            direction,
            lambda a, b: -1 if a > b else (1 if a < b else 0),
        )
    if key == "session":
        return _compare_nullable(
            read_state_timestamp(left),
            read_state_timestamp(right),
            direction,
            lambda a, b: -1 if a > b else (1 if a < b else 0),
        )
    if key == "ip":
        return _compare_nullable(
            _parse_ip_number(left.get("ip")),
            _parse_ip_number(right.get("ip")),
            direction,
            lambda a, b: -1 if a < b else (1 if a > b else 0),
        )

    if key == "hostname":
        lv, rv = (
            normalize_text(left.get("hostname")),
            normalize_text(right.get("hostname")),
        )
    elif key == "mac":
        lv, rv = normalize_text(left.get("mac")), normalize_text(right.get("mac"))
    else:
        return 0
    return _compare_nullable(
        lv,
        rv,
        direction,
        lambda a, b: -1 if a.lower() < b.lower() else (1 if a.lower() > b.lower() else 0),
    )


def sort_items(
    items: list[dict[str, Any]],
    sort_key: str | None = None,
    direction: str | None = None,
) -> list[dict[str, Any]]:
    indexed = list(enumerate(items))

    def cmp(left: tuple[int, dict[str, Any]], right: tuple[int, dict[str, Any]]) -> int:
        li, lv = left
        ri, rv = right
        if not sort_key or not direction:
            compared = _compare_default(lv, rv)
        else:
            compared = _compare_sort_key(lv, rv, sort_key, direction)
        if compared != 0:
            return compared
        return -1 if li < ri else (1 if li > ri else 0)

    from functools import cmp_to_key

    return [entry[1] for entry in sorted(indexed, key=cmp_to_key(cmp))]


def cycle_direction(direction: str | None) -> str | None:
    if not direction:
        return "asc"
    if direction == "asc":
        return "desc"
    return None


def validate_contract_fields(item: dict[str, Any]) -> bool:
    required = [
        "status",
        "state_changed_at",
        "online_since",
        "idle_since",
        "offline_since",
        "last_known_ip",
        "last_known_hostname",
    ]
    return all(field in item for field in required)
