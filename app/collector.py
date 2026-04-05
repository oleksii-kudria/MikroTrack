from __future__ import annotations

from typing import Any

from app.mikrotik_client import MikroTikClient


def collect_dhcp_leases(client: MikroTikClient) -> list[dict[str, Any]]:
    leases_resource = client.get_resource("/ip/dhcp-server/lease")
    leases = leases_resource.get()

    result: list[dict[str, Any]] = []
    for lease in leases:
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
