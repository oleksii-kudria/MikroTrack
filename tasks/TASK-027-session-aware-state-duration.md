# TASK-027 - Session-aware Last Change and State Duration Logic

## Опис (UA)

Поточна реалізація поля `Last change` не враховує різницю між:
- зміною стану (online/idle/offline)
- початком та завершенням сесії присутності пристрою

Це призводить до некоректної інтерпретації часу:
- idle перезаписує реальний час присутності
- неможливо зрозуміти, скільки пристрій онлайн або офлайн

---

## Мета (UA)

1. Впровадити session-aware модель часу
2. Розділити:
   - час зміни стану
   - час початку online-сесії
   - час початку offline-сесії
3. Забезпечити коректне відображення в UI

---

## Definitions (EN)

### States
- online
- idle
- offline
- permanent
- unknown

### Time Fields

```python
device.state_changed_at
device.online_since
device.offline_since
```

---

## 1. Core Concept (UA)

- online + idle = одна сесія присутності
- offline = завершення сесії
- новий online після offline = нова сесія

---

## 2. State Transition Rules (UA)

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

## 3. Invalid Transitions (UA)

Не допускати:

```text
offline → idle
```

---

## 4. Duration Calculation (UA)

### Presence duration

```python
if state in ["online", "idle"]:
    duration = now - online_since
```

---

### Offline duration

```python
if state == "offline":
    duration = now - offline_since
```

---

### Idle duration

```python
if state == "idle":
    idle_duration = now - state_changed_at
```

---

## 5. UI Requirements (UA)

### Online

- Online since: HH:MM
- Last change: HH:MM

---

### Idle

- Online since: HH:MM
- Idle since: HH:MM

---

### Offline

- Offline since: HH:MM

---

## 6. Events (EN)

System MUST generate:

- state_changed
- session_started
- session_ended

Example:

```json
{
  "type": "session_started",
  "mac": "20:37:A5:87:2A:13",
  "timestamp": "..."
}
```

---

## 7. Вплив на журнали подій (UA)

НЕОБХІДНО:

- додати session_started
- додати session_ended
- логувати точні переходи станів

---

## 8. Вплив на документацію (UA + EN)

Українською:
- опис session model
- правила переходів

English:
- session-aware logic
- duration calculation

---

## 9. Acceptance Criteria (UA)

- idle НЕ скидає online_since
- offline скидає online_since
- online після offline створює нову сесію
- duration рахується коректно
- UI відображає правильний час

---

## Результат (UA)

Система:

- коректно відображає час присутності
- не втрачає історію online
- дає зрозумілу картину стану пристрою
