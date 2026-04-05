from __future__ import annotations

import logging
from typing import Any

from app.errors import DhcpFetchError, EmptyDhcpLeasesError, UnexpectedMikroTikResponseError
from app.mikrotik_client import MikroTikClient

logger = logging.getLogger("mikrotrack.collector")


def collect_dhcp_leases(client: MikroTikClient) -> list[dict[str, Any]]:
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
