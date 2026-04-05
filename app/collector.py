from __future__ import annotations

import logging
from typing import Any

from app.errors import DhcpFetchError, EmptyDhcpLeasesError, UnexpectedMikroTikResponseError
from app.mikrotik_client import MikroTikClient

logger = logging.getLogger("mikrotrack.collector")


def get_dhcp_leases(client: MikroTikClient) -> list[dict[str, Any]]:
    logger.info("Requesting DHCP leases from MikroTik API")
    logger.debug("Executing API call: /ip/dhcp-server/lease get()")

    try:
        leases_resource = client.get_resource("/ip/dhcp-server/lease")
        leases = leases_resource.get()
    except Exception as error:
        raise DhcpFetchError("Failed to fetch DHCP leases") from error

    if not isinstance(leases, list):
        raise UnexpectedMikroTikResponseError("DHCP lease response is not a list")

    logger.debug("Fetched %d raw DHCP lease records", len(leases))

    if not leases:
        raise EmptyDhcpLeasesError("DHCP lease list is empty")

    result: list[dict[str, Any]] = []
    for index, lease in enumerate(leases):
        if not isinstance(lease, dict):
            raise UnexpectedMikroTikResponseError("DHCP lease item is not a dictionary")

        logger.debug("Normalizing lease #%d", index + 1)
        result.append(
            {
                "address": lease.get("address", ""),
                "mac_address": lease.get("mac-address", ""),
                "host_name": lease.get("host-name", ""),
                "status": lease.get("status", "unknown"),
                "server": lease.get("server", ""),
            }
        )

    logger.info("DHCP lease normalization complete: %d records", len(result))
    logger.debug("Normalized leases sample (up to 2): %s", result[:2])

    return result


def collect_dhcp_leases(client: MikroTikClient) -> list[dict[str, Any]]:
    """Backward-compatible wrapper for older call sites."""

    return get_dhcp_leases(client)


def get_arp_entries(client: MikroTikClient) -> list[dict[str, Any]]:
    logger.info("Requesting ARP entries from MikroTik API")
    logger.debug("Executing API call: /ip/arp get()")

    try:
        arp_resource = client.get_resource("/ip/arp")
        arp_entries = arp_resource.get()
    except Exception as error:
        raise UnexpectedMikroTikResponseError("Failed to fetch ARP entries") from error

    if not isinstance(arp_entries, list):
        raise UnexpectedMikroTikResponseError("ARP response is not a list")

    logger.info("ARP entries fetched: %d", len(arp_entries))
    logger.debug("raw ARP count: %d", len(arp_entries))

    normalized: list[dict[str, Any]] = []
    for entry in arp_entries:
        if not isinstance(entry, dict):
            raise UnexpectedMikroTikResponseError("ARP item is not a dictionary")

        normalized.append(
            {
                "mac_address": entry.get("mac-address", ""),
                "ip_address": entry.get("address", ""),
                "interface": entry.get("interface", ""),
            }
        )

    logger.debug("sample ARP entry: %s", normalized[0] if normalized else {})
    return normalized
