# Device Model

## 🇺🇦 Українською

## DHCP поля

MikroTrack читає DHCP leases з `/ip/dhcp-server/lease/print` та нормалізує:

- `address` → `ip_address`
- `mac-address` → `mac_address`
- `host-name` → `host_name`
- `status` → `dhcp_status`
- `dynamic` → підказка static/dynamic
- `comment` → `dhcp_comment`
- `server` (якщо є) → metadata джерела

## ARP поля

MikroTrack читає ARP table з `/ip/arp/print` та нормалізує:

- `address` → `ip_address`
- `mac-address` → `mac_address`
- `interface` → `interface`
- `status` → `arp_status`
- `derived state` → `arp_state`
- `dynamic`/router flags → `arp_flags`
- `comment` → `arp_comment`

## Bridge Host поля

MikroTrack читає bridge host table з `/interface/bridge/host/print` та нормалізує:

- `mac-address` → `mac_address`
- `interface` → `bridge_host_interface`
- `last-seen` → `bridge_host_last_seen`
- derived flag → `bridge_host_present`

## Прапорці

### DHCP flags

- `dynamic` — lease створений автоматично DHCP-сервером
- `static` — lease закріплений вручну

### ARP flags

- `dynamic` — запис вивчений динамічно
- `dhcp` — створений із DHCP контексту
- `complete` — повний L2/L3 binding
- `published` — proxy/published ARP поведінка
- `invalid` — невалідний запис
- `disabled` — запис вимкнено на роутері

## Статуси

### DHCP status

- `waiting`
- `offered`
- `bound`

### ARP status

- `reachable`
- `stale`
- `delay`
- `probe`
- `failed`
- `incomplete`
- `permanent`

### Device state mapping (ARP + Bridge Host fusion)

- `reachable` ARP → `online` (highest priority)
- if `bridge_host_present = true` → `online`
- `stale` / `delay` / `probe` → `idle`
- `failed` / `incomplete` → `offline`
- `permanent` + no bridge host → `unknown` + badge `PERM`
- unknown values → `unknown`

> `permanent` саме по собі не означає `online`; це badge, а не state.

### Session-aware time model

- `state_changed_at` — коли востаннє змінився state (`online`/`idle`/`offline`)
- `online_since` — початок поточної online-сесії (спільний для `online` і `idle`)
- `offline_since` — початок поточної offline-сесії

Правила:

- `online` ↔ `idle` змінює лише `state_changed_at`, але не скидає `online_since`
- `online/idle` → `offline` скидає `online_since` і встановлює `offline_since`
- `offline` → `online` стартує нову сесію (`online_since = now`, `offline_since = null`)
- `offline` → `idle` вважається невалідним переходом і нормалізується до `offline → online` (новий сеанс)
- якщо стан не змінився в наступному poll, `state_changed_at` / `online_since` / `offline_since` залишаються без змін (stable timestamps)
- backend повертає ці timestamps у raw ISO-8601 вигляді без перерахунку на кожному poll

### Entity classification

- `entity_type = client` — звичайний клієнт (DHCP/ARP, не локальний інтерфейс)
- `entity_type = interface` — локальний MAC інтерфейсу MikroTik
- `interface_name` — імʼя інтерфейсу (наприклад `ether3`)
- `badges` — список незалежних badge (`PERM`, `INTERFACE`, `LINK-LOCAL`)

## Приклад unified JSON

```json
[
  {
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "ip_address": "192.168.88.10",
    "host_name": "workstation-01",
    "source": "dhcp+arp",
    "dhcp_status": "bound",
    "arp_status": "reachable",
    "arp_state": "online",
    "dhcp_flags": ["dynamic"],
    "arp_flags": ["dynamic", "complete"],
    "dhcp_comment": "Office host",
    "arp_comment": "",
    "arp_type": "dynamic",
    "created_by": "mikrotrack"
  }
]
```

---

## 🇬🇧 English

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
- `derived state` → `arp_state`
- `dynamic`/router flags → `arp_flags`
- `comment` → `arp_comment`

## Bridge Host fields

MikroTrack reads bridge host table from `/interface/bridge/host/print` and normalizes:

- `mac-address` → `mac_address`
- `interface` → `bridge_host_interface`
- `last-seen` → `bridge_host_last_seen`
- derived flag → `bridge_host_present`

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
- `delay`
- `probe`
- `failed`
- `incomplete`
- `permanent`

### Device state mapping (ARP + Bridge Host fusion)

- `reachable` ARP → `online` (highest priority)
- if `bridge_host_present = true` → `online`
- `stale` / `delay` / `probe` → `idle`
- `failed` / `incomplete` → `offline`
- `permanent` + no bridge host → `unknown` + `PERM` badge
- unknown values → `unknown`

> `permanent` alone must not be interpreted as `online`; it is a badge, not a state.

### Session-aware time model

- `state_changed_at` — timestamp of the most recent state transition (`online`/`idle`/`offline`)
- `online_since` — start of the current presence session (shared by `online` and `idle`)
- `offline_since` — start of the current offline session

Rules:

- `online` ↔ `idle` updates only `state_changed_at`, keeping `online_since`
- `online/idle` → `offline` resets `online_since` and sets `offline_since`
- `offline` → `online` starts a new session (`online_since = now`, `offline_since = null`)
- `offline` → `idle` is considered invalid and is normalized as `offline → online` (new session)
- if state does not change on the next poll, `state_changed_at` / `online_since` / `offline_since` must stay unchanged (stable timestamps)
- backend returns these values as raw ISO-8601 timestamps instead of recalculating them every poll

### Entity classification

- `entity_type = client` — normal client host (DHCP/ARP, not local interface)
- `entity_type = interface` — local MikroTik interface MAC
- `interface_name` — interface name (for example `ether3`)
- `badges` — independent badge list (`PERM`, `INTERFACE`, `LINK-LOCAL`)
