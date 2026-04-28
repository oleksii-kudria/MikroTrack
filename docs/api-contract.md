# Web UI API Contract

## 🇺🇦 Українською

Цей документ фіксує **стабільний контракт** між backend (`collector` + `API`) та Web UI для endpoint `GET /api/devices` (alias: `GET /api/v1/devices`).

## Endpoint

- **Method:** `GET`
- **Path:** `/api/devices`
- **Alias:** `/api/v1/devices`
- **Response content type:** `application/json`

## Response format

```json
{
  "items": [
    {
      "mac": "AA:BB:CC:DD:EE:FF",
      "is_random_mac": false,
      "mac_vendor": "Apple, Inc.",
      "ip": "192.168.1.10",
      "hostname": "laptop",
      "status": "online",
      "state_changed_at": "2026-04-10T19:00:00+00:00",
      "online_since": "2026-04-10T19:00:00+00:00",
      "idle_since": null,
      "offline_since": null,
      "last_known_ip": "192.168.1.10",
      "last_known_hostname": "laptop",
      "ip_is_stale": false,
      "hostname_is_stale": false,
      "data_is_stale": false,
      "comments": "dhcp: Office laptop",
      "comments_badge": "DHCP: Office laptop",
      "badges": ["PERM"],
      "entity_type": "client",
      "active": true,
      "flags": {
        "source": "dhcp+arp",
        "dhcp_flag": "D",
        "has_dhcp_lease": true,
        "has_arp_entry": true,
        "bridge_host_present": true,
        "arp_flag": "DC",
        "state": "online"
      }
    }
  ],
  "generated_at": "2026-04-10T19:05:00+00:00"
}
```

## Device field contract (`items[]`)

> Принцип стабільності: поля нижче **завжди присутні** у відповіді одного device. Якщо даних немає — повертається `null`, `""`, `false`, `[]` або `"-"` (залежно від поля), але поле не зникає.

### 1) Core identity

| Field | Type | Required | Nullable | Source class | Description |
|---|---|---|---|---|---|
| `mac` | string | yes | no | raw | Device MAC (канонічний key для ідентичності). |
| `ip` | string | yes | no | raw/derived | Поточний `ip_address` зі snapshot; може бути `""`. |
| `hostname` | string | yes | no | raw/derived | Поточний `host_name`; може бути `""`. |
| `is_random_mac` | boolean | yes | no | computed | Ознака random/local MAC, обчислюється backend напряму з MAC бітів. |
| `mac_vendor` | string | yes | yes | computed | Назва вендора за OUI або `null` для невалідного/unknown OUI; для random MAC — informational-only. |

### 2) State/session

| Field | Type | Required | Nullable | Source class | Description |
|---|---|---|---|---|---|
| `status` | string enum | yes | no | computed | Effective state для UI: `online \| idle \| offline \| unknown`. |
| `state_changed_at` | string (ISO-8601) | yes | yes | computed | Останній момент зміни presence state. |
| `online_since` | string (ISO-8601) | yes | yes | computed | Початок поточної online-сесії. |
| `idle_since` | string (ISO-8601) | yes | yes | computed | Час переходу в `idle` у межах online-сесії. |
| `offline_since` | string (ISO-8601) | yes | yes | computed | Початок поточної offline-сесії. |

### 3) Last-known identity

| Field | Type | Required | Nullable | Source class | Description |
|---|---|---|---|---|---|
| `last_known_ip` | string | yes | no | computed | Остання відома IP для offline/partial snapshot. |
| `last_known_hostname` | string | yes | no | computed | Останній відомий hostname. |
| `ip_is_stale` | boolean | yes | no | computed | `true`, якщо `last_known_ip` застарілий відносно поточного стану. |
| `hostname_is_stale` | boolean | yes | no | computed | `true`, якщо `last_known_hostname` застарілий. |
| `data_is_stale` | boolean | yes | no | computed | Узагальнений stale-індикатор для UI. |

### 4) Flags/source

