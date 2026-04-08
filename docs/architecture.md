# Architecture

## 🇺🇦 Українською

## Поточний стан: Collector + JSON persistence

MikroTrack зараз працює як **collector-сервіс** із JSON snapshots.

Відповідальність:

- підключення до MikroTik через RouterOS API (SSL)
- збір DHCP leases, ARP entries та Bridge Host entries
- нормалізація і обʼєднання у unified device model
- вивід результату у логи/stdout
- збереження snapshot у JSON (за потреби)

## Майбутнє: Storage

Наступний етап storage шару:

- snapshots + diff
- optional relational DB
- retention та історія змін

## Майбутнє: API

Планований API шар:

- доступ до останнього snapshot
- query/filter для пристроїв
- health/status endpoint

## Майбутнє: UI

Планований UI шар:

- dashboard для мережевої видимості
- searchable table пристроїв
- статуси та troubleshooting hints

---

## 🇬🇧 English

## Current: Collector + JSON persistence

MikroTrack currently runs as a **collector service** with JSON snapshots.

Responsibilities:

- connect to MikroTik via RouterOS API (SSL)
- collect DHCP leases, ARP entries, and Bridge Host entries
- normalize and merge data into a unified device model
- output data to logs/stdout
- persist snapshots to JSON (optional)

## Future: Storage

Next storage layer direction:

- snapshots + diff
- optional relational DB
- retention and history policies

## Future: API

Planned API layer:

- access latest snapshot
- query/filter devices
- health/status endpoint

## Future: UI

Planned UI layer:

- dashboard for device visibility
- searchable device table
- status indicators and troubleshooting hints
