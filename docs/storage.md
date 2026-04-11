# Storage / Persistence

## 🇺🇦 Українською

## Canonical deployment mapping

Використовуйте один узгоджений варіант:

- Host: `./data/snapshots`
- Container: `/data/snapshots`
- Env: `PERSISTENCE_PATH=/data/snapshots`

`docker-compose.yml`:

```yaml
services:
  mikrotrack-app:
    volumes:
      - ./data/snapshots:/data/snapshots
```

## Як працює persistence

- `PERSISTENCE_ENABLED=true` вмикає snapshot persistence.
- Кожен цикл створює JSON snapshot `YYYY-MM-DDTHH-MM-SS.json`.
- Після запису snapshot виконується diff з попереднім snapshot.
- Події додаються в `events.jsonl` (append-only).
- Retention cleanup контролюється `PERSISTENCE_RETENTION_DAYS`.

## Snapshot schema (коротко)

Стабільні ключі:

- `mac_address`
- `ip_address`
- `host_name`
- `source`
- `entity_type` / `interface_name` / `badges`

Session/time fields:

- `state_changed_at`, `online_since`, `idle_since`, `offline_since`

Derived fields:

- `evidence`, `dhcp_flags`, `arp_flags`, `has_dhcp_lease`, `has_arp_entry`
- `last_known_ip`, `last_known_hostname`, `ip_is_stale`, `hostname_is_stale`, `data_is_stale`

## Event schema (коротко)

Кожен рядок `events.jsonl` — окремий JSON object з мінімумом:

- `timestamp`
- `event_type`
- `mac`

Практичні приклади:

```json
{"timestamp":"2026-04-11T10:02:00+00:00","event_type":"FIELD_CHANGE","mac":"AA:BB:CC:DD:EE:FF","field_name":"ip_address","previous_value":"192.168.88.10","current_value":"192.168.88.11"}
{"timestamp":"2026-04-11T10:03:00+00:00","event_type":"state_changed","mac":"AA:BB:CC:DD:EE:FF","old_state":"online","new_state":"idle"}
{"timestamp":"2026-04-11T10:15:00+00:00","event_type":"device_offline","mac":"AA:BB:CC:DD:EE:FF","reason":"idle_timeout"}
```

## Очікувані warning-сценарії (не критичні)

- `Failed to fetch /interface/wireless entries: ... no such command prefix`
- `WARNING: Persistence path may not be mounted to host`
- `persistence: skipping device without MAC key`

Ці попередження самі по собі не зупиняють collector.

## Реальні persistence errors

- `[PERSISTENCE_ERROR] ...`
- постійні помилки запису snapshot/events
- критично низьке місце на диску (після warning)

## Operator verification

```bash
# snapshot files
ls -lah ./data/snapshots/*.json | tail -n 5

# events stream
tail -n 20 ./data/snapshots/events.jsonl

# latest snapshot from API
curl -s http://localhost:8000/api/v1/snapshots/latest | jq '.filename'

# diff/persistence logs
docker compose logs mikrotrack-app --tail=200 | rg "Diff summary|DIFF_|Events persisted|PERSISTENCE_ERROR"

# effective compose mapping
docker compose config | rg "snapshots"
```

---

## 🇬🇧 English

## Canonical deployment mapping

Use one consistent mapping:

- Host: `./data/snapshots`
- Container: `/data/snapshots`
- Env: `PERSISTENCE_PATH=/data/snapshots`

`docker-compose.yml`:

```yaml
services:
  mikrotrack-app:
    volumes:
      - ./data/snapshots:/data/snapshots
```

## How persistence works

- `PERSISTENCE_ENABLED=true` enables snapshot persistence.
- Each cycle writes a JSON snapshot `YYYY-MM-DDTHH-MM-SS.json`.
- After writing, diff runs against the previous snapshot.
- Events are appended to `events.jsonl`.
- Retention cleanup uses `PERSISTENCE_RETENTION_DAYS`.

## Snapshot schema (short)

Stable keys:

- `mac_address`
- `ip_address`
- `host_name`
- `source`
- `entity_type` / `interface_name` / `badges`

Session/time fields:

- `state_changed_at`, `online_since`, `idle_since`, `offline_since`

Derived fields:

- `evidence`, `dhcp_flags`, `arp_flags`, `has_dhcp_lease`, `has_arp_entry`
- `last_known_ip`, `last_known_hostname`, `ip_is_stale`, `hostname_is_stale`, `data_is_stale`

## Event schema (short)

Each `events.jsonl` line is one JSON object with at least:

- `timestamp`
- `event_type`
- `mac`

Practical examples:

```json
{"timestamp":"2026-04-11T10:02:00+00:00","event_type":"FIELD_CHANGE","mac":"AA:BB:CC:DD:EE:FF","field_name":"ip_address","previous_value":"192.168.88.10","current_value":"192.168.88.11"}
{"timestamp":"2026-04-11T10:03:00+00:00","event_type":"state_changed","mac":"AA:BB:CC:DD:EE:FF","old_state":"online","new_state":"idle"}
{"timestamp":"2026-04-11T10:15:00+00:00","event_type":"device_offline","mac":"AA:BB:CC:DD:EE:FF","reason":"idle_timeout"}
```

## Expected warning scenarios (non-critical)

- `Failed to fetch /interface/wireless entries: ... no such command prefix`
- `WARNING: Persistence path may not be mounted to host`
- `persistence: skipping device without MAC key`

These warnings do not stop collector execution by themselves.

## Real persistence errors

- `[PERSISTENCE_ERROR] ...`
- recurring snapshot/events write failures
- critical low-disk follow-up condition

## Operator verification

```bash
# snapshot files
ls -lah ./data/snapshots/*.json | tail -n 5

# events stream
tail -n 20 ./data/snapshots/events.jsonl

# latest snapshot from API
curl -s http://localhost:8000/api/v1/snapshots/latest | jq '.filename'

# diff/persistence logs
docker compose logs mikrotrack-app --tail=200 | rg "Diff summary|DIFF_|Events persisted|PERSISTENCE_ERROR"

# effective compose mapping
docker compose config | rg "snapshots"
```