| Field | Type | Required | Nullable | Source class | Description |
|---|---|---|---|---|---|
| `flags.source` | string | yes | no | raw/derived | Джерело у форматі `dhcp+arp`, `arp`, `dhcp`, `-` тощо. |
| `flags.dhcp_flag` | string | yes | yes | computed | `D`/`S` для lease-типу; `null`, якщо lease відсутній. |
| `flags.arp_flag` | string | yes | yes | computed | `D`/`S` + optional `C`; `null`, якщо ARP entry відсутній. |
| `flags.has_dhcp_lease` | boolean | yes | no | raw/derived | Наявність DHCP lease. |
| `flags.has_arp_entry` | boolean | yes | no | raw/derived | Наявність ARP entry. |
| `flags.bridge_host_present` | boolean | yes | no | raw/derived | Bridge host evidence of presence. |
| `flags.state` | string enum | yes | no | computed | Дублює effective state (`status`) для backward-compatible UI logic. |

### 5) Derived/UI helper fields

| Field | Type | Required | Nullable | Source class | Description |
|---|---|---|---|---|---|
| `comments` | string | yes | no | UI helper | Обʼєднане представлення `dhcp_comment` + `arp_comment`, fallback `"-"`. |
| `comments_badge` | string | yes | no | UI helper | Коротке badge-представлення comments, fallback `"-"`. |
| `badges` | array[string] | yes | no | computed/UI helper | Нормалізований список badge (`PERM`, `INTERFACE`, `LINK-LOCAL`, ...). |
| `entity_type` | string enum | yes | no | computed | `client` або `interface`. |
| `active` | boolean | yes | no | computed/UI helper | `true` тільки коли `status == online`. |

## Raw vs computed vs UI helper

- **Raw (collector/snapshot):** MAC/IP/hostname базові значення, source fragments, DHCP/ARP evidence.
- **Computed (backend state logic):** `status`, `*_since`, stale-поля, flags (`dhcp_flag`, `arp_flag`, `has_*`).
- **UI helper (presentation contract):** `comments`, `comments_badge`, `active`, normalized `badges`.

Backend зобовʼязаний зберігати ці групи сумісними між релізами: UI не повинен відновлювати state logic на клієнті.

## Null behavior guarantees

### General

- Для contract-полів немає режиму «іноді є / іноді нема».
- Коли значення невідоме — повертається `null` (для timestamp/optional flag), а не видаляється поле.

### State-dependent timestamps

- `unknown` → `state_changed_at` може бути `null`; `online_since = null`; `idle_since = null`; `offline_since = null`.
- `online` → `online_since` non-null; `idle_since = null`; `offline_since = null`.
- `idle` → `online_since` non-null; `idle_since` non-null; `offline_since = null`.
- `offline` → `offline_since` non-null; `online_since = null`; `idle_since = null`.

### Last-known fallback

- Якщо поточний `ip` порожній, backend повертає `last_known_ip` (за наявності) + `ip_is_stale=true`.
- Якщо поточний `hostname` порожній, backend повертає `last_known_hostname` (за наявності) + `hostname_is_stale=true`.
- `data_is_stale=true`, якщо будь-яка identity частина працює як last-known.

## Sorting dependencies (UI)

UI sorting залежить від стабільно гарантованих backend-полів:

- primary state bucket: `status` (`online → idle → offline → unknown`)
- within-state timing: `online_since`, `idle_since`, `offline_since`, fallback `state_changed_at`
- lexicographic fallback: `hostname`, далі `ip`

Backend гарантує, що ці поля завжди присутні у `items[]` з очікуваними типами.

## API guarantees

Backend гарантує для `GET /api/devices`:

1. **Stable structure:** `{"items": [...], "generated_at": ...}`.
2. **Stable device keys:** перелік contract-полів не флуктуює між запитами.
3. **Predictable nullability:** nullable-поля повертаються як `null`, не пропускаються.
4. **Consistent names:** ті самі field names для всіх devices.
5. **Deterministic derived values:** state/flags/UI helper fields формуються backend-логікою, а не frontend re-implementation.

---

## 🇬🇧 English

This document defines the **stable contract** between backend (`collector` + `API`) and Web UI for `GET /api/devices` (alias: `GET /api/v1/devices`).

## Endpoint

- **Method:** `GET`
- **Path:** `/api/devices`
- **Alias:** `/api/v1/devices`
- **Response content type:** `application/json`

## Response format

