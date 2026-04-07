from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("mikrotrack.device_builder")


def build_devices(dhcp: list[dict[str, Any]], arp: list[dict[str, Any]]) -> list[dict[str, Any]]:
    devices_by_mac: dict[str, dict[str, Any]] = {}

    for lease in dhcp:
        mac_address = lease.get("mac_address", "")
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
        }
        logger.debug("merge steps: added DHCP device for MAC=%s", mac_address)

    for entry in arp:
        mac_address = entry.get("mac_address", "")
        if not mac_address:
            logger.debug("Skipping ARP entry without MAC: %s", entry)
            continue

        arp_ip = entry.get("ip_address", "")
        existing = devices_by_mac.get(mac_address)

        if existing is None:
            devices_by_mac[mac_address] = {
                "mac_address": mac_address,
                "ip_address": arp_ip,
                "host_name": "",
                "dhcp_comment": "",
                "arp_comment": entry.get("comment", ""),
                "dhcp_status": "unknown",
                "arp_status": entry.get("status", "unknown"),
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
            }
            logger.debug("merge steps: added ARP-only device for MAC=%s", mac_address)
            continue

        if "arp" not in existing["source"]:
            existing["source"].append("arp")

        if arp_ip and existing.get("ip_address") != arp_ip:
            logger.debug(
                "merge steps: MAC=%s IP updated from %s to %s (ARP wins)",
                mac_address,
                existing.get("ip_address", ""),
                arp_ip,
            )
            existing["ip_address"] = arp_ip
        else:
            logger.debug("merge steps: MAC=%s merged with ARP", mac_address)

        existing["arp_comment"] = entry.get("comment", "")
        existing["arp_status"] = entry.get("status", "unknown")
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
        if existing["created_by"] != "dhcp":
            existing["created_by"] = "manual"
        logger.debug(
            "merge steps: MAC=%s updated comments/status/flags from ARP",
            mac_address,
        )

    devices = list(devices_by_mac.values())
    logger.debug("Device sample after merge: %s", devices[0] if devices else {})
    logger.info("Devices built: %d", len(devices))
    return devices
