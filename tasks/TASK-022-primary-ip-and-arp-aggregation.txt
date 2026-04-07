# TASK-022 - Primary IP Selection & Multi-ARP Handling

## Context
In MikroTrack, a single device (MAC) can have multiple ARP records:
- different IPs
- different statuses (reachable, stale, failed)

Additionally, devices may use link-local IPs (169.254.x.x) when DHCP fails.

Current issue:
- system treats ARP as single record
- incorrect IP and status selection
- link-local IPs displayed as primary

## Goal
Implement correct logic for:
1. Multi-ARP handling per MAC
2. Primary IP selection
3. Link-local (169.254.x.x) handling

## Definitions
### ARP Record
Fields:
- ip
- mac
- flags (D, C)
- status (reachable, stale, failed, etc.)

### Device
Aggregated entity by MAC

## Rules

## 1. Group ARP Records
ALL ARP records MUST be grouped by MAC.

arp_records_by_mac = group_by(mac)

## 2. ARP Status Priority
1. reachable / complete
2. stale
3. delay / probe
4. failed

## 3. Link-Local Detection
169.254.0.0/16

def is_link_local(ip):
    return ip.startswith("169.254.")

## 4. Primary IP Selection
Priority:
1. DHCP (non link-local)
2. ARP (non link-local)
3. ARP (link-local)
4. None

def select_primary_ip(device):
    if device.dhcp.has_lease and not is_link_local(device.dhcp.ip):
        return device.dhcp.ip

    arp_sorted = sort_by_status(device.arp_records)

    for r in arp_sorted:
        if not is_link_local(r.ip) and r.status != "failed":
            return r.ip

    for r in arp_sorted:
        if is_link_local(r.ip) and r.status != "failed":
            return r.ip

    return None

## 5. Device Status Logic
reachable → online  
stale → unknown  
failed → offline  

## 6. Additional ARP Records
device.arp_secondary = [...]

## 7. UI Requirements
Primary:
- primary_ip
- flags
- status

Additional:
+N ARP records

Link-local badge:
LINK-LOCAL

## 8. Constraints
- NO RECORD ≠ STATIC
- DO NOT use failed as primary
- DO NOT prioritize link-local

## 9. Events
- primary_ip changed
- ARP added/removed
- status changed

## 10. Acceptance
- multi-ARP supported
- correct IP selection
- correct UI

## Result
System reflects real network state
