# TASK-063 - Fix reconnect timer reset (online_since not reset after offline)

## Опис / Description

### UA
Після виконання TASK-062 статуси працюють коректно:
- online → idle → offline
- reconnect → online

Але залишилась проблема з таймером:

Після reconnect:
```
offline → online
```

значення:
```
online_since
```

НЕ оновлюється, а продовжує попередню сесію.

---

## Симптом / Symptom

Було:
```
online_since: 10:30
idle → offline
```

Після reconnect:
```
status: online
online_since: 10:30   ❌ (НЕ reset)
```

Очікується:
```
online_since: NOW     ✅
```

---

## Причина / Root cause

### 1. Persistence (events generation)

У `_generate_diff_events()` використовується:

```python
previous_fused_state = _derive_device_state(previous)
```

але НЕ враховується:
- idle timeout
- previous_effective_state

→ генерується подія:

```
idle → online
```

замість:

```
offline → online
```

---

### 2. API (session reconstruction)

У `app/api/main.py`:

```python
if current_state in {"online", "idle"}:
    if previous_state not in {"online", "idle"}:
        online_since = timestamp
```

→ при `idle → online`:
- нова сесія НЕ створюється
- таймер НЕ reset

---

## Очікувана поведінка / Expected behavior

### UA

Якщо пристрій:
1. був idle
2. перевищив idle timeout
3. перейшов в offline
4. reconnect

→ має бути:

```
offline → online
```

і:
```
online_since = now
```

---

## Що треба зробити / Required changes

---

### 1. FIX events generation

#### Файл:
```
app/persistence.py
```

#### Функція:
```
_generate_diff_events()
```

---

### Додати effective state логіку

Перед:

```python
previous_fused_state = _derive_device_state(previous)
```

додати:

```python
previous_state = _derive_device_state(previous)

previous_effective_state = previous_state

if (
    previous_state == "idle"
    and _idle_timeout_exceeded(previous=previous, now=datetime.now())
):
    previous_effective_state = "offline"
```

---

### Використовувати effective state

Замість:

```python
old_value = previous_fused_state
```

використовувати:

```python
old_value = previous_effective_state
```

І аналогічно для:
- state_changed
- arp_state_changed
- session_started

---

### 2. FIX session_started event

Переконатися, що:

```
previous_effective_state == "offline"
AND current_state == "online"
```

→ генерується:

```
session_started
```

---

## Критерії приймання / Acceptance criteria

- reconnect після offline → новий `online_since`
- timer починається з 00:00
- генерується:
  - `state_changed: offline -> online`
  - `session_started`
- API НЕ продовжує стару сесію
- idle timeout коректно впливає на reconnect

---

## Результат

Було:
```
online_since = OLD
```

Стає:
```
online_since = NOW
timer = 00:00
```
