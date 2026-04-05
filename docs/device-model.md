# Device Model

## DHCP fields

MikroTrack reads DHCP leases from `/ip/dhcp-server/lease/print` and normalizes:

- `address` → `ip_address`
- `mac-address` → `mac_address`
- `host-name` → `host_name`
- `status` → `dhcp_status`
- `dynamic` → static/dynamic source hint
- `comment` → `dhcp_comment`
- `server` (if available) → source metadata

## ARP fields

MikroTrack reads ARP table from `/ip/arp/print` and normalizes:

- `address` → `ip_address`
- `mac-address` → `mac_address`
- `interface` → `interface`
- `status` → `arp_status`
- `dynamic`/router flags → `arp_flags`
- `comment` → `arp_comment`

## Flags

### DHCP flags

- `dynamic` — lease created automatically by DHCP server
- `static` — manually pinned lease

### ARP flags

- `dynamic` — learned dynamically
- `dhcp` — created from DHCP context
- `complete` — entry contains full L2/L3 binding
- `published` — proxy/published ARP behavior
- `invalid` — invalid entry
- `disabled` — entry disabled on router

## Status

### DHCP status

- `waiting`
- `offered`
- `bound`

### ARP status

- `reachable`
- `stale`
- `failed`
- `incomplete`

## Unified JSON example

```json
[
  {
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "ip_address": "192.168.88.10",
    "host_name": "workstation-01",
    "source": "dhcp+arp",
    "dhcp_status": "bound",
    "arp_status": "reachable",
    "dhcp_flags": ["dynamic"],
    "arp_flags": ["dynamic", "complete"],
    "dhcp_comment": "Office host",
    "arp_comment": "",
    "arp_type": "dynamic",
    "created_by": "mikrotrack"
  }
]
```
