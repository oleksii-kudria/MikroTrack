# MikroTrack

## 🇺🇦 Українською

MikroTrack — lightweight collector + API + Web UI для моніторингу мережі MikroTik без окремої БД.

### Що реально збирає collector

- DHCP leases (`/ip/dhcp-server/lease`)
- ARP table (`/ip/arp`)
- Bridge host table (`/interface/bridge/host`)
- Interface MAC inventory (`/interface`, `/interface/bridge`, `/interface/vlan`)
- Optional: `/interface/wireless` (якщо недоступний на конкретному RouterOS/device, collector логує INFO skip і продовжує роботу)

### Architecture (current runtime)

- `mikrotrack-app`: collector + persistence + FastAPI (`/api/v1/*`, `/api/devices`, `/health`)
- `mikrotrack-web`: FastAPI + HTML UI (`/`, `/health`, проксі до backend API)
- persistence: JSON snapshots + `events.jsonl` у `PERSISTENCE_PATH`
- без зовнішньої БД

### Quick Start (recommended deployment)

```bash
git clone <repo-url>
cd MikroTrack
cp .env.example .env
mkdir -p ./data/snapshots
docker compose up --build
```

### Deployment path and volume mapping (canonical)

Canonical runtime mapping:

- host path: `./data/snapshots`
- container path: `/data/snapshots`
- env: `PERSISTENCE_PATH=/data/snapshots`

`docker-compose.yml`:

```yaml
services:
  mikrotrack-app:
    volumes:
      - ./data/snapshots:/data/snapshots
```

### Key parameters

- `RUN_MODE` (`once` / `loop`)
- `COLLECTION_INTERVAL`
- `PERSISTENCE_ENABLED`
- `PERSISTENCE_PATH`
- `PERSISTENCE_RETENTION_DAYS`
- `IDLE_TIMEOUT_SECONDS`
- `API_ENABLED`, `API_HOST`, `API_PORT`
- `WEB_HOST`, `WEB_PORT`, `BACKEND_API_URL`
- `LOG_LEVEL`, `PRINT_RESULT_TO_STDOUT`

### State model and time fields

Core states:

- `online`
- `idle`
- `offline`
- `unknown`

Time fields:

- `state_changed_at`: остання зміна стану
- `online_since`: початок поточної online-сесії
- `idle_since`: момент переходу в idle (в межах online-сесії)
- `offline_since`: початок offline-сесії

Behavior:

- `online ↔ idle`: оновлюється `state_changed_at`, `online_since` зберігається
- `online/idle → offline`: `offline_since` встановлюється, online timestamps очищаються
- `offline → online|idle`: стартує нова online-сесія (`online_since = now`, `offline_since = null`)
- `unknown`: time fields можуть бути `null`
- за відсутності explicit sorting UI використовує default state order: `online → idle → offline → unknown`

### Snapshot schema (practical)

Stable identity/core fields:

- `mac_address` (primary key)
- `ip_address`, `host_name`
- `source`, `entity_type`, `interface_name`, `badges`

State/session fields:

- `arp_status`, `arp_state`, `fused_state`
- `state_changed_at`, `online_since`, `idle_since`, `offline_since`

Derived/calculated fields (можуть змінюватися між poll-ами):

- `evidence`, `has_dhcp_lease`, `has_arp_entry`
- `dhcp_flags`, `arp_flags`
- stale identity fields: `last_known_ip`, `last_known_hostname`, `ip_is_stale`, `hostname_is_stale`, `data_is_stale`

Поля, які часто можуть бути порожні (`""` або `null`):

- `host_name`, `dhcp_comment`, `arp_comment`, `bridge_host_last_seen`, `idle_since`

Minimal snapshot device example:

```json
{
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "ip_address": "192.168.88.10",
  "host_name": "workstation-01",
  "source": ["dhcp", "arp"],
  "arp_status": "reachable",
  "fused_state": "online",
  "state_changed_at": "2026-04-11T10:00:00+00:00",
  "online_since": "2026-04-11T10:00:00+00:00",
  "idle_since": null,
  "offline_since": null
}
```

