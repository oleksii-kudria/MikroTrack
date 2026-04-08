# TASK-030 - Preserve state session timestamps across unchanged polls

## Опис (UA)

Після впровадження session-aware логіки timestamps `online_since`, `offline_since` та `state_changed_at` усе ще перезаписуються під час кожного нового poll, навіть якщо derived state пристрою не змінився.

Симптоми:
- online devices щоразу отримують новий `online_since`
- offline devices щоразу отримують новий `offline_since`
- `Last change` оновлюється без реального state transition
- live timers у UI "стрибають" після кожного циклу колектора

Це означає, що backend не зберігає початок поточного стану, а лише час останнього підтвердження snapshot.

---

## Мета (UA)

1. Зберігати session timestamps між незмінними poll циклами
2. Оновлювати timestamps тільки при реальному state transition
3. Усунути повторне створення online/offline сесії без зміни стану
4. Додати діагностичні логи для перевірки merge logic

---

## Definitions (EN)

```python
device.state
device.online_since
device.offline_since
device.state_changed_at
```

### Possible states
- online
- idle
- offline
- permanent
- unknown

---

## 1. Core Rule (UA)

Якщо `new_state == old_state`, timestamps НЕ змінюються.

```python
if new_state == old_state:
    online_since = old_device.online_since
    offline_since = old_device.offline_since
    state_changed_at = old_device.state_changed_at
```

---

## 2. Required Merge Logic (UA)

Для кожного MAC необхідно:

1. знайти попередній device record
2. обчислити `new_state`
3. порівняти `old_state` і `new_state`
4. або зберегти старі timestamps
5. або застосувати transition rules

---

## 3. State Preservation Rules (UA)

### unchanged: online -> online

```python
online_since = old.online_since
offline_since = None
state_changed_at = old.state_changed_at
```

---

### unchanged: idle -> idle

```python
online_since = old.online_since
offline_since = None
state_changed_at = old.state_changed_at
```

---

### unchanged: offline -> offline

```python
online_since = None
offline_since = old.offline_since
state_changed_at = old.state_changed_at
```

---

### unchanged: permanent -> permanent

```python
online_since = old.online_since
offline_since = old.offline_since
state_changed_at = old.state_changed_at
```

---

### unchanged: unknown -> unknown

```python
online_since = old.online_since
offline_since = old.offline_since
state_changed_at = old.state_changed_at
```

---

## 4. Real Transition Rules (UA)

### offline -> online

```python
online_since = now
offline_since = None
state_changed_at = now
```

---

### online -> idle

```python
online_since = old.online_since
offline_since = None
state_changed_at = now
```

---

### idle -> online

```python
online_since = old.online_since
offline_since = None
state_changed_at = now
```

---

### online -> offline

```python
online_since = None
offline_since = now
state_changed_at = now
```

---

### idle -> offline

```python
online_since = None
offline_since = now
state_changed_at = now
```

---

## 5. New Device Logic (UA)

Якщо MAC з'явився вперше:

- створити новий record
- ініціалізувати timestamps відповідно до initial state

Приклад:

```python
if old_device is None:
    if new_state in ["online", "idle"]:
        online_since = now
        offline_since = None
        state_changed_at = now
    elif new_state == "offline":
        online_since = None
        offline_since = now
        state_changed_at = now
```

---

## 6. Explicit No-Refresh Rule (UA)

ЗАБОРОНЕНО:

- оновлювати `online_since` просто тому, що пристрій все ще online
- оновлювати `offline_since` просто тому, що пристрій все ще offline
- оновлювати `state_changed_at` на кожному poll

---

## 7. Debug Logging (UA)

Додати debug/info logging для одного device merge decision.

Лог повинен містити:

- mac
- old_state
- new_state
- old_online_since
- new_online_since
- old_offline_since
- new_offline_since
- decision

Приклад:

```text
MAC 20:37:A5:87:2A:13 old_state=online new_state=online old_online_since=2026-04-08T16:03:00+03:00 new_online_since=2026-04-08T16:03:00+03:00 decision=keep_existing_timestamps
```

---

## 8. Persistence Requirements (UA)

НЕОБХІДНО перевірити, що:
- попередній snapshot коректно завантажується
- merge виконується на основі попереднього стану
- serialization/deserialization не обнуляє timestamps
- MAC-based matching працює стабільно

---

## 9. API Requirements (EN)

Backend MUST return stable raw timestamps across unchanged polls.

Example:

### Poll #1

```json
{
  "mac": "20:37:A5:87:2A:13",
  "state": "online",
  "online_since": "2026-04-08T16:03:00+03:00",
  "state_changed_at": "2026-04-08T16:03:00+03:00"
}
```

### Poll #2 (same state)

```json
{
  "mac": "20:37:A5:87:2A:13",
  "state": "online",
  "online_since": "2026-04-08T16:03:00+03:00",
  "state_changed_at": "2026-04-08T16:03:00+03:00"
}
```

---

## 10. Вплив на журнали подій (UA)

НЕОБХІДНО:

- не генерувати state-change події без реальної зміни стану
- не вважати кожен poll новою session event
- логувати тільки реальні transitions

---

## 11. Вплив на документацію (UA + EN)

Українською:
- пояснення merge logic для timestamps
- правило unchanged poll != state change
- приклади переходів та збереження часу

English:
- timestamp preservation across polls
- state transition vs snapshot refresh
- session timestamp merge rules

---

## 12. Acceptance Criteria (UA)

- online device зберігає один і той самий `online_since` між poll циклами
- offline device зберігає один і той самий `offline_since` між poll циклами
- `state_changed_at` не змінюється без transition
- UI timers більше не скидаються після refresh
- debug logs показують коректне рішення `keep_existing_timestamps`
- API повертає стабільні raw timestamps

---

## Результат (UA)

Backend:
- коректно відрізняє state transition від snapshot refresh
- зберігає початок поточного online/offline стану
- забезпечує стабільну основу для live timers у UI
