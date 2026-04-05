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
- без persistence (поки що)
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

### Документація

- MikroTik setup → [`docs/mikrotik-setup.md`](docs/mikrotik-setup.md)
- Device model → [`docs/device-model.md`](docs/device-model.md)
- Scheduler → [`docs/scheduler.md`](docs/scheduler.md)
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
- no persistence (yet)
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

### Documentation

- MikroTik setup → [`docs/mikrotik-setup.md`](docs/mikrotik-setup.md)
- Device model → [`docs/device-model.md`](docs/device-model.md)
- Scheduler → [`docs/scheduler.md`](docs/scheduler.md)
- Troubleshooting → [`docs/troubleshooting.md`](docs/troubleshooting.md)
- Architecture → [`docs/architecture.md`](docs/architecture.md)