### Event schema (`events.jsonl`)

Події, які реально пишуться:

- presence/identity: `NEW_DEVICE`, `DEVICE_REMOVED`, `IP_CHANGED`, `HOSTNAME_CHANGED`
- generic diff: `FIELD_CHANGE`
- dhcp/arp/source: `DHCP_*`, `ARP_*`, `SOURCE_CHANGED`, `DEVICE_IP_ASSIGNMENT_CHANGED`
- state/session: `arp_state_changed`, `state_changed`, `device_online`, `device_idle`, `device_offline`, `session_started`, `session_ended`

Minimal examples:

```json
{"timestamp":"2026-04-11T10:02:00+00:00","event_type":"FIELD_CHANGE","mac":"AA:BB:CC:DD:EE:FF","device_mac":"AA:BB:CC:DD:EE:FF","field_name":"ip_address","previous_value":"192.168.88.10","current_value":"192.168.88.11"}
{"timestamp":"2026-04-11T10:03:00+00:00","event_type":"state_changed","mac":"AA:BB:CC:DD:EE:FF","old_state":"online","new_state":"idle"}
{"timestamp":"2026-04-11T10:15:00+00:00","event_type":"device_offline","mac":"AA:BB:CC:DD:EE:FF","reason":"idle_timeout"}
```

### Expected warnings vs real errors

Expected warnings (collector продовжує роботу):

- `Skipping optional resource /interface/wireless: unsupported on this device`
- `Persistence path may not be mounted to host`
- `persistence: skipping device without MAC key`

Real errors (потребують втручання):

- `[PERSISTENCE_ERROR] ...`
- MikroTik connection/auth/TLS/protocol errors
- repeated snapshot write failures

### Operator verification (quick checks)

```bash
# 1) snapshots exist
ls -lah ./data/snapshots/*.json | tail -n 5

# 2) events.jsonl is written
tail -n 20 ./data/snapshots/events.jsonl

# 3) latest API snapshot
curl -s http://localhost:8000/api/v1/snapshots/latest | jq '.filename'

# 4) latest diff-related logs
docker compose logs mikrotrack-app --tail=200 | rg "Diff summary|DIFF_|Events persisted"

# 5) verify volume mapping
docker compose config | rg "snapshots"
```

### Тести (critical logic)

Запуск усіх тестів:

```bash
pytest -q
pytest -q tests/test_ui_regression.py
```

Покриті критичні сценарії:

- MAC fallback індексація (`mac_address`/`mac`) і warning при відсутності MAC
- timezone-aware datetime parsing (`naive`, `+00:00`, `Z`) та idle timeout
- state transitions (`online→idle`, `idle→offline`, `online→offline`, `offline→online`)
- extended diff events (`FIELD_CHANGE`, `state_changed`, `IP_CHANGED`, `HOSTNAME_CHANGED`)
- last-known поля для offline devices (`last_known_ip`, `ip_is_stale`)
- serialization safety для `datetime`, `set`, `tuple`, `bytes`, nested structures
- UI regression: default/explicit sorting, End/All mode, summary-vs-filter separation, unknown handling, empty/null deterministic behavior, contract assumptions

### Toolchain versions (pinned)

- Python: `3.12` (CI baseline via GitHub Actions)
- Ruff: `0.4.7` (must match CI + pre-commit)

If your local `ruff --version` is different, reinstall:

```bash
pip install --upgrade --force-reinstall ruff==0.4.7
```

### CI (quality gate)

