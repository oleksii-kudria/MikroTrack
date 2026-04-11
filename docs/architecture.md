# Architecture

## 🇺🇦 Українською

## Поточна runtime-архітектура (Phase 1 baseline)

MikroTrack уже має production-usable runtime без окремої БД:

- **mikrotrack-app container**
  - collector loop/once
  - RouterOS API integration
  - snapshot persistence (`*.json`)
  - event diff + `events.jsonl`
  - FastAPI endpoints: `/health`, `/api/v1/snapshots`, `/api/v1/snapshots/latest`, `/api/v1/events`, `/api/devices`
- **mikrotrack-web container**
  - FastAPI + template UI
  - timeline/events view
  - devices table UI (filters/mode/sorting/live timers)
  - backend proxy to `/api/devices`

## Data flow

1. Collector reads DHCP + ARP + bridge host + interface MAC sources.
2. Device builder merges data into unified device model keyed by MAC.
3. Persistence layer enriches stable timestamps and stale identity fields.
4. New snapshot is written into `PERSISTENCE_PATH`.
5. Diff vs previous snapshot generates events into `events.jsonl`.
6. API serves latest state; Web UI renders timeline and devices table.

## Storage model

- snapshots: one JSON file per cycle
- events: append-only `events.jsonl`
- retention: `PERSISTENCE_RETENTION_DAYS`

---

## 🇬🇧 English

## Current runtime architecture (Phase 1 baseline)

MikroTrack already provides a production-usable runtime without a dedicated DB:

- **mikrotrack-app container**
  - collector loop/once
  - RouterOS API integration
  - snapshot persistence (`*.json`)
  - event diff + `events.jsonl`
  - FastAPI endpoints: `/health`, `/api/v1/snapshots`, `/api/v1/snapshots/latest`, `/api/v1/events`, `/api/devices`
- **mikrotrack-web container**
  - FastAPI + template UI
  - timeline/events view
  - devices table UI (filters/mode/sorting/live timers)
  - backend proxy to `/api/devices`

## Data flow

1. Collector reads DHCP + ARP + bridge host + interface MAC sources.
2. Device builder merges data into a unified MAC-keyed model.
3. Persistence enriches stable timestamps and stale identity fields.
4. A new snapshot is written to `PERSISTENCE_PATH`.
5. Diff vs previous snapshot appends events into `events.jsonl`.
6. API serves current state; Web UI renders timeline and devices table.

## Storage model

- snapshots: one JSON file per cycle
- events: append-only `events.jsonl`
- retention: `PERSISTENCE_RETENTION_DAYS`
