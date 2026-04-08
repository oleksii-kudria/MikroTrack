# TASK-028 - Stable timestamps for online_since and state_changed_at

## Опис (UA)

Наразі timestamps `online_since` та `state_changed_at` оновлюються при кожному циклі колектора (poll), навіть якщо стан пристрою не змінився.

Це призводить до:
- некоректного відображення часу онлайн
- неможливості визначити реальну тривалість сесії
- "стрибаючих" значень у UI (16:03 → 16:04 → 16:05)

---

## Мета (UA)

1. Забезпечити стабільність timestamps
2. Оновлювати timestamps ТІЛЬКИ при зміні стану
3. Зберегти коректну session-aware логіку

---

## Definitions (EN)

```python
device.state
device.state_changed_at
device.online_since
device.offline_since
```

---

## 1. Основне правило (UA)

Timestamps НЕ повинні оновлюватись при кожному poll.

Оновлення дозволено ТІЛЬКИ при state transition.

---

## 2. Transition-based Updates (UA)

### offline → online

```python
state_changed_at = now
online_since = now
offline_since = None
```

---

### online → idle

```python
state_changed_at = now
# online_since НЕ змінюється
```

---

### idle → online

```python
state_changed_at = now
# online_since НЕ змінюється
```

---

### online → offline

```python
state_changed_at = now
offline_since = now
online_since = None
```

---

### idle → offline

```python
state_changed_at = now
offline_since = now
online_since = None
```

---

## 3. No-change Scenario (UA)

Якщо стан НЕ змінився:

```python
if new_state == current_state:
    # НЕ оновлювати timestamps
    pass
```

---

## 4. Detection Logic (UA)

Перед оновленням:

```python
if new_state != current_state:
    apply_transition_rules()
else:
    keep_existing_timestamps()
```

---

## 5. Data Persistence (UA)

НЕОБХІДНО:
- зберігати timestamps між циклами
- використовувати persistence (snapshots / DB)

---

## 6. API Requirements (EN)

Backend MUST return raw timestamps:

```json
{
  "state": "online",
  "online_since": "2026-04-08T16:08:00+03:00",
  "state_changed_at": "2026-04-08T16:10:00+03:00"
}
```

---

## 7. Вплив на журнали подій (UA)

- фіксувати тільки реальні зміни стану
- не генерувати події при кожному poll

---

## 8. Вплив на документацію (UA + EN)

Українською:
- пояснення stable timestamps
- приклади transition logic

English:
- stable timestamp handling
- session-aware state tracking

---

## 9. Acceptance Criteria (UA)

- timestamps НЕ змінюються без state change
- online_since стабільний протягом сесії
- state_changed_at змінюється тільки при transition
- UI більше не "стрибає"
- persistence працює коректно

---

## Результат (UA)

Система:
- коректно відображає тривалість онлайн/офлайн
- не перезаписує час при кожному циклі
- забезпечує стабільну основу для live timers
