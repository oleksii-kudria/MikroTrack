# Operator Playbook

## 🇺🇦 Українською

Короткий operational runbook для швидкої перевірки runtime-стану MikroTrack та первинної діагностики інцидентів.

## Quick health check

Виконуйте по порядку:

```bash
# 1) containers must be up

docker ps --format 'table {{.Names}}\t{{.Status}}' | rg 'mikrotrack-app|mikrotrack-web'

# 2) app logs should show active cycles

docker logs mikrotrack-app --tail 200 | rg 'Starting collection cycle|Diff summary|Events persisted|DIFF_ERROR|PERSISTENCE_ERROR'

# 3) snapshots must exist and keep growing

docker exec mikrotrack-app sh -c 'ls -lah /data/snapshots/*.json 2>/dev/null | tail -n 5'

# 4) events file should exist (after first real diff/event)

docker exec mikrotrack-app sh -c 'ls -lah /data/snapshots/events.jsonl && tail -n 20 /data/snapshots/events.jsonl'

# 5) API must respond

curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/api/devices | jq '.items | length'

# 6) Web UI must open

curl -I http://127.0.0.1:8080/
```

Що вважати healthy:
- `mikrotrack-app` і `mikrotrack-web` у статусі `Up`
- у логах регулярно є `Starting collection cycle`
- нові snapshot JSON-файли з’являються з новими timestamp
- API повертає non-empty `items` (або очікувано `0` для порожньої мережі)

## Persistence verification

```bash
# Show persistence path inside container

docker exec mikrotrack-app sh -c 'echo PERSISTENCE_PATH=${PERSISTENCE_PATH}; ls -lah ${PERSISTENCE_PATH:-/data/snapshots}'

# Check snapshot timeline growth (mtime sorted)

docker exec mikrotrack-app sh -c 'ls -1t /data/snapshots/*.json 2>/dev/null | head -n 10'

# Check events file

docker exec mikrotrack-app sh -c 'test -f /data/snapshots/events.jsonl && tail -n 20 /data/snapshots/events.jsonl || echo events.jsonl-not-found-yet'

# Check permissions

docker exec mikrotrack-app sh -c 'id; ls -ld /data /data/snapshots; touch /data/snapshots/.write_test && rm /data/snapshots/.write_test'

# Verify volume mapping from compose config

docker compose config | rg '/data/snapshots|./data/snapshots'
```

## Diff та events verification

```bash
# Latest DIFF errors

docker logs mikrotrack-app --tail 500 | rg '\[DIFF_ERROR\]|diff processing failed with traceback'

# Diff summary + persisted events

docker logs mikrotrack-app --tail 500 | rg 'Diff summary|Events persisted|No events were persisted'

# Find traceback fragments quickly

docker logs mikrotrack-app --tail 500 | rg 'Traceback|Exception|ERROR'
```

Як відрізнити diff-проблему від collector-проблеми:
- collector працює, якщо є `Starting collection cycle` і оновлюються snapshot-и.
- diff-проблема підтверджується `diff processing failed with traceback` або `[DIFF_ERROR] Failed to process snapshots`.
- якщо немає нових snapshot-ів, проблема зазвичай до diff (API/MikroTik connection/persistence write).

## API verification

```bash
# Raw devices payload

curl -fsS http://127.0.0.1:8000/api/devices | jq '{count: (.items | length), first: .items[0]}'

# Quick non-empty check (exit code 0 only when >0)

curl -fsS http://127.0.0.1:8000/api/devices | jq -e '.items | length > 0'

# Verify required fields in each item

curl -fsS http://127.0.0.1:8000/api/devices \
  | jq -e '.items[] | has("status") and has("state_changed_at") and has("online_since") and has("idle_since") and has("offline_since")' \
  >/dev/null && echo 'required fields present'
```

## Expected warnings vs real errors

Нормально (collector може продовжувати):
- `Failed to fetch /interface/wireless entries: ...` (optional wireless interface collection)
- `WARNING: Persistence path may not be mounted to host`
- `persistence: skipping device without MAC key`
- `events.jsonl` відсутній на першому snapshot або коли не було змін

Реальні проблеми (потрібна реакція):
- `[DIFF_ERROR] Failed to process snapshots`
- `[PERSISTENCE_ERROR] ...`
- repeated API connection failures (`Unable to connect to MikroTik API. Check IP/port.`)
- traceback у логах (`diff processing failed with traceback`, `Traceback ...`)

## Minimal incident response flow

1. Переконайтесь, що `mikrotrack-app` / `mikrotrack-web` запущені.
2. Перевірте, що collection cycle виконується (`Starting collection cycle`).
3. Перевірте наявність і приріст snapshot-ів.
4. Перевірте diff/events (`Diff summary`, `Events persisted`, `[DIFF_ERROR]`).
5. Перевірте API (`/health`, `/api/devices`).
6. Перевірте volume mapping і права на persistence path.
7. Зберіть останні логи та 1-2 останні snapshot-файли для аналізу.

## What to attach when reporting a bug

Мінімальний набір для інциденту:

```bash
# Container status

docker compose ps

# App logs (last 300 lines)

docker logs mikrotrack-app --tail 300 > mikrotrack-app.tail300.log

# Web logs (last 150 lines)

docker logs mikrotrack-web --tail 150 > mikrotrack-web.tail150.log

# Last snapshots list + latest file

ls -lah ./data/snapshots/*.json | tail -n 10 > snapshots.tail10.txt
LATEST_SNAPSHOT=$(ls -1t ./data/snapshots/*.json | head -n 1)
cp "$LATEST_SNAPSHOT" ./latest-snapshot.json

# Events tail

tail -n 200 ./data/snapshots/events.jsonl > events.tail200.jsonl
```