```json
{
  "items": [
    {
      "mac": "AA:BB:CC:DD:EE:FF",
      "is_random_mac": false,
      "mac_vendor": "Apple, Inc.",
      "ip": "192.168.1.10",
      "hostname": "laptop",
      "status": "online",
      "state_changed_at": "2026-04-10T19:00:00+00:00",
      "online_since": "2026-04-10T19:00:00+00:00",
      "idle_since": null,
      "offline_since": null,
      "last_known_ip": "192.168.1.10",
      "last_known_hostname": "laptop",
      "ip_is_stale": false,
      "hostname_is_stale": false,
      "data_is_stale": false,
      "comments": "dhcp: Office laptop",
      "comments_badge": "DHCP: Office laptop",
      "badges": ["PERM"],
      "entity_type": "client",
      "active": true,
      "flags": {
        "source": "dhcp+arp",
        "dhcp_flag": "D",
        "has_dhcp_lease": true,
        "has_arp_entry": true,
        "bridge_host_present": true,
        "arp_flag": "DC",
        "state": "online"
      }
    }
  ],
  "generated_at": "2026-04-10T19:05:00+00:00"
}
```

## Device field contract (`items[]`)

> Stability rule: all fields listed below are always present for each device item. If data is missing, the API returns `null`, `""`, `false`, `[]`, or `"-"` (field-specific), but never drops the field.

### 1) Core identity

| Field | Type | Required | Nullable | Source class | Description |
|---|---|---|---|---|---|
| `mac` | string | yes | no | raw | Device MAC (canonical identity key). |
| `ip` | string | yes | no | raw/derived | Current `ip_address` from snapshot; may be `""`. |
| `hostname` | string | yes | no | raw/derived | Current `host_name`; may be `""`. |
| `is_random_mac` | boolean | yes | no | computed | Random/local MAC flag computed directly from MAC bit structure. |
| `mac_vendor` | string | yes | yes | computed | Vendor resolved by OUI or `null` for invalid/unknown OUI; for random MAC it is informational-only. |

### 2) State/session

| Field | Type | Required | Nullable | Source class | Description |
|---|---|---|---|---|---|
| `status` | string enum | yes | no | computed | Effective UI state: `online \| idle \| offline \| unknown`. |
| `state_changed_at` | string (ISO-8601) | yes | yes | computed | Latest presence-state transition timestamp. |
| `online_since` | string (ISO-8601) | yes | yes | computed | Start of the current online session. |
| `idle_since` | string (ISO-8601) | yes | yes | computed | Timestamp when the device entered `idle` in the current online session. |
| `offline_since` | string (ISO-8601) | yes | yes | computed | Start of the current offline session. |

### 3) Last-known identity

| Field | Type | Required | Nullable | Source class | Description |
|---|---|---|---|---|---|
| `last_known_ip` | string | yes | no | computed | Last known IP for offline/partial snapshot cases. |
| `last_known_hostname` | string | yes | no | computed | Last known hostname. |
| `ip_is_stale` | boolean | yes | no | computed | `true` when `last_known_ip` is stale vs current state. |
| `hostname_is_stale` | boolean | yes | no | computed | `true` when `last_known_hostname` is stale. |
| `data_is_stale` | boolean | yes | no | computed | Consolidated stale indicator for UI. |

### 4) Flags/source

| Field | Type | Required | Nullable | Source class | Description |
|---|---|---|---|---|---|
| `flags.source` | string | yes | no | raw/derived | Source aggregate, e.g. `dhcp+arp`, `arp`, `dhcp`, `-`. |
| `flags.dhcp_flag` | string | yes | yes | computed | `D`/`S` lease type; `null` when no lease exists. |
| `flags.arp_flag` | string | yes | yes | computed | `D`/`S` with optional `C`; `null` when no ARP entry exists. |
| `flags.has_dhcp_lease` | boolean | yes | no | raw/derived | DHCP lease presence flag. |
| `flags.has_arp_entry` | boolean | yes | no | raw/derived | ARP entry presence flag. |
| `flags.bridge_host_present` | boolean | yes | no | raw/derived | Bridge-host presence evidence. |
| `flags.state` | string enum | yes | no | computed | Mirrors effective `status` for backward-compatible UI logic. |

### 5) Derived/UI helper fields

| Field | Type | Required | Nullable | Source class | Description |
|---|---|---|---|---|---|
| `comments` | string | yes | no | UI helper | Combined `dhcp_comment` + `arp_comment`, fallback `"-"`. |
| `comments_badge` | string | yes | no | UI helper | Compact comment badge label, fallback `"-"`. |
| `badges` | array[string] | yes | no | computed/UI helper | Normalized badge list (`PERM`, `INTERFACE`, `LINK-LOCAL`, ...). |
| `entity_type` | string enum | yes | no | computed | `client` or `interface`. |
| `active` | boolean | yes | no | computed/UI helper | `true` only when `status == online`. |

