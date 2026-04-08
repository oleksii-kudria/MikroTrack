# TASK-031 - Populate and preserve session timestamps for all aggregated devices

## Контекст

На даний момент у snapshot для більшості пристроїв відсутні поля:
- state_changed_at
- online_since
- offline_since

Це призводить до того, що UI не може коректно рахувати тривалість сесії і використовує fallback (час snapshot), через що таймер "скидається" на кожному poll.

При цьому для окремих пристроїв (наприклад manual/arp) timestamps присутні і працюють коректно.

## Проблема

Під час побудови aggregated device:
- timestamps або не ініціалізуються
- або не зберігаються між snapshot-ами
- або не копіюються з попереднього стану

Особливо це стосується пристроїв з source:
- dhcp
- arp
- bridge_host

## Мета

Забезпечити:
1. Наявність timestamps для ВСІХ пристроїв
2. Коректне збереження timestamps між snapshot-ами
3. Відсутність залежності від snapshot time як fallback

## Вимоги

### 1. Обов’язкові поля

Для кожного aggregated device (по MAC):

- state_changed_at: datetime | null
- online_since: datetime | null
- offline_since: datetime | null

Ці поля повинні завжди бути присутні в snapshot (навіть якщо null).

---

### 2. Merge логіка (ключ - MAC)

При побудові нового snapshot:

- знайти previous device по mac_address
- виконати merge стану

---

### 3. Правила переходів стану

Визначення state (вже існує):
- online
- idle
- offline
- unknown

#### Основні правила:

##### a) Стан НЕ змінився

```python
if old_state == new_state:
    state_changed_at = old.state_changed_at
    online_since = old.online_since
    offline_since = old.offline_since
```

---

##### b) online <-> idle

Це НЕ вважається розривом сесії

```python
if old_state in ["online", "idle"] and new_state in ["online", "idle"]:
    online_since = old.online_since
    state_changed_at = old.state_changed_at
    offline_since = None
```

---

##### c) offline -> online

```python
online_since = now
state_changed_at = now
offline_since = None
```

---

##### d) online/idle -> offline

```python
offline_since = now
state_changed_at = now
```

---

##### e) unknown

unknown НЕ повинен скидати сесію, якщо є достатньо evidence:

```python
if new_state == "unknown" and (bridge_host_present or arp_status in ["reachable", "delay"]):
    treat_as_previous_state = True
```

---

### 4. Ініціалізація (перший запуск)

Якщо previous device відсутній:

```python
if new_state in ["online", "idle"]:
    online_since = now
    state_changed_at = now

elif new_state == "offline":
    offline_since = now
    state_changed_at = now
```

---

### 5. Заборонено

- Використовувати snapshot_mtime як fallback для online_since
- Перезаписувати timestamps при кожному poll без зміни стану

---

### 6. Логування (обов’язково)

Для DEBUG режиму додати лог:

```text
MAC=XX:XX
old_state=online
new_state=online
old_online_since=...
new_online_since=...
decision=preserved
```

---

### 7. API вимоги

API НЕ повинно:
- підставляти snapshot time, якщо timestamps null

API повинно:
- повертати timestamps як є
- дозволяти UI самому вирішувати fallback

---

## Очікуваний результат

- Таймер у UI НЕ скидається між poll
- Для всіх пристроїв є стабільний online_since
- Перехід online -> offline -> online коректно відображає історію
- Дані придатні для побудови timeline / history

---

## Додатково (опціонально)

У майбутньому:
- зберігати історію state transitions у events.jsonl
- будувати session timeline

```text
event_type: state_changed
mac: XX
from: online
to: offline
timestamp: ...
```