---

## 🇬🇧 English

Short operational runbook for fast MikroTrack runtime verification and first-line incident diagnostics.

## Quick health check

Run in sequence:

```bash
# 1) containers must be up

docker ps --format 'table {{.Names}}\t{{.Status}}' | rg 'mikrotrack-app|mikrotrack-web'

# 2) app logs should show active cycles

docker logs mikrotrack-app --tail 200 | rg 'Starting collection cycle|Diff summary|Events persisted|DIFF_ERROR|PERSISTENCE_ERROR'

# 3) snapshots must exist and keep growing

docker exec mikrotrack-app sh -c 'ls -lah /data/snapshots/*.json 2>/dev/null | tail -n 5'

# 4) events file should exist (after first real diff/event)

docker exec mikrotrack-app sh -c 'ls -lah /data/snapshots/events.jsonl && tail -n 20 /data/snapshots/events.jsonl'

# 5) API must respond

curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/api/devices | jq '.items | length'

# 6) Web UI must open

curl -I http://127.0.0.1:8080/
```

Healthy baseline:
- `mikrotrack-app` and `mikrotrack-web` are `Up`
- logs regularly contain `Starting collection cycle`
- new snapshot JSON files appear with newer timestamps
- API returns non-empty `items` (or `0` for an intentionally empty network)

## Persistence verification

```bash
# Show persistence path inside container

docker exec mikrotrack-app sh -c 'echo PERSISTENCE_PATH=${PERSISTENCE_PATH}; ls -lah ${PERSISTENCE_PATH:-/data/snapshots}'

# Check snapshot timeline growth (mtime sorted)

docker exec mikrotrack-app sh -c 'ls -1t /data/snapshots/*.json 2>/dev/null | head -n 10'

# Check events file

docker exec mikrotrack-app sh -c 'test -f /data/snapshots/events.jsonl && tail -n 20 /data/snapshots/events.jsonl || echo events.jsonl-not-found-yet'

# Check permissions

docker exec mikrotrack-app sh -c 'id; ls -ld /data /data/snapshots; touch /data/snapshots/.write_test && rm /data/snapshots/.write_test'

# Verify volume mapping from compose config

docker compose config | rg '/data/snapshots|./data/snapshots'
```

## Diff and events verification

```bash
# Latest DIFF errors

docker logs mikrotrack-app --tail 500 | rg '\[DIFF_ERROR\]|diff processing failed with traceback'

# Diff summary + persisted events

docker logs mikrotrack-app --tail 500 | rg 'Diff summary|Events persisted|No events were persisted'

# Find traceback fragments quickly

docker logs mikrotrack-app --tail 500 | rg 'Traceback|Exception|ERROR'
```

How to separate diff issues from collector issues:
- collector is alive when `Starting collection cycle` appears and snapshots are still updated.
- diff issue is confirmed by `diff processing failed with traceback` or `[DIFF_ERROR] Failed to process snapshots`.
- if snapshots stop updating, root cause is usually before diff (API/MikroTik connection/persistence write).

## API verification

```bash
# Raw devices payload

curl -fsS http://127.0.0.1:8000/api/devices | jq '{count: (.items | length), first: .items[0]}'

# Quick non-empty check (exit code 0 only when >0)

curl -fsS http://127.0.0.1:8000/api/devices | jq -e '.items | length > 0'

# Verify required fields in each item

curl -fsS http://127.0.0.1:8000/api/devices \
  | jq -e '.items[] | has("status") and has("state_changed_at") and has("online_since") and has("idle_since") and has("offline_since")' \
  >/dev/null && echo 'required fields present'
```

## Expected warnings vs real errors

Expected (collector can continue):
- `Failed to fetch /interface/wireless entries: ...` (optional wireless interface collection)
- `WARNING: Persistence path may not be mounted to host`
- `persistence: skipping device without MAC key`
- `events.jsonl` may be absent on the first snapshot or when no state changes happened

Real problems (require action):
- `[DIFF_ERROR] Failed to process snapshots`
- `[PERSISTENCE_ERROR] ...`
- repeated API connection failures (`Unable to connect to MikroTik API. Check IP/port.`)
- traceback in logs (`diff processing failed with traceback`, `Traceback ...`)

## Minimal incident response flow

1. Verify `mikrotrack-app` / `mikrotrack-web` container status.
2. Verify the collection cycle is running (`Starting collection cycle`).
3. Verify snapshots exist and keep growing.
4. Verify diff/events (`Diff summary`, `Events persisted`, `[DIFF_ERROR]`).
5. Verify API (`/health`, `/api/devices`).
6. Verify volume mapping and persistence path permissions.
7. Collect logs and the latest snapshot artifacts for analysis.

## What to attach when reporting a bug

Minimal incident bundle:

```bash
# Container status

docker compose ps

# App logs (last 300 lines)

docker logs mikrotrack-app --tail 300 > mikrotrack-app.tail300.log

# Web logs (last 150 lines)

docker logs mikrotrack-web --tail 150 > mikrotrack-web.tail150.log

# Last snapshots list + latest file

ls -lah ./data/snapshots/*.json | tail -n 10 > snapshots.tail10.txt
LATEST_SNAPSHOT=$(ls -1t ./data/snapshots/*.json | head -n 1)
cp "$LATEST_SNAPSHOT" ./latest-snapshot.json

# Events tail

tail -n 200 ./data/snapshots/events.jsonl > events.tail200.jsonl
```