## Raw vs computed vs UI helper

- **Raw (collector/snapshot):** base MAC/IP/hostname values, source fragments, DHCP/ARP evidence.
- **Computed (backend state logic):** `status`, `*_since`, stale fields, flags (`dhcp_flag`, `arp_flag`, `has_*`).
- **UI helper (presentation contract):** `comments`, `comments_badge`, `active`, normalized `badges`.

Backend owns these transformations; UI must consume them as contract outputs.

## Null behavior guarantees

### General

- No "sometimes present / sometimes missing" behavior for contract fields.
- Unknown values are returned as `null` (for timestamp/optional flags), not by omitting keys.

### State-dependent timestamps

- `unknown` → `state_changed_at` may be `null`; `online_since = null`; `idle_since = null`; `offline_since = null`.
- `online` → `online_since` non-null; `idle_since = null`; `offline_since = null`.
- `idle` → `online_since` non-null; `idle_since` non-null; `offline_since = null`.
- `offline` → `offline_since` non-null; `online_since = null`; `idle_since = null`.

### Last-known fallback

- If current `ip` is empty, backend returns `last_known_ip` when available, with `ip_is_stale=true`.
- If current `hostname` is empty, backend returns `last_known_hostname` when available, with `hostname_is_stale=true`.
- `data_is_stale=true` when any identity component is served as last-known.

## Sorting dependencies (UI)

UI sorting depends on backend-guaranteed fields:

- primary state bucket: `status` (`online → idle → offline → unknown`)
- within-state timing: `online_since`, `idle_since`, `offline_since`, fallback `state_changed_at`
- lexical fallback: `hostname`, then `ip`

Backend guarantees these fields are always present in `items[]` with stable names and types.

## API guarantees

For `GET /api/devices`, backend guarantees:

1. **Stable envelope:** `{"items": [...], "generated_at": ...}`.
2. **Stable device keys:** contract field set does not fluctuate per request.
3. **Predictable nullability:** nullable fields return `null`, not missing keys.
4. **Consistent naming:** same field names for all devices.
5. **Deterministic derived values:** state/flags/UI helper fields are backend-authored, not frontend re-implemented.

## Optional JSON Schema snippet (bonus)

```json
{
  "type": "object",
  "required": ["items", "generated_at"],
  "properties": {
    "generated_at": { "type": "string", "format": "date-time" },
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "mac", "ip", "hostname", "status", "state_changed_at",
          "online_since", "idle_since", "offline_since",
          "last_known_ip", "last_known_hostname",
          "ip_is_stale", "hostname_is_stale", "data_is_stale",
          "comments", "comments_badge", "badges", "entity_type", "active", "flags"
        ],
        "properties": {
          "mac": { "type": "string" },
          "ip": { "type": "string" },
          "hostname": { "type": "string" },
          "status": { "enum": ["online", "idle", "offline", "unknown"] },
          "state_changed_at": { "type": ["string", "null"], "format": "date-time" },
          "online_since": { "type": ["string", "null"], "format": "date-time" },
          "idle_since": { "type": ["string", "null"], "format": "date-time" },
          "offline_since": { "type": ["string", "null"], "format": "date-time" },
          "last_known_ip": { "type": "string" },
          "last_known_hostname": { "type": "string" },
          "ip_is_stale": { "type": "boolean" },
          "hostname_is_stale": { "type": "boolean" },
          "data_is_stale": { "type": "boolean" },
          "comments": { "type": "string" },
          "comments_badge": { "type": "string" },
          "badges": { "type": "array", "items": { "type": "string" } },
          "entity_type": { "type": "string", "enum": ["client", "interface"] },
          "active": { "type": "boolean" },
          "flags": {
            "type": "object",
            "required": ["source", "dhcp_flag", "has_dhcp_lease", "has_arp_entry", "bridge_host_present", "arp_flag", "state"],
            "properties": {
              "source": { "type": "string" },
              "dhcp_flag": { "type": ["string", "null"] },
              "has_dhcp_lease": { "type": "boolean" },
              "has_arp_entry": { "type": "boolean" },
              "bridge_host_present": { "type": "boolean" },
              "arp_flag": { "type": ["string", "null"] },
              "state": { "enum": ["online", "idle", "offline", "unknown"] }
            }
          }
        }
      }
    }
  }
}
```
