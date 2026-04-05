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
                "ip_address": lease.get("address", ""),
                "mac_address": lease.get("mac-address", ""),
                "host_name": lease.get("host-name", ""),
                "comment": lease.get("comment", ""),
                "status": lease.get("status", "unknown"),
                "dynamic": lease.get("dynamic", "false") == "true",
                "expires_after": lease.get("expires-after", ""),
                "last_seen": lease.get("last-seen", ""),
            }
        )

    logger.info("DHCP enriched records count: %d", len(result))
    logger.debug("DHCP enriched record sample (up to 2): %s", result[:2])

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
    for index, entry in enumerate(arp_entries):
        if not isinstance(entry, dict):
            raise UnexpectedMikroTikResponseError("ARP item is not a dictionary")

        logger.debug("Normalizing ARP entry #%d", index + 1)
        normalized.append(
            {
                "mac_address": entry.get("mac-address", ""),
                "ip_address": entry.get("address", ""),
                "interface": entry.get("interface", ""),
                "comment": entry.get("comment", ""),
                "status": entry.get("status", "unknown"),
                "dynamic": entry.get("dynamic", "false") == "true",
                "dhcp": entry.get("dhcp", "false") == "true",
                "complete": entry.get("complete", "false") == "true",
                "disabled": entry.get("disabled", "false") == "true",
                "invalid": entry.get("invalid", "false") == "true",
                "published": entry.get("published", "false") == "true",
            }
        )

    logger.info("ARP enriched records count: %d", len(normalized))
    logger.debug("ARP enriched record sample: %s", normalized[0] if normalized else {})
    return normalized
