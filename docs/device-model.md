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
- `permanent` + `bridge_host_present = true` → `online` + badge `PERM`
- `permanent` + `bridge_host_present = false` → `idle` + badge `PERM`
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
- `offline_since` є source of truth для завершення попередньої сесії: якщо поле присутнє у snapshot, попередній effective state завжди примусово трактується як `offline` (незалежно від `online_since` або сирого ARP)
- повторне підключення після `offline` (включно з появою через `bridge_host_present = true`) завжди створює нову session boundary: `online_since = now`, `idle_since = null`, `offline_since = null`
- `offline` є стабільним станом: `offline → offline` не створює нову session boundary і не перезапускає таймер (`offline_since` та `state_changed_at` зберігаються)
- `offline` → `idle` більше не вважається автоматичним reconnect: перехід у `online` дозволено лише за наявності нових evidence (`bridge_host_present = true` або ARP `reachable`/`complete`); без evidence стан лишається `offline`
- для `PERM` (`arp_status = permanent`) значення `bridge_host_present = false` забороняє false reconnect `offline → online`: навіть якщо fused/raw state коливається до `idle`, persisted presence лишається `offline` до появи реального signal
- якщо `active = false`, `bridge_host_present = false` і `idle_duration_seconds >= IDLE_TIMEOUT_SECONDS`, пристрій примусово переходить у `offline` (включно з `arp_status = permanent` / badge `PERM`)
- API (`/api/devices`) застосовує той самий timeout-захист: якщо `idle_since` уже прострочений, `bridge_host_present = false`, а `offline_since` ще відсутній у snapshot, API все одно повертає `status = offline` і `flags.state = offline`
- якщо стан не змінився в наступному poll, `state_changed_at` / `online_since` / `offline_since` залишаються без змін (stable timestamps)
- backend повертає ці timestamps у raw ISO-8601 вигляді без перерахунку на кожному poll
- API має пріоритет подій над snapshot: якщо `events.state_changed_at >= snapshot.state_changed_at`, використовуються `state_changed_at` / `online_since` / `idle_since` / `offline_since` із events (щоб `SESSION_STARTED` завжди скидав `online_since`)

### UI live timers + tooltip absolute timestamps

- Frontend рендерить відносний час самостійно (на основі `Date.now()` + raw timestamps з API), без додаткових API-викликів.
- Таймер оновлюється щосекунди, тому значення не "стрибають" лише раз на poll.
- Для `online` таймер рахується від `online_since`, tooltip: `Online since: HH:MM`.
- Для `idle` таймер також рахується від `online_since`, tooltip містить два рядки: `Online since` + `Idle since` (`state_changed_at`).
- Для `offline` таймер рахується від `offline_since`, tooltip: `Offline since: HH:MM`.
- Для fallback-сценарію `unknown` таймер рахується від `state_changed_at`, tooltip: `Last change: HH:MM`.
- Формат відносного часу:
  - `< 1h` → `MM:SS`
  - `>= 1h` → `HH:MM:SS`
  - `>= 1 day` → `N day(s) ago`

### Entity classification

- `entity_type = client` — звичайний клієнт (DHCP/ARP, не локальний інтерфейс)
- `entity_type = interface` — локальний MAC інтерфейсу MikroTik
- `interface_name` — імʼя інтерфейсу (наприклад `ether3`)
- `badges` — список незалежних badge (`PERM`, `INTERFACE`, `LINK-LOCAL`)

### Last known identity for offline devices

Коли пристрій переходить у `offline` і DHCP lease зникає в наступних poll'ах:

- `ip_address` може бути відновлений із попереднього snapshot
- `host_name` може бути відновлений із попереднього snapshot

Додатково зберігаються:

- `last_known_ip`
- `last_known_hostname`
- `ip_is_stale`
- `hostname_is_stale`
- `data_is_stale`

UI показує такі поля як last known (badge `STALE` + tooltip).

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
- `permanent` + `bridge_host_present = true` → `online` + `PERM` badge
- `permanent` + `bridge_host_present = false` → `idle` + `PERM` badge
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
- `offline_since` is the source of truth for session termination: if this field exists in the snapshot, the previous effective state is always force-resolved as `offline` (regardless of `online_since` or raw ARP evidence)
- reconnect after `offline` (including recovery via `bridge_host_present = true`) always creates a new session boundary: `online_since = now`, `idle_since = null`, `offline_since = null`
- `offline` is a stable state: `offline → offline` must not create a new session boundary or restart timers (`offline_since` and `state_changed_at` are preserved)
- `offline` → `idle` is no longer treated as an automatic reconnect: promotion to `online` is allowed only with fresh evidence (`bridge_host_present = true` or ARP `reachable`/`complete`); without evidence the device remains `offline`
- for `PERM` devices (`arp_status = permanent`), `bridge_host_present = false` explicitly blocks false reconnects `offline → online`: even if fused/raw state briefly oscillates to `idle`, persisted presence stays `offline` until real evidence appears
- if `active = false`, `bridge_host_present = false`, and `idle_duration_seconds >= IDLE_TIMEOUT_SECONDS`, device is force-transitioned to `offline` (including `arp_status = permanent` / `PERM` badge)
- API (`/api/devices`) applies the same timeout safeguard: if `idle_since` is already expired, `bridge_host_present = false`, and `offline_since` is still missing in the snapshot, the API still resolves `status = offline` and `flags.state = offline`
- if state does not change on the next poll, `state_changed_at` / `online_since` / `offline_since` must stay unchanged (stable timestamps)
- backend returns these values as raw ISO-8601 timestamps instead of recalculating them every poll
- API gives event data higher priority than snapshot fields: if `events.state_changed_at >= snapshot.state_changed_at`, `state_changed_at` / `online_since` / `idle_since` / `offline_since` are taken from events (so `SESSION_STARTED` always resets `online_since`)

### UI live timers + absolute timestamp tooltip

- The frontend renders relative time on its own (`Date.now()` + raw API timestamps), without extra API calls.
- The timer updates every second, so values stay smooth instead of jumping once per collector poll.
- For `online`, the timer starts at `online_since`; tooltip: `Online since: HH:MM`.
- For `idle`, the timer also starts at `online_since`; tooltip shows two lines: `Online since` and `Idle since` (`state_changed_at`).
- For `offline`, the timer starts at `offline_since`; tooltip: `Offline since: HH:MM`.
- For the `unknown` fallback, the timer starts at `state_changed_at`; tooltip: `Last change: HH:MM`.
- Relative-time format:
  - `< 1h` → `MM:SS`
  - `>= 1h` → `HH:MM:SS`
  - `>= 1 day` → `N day(s) ago`

### Entity classification

- `entity_type = client` — normal client host (DHCP/ARP, not local interface)
- `entity_type = interface` — local MikroTik interface MAC
- `interface_name` — interface name (for example `ether3`)
- `badges` — independent badge list (`PERM`, `INTERFACE`, `LINK-LOCAL`)

### Last known identity for offline devices

When a device is `offline` and its DHCP lease disappears in later polls:

- `ip_address` can be restored from the previous snapshot
- `host_name` can be restored from the previous snapshot

Additional persisted fields:

- `last_known_ip`
- `last_known_hostname`
- `ip_is_stale`
- `hostname_is_stale`
- `data_is_stale`

UI renders these as last known values (with `STALE` badge + tooltip).
