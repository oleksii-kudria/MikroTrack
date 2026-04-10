from __future__ import annotations

from typing import Any

_IDLE_ARP_STATUSES = {"stale", "permanent"}
_OFFLINE_ARP_STATUSES = {"failed", "incomplete"}
_ONLINE_ARP_STATUSES = {"reachable", "complete", "delay", "probe"}


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
    return "unknown"


def fused_device_state(raw_status: Any, bridge_host_present: bool) -> str:
    status = normalize_arp_status(raw_status)

    if status in _ONLINE_ARP_STATUSES:
        return "online"
    if bridge_host_present:
        return "online"
    if status in _IDLE_ARP_STATUSES:
        return "idle"
    if status in _OFFLINE_ARP_STATUSES:
        return "offline"
    return "unknown"
