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
            "ip_address": lease.get("address", ""),
            "host_name": lease.get("host_name", ""),
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

    devices = list(devices_by_mac.values())
    logger.info("Devices built: %d", len(devices))
    return devices
