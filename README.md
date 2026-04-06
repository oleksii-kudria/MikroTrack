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
```

### Event-driven diff

Після кожного нового snapshot (починаючи з другого файлу) застосунок виконує event-driven diff з попереднім snapshot за `mac_address` і фіксує кожну зміну стану пристрою.

Логи (DEBUG) містять події:

- presence: `NEW_DEVICE`, `DEVICE_REMOVED`
- identity: `IP_CHANGED`, `HOSTNAME_CHANGED`
- DHCP: `DHCP_ADDED`, `DHCP_REMOVED`, `DHCP_DYNAMIC_CHANGED`, `DHCP_STATUS_CHANGED`, `DHCP_COMMENT_CHANGED`
- ARP: `ARP_ADDED`, `ARP_REMOVED`, `ARP_DYNAMIC_CHANGED`, `ARP_FLAG_CHANGED`
- source: `SOURCE_CHANGED`
- combined: `DEVICE_IP_ASSIGNMENT_CHANGED`

Кожна подія має timestamp та серіалізується у `events.jsonl` в `PERSISTENCE_PATH` (готовність для web UI).

У логах INFO є summary:

- `new`
- `removed`
- `changed`
- `events`

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
```

### Event-driven diff

After each new snapshot (starting from the second file), the app computes an event-driven diff against the previous snapshot keyed by `mac_address` and records every device state transition.

DEBUG logs include events:

- presence: `NEW_DEVICE`, `DEVICE_REMOVED`
- identity: `IP_CHANGED`, `HOSTNAME_CHANGED`
- DHCP: `DHCP_ADDED`, `DHCP_REMOVED`, `DHCP_DYNAMIC_CHANGED`, `DHCP_STATUS_CHANGED`, `DHCP_COMMENT_CHANGED`
- ARP: `ARP_ADDED`, `ARP_REMOVED`, `ARP_DYNAMIC_CHANGED`, `ARP_FLAG_CHANGED`
- source: `SOURCE_CHANGED`
- combined: `DEVICE_IP_ASSIGNMENT_CHANGED`

Each event has a timestamp and is persisted to `events.jsonl` under `PERSISTENCE_PATH` (ready for web UI integration).

INFO logs include a summary with:

- `new`
- `removed`
- `changed`
- `events`

### Documentation

- MikroTik setup → [`docs/mikrotik-setup.md`](docs/mikrotik-setup.md)
- Device model → [`docs/device-model.md`](docs/device-model.md)
- Scheduler → [`docs/scheduler.md`](docs/scheduler.md)
- Storage → [`docs/storage.md`](docs/storage.md)
- Troubleshooting → [`docs/troubleshooting.md`](docs/troubleshooting.md)
- Architecture → [`docs/architecture.md`](docs/architecture.md)
