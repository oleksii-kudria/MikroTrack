# Architecture

## Current: Collector

MikroTrack is currently a **collector-only** service.

Responsibilities:

- connect to MikroTik via RouterOS API (SSL)
- collect DHCP leases and ARP entries
- normalize and merge data into unified device model
- output data to logs/stdout for further processing

## Future: Storage

Planned storage layer can persist snapshots and history:

- JSON snapshots
- relational DB (optional)
- retention and history policies

## Future: API

Planned API layer can provide:

- access to latest collected snapshot
- query/filter for devices
- health/status endpoint

## Future: UI

Planned UI layer can provide:

- dashboard for device visibility
- searchable device table
- status indicators and troubleshooting hints

---

Target direction: evolve from collector into full observability pipeline while keeping current collector simple and reliable.
