# Troubleshooting

## 🇺🇦 Українською

## MikroTik API error categories

- `connection_error`
- `tls_error`
- `authentication_failed`
- `access_denied`
- `api_protocol_error`
- `unexpected_response`

### connection_error

Перевірте:

- доступність `MIKROTIK_HOST:MIKROTIK_PORT`
- увімкнений `api`/`api-ssl`
- firewall/ACL/DNS маршрутизацію

### tls_error

Перевірте:

- `MIKROTIK_USE_SSL=true`
- сертифікат для `api-ssl`
- `MIKROTIK_SSL_VERIFY` для self-signed сценарію
- коректний час на роутері

### authentication_failed

Перевірте:

- `MIKROTIK_USERNAME`, `MIKROTIK_PASSWORD`
- політики користувача (`read`, `api`)

### access_denied

Перевірте:

- allow-list в `/ip service api-ssl address`
- політики user group

### api_protocol_error / unexpected_response

Перевірте:

- сумісність RouterOS API
- доступність endpoint-ів, які collector читає

## Expected warnings (not real failures)

Це очікувані стани; collector може працювати далі:

- `Skipping optional resource /interface/wireless: unsupported on this device`
  - Причина: на пристрої немає wireless package/resource.
- `Persistence path may not be mounted to host`
  - Причина: path існує в контейнері, але host mount може бути неочевидним.
- `persistence: skipping device without MAC key`
  - Причина: legacy/invalid snapshot entry без `mac_address`/`mac`.

## Real persistence issues

Ознаки реальної проблеми:

- `[PERSISTENCE_ERROR] ...`
- snapshot-и не з'являються в `PERSISTENCE_PATH`
- `events.jsonl` не оновлюється при змінах у мережі

Перевірки:

- `PERSISTENCE_ENABLED=true`
- `PERSISTENCE_PATH=/data/snapshots`
- volume mapping: `./data/snapshots:/data/snapshots`
- права запису на host директорію
- вільне місце на диску

## Operator-oriented quick verification

```bash
# app/web status
docker compose ps

# app health
curl -s http://localhost:8000/health

# snapshots present
ls -lah ./data/snapshots/*.json | tail -n 5

# events stream alive
tail -n 20 ./data/snapshots/events.jsonl

# diff/errors logs
docker compose logs mikrotrack-app --tail=200 | rg "Diff summary|DIFF_|PERSISTENCE_ERROR|Events persisted"

# mounted path check
docker compose config | rg "snapshots"
```

---

## 🇬🇧 English

## MikroTik API error categories

- `connection_error`
- `tls_error`
- `authentication_failed`
- `access_denied`
- `api_protocol_error`
- `unexpected_response`

### connection_error

Check:

- reachability of `MIKROTIK_HOST:MIKROTIK_PORT`
- `api`/`api-ssl` service state
- firewall/ACL/DNS routing

### tls_error

Check:

- `MIKROTIK_USE_SSL=true`
- certificate assignment for `api-ssl`
- `MIKROTIK_SSL_VERIFY` for self-signed setup
- router time correctness

### authentication_failed

Check:

- `MIKROTIK_USERNAME`, `MIKROTIK_PASSWORD`
- user policy rights (`read`, `api`)

### access_denied

Check:

- `/ip service api-ssl address` allow-list
- user group policies

### api_protocol_error / unexpected_response

Check:

- RouterOS API compatibility
- availability of collector-read resources

## Expected warnings (not real failures)

These are expected conditions; collector can continue:

- `Skipping optional resource /interface/wireless: unsupported on this device`
  - Cause: wireless resource/package is unavailable on this device.
- `Persistence path may not be mounted to host`
  - Cause: container path exists, but host mount may be missing/misconfigured.
- `persistence: skipping device without MAC key`
  - Cause: legacy/invalid snapshot item without `mac_address`/`mac`.

## Real persistence issues

Symptoms of actual problems:

- `[PERSISTENCE_ERROR] ...`
- snapshots are not created under `PERSISTENCE_PATH`
- `events.jsonl` is not updated while state changes happen

Checks:

- `PERSISTENCE_ENABLED=true`
- `PERSISTENCE_PATH=/data/snapshots`
- volume mapping: `./data/snapshots:/data/snapshots`
- host directory write permissions
- available free disk space

## Operator-oriented quick verification

```bash
# app/web status
docker compose ps

# app health
curl -s http://localhost:8000/health

# snapshots present
ls -lah ./data/snapshots/*.json | tail -n 5

# events stream alive
tail -n 20 ./data/snapshots/events.jsonl

# diff/errors logs
docker compose logs mikrotrack-app --tail=200 | rg "Diff summary|DIFF_|PERSISTENCE_ERROR|Events persisted"

# mounted path check
docker compose config | rg "snapshots"
```
