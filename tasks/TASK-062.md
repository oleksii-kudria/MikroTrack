# TASK-062 - Fix reconnect state (idle -> online bug with bridge_host)

## Опис / Description

### UA
Після виконання TASK-060 та TASK-061 спостерігається некоректна поведінка:

Коли пристрій:
1. переходить у стан `offline` (через idle timeout або втрату активності)
2. знову з'являється в мережі (`bridge_host_present = true`)

→ він переходить у стан `idle`, а не `online`.

---

## Причина / Root cause

### 1. API рівень

Функція `_resolve_api_state()` в `app/api/main.py` НЕ враховує пріоритет:

```
bridge_host_present = true → MUST BE online
```

Зараз порядок такий:
- offline_since
- idle_since
- online_since

→ через це старий `idle_since` "перемагає" і повертається `idle`.

---

### 2. Persistence рівень

У `_apply_stable_timestamps()`:

якщо попередній стан був `idle`, навіть якщо він вже прострочений по timeout,
reconnect обробляється як:

```
idle → online (та сама сесія)
```

замість:

```
offline → online (нова сесія)
```

---

## Очікувана поведінка / Expected behavior

### UA

1. Якщо:
```
bridge_host_present = true
```

→ статус ЗАВЖДИ `online`

2. Якщо пристрій повернувся після timeout:
- починається нова сесія
- `online_since` оновлюється
- `idle_since = null`
- `offline_since = null`

---

## Що треба зробити / Required changes

---

### 1. FIX API layer

#### Файл:
```
app/api/main.py
```

#### Функція:
```
_resolve_api_state()
```

#### Додати на початок:

```python
if bridge_host_present:
    return "online"
```

Це має бути ДО будь-яких перевірок idle/offline.

---

### 2. FIX persistence session logic

#### Файл:
```
app/persistence.py
```

#### Функція:
```
_apply_stable_timestamps()
```

#### Додати логіку перед merge:

```python
previous_effective_state = previous_state

if (
    previous_state == "idle"
    and isinstance(now_dt, datetime)
    and _idle_timeout_exceeded(previous=previous, now=now_dt)
):
    previous_effective_state = "offline"
```

І далі використовувати `previous_effective_state` замість `previous_state`
у логіці переходів.

---

### 3. FIX reconnect behavior

При:

```
previous_effective_state == "offline"
AND current_bridge_host_present == true
```

→ примусово:

```python
device["online_since"] = now_iso
device["idle_since"] = None
device["offline_since"] = None
device["state_changed_at"] = now_iso
```

---

## Критерії приймання / Acceptance criteria

- reconnect → `online`, НЕ `idle`
- `bridge_host_present = true` → завжди `online`
- після reconnect:
  - `online_since` оновлюється
  - `idle_since = null`
- idle timeout → наступний reconnect стартує нову сесію
- API більше НЕ повертає `idle`, якщо є `bridge_host_present`

---

## Приклад (expected)

Було:

```
status: offline
```

Після reconnect:

```
bridge_host_present: true
status: online
idle_since: null
online_since: NEW timestamp
```
