# MikroTrack

## 🇺🇦 Українською

MikroTrack — це lightweight collector для моніторингу мережі на MikroTik.

Збирає:
- DHCP leases
- ARP table

Формує:
- єдину модель пристрою (unified device model)

### Архітектура (коротко)

- collector + API (app container)
- persistence через JSON snapshots + events.jsonl
- web UI (окремий web container)
- без окремої БД

### Quick Start

```bash
git clone <repo-url>
cd MikroTrack
cp .env.example .env
docker compose up --build
```

### Основні параметри

- `LOG_LEVEL`
- `RUN_MODE`
- `COLLECTION_INTERVAL`
- `PRINT_RESULT_TO_STDOUT`
- `PERSISTENCE_ENABLED`
- `PERSISTENCE_PATH`
- `PERSISTENCE_RETENTION_DAYS`
- `IDLE_TIMEOUT_SECONDS`
- `API_ENABLED`
- `API_HOST` / `API_PORT`
- `WEB_HOST` / `WEB_PORT`
- `BACKEND_API_URL`

### Persistence

Snapshot-файли зберігаються у директорії `PERSISTENCE_PATH`.

- Формат імені: `YYYY-MM-DDTHH-MM-SS.json`
- Збереження вмикається через `PERSISTENCE_ENABLED=true`
- Автоматично створюється директорія, якщо її ще немає
- На старті виконується перевірка шляху, прав запису та вільного місця
- Старі файли видаляються за політикою `PERSISTENCE_RETENTION_DAYS`

Приклад:

```env
PERSISTENCE_ENABLED=true
PERSISTENCE_PATH=/data/snapshots
PERSISTENCE_RETENTION_DAYS=7
IDLE_TIMEOUT_SECONDS=900
```

### Event-driven diff

Після кожного нового snapshot (починаючи з другого файлу) застосунок виконує event-driven diff з попереднім snapshot за MAC-ключем з fallback:

- `mac_address` (пріоритет)
- `mac` (fallback)

Якщо обох ключів немає, запис пропускається з warning логом:

- `WARNING persistence: skipping device without MAC key`

Це виправляє кейс, коли `events.jsonl` не створювався для snapshot-ів, що містили лише `mac`.

Уся внутрішня datetime-логіка diff нормалізується до timezone-aware UTC:

- legacy snapshot-и без timezone (наприклад, `2026-04-10T19:41:29`) підтримуються та трактуються як UTC
- значення із `Z` та `+00:00` також підтримуються
- нові timestamps (`state_changed_at`, `online_since`, `idle_since`, `offline_since`, event `timestamp`) записуються у єдиному форматі з offset, наприклад `2026-04-10T19:47:01+00:00`

Логи (DEBUG) містять події:

- presence: `NEW_DEVICE`, `DEVICE_REMOVED`
- extended diff: `FIELD_CHANGE` (`state`, `ip_address`, `hostname`, `dhcp_lease_type`, `dhcp_presence`, `dhcp_flags`, `arp_flags`, `dhcp_comment`, `arp_comment`, `source`)
- identity: `IP_CHANGED`, `HOSTNAME_CHANGED`
- DHCP: `DHCP_ADDED`, `DHCP_REMOVED`, `DHCP_DYNAMIC_CHANGED`, `DHCP_STATUS_CHANGED`, `DHCP_COMMENT_CHANGED`
- ARP: `ARP_ADDED`, `ARP_REMOVED`, `ARP_DYNAMIC_CHANGED`, `ARP_FLAG_CHANGED`
- source: `SOURCE_CHANGED`
- combined: `DEVICE_IP_ASSIGNMENT_CHANGED`

Кожна подія перед записом у `events.jsonl` проходить safe serialization у `PERSISTENCE_PATH` (готовність для web UI):

- `datetime` → ISO-8601 string через `isoformat()`
- `set` / `tuple` → `list`
- `bytes` → UTF-8 string (або `repr(...)`, якщо декодування неможливе)
- `dict` / `list` → рекурсивна нормалізація
- інші нестандартні типи → `str(value)`

Якщо конкретна подія не серіалізується навіть після нормалізації, diff не падає: у логи записуються `event_type`, `mac`, payload та stack trace (`logger.exception`), а інші події продовжують зберігатися.

`FIELD_CHANGE` подія містить: `device_mac`, `field_name`, `previous_value`, `current_value`, `timestamp`.

У логах INFO є summary:

- `new`
- `removed`
- `changed`
- `events`

### Last known IP/hostname for offline devices (DHCP expiration)

When a device goes `offline` and DHCP lease later disappears, MikroTrack keeps the latest known identity fields:

