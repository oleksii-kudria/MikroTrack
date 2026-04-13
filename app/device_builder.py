from __future__ import annotations

import logging
from ipaddress import ip_address
from typing import Any

from app.arp_logic import fused_device_state, normalize_arp_status
from app.mac_metadata import is_random_mac, lookup_mac_vendor, normalize_mac

logger = logging.getLogger("mikrotrack.device_builder")

_ARP_STATUS_PRIORITY = {
    "reachable": 0,
    "complete": 0,
    "stale": 1,
    "delay": 2,
    "probe": 2,
    "failed": 3,
}


def _normalize_mac(mac_raw: Any) -> str:
    return normalize_mac(mac_raw)


def _is_random_mac(mac_raw: Any) -> bool:
    return is_random_mac(mac_raw)


def _is_link_local(ip_raw: str) -> bool:
    ip_text = str(ip_raw or "").strip()
    if not ip_text:
        return False
    try:
        return ip_address(ip_text).is_link_local
    except ValueError:
        return False


def _arp_priority(entry: dict[str, Any]) -> tuple[int, int]:
    status = normalize_arp_status(entry.get("status", "unknown"))
    status_priority = _ARP_STATUS_PRIORITY.get(status, 2)
    link_local_priority = 1 if _is_link_local(str(entry.get("ip_address", ""))) else 0
    return status_priority, link_local_priority


def _select_primary_arp(arp_records: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        record
        for record in arp_records
        if normalize_arp_status(record.get("status", "")) != "failed"
    ]
    if not candidates:
        return None
    by_status = sorted(
        candidates,
        key=lambda entry: _ARP_STATUS_PRIORITY.get(str(entry.get("status", "")).strip().lower(), 2),
    )
    for record in by_status:
        if not _is_link_local(str(record.get("ip_address", ""))):
            return record
    return by_status[0]


