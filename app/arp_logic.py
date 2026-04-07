from __future__ import annotations

from typing import Any

_IDLE_ARP_STATUSES = {"stale", "delay", "probe"}
_OFFLINE_ARP_STATUSES = {"failed", "incomplete"}
_ONLINE_ARP_STATUSES = {"reachable", "complete"}


def normalize_arp_status(raw_status: Any) -> str:
    status = str(raw_status or "").strip().lower()
    return status or "unknown"


def arp_state_from_status(raw_status: Any) -> str:
    status = normalize_arp_status(raw_status)

    if status in _ONLINE_ARP_STATUSES:
        return "online"
    if status in _IDLE_ARP_STATUSES:
        return "idle"
    if status in _OFFLINE_ARP_STATUSES:
        return "offline"
    if status == "permanent":
        return "permanent"
    return "unknown"