Локальний CI-equivalent мінімум:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt ruff==0.4.7
ruff check app web tests
ruff format --check app web tests
PYTHONPATH=. pytest -q
PYTHONPATH=. pytest -q tests/test_ui_regression.py tests/test_web_timeline.py
```

Workflow і деталізований опис quality gate:
- [`docs/ci-quality-gate.md`](docs/ci-quality-gate.md)

### Pre-commit hooks (recommended developer setup)

Щоб ловити formatting/lint проблеми до push і зменшити "format-only" CI failures:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Що перевіряють hooks:

- `ruff` (lint для `app`, `web`, `tests`)
- `ruff-format` (format для `app`, `web`, `tests`)
- базові hygiene checks (`trailing whitespace`, `end-of-file newline`, `yaml`, `large files`, `merge conflicts`)

Bypass (`git commit --no-verify`) має бути винятком для аварійних випадків, не стандартним workflow.

Рекомендована повна локальна перевірка перед push:

```bash
pre-commit run --all-files
ruff format .
PYTHONPATH=. pytest -q
PYTHONPATH=. pytest -q tests/test_ui_regression.py tests/test_web_timeline.py
```

Якщо в репозиторії є історичні невідформатовані файли, зробіть одноразовий formatting baseline-коміт:

```bash
ruff format .
git add .
git commit -m "chore: apply repository-wide formatting baseline"
```

### Documentation

- Architecture → [`docs/architecture.md`](docs/architecture.md)
- API contract (Web UI) → [`docs/api-contract.md`](docs/api-contract.md)
- Device model → [`docs/device-model.md`](docs/device-model.md)
- Storage/persistence → [`docs/storage.md`](docs/storage.md)
- Operator playbook → [`docs/operator-playbook.md`](docs/operator-playbook.md)
- Troubleshooting → [`docs/troubleshooting.md`](docs/troubleshooting.md)
- Scheduler → [`docs/scheduler.md`](docs/scheduler.md)
- MikroTik setup → [`docs/mikrotik-setup.md`](docs/mikrotik-setup.md)
- UI regression tests → [`docs/ui-regression-tests.md`](docs/ui-regression-tests.md)
- CI quality gate → [`docs/ci-quality-gate.md`](docs/ci-quality-gate.md)

---

## 🇬🇧 English

MikroTrack is a lightweight collector + API + Web UI for MikroTik network monitoring, with no external database.

### What the collector actually uses

- DHCP leases (`/ip/dhcp-server/lease`)
- ARP table (`/ip/arp`)
- Bridge host table (`/interface/bridge/host`)
- Interface MAC inventory (`/interface`, `/interface/bridge`, `/interface/vlan`)
- Optional: `/interface/wireless` (if unavailable on a specific RouterOS/device, collector logs an INFO skip and continues)

### Architecture (current runtime)

- `mikrotrack-app`: collector + persistence + FastAPI (`/api/v1/*`, `/api/devices`, `/health`)
- `mikrotrack-web`: FastAPI + HTML UI (`/`, `/health`, backend API proxy)
- persistence: JSON snapshots + `events.jsonl` under `PERSISTENCE_PATH`
- no dedicated DB

### Quick Start (recommended deployment)

```bash
git clone <repo-url>
cd MikroTrack
cp .env.example .env
mkdir -p ./data/snapshots
docker compose up --build
```

### Deployment path and volume mapping (canonical)

Canonical runtime mapping:

- host path: `./data/snapshots`
- container path: `/data/snapshots`
- env: `PERSISTENCE_PATH=/data/snapshots`

`docker-compose.yml`:

```yaml
services:
  mikrotrack-app:
    volumes:
      - ./data/snapshots:/data/snapshots
```

### Key parameters

- `RUN_MODE` (`once` / `loop`)
- `COLLECTION_INTERVAL`
- `PERSISTENCE_ENABLED`
- `PERSISTENCE_PATH`
- `PERSISTENCE_RETENTION_DAYS`
- `IDLE_TIMEOUT_SECONDS`
- `API_ENABLED`, `API_HOST`, `API_PORT`
- `WEB_HOST`, `WEB_PORT`, `BACKEND_API_URL`
- `LOG_LEVEL`, `PRINT_RESULT_TO_STDOUT`

### State model and time fields

Core states:

- `online`
- `idle`
- `offline`
- `unknown`

Time fields:

- `state_changed_at`: latest state transition timestamp
- `online_since`: current online-session start
- `idle_since`: idle transition timestamp (inside online session)
- `offline_since`: current offline-session start

Behavior:

- `online ↔ idle`: updates `state_changed_at`, keeps `online_since`
- `online/idle → offline`: sets `offline_since`, clears online timestamps
- `offline → online|idle`: starts a new online session (`online_since = now`, `offline_since = null`)
- `unknown`: time fields may be `null`
- without explicit sorting, UI default state order is `online → idle → offline → unknown`

### Snapshot schema (practical)

Stable identity/core fields:

- `mac_address` (primary key)
- `ip_address`, `host_name`
- `source`, `entity_type`, `interface_name`, `badges`

State/session fields:

- `arp_status`, `arp_state`, `fused_state`
- `state_changed_at`, `online_since`, `idle_since`, `offline_since`

Derived/calculated fields (can change between polls):

- `evidence`, `has_dhcp_lease`, `has_arp_entry`
- `dhcp_flags`, `arp_flags`
- stale identity fields: `last_known_ip`, `last_known_hostname`, `ip_is_stale`, `hostname_is_stale`, `data_is_stale`

Fields that may be empty (`""` or `null`):

- `host_name`, `dhcp_comment`, `arp_comment`, `bridge_host_last_seen`, `idle_since`

Minimal snapshot device example:

```json
{
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "ip_address": "192.168.88.10",
  "host_name": "workstation-01",
  "source": ["dhcp", "arp"],
  "arp_status": "reachable",
  "fused_state": "online",
  "state_changed_at": "2026-04-11T10:00:00+00:00",
  "online_since": "2026-04-11T10:00:00+00:00",
  "idle_since": null,
  "offline_since": null
}
```

### Event schema (`events.jsonl`)

Events that are actually persisted:

- presence/identity: `NEW_DEVICE`, `DEVICE_REMOVED`, `IP_CHANGED`, `HOSTNAME_CHANGED`
- generic diff: `FIELD_CHANGE`
- dhcp/arp/source: `DHCP_*`, `ARP_*`, `SOURCE_CHANGED`, `DEVICE_IP_ASSIGNMENT_CHANGED`
- state/session: `arp_state_changed`, `state_changed`, `device_online`, `device_idle`, `device_offline`, `session_started`, `session_ended`

Minimal examples:

```json
{"timestamp":"2026-04-11T10:02:00+00:00","event_type":"FIELD_CHANGE","mac":"AA:BB:CC:DD:EE:FF","device_mac":"AA:BB:CC:DD:EE:FF","field_name":"ip_address","previous_value":"192.168.88.10","current_value":"192.168.88.11"}
{"timestamp":"2026-04-11T10:03:00+00:00","event_type":"state_changed","mac":"AA:BB:CC:DD:EE:FF","old_state":"online","new_state":"idle"}
{"timestamp":"2026-04-11T10:15:00+00:00","event_type":"device_offline","mac":"AA:BB:CC:DD:EE:FF","reason":"idle_timeout"}
```

### Expected warnings vs real errors

Expected warnings (collector continues):

- `Skipping optional resource /interface/wireless: unsupported on this device`
- `Persistence path may not be mounted to host`
- `persistence: skipping device without MAC key`

Real errors (require operator action):

- `[PERSISTENCE_ERROR] ...`
- MikroTik connection/auth/TLS/protocol errors
- repeated snapshot write failures

### Operator verification (quick checks)

```bash
# 1) snapshots exist
ls -lah ./data/snapshots/*.json | tail -n 5

# 2) events.jsonl is written
tail -n 20 ./data/snapshots/events.jsonl

# 3) latest API snapshot
curl -s http://localhost:8000/api/v1/snapshots/latest | jq '.filename'

# 4) latest diff-related logs
docker compose logs mikrotrack-app --tail=200 | rg "Diff summary|DIFF_|Events persisted"

# 5) verify volume mapping
docker compose config | rg "snapshots"
```

### Tests (critical logic)

Run the full test suite:

```bash
pytest -q
pytest -q tests/test_ui_regression.py
```

Covered critical scenarios:

- MAC fallback indexing (`mac_address`/`mac`) and warning when MAC is missing
- timezone-aware datetime parsing (`naive`, `+00:00`, `Z`) and idle timeout stability
- state transitions (`online→idle`, `idle→offline`, `online→offline`, `offline→online`)
- extended diff events (`FIELD_CHANGE`, `state_changed`, `IP_CHANGED`, `HOSTNAME_CHANGED`)
- last-known fields for offline devices (`last_known_ip`, `ip_is_stale`)
- serialization safety for `datetime`, `set`, `tuple`, `bytes`, and nested structures
- UI regression: default/explicit sorting, End/All mode, summary-vs-filter separation, unknown handling, empty/null deterministic behavior, contract assumptions

### Toolchain versions (pinned)

- Python: `3.12` (CI baseline via GitHub Actions)
- Ruff: `0.4.7` (must match CI + pre-commit)

If local `ruff --version` is different, reinstall:

```bash
pip install --upgrade --force-reinstall ruff==0.4.7
```

### CI (quality gate)

Minimal local CI-equivalent sequence:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt ruff==0.4.7
ruff check app web tests
ruff format --check app web tests
PYTHONPATH=. pytest -q
PYTHONPATH=. pytest -q tests/test_ui_regression.py tests/test_web_timeline.py
```

Workflow details and quality-gate policy:
- [`docs/ci-quality-gate.md`](docs/ci-quality-gate.md)

### Pre-commit hooks (recommended developer setup)

To catch formatting/lint issues before push and reduce "format-only" CI failures:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Hooks included:

- `ruff` (lint for `app`, `web`, `tests`)
- `ruff-format` (formatting for `app`, `web`, `tests`)
- baseline hygiene checks (`trailing whitespace`, `end-of-file newline`, `yaml`, `large files`, `merge conflicts`)

Bypass (`git commit --no-verify`) should remain an exception for emergency cases, not a normal workflow.

Recommended full local pre-push check:

```bash
pre-commit run --all-files
ruff format .
PYTHONPATH=. pytest -q
PYTHONPATH=. pytest -q tests/test_ui_regression.py tests/test_web_timeline.py
```

If legacy unformatted files exist in the repo, make a one-time formatting baseline commit:

```bash
ruff format .
git add .
git commit -m "chore: apply repository-wide formatting baseline"
```

### Debugging local vs CI formatting drift

If everything is formatted locally but CI reports `Would reformat`:

```bash
ruff --version
pre-commit run --all-files
git diff -- app web tests
```

Verify that:

- `ruff --version` == `0.4.7`
- pre-commit is using `rev: v0.4.7`
- `git ls-files --eol` shows no unexpected `crlf` for source files
- any changes produced by `pre-commit run --all-files` were committed

### Documentation

- Architecture → [`docs/architecture.md`](docs/architecture.md)
- API contract (Web UI) → [`docs/api-contract.md`](docs/api-contract.md)
- Device model → [`docs/device-model.md`](docs/device-model.md)
- Storage/persistence → [`docs/storage.md`](docs/storage.md)
- Operator playbook → [`docs/operator-playbook.md`](docs/operator-playbook.md)
- Troubleshooting → [`docs/troubleshooting.md`](docs/troubleshooting.md)
- Logging policy → [`docs/logging-policy.md`](docs/logging-policy.md)
- Scheduler → [`docs/scheduler.md`](docs/scheduler.md)
- MikroTik setup → [`docs/mikrotik-setup.md`](docs/mikrotik-setup.md)
- UI regression tests → [`docs/ui-regression-tests.md`](docs/ui-regression-tests.md)
- CI quality gate → [`docs/ci-quality-gate.md`](docs/ci-quality-gate.md)
