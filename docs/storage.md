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

## Перевірки надійності (storage robustness)

Під час старту, якщо `PERSISTENCE_ENABLED=true`, MikroTrack виконує перевірки:

- валідація `PERSISTENCE_PATH`
- автостворення директорії (якщо її немає)
- тест запису у директорію
- перевірка вільного місця (<50MB)
- попередження про можливу відсутність Docker volume mapping

Логи успішної ініціалізації:

- `Persistence enabled: true`
- `Persistence path: /data/snapshots`

Типові повідомлення:

- `[PERSISTENCE_ERROR] Persistence path is not writable or does not exist`  
  `Recommendation: Verify volume mapping and directory permissions on host`
- `[PERSISTENCE_ERROR] Failed to create persistence directory`  
  `Recommendation: Check permissions or create directory manually on host`
- `[PERSISTENCE_ERROR] Persistence path is not writable`  
  `Recommendation: Check filesystem permissions and Docker volume mapping`
- `[LOW_DISK_SPACE] Available disk space is low (<50MB)`  
  `Recommendation: Clean up old snapshots or increase storage`
- `WARNING: Persistence path may not be mounted to host`  
  `Recommendation: Verify docker-compose volume mapping`

## Event-driven diff (аналіз змін)

Під час кожного нового збереження MikroTrack порівнює поточний snapshot із попереднім у `PERSISTENCE_PATH` за MAC-ключем:

- спочатку `mac_address`
- fallback: `mac`

Це забезпечує сумісність зі старими й новими snapshot-схемами. Якщо в записі немає обох ключів, запис пропускається з warning логом:

- `WARNING persistence: skipping device without MAC key`

Раніше `events.jsonl` міг не створюватися, якщо snapshot містив тільки `mac` (без `mac_address`), бо diff не міг коректно зіставити пристрої між snapshot-ами.

Якщо попереднього snapshot немає:

- `[DIFF_SKIPPED] No previous snapshot found`

### Типи подій (DEBUG)

- Presence: `NEW_DEVICE`, `DEVICE_REMOVED`
- Extended diff: `FIELD_CHANGE` (state, ip_address, hostname, dhcp_lease_type, dhcp_presence, dhcp_flags, arp_flags, dhcp_comment, arp_comment, source)
- IP/identity: `IP_CHANGED`, `HOSTNAME_CHANGED`
- DHCP: `DHCP_ADDED`, `DHCP_REMOVED`, `DHCP_DYNAMIC_CHANGED`, `DHCP_STATUS_CHANGED`, `DHCP_COMMENT_CHANGED`
- ARP: `ARP_ADDED`, `ARP_REMOVED`, `ARP_DYNAMIC_CHANGED`, `ARP_FLAG_CHANGED`, `arp_status_changed`, `arp_state_changed`
- Session/state: `state_changed`, `session_started`, `session_ended`
- Source: `SOURCE_CHANGED`
- Combined: `DEVICE_IP_ASSIGNMENT_CHANGED`

### Формат події

```json
{
  "timestamp": "2026-04-10T10:15:30",
  "event_type": "FIELD_CHANGE",
  "mac": "AA:BB:CC:DD:EE:FF",
  "device_mac": "AA:BB:CC:DD:EE:FF",
  "field_name": "ip_address",
  "previous_value": "192.168.1.10",
  "current_value": "192.168.1.25",
  "old_value": "192.168.1.10",
  "new_value": "192.168.1.25"
}
```

INFO log example:

- `INFO diff: detected change field=ip_address mac=AA:BB:CC:DD:EE:FF old=192.168.1.10 new=192.168.1.25`

### Збереження подій

Події записуються у `events.jsonl` в тій же директорії `PERSISTENCE_PATH`. Це підготовка до інтеграції web UI (таймлайн/історія змін).

### Підсумок змін (INFO)

- `Diff summary:`
- `- new: X`
- `- removed: X`
- `- changed: X`
- `- events: X`

Помилки обробки diff:

- `[DIFF_ERROR] Failed to process snapshots`
- `Recommendation: Verify snapshot format and integrity`

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

## Storage robustness checks

At startup, when `PERSISTENCE_ENABLED=true`, MikroTrack runs:

- `PERSISTENCE_PATH` validation
- automatic directory creation (if missing)
- write probe for path permissions
- free disk space check (<50MB)
- warning when Docker volume mapping may be missing

Initialization logs:

- `Persistence enabled: true`
- `Persistence path: /data/snapshots`

Typical messages:

- `[PERSISTENCE_ERROR] Persistence path is not writable or does not exist`  
  `Recommendation: Verify volume mapping and directory permissions on host`
- `[PERSISTENCE_ERROR] Failed to create persistence directory`  
  `Recommendation: Check permissions or create directory manually on host`
- `[PERSISTENCE_ERROR] Persistence path is not writable`  
  `Recommendation: Check filesystem permissions and Docker volume mapping`
- `[LOW_DISK_SPACE] Available disk space is low (<50MB)`  
  `Recommendation: Clean up old snapshots or increase storage`
- `WARNING: Persistence path may not be mounted to host`  
  `Recommendation: Verify docker-compose volume mapping`

## Event-driven diff (change analysis)

On every new save, MikroTrack compares the current snapshot with the latest previous file in `PERSISTENCE_PATH` using a MAC key with fallback:

- first `mac_address`
- fallback: `mac`

This keeps diff behavior backward-compatible across snapshot schema variants. If both keys are missing, the record is skipped with a warning log:

- `WARNING persistence: skipping device without MAC key`

Previously, `events.jsonl` could be missing when snapshots had only `mac` (without `mac_address`) because diff indexing could not match the same device across snapshots.

If no previous snapshot exists:

- `[DIFF_SKIPPED] No previous snapshot found`

### Event types (DEBUG)

- Presence: `NEW_DEVICE`, `DEVICE_REMOVED`
- Extended diff: `FIELD_CHANGE` (state, ip_address, hostname, dhcp_lease_type, dhcp_presence, dhcp_flags, arp_flags, dhcp_comment, arp_comment, source)
- IP/identity: `IP_CHANGED`, `HOSTNAME_CHANGED`
- DHCP: `DHCP_ADDED`, `DHCP_REMOVED`, `DHCP_DYNAMIC_CHANGED`, `DHCP_STATUS_CHANGED`, `DHCP_COMMENT_CHANGED`
- ARP: `ARP_ADDED`, `ARP_REMOVED`, `ARP_DYNAMIC_CHANGED`, `ARP_FLAG_CHANGED`, `arp_status_changed`, `arp_state_changed`
- Session/state: `state_changed`, `session_started`, `session_ended`
- Source: `SOURCE_CHANGED`
- Combined: `DEVICE_IP_ASSIGNMENT_CHANGED`

### Event format

```json
{
  "timestamp": "2026-04-10T10:15:30",
  "event_type": "FIELD_CHANGE",
  "mac": "AA:BB:CC:DD:EE:FF",
  "device_mac": "AA:BB:CC:DD:EE:FF",
  "field_name": "ip_address",
  "previous_value": "192.168.1.10",
  "current_value": "192.168.1.25",
  "old_value": "192.168.1.10",
  "new_value": "192.168.1.25"
}
```

INFO log example:

- `INFO diff: detected change field=ip_address mac=AA:BB:CC:DD:EE:FF old=192.168.1.10 new=192.168.1.25`

### Event persistence

Events are appended to `events.jsonl` in the same `PERSISTENCE_PATH` directory, preparing data for a web UI timeline/history view.

### Diff summary (INFO)

- `Diff summary:`
- `- new: X`
- `- removed: X`
- `- changed: X`
- `- events: X`

Diff error handling:

- `[DIFF_ERROR] Failed to process snapshots`
- `Recommendation: Verify snapshot format and integrity`

## Docker volume mapping

Example mapping in `docker-compose.yml`:

```yaml
services:
  app:
    volumes:
      - ./data/snapshots:/data/snapshots
```
