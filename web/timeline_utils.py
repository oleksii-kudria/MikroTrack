from __future__ import annotations

from datetime import datetime


def parse_timestamp(value: object) -> datetime:
    if not isinstance(value, str):
        return datetime.min

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min


def assignment(value: object) -> str:
    if value is True:
        return "dynamic"
    if value is False:
        return "static"
    text = str(value).strip().lower()
    if text in {"true", "dynamic"}:
        return "dynamic"
    if text in {"false", "static"}:
        return "static"
    return text or "unknown"


def readable_description(event: dict[str, object]) -> str:
    event_type = str(event.get("event_type", "")).upper()
    old_value = event.get("old_value")
    new_value = event.get("new_value")

    descriptions: dict[str, str] = {
        "DEVICE_IP_ASSIGNMENT_CHANGED": (
            f"DHCP lease changed from {assignment(old_value)} to {assignment(new_value)}"
        ),
        "IP_CHANGED": f"IP changed from {old_value or 'unknown'} to {new_value or 'unknown'}",
        "SOURCE_CHANGED": f"Source changed from {old_value or 'unknown'} to {new_value or 'unknown'}",
        "ARP_STATUS_CHANGED": f"ARP status changed from {old_value or 'unknown'} to {new_value or 'unknown'}",
        "ARP_STATE_CHANGED": f"ARP state changed from {old_value or 'unknown'} to {new_value or 'unknown'}",
    }
    if event_type in descriptions:
        return descriptions[event_type]
    if old_value is not None or new_value is not None:
        return f"{event_type} changed from {old_value or 'unknown'} to {new_value or 'unknown'}"
    return event_type.replace("_", " ").title()


def group_events(events: list[dict[str, object]]) -> list[dict[str, object]]:
    sorted_events = sorted(
        events,
        key=lambda item: (str(item.get("mac", "")), parse_timestamp(item.get("timestamp"))),
    )
    groups: list[dict[str, object]] = []

    for event in sorted_events:
        mac = str(event.get("mac", "")).strip()
        timestamp = parse_timestamp(event.get("timestamp"))

        latest_group = groups[-1] if groups else None
        if (
            latest_group is not None
            and latest_group["mac"] == mac
            and isinstance(latest_group["timestamp_obj"], datetime)
            and abs((timestamp - latest_group["timestamp_obj"]).total_seconds()) <= 1
        ):
            latest_group["events"].append(event)
            latest_group["changes"].append(readable_description(event))
            if timestamp > latest_group["timestamp_obj"]:
                latest_group["timestamp_obj"] = timestamp
                latest_group["timestamp"] = str(event.get("timestamp", "-"))
            continue

        groups.append(
            {
                "mac": mac,
                "timestamp": str(event.get("timestamp", "-")),
                "timestamp_obj": timestamp,
                "event_type": str(event.get("event_type", "-")),
                "events": [event],
                "changes": [readable_description(event)],
            }
        )

    for group in groups:
        group.pop("timestamp_obj", None)

    return groups
