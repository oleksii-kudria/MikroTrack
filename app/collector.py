from __future__ import annotations

import logging
from typing import Any

from app.errors import DhcpFetchError, EmptyDhcpLeasesError, UnexpectedMikroTikResponseError
from app.mikrotik_client import MikroTikClient

logger = logging.getLogger("mikrotrack.collector")


def _is_expected_unsupported_resource_error(error: Exception) -> bool:
    message = str(error).lower()
    expected_markers = (
        "no such command",
        "no such command prefix",
        "unknown parameter",
        "not supported",
        "resource does not exist",
    )
    return any(marker in message for marker in expected_markers)


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
                "has_dhcp_lease": True,
                "dhcp_is_dynamic": lease.get("dynamic", "false") == "true",
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
                "has_arp_entry": True,
            }
        )

    logger.info("ARP enriched records count: %d", len(normalized))
    logger.debug("ARP enriched record sample: %s", normalized[0] if normalized else {})
    return normalized


def get_bridge_hosts(client: MikroTikClient) -> list[dict[str, Any]]:
    logger.info("Requesting bridge host entries from MikroTik API")
    logger.debug("Executing API call: /interface/bridge/host get()")

    try:
        bridge_host_resource = client.get_resource("/interface/bridge/host")
        bridge_hosts = bridge_host_resource.get()
    except Exception as error:
        raise UnexpectedMikroTikResponseError("Failed to fetch bridge host entries") from error

    if not isinstance(bridge_hosts, list):
        raise UnexpectedMikroTikResponseError("Bridge host response is not a list")

    logger.info("Bridge host entries fetched: %d", len(bridge_hosts))

    normalized: list[dict[str, Any]] = []
    for index, entry in enumerate(bridge_hosts):
        if not isinstance(entry, dict):
            raise UnexpectedMikroTikResponseError("Bridge host item is not a dictionary")

        logger.debug("Normalizing bridge host entry #%d", index + 1)
        normalized.append(
            {
                "mac_address": entry.get("mac-address", ""),
                "interface": entry.get("interface", ""),
                "bridge_host_last_seen": entry.get("last-seen", ""),
                "bridge_host_present": True,
            }
        )

    logger.info("Bridge host enriched records count: %d", len(normalized))
    logger.debug("Bridge host enriched record sample: %s", normalized[0] if normalized else {})
    return normalized


def get_interface_macs(client: MikroTikClient) -> list[dict[str, str]]:
    resources = (
        ("/interface", "interface"),
        ("/interface/bridge", "bridge"),
        ("/interface/vlan", "vlan"),
        ("/interface/wireless", "wireless"),
    )
    result_by_mac: dict[str, dict[str, str]] = {}

    for path, source in resources:
        logger.debug("Executing API call: %s get()", path)
        try:
            resource = client.get_resource(path)
            entries = resource.get()
        except Exception as error:
            if path == "/interface/wireless" and _is_expected_unsupported_resource_error(error):
                logger.info(
                    "Skipping optional resource %s: unsupported on this device",
                    path,
                )
                logger.debug("Optional resource skip reason for %s: %s", path, error)
                continue
            logger.warning("Failed to fetch %s entries: %s", path, error)
            continue

        if not isinstance(entries, list):
            logger.warning("Unexpected response type for %s: %s", path, type(entries).__name__)
            continue

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            mac_address = str(entry.get("mac-address", "")).strip()
            if not mac_address:
                continue

            if mac_address in result_by_mac:
                continue

            result_by_mac[mac_address] = {
                "mac_address": mac_address,
                "interface_name": str(entry.get("name", "")).strip(),
                "interface_source": source,
            }

    result = list(result_by_mac.values())
    logger.info("Interface MAC records fetched: %d", len(result))
    logger.debug("Interface MAC sample: %s", result[:2])
    return result