- `ip_address`
- `host_name`

Snapshot enrichment also stores:

- `last_known_ip`
- `last_known_hostname`
- stale flags (`ip_is_stale`, `hostname_is_stale`, `data_is_stale`)

In Web UI, stale values are rendered with a muted style and `STALE` badge/tooltip so operators understand this is last known data.

### Web UI: toolbar, filters, mode, summary

У вкладці Devices toolbar працює як єдина система:

- Layout побудовано у логічному потоці: `Filters → Mode → Summary → Actions`.
- Active filters відображаються як **ті самі badge-компоненти**, що й у таблиці (без окремих стилів).
- Active filters клікабельні (hover/pointer/active) і підтримують очищення як через `Clear ✕`, так і прямим кліком по badge.
- `Mode` має 2 стани:
  - `End` (за замовчуванням): приховує `BRIDGE`, `COMPLETE`, `INTERFACE` та пристрої зі статусом `unknown`.
  - `All`: показує всі записи.
- `Devices: X | ...` summary рахується **тільки з dataset поточного mode** (End/All), але **не залежить від filters**.

Порядок обробки:

1. Завантажується повний набір даних
2. Застосовується display mode (`End` / `All`)
3. Рахується summary для dataset поточного mode
4. Застосовуються активні filters (status/assignment) для таблиці
5. Застосовується сортування
6. Відбувається рендер таблиці

Кольори статусів уніфіковані між status dot, badge та summary.

### Web UI: сортування таблиці Devices

- Підтримується тільки **single-column sorting**.
- Стан сортування для кожного заголовка: `none → asc → desc`.
- Якщо користувач обрав стовпчик, застосовується лише це explicit sorting (без multi-column chaining).
- Якщо explicit sorting не обрано, використовується default порядок:
  1. `online`
  2. `idle`
  3. `offline`
  4. `unknown`
- Усередині статусних груп:
  - `online` → `online_since`
  - `idle` → `idle_since`
  - `offline` → `offline_since`
  - `unknown` → тільки алфавітне сортування (без date fallback)
- Для `unknown` і для порожніх значень діє стабільна deterministic поведінка без прихованих режимів.

### Документація

- MikroTik setup → [`docs/mikrotik-setup.md`](docs/mikrotik-setup.md)
- Device model → [`docs/device-model.md`](docs/device-model.md)
- Scheduler → [`docs/scheduler.md`](docs/scheduler.md)
- Storage → [`docs/storage.md`](docs/storage.md)
- Troubleshooting → [`docs/troubleshooting.md`](docs/troubleshooting.md)
- Architecture → [`docs/architecture.md`](docs/architecture.md)

---

## 🇬🇧 English

MikroTrack is a lightweight network monitoring collector for MikroTik.

Collects:
- DHCP leases
- ARP table

Builds:
- unified device model

### Architecture (short)

- collector + API (app container)
- JSON snapshot + events.jsonl persistence
- web UI (separate web container)
- no dedicated DB

### Quick Start

```bash
git clone <repo-url>
cd MikroTrack
cp .env.example .env
docker compose up --build
```

### Key parameters

- `LOG_LEVEL`
- `RUN_MODE`
- `COLLECTION_INTERVAL`
- `PRINT_RESULT_TO_STDOUT`
- `PERSISTENCE_ENABLED`
- `PERSISTENCE_PATH`
- `PERSISTENCE_RETENTION_DAYS`
- `IDLE_TIMEOUT_SECONDS`
- `API_ENABLED`
- `API_HOST` / `API_PORT`
- `WEB_HOST` / `WEB_PORT`
- `BACKEND_API_URL`

### Persistence

Snapshot files are stored in `PERSISTENCE_PATH`.

- File name format: `YYYY-MM-DDTHH-MM-SS.json`
- Enable via `PERSISTENCE_ENABLED=true`
- Directory is created automatically if missing
- On startup, path, write permissions, and free disk space are validated
- Old files are removed using `PERSISTENCE_RETENTION_DAYS`

Example:

```env
PERSISTENCE_ENABLED=true
PERSISTENCE_PATH=/data/snapshots
PERSISTENCE_RETENTION_DAYS=7
IDLE_TIMEOUT_SECONDS=900
```

### Event-driven diff

After each new snapshot (starting from the second file), the app computes an event-driven diff against the previous snapshot using MAC key fallback:

- `mac_address` (priority)
- `mac` (fallback)

If both keys are missing, the record is skipped with a warning log:

- `WARNING persistence: skipping device without MAC key`

This fixes the case where `events.jsonl` was not created for snapshots containing only `mac`.

All internal diff datetimes are normalized to timezone-aware UTC values:

- legacy snapshots without timezone (for example, `2026-04-10T19:41:29`) are still supported and interpreted as UTC
- `Z` and `+00:00` timestamps are both supported
- new timestamps (`state_changed_at`, `online_since`, `idle_since`, `offline_since`, event `timestamp`) are persisted in one offset-aware format, for example `2026-04-10T19:47:01+00:00`

DEBUG logs include events:

- presence: `NEW_DEVICE`, `DEVICE_REMOVED`
- extended diff: `FIELD_CHANGE` (`state`, `ip_address`, `hostname`, `dhcp_lease_type`, `dhcp_presence`, `dhcp_flags`, `arp_flags`, `dhcp_comment`, `arp_comment`, `source`)
- identity: `IP_CHANGED`, `HOSTNAME_CHANGED`
- DHCP: `DHCP_ADDED`, `DHCP_REMOVED`, `DHCP_DYNAMIC_CHANGED`, `DHCP_STATUS_CHANGED`, `DHCP_COMMENT_CHANGED`
- ARP: `ARP_ADDED`, `ARP_REMOVED`, `ARP_DYNAMIC_CHANGED`, `ARP_FLAG_CHANGED`
- source: `SOURCE_CHANGED`
- combined: `DEVICE_IP_ASSIGNMENT_CHANGED`

Each event is safely normalized before JSONL persistence to `events.jsonl` under `PERSISTENCE_PATH` (ready for web UI integration):

- `datetime` → ISO-8601 string via `isoformat()`
- `set` / `tuple` → `list`
- `bytes` → UTF-8 string (or `repr(...)` when decoding fails)
- `dict` / `list` → recursive normalization
- other non-standard Python types → `str(value)`

If a specific event still cannot be serialized after normalization, diff does not crash: logs include `event_type`, `mac`, payload preview, and full stack trace (`logger.exception`), while other events continue to persist.

`FIELD_CHANGE` events contain: `device_mac`, `field_name`, `previous_value`, `current_value`, `timestamp`.

INFO logs include a summary with:

- `new`
- `removed`
- `changed`
- `events`

### Last known IP/hostname for offline devices (DHCP expiration)

When a device becomes `offline` and its DHCP lease is later removed, MikroTrack preserves the latest known identity fields:

- `ip_address`
- `host_name`

Snapshot enrichment also keeps:

- `last_known_ip`
- `last_known_hostname`
- stale flags (`ip_is_stale`, `hostname_is_stale`, `data_is_stale`)

In Web UI, stale values are displayed with muted styling and a `STALE` badge/tooltip to make it explicit that these are last known values.

### Web UI: toolbar, filters, mode, summary

In the Devices tab, the toolbar behaves as one coherent system:

- The layout follows a logical flow: `Filters → Mode → Summary → Actions`.
- Active filters use the **same badge component** as table badges (no separate filter-only styling).
- Active filters are clickable (hover/pointer/active) and can be cleared via `Clear ✕` or by clicking a filter badge directly.
- `Mode` has 2 states:
  - `End` (default): hides `BRIDGE`, `COMPLETE`, `INTERFACE`, and `unknown` status devices.
  - `All`: shows all records.
- `Devices: X | ...` summary is calculated **only from the current mode dataset** (End/All) and **does not depend on filters**.

Processing order:

1. Full dataset is loaded
2. Display mode (`End` / `All`) is applied
3. Summary is recalculated for the current mode dataset
4. Active filters (status/assignment) are applied to table rows
5. Sorting is applied
6. Rows are rendered

Status colors are unified across status dots, badges, and summary.

### Web UI: Devices table sorting

- Only **single-column sorting** is supported.
- Header click state is `none → asc → desc`.
- When a user picks a column, only that explicit sort is applied (no multi-column chaining).
- When no explicit sort is selected, default ordering is used:
  1. `online`
  2. `idle`
  3. `offline`
  4. `unknown`
- Within status groups:
  - `online` → `online_since`
  - `idle` → `idle_since`
  - `offline` → `offline_since`
  - `unknown` → alphabetical only (no date fallback)
- `unknown` and empty values use stable deterministic behavior with no hidden sort modes.

### Documentation

- MikroTik setup → [`docs/mikrotik-setup.md`](docs/mikrotik-setup.md)
- Device model → [`docs/device-model.md`](docs/device-model.md)
- Scheduler → [`docs/scheduler.md`](docs/scheduler.md)
- Storage → [`docs/storage.md`](docs/storage.md)
- Troubleshooting → [`docs/troubleshooting.md`](docs/troubleshooting.md)
- Architecture → [`docs/architecture.md`](docs/architecture.md)
