from __future__ import annotations

from typing import Any

from app.errors import DhcpFetchError, EmptyDhcpLeasesError, UnexpectedMikroTikResponseError
from app.mikrotik_client import MikroTikClient


def collect_dhcp_leases(client: MikroTikClient) -> list[dict[str, Any]]:
    try:
        leases_resource = client.get_resource("/ip/dhcp-server/lease")
        leases = leases_resource.get()
    except Exception as error:
        raise DhcpFetchError("Failed to fetch DHCP leases") from error

    if not isinstance(leases, list):
        raise UnexpectedMikroTikResponseError("DHCP lease response is not a list")

    if not leases:
        raise EmptyDhcpLeasesError("DHCP lease list is empty")

    result: list[dict[str, Any]] = []
    for lease in leases:
        if not isinstance(lease, dict):
            raise UnexpectedMikroTikResponseError("DHCP lease item is not a dictionary")

        result.append(
            {
                "address": lease.get("address", ""),
                "mac_address": lease.get("mac-address", ""),
                "host_name": lease.get("host-name", ""),
                "status": lease.get("status", "unknown"),
                "server": lease.get("server", ""),
            }
        )

    return result
