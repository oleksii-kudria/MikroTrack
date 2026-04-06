# MikroTrack

## 🇺🇦 Українською

MikroTrack — це lightweight collector для моніторингу мережі на MikroTik.

Збирає:
- DHCP leases
- ARP table

Формує:
- єдину модель пристрою (unified device model)

### Архітектура (коротко)

- лише collector
- persistence через JSON snapshots
- без API
- без UI

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

### Snapshot diff

Після кожного нового snapshot (починаючи з другого файлу) застосунок виконує diff з попереднім snapshot та логує:

- нові пристрої
- зниклі пристрої
- зміни IP
- зміни hostname

У логах також виводиться summary:

- `new`
- `removed`
- `changed`

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

- collector only
- JSON snapshot persistence
- no API
- no UI

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

### Snapshot diff

After each new snapshot (starting from the second file), the app computes a diff against the previous snapshot and logs:

- new devices
- removed devices
- IP changes
- hostname changes

It also prints a diff summary with:

- `new`
- `removed`
- `changed`

### Documentation

- MikroTik setup → [`docs/mikrotik-setup.md`](docs/mikrotik-setup.md)
- Device model → [`docs/device-model.md`](docs/device-model.md)
- Scheduler → [`docs/scheduler.md`](docs/scheduler.md)
- Storage → [`docs/storage.md`](docs/storage.md)
- Troubleshooting → [`docs/troubleshooting.md`](docs/troubleshooting.md)
- Architecture → [`docs/architecture.md`](docs/architecture.md)