def build_devices(
    dhcp: list[dict[str, Any]],
    arp: list[dict[str, Any]],
    bridge_hosts: list[dict[str, Any]] | None = None,
    interface_macs: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    devices_by_mac: dict[str, dict[str, Any]] = {}
    bridge_hosts = bridge_hosts or []
    interface_macs = interface_macs or []
    interface_by_mac = {
        _normalize_mac(item.get("mac_address", "")): item
        for item in interface_macs
        if _normalize_mac(item.get("mac_address", ""))
    }

    for lease in dhcp:
        mac_address = _normalize_mac(lease.get("mac_address", ""))
        if not mac_address:
            logger.debug("Skipping DHCP lease without MAC: %s", lease)
            continue

        devices_by_mac[mac_address] = {
            "mac_address": mac_address,
            "ip_address": lease.get("ip_address", ""),
            "host_name": lease.get("host_name", ""),
            "dhcp_comment": lease.get("comment", ""),
            "arp_comment": "",
            "dhcp_status": lease.get("status", "unknown"),
            "arp_status": "unknown",
            "arp_state": "unknown",
            "fused_state": "unknown",
            "bridge_host_present": False,
            "bridge_host_interface": "",
            "bridge_host_last_seen": "",
            "evidence": {
                "arp_status": "unknown",
                "bridge_host_present": False,
                "bridge_host_last_seen": "",
            },
            "dhcp_flags": {
                "dynamic": lease.get("dynamic", False),
            },
            "has_dhcp_lease": bool(lease.get("has_dhcp_lease", True)),
            "dhcp_is_dynamic": bool(lease.get("dhcp_is_dynamic", lease.get("dynamic", False))),
            "arp_flags": {
                "dynamic": False,
                "dhcp": False,
                "complete": False,
                "disabled": False,
                "invalid": False,
                "published": False,
            },
            "has_arp_entry": False,
            "created_by": "dhcp",
            "arp_type": "unknown",
            "source": ["dhcp"],
            "entity_type": "client",
            "interface_name": "",
            "badges": [],
            "is_random_mac": False,
            "mac_vendor": None,
        }
        logger.debug("merge steps: added DHCP device for MAC=%s", mac_address)

    arp_records_by_mac: dict[str, list[dict[str, Any]]] = {}
    for entry in arp:
        mac_address = _normalize_mac(entry.get("mac_address", ""))
        if not mac_address:
            logger.debug("Skipping ARP entry without MAC: %s", entry)
            continue
        arp_records_by_mac.setdefault(mac_address, []).append(entry)

    for mac_address, mac_arp_records in arp_records_by_mac.items():
        primary_arp = _select_primary_arp(mac_arp_records)
        display_arp = (
            primary_arp
            if primary_arp is not None
            else sorted(mac_arp_records, key=_arp_priority)[0]
        )

        arp_secondary = [
            record
            for record in sorted(mac_arp_records, key=_arp_priority)
            if record is not display_arp
        ]

        entry = display_arp
        mac_address = _normalize_mac(entry.get("mac_address", ""))
        arp_status = normalize_arp_status(entry.get("status", "unknown"))
        arp_state = fused_device_state(arp_status, bridge_host_present=False)

        arp_ip = primary_arp.get("ip_address", "") if primary_arp is not None else ""
        existing = devices_by_mac.get(mac_address)

        if existing is None:
            devices_by_mac[mac_address] = {
                "mac_address": mac_address,
                "ip_address": arp_ip,
                "host_name": "",
                "dhcp_comment": "",
                "arp_comment": entry.get("comment", ""),
                "dhcp_status": "unknown",
                "arp_status": arp_status,
                "arp_state": arp_state,
                "fused_state": arp_state,
                "bridge_host_present": False,
                "bridge_host_interface": "",
                "bridge_host_last_seen": "",
                "evidence": {
                    "arp_status": arp_status,
                    "bridge_host_present": False,
                    "bridge_host_last_seen": "",
                },
                "dhcp_flags": {},
                "has_dhcp_lease": False,
                "dhcp_is_dynamic": None,
                "arp_flags": {
                    "dynamic": entry.get("dynamic", False),
                    "dhcp": entry.get("dhcp", False),
                    "complete": entry.get("complete", False),
                    "disabled": entry.get("disabled", False),
                    "invalid": entry.get("invalid", False),
                    "published": entry.get("published", False),
                },
                "has_arp_entry": bool(entry.get("has_arp_entry", True)),
                "created_by": "manual",
                "arp_type": "dynamic" if entry.get("dynamic", False) else "static",
                "source": ["arp"],
                "arp_records": sorted(mac_arp_records, key=_arp_priority),
                "arp_secondary": arp_secondary,
                "entity_type": "client",
                "interface_name": "",
                "badges": [],
                "is_random_mac": False,
                "mac_vendor": None,
            }
            logger.debug("merge steps: added ARP-only device for MAC=%s", mac_address)
            continue

        if "arp" not in existing["source"]:
            existing["source"].append("arp")

        logger.debug("merge steps: MAC=%s merged with ARP", mac_address)

        existing["arp_comment"] = entry.get("comment", "")
        existing["arp_status"] = arp_status
        existing["arp_state"] = arp_state
        existing["fused_state"] = arp_state
        existing["arp_flags"] = {
            "dynamic": entry.get("dynamic", False),
            "dhcp": entry.get("dhcp", False),
            "complete": entry.get("complete", False),
            "disabled": entry.get("disabled", False),
            "invalid": entry.get("invalid", False),
            "published": entry.get("published", False),
        }
        existing["has_arp_entry"] = bool(entry.get("has_arp_entry", True))
        existing["arp_type"] = "dynamic" if entry.get("dynamic", False) else "static"
        existing["arp_records"] = sorted(mac_arp_records, key=_arp_priority)
        existing["arp_secondary"] = arp_secondary
        if existing["created_by"] != "dhcp":
            existing["created_by"] = "manual"
        logger.debug(
            "merge steps: MAC=%s updated comments/status/flags from ARP",
            mac_address,
        )

        dhcp_ip = str(existing.get("ip_address", "")).strip()
        if dhcp_ip and not _is_link_local(dhcp_ip):
            continue

        if arp_ip and (not dhcp_ip or _is_link_local(dhcp_ip)):
            logger.debug("merge steps: MAC=%s primary IP set from ARP=%s", mac_address, arp_ip)
            existing["ip_address"] = arp_ip

    bridge_records_by_mac: dict[str, list[dict[str, Any]]] = {}
    for record in bridge_hosts:
        mac_address = _normalize_mac(record.get("mac_address", ""))
        if not mac_address:
            continue
        bridge_records_by_mac.setdefault(mac_address, []).append(record)

    for mac_address, records in bridge_records_by_mac.items():
        selected = records[0]
        existing = devices_by_mac.get(mac_address)
        if existing is None:
            devices_by_mac[mac_address] = {
                "mac_address": mac_address,
                "ip_address": "",
                "host_name": "",
                "dhcp_comment": "",
                "arp_comment": "",
                "dhcp_status": "unknown",
                "arp_status": "unknown",
                "arp_state": "online",
                "fused_state": "online",
                "bridge_host_present": True,
                "bridge_host_interface": selected.get("interface", ""),
                "bridge_host_last_seen": selected.get("bridge_host_last_seen", ""),
                "evidence": {
                    "arp_status": "unknown",
                    "bridge_host_present": True,
                    "bridge_host_last_seen": selected.get("bridge_host_last_seen", ""),
                },
                "dhcp_flags": {},
                "has_dhcp_lease": False,
                "dhcp_is_dynamic": None,
                "arp_flags": {
                    "dynamic": False,
                    "dhcp": False,
                    "complete": False,
                    "disabled": False,
                    "invalid": False,
                    "published": False,
                },
                "has_arp_entry": False,
                "created_by": "manual",
                "arp_type": "unknown",
                "source": ["bridge_host"],
                "arp_records": [],
                "arp_secondary": [],
                "entity_type": "client",
                "interface_name": "",
                "badges": [],
                "is_random_mac": False,
                "mac_vendor": None,
            }
            continue

        if "bridge_host" not in existing["source"]:
            existing["source"].append("bridge_host")

        existing["bridge_host_present"] = True
        existing["bridge_host_interface"] = selected.get("interface", "")
        existing["bridge_host_last_seen"] = selected.get("bridge_host_last_seen", "")

    for device in devices_by_mac.values():
        bridge_host_present = bool(device.get("bridge_host_present", False))
        arp_status = normalize_arp_status(device.get("arp_status", "unknown"))
        fused_state = fused_device_state(arp_status, bridge_host_present)
        device["arp_state"] = fused_state
        device["fused_state"] = fused_state
        device["evidence"] = {
            "arp_status": arp_status,
            "bridge_host_present": bridge_host_present,
            "bridge_host_last_seen": str(device.get("bridge_host_last_seen", "")),
        }
        logger.debug(
            "MAC=%s arp_status=%s fused_state=%s decision=normalized",
            str(device.get("mac_address", "")).strip(),
            arp_status,
            fused_state,
        )
        badges: list[str] = []
        is_random_mac_address = _is_random_mac(device.get("mac_address", ""))
        mac_vendor = lookup_mac_vendor(device.get("mac_address", ""))
        device["is_random_mac"] = is_random_mac_address
        device["mac_vendor"] = mac_vendor

        if is_random_mac_address:
            badges.append("RANDOM")
        elif arp_status == "permanent":
            badges.append("STATIC")
            logger.info(
                "ARP permanent entry is treated as STATIC metadata for MAC %s",
                str(device.get("mac_address", "")).strip().upper() or "unknown",
            )
        if _is_link_local(str(device.get("ip_address", ""))):
            badges.append("LINK-LOCAL")
        if (
            not bool(device.get("has_arp_entry", False))
            and not bool(device.get("has_dhcp_lease", False))
            and bridge_host_present
        ):
            badges.append("BRIDGE")

        interface = interface_by_mac.get(_normalize_mac(device.get("mac_address", "")))
        if interface is not None:
            device["entity_type"] = "interface"
            device["interface_name"] = str(interface.get("interface_name", "")).strip()
            badges.append("INTERFACE")
        else:
            device["entity_type"] = "client"
            device["interface_name"] = ""
        device["badges"] = badges

    for device in devices_by_mac.values():
        if "arp_records" not in device:
            device["arp_records"] = []
        if "arp_secondary" not in device:
            device["arp_secondary"] = []

    devices = list(devices_by_mac.values())
    logger.debug("Device sample after merge: %s", devices[0] if devices else {})
    logger.info("Devices built: %d", len(devices))
    return devices
