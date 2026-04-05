# Storage / Persistence

## 🇺🇦 Українською

## Як працює persistence

MikroTrack може зберігати результат кожного циклу збору у JSON snapshot.

- Увімкнення: `PERSISTENCE_ENABLED=true`
- Шлях до директорії: `PERSISTENCE_PATH`
- Retention: `PERSISTENCE_RETENTION_DAYS`

Формат файлу:

- `YYYY-MM-DDTHH-MM-SS.json`
- приклад: `2026-04-05T23-10-00.json`

## Структура директорій

Приклад для Linux/Container:

```text
/data/snapshots/
  ├─ 2026-04-05T23-10-00.json
  ├─ 2026-04-05T23-11-00.json
  └─ ...
```

## Приклад snapshot

```json
[
  {
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "ip_address": "192.168.88.10",
    "host_name": "workstation-01",
    "source": "dhcp+arp"
  }
]
```

## Підготовка директорії

```bash
mkdir -p /data/snapshots
chmod 755 /data/snapshots
```

## Docker volume mapping

Приклад мапінгу volume у `docker-compose.yml`:

```yaml
services:
  app:
    volumes:
      - ./data/snapshots:/data/snapshots
```

---

## 🇬🇧 English

## How persistence works

MikroTrack can save each collection cycle result as a JSON snapshot.

- Enable: `PERSISTENCE_ENABLED=true`
- Snapshot directory path: `PERSISTENCE_PATH`
- Retention: `PERSISTENCE_RETENTION_DAYS`

File format:

- `YYYY-MM-DDTHH-MM-SS.json`
- example: `2026-04-05T23-10-00.json`

## Directory structure

Linux/Container example:

```text
/data/snapshots/
  ├─ 2026-04-05T23-10-00.json
  ├─ 2026-04-05T23-11-00.json
  └─ ...
```

## Snapshot example

```json
[
  {
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "ip_address": "192.168.88.10",
    "host_name": "workstation-01",
    "source": "dhcp+arp"
  }
]
```

## Directory preparation

```bash
mkdir -p /data/snapshots
chmod 755 /data/snapshots
```

## Docker volume mapping

Example mapping in `docker-compose.yml`:

```yaml
services:
  app:
    volumes:
      - ./data/snapshots:/data/snapshots
```
