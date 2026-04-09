# TASK-053 - Fix API device status mapping to keep offline after idle timeout

## Overview / Опис

### UA
У поточній реалізації `/api/devices` повертає суперечливі дані:
- timestamps (`offline_since`, `state_changed_at`) показують, що пристрій вже `offline`
- але поля `state` / `status` залишаються `idle`

Це призводить до некоректного відображення у UI та створює розсинхрон між backend логікою і API.

### EN
The current `/api/devices` response contains inconsistent data:
- timestamps (`offline_since`, `state_changed_at`) indicate the device is `offline`
- but `state` / `status` fields still show `idle`

This causes incorrect UI behavior and desynchronization between backend logic and API output.

---

## Problem description / Опис проблеми

### UA

Приклад:

```
arp_state = "offline"
offline_since != null
online_since = null
```

але:

```
status = "idle"
state = "idle"
```

Очікування:
```
status = "offline"
state = "offline"
```

### EN

Example:

```
arp_state = "offline"
offline_since != null
online_since = null
```

but:

```
status = "idle"
state = "idle"
```

Expected:

```
status = "offline"
state = "offline"
```

---

## Root cause / Причина

### UA
При формуванні API відповіді використовується неправильний пріоритет:
- `arp_status` (stale) → `idle`
- навіть якщо backend вже визначив `offline`

### EN
Incorrect priority in API mapping:
- `arp_status` (stale) → `idle`
- even when backend already resolved `offline`

---

## Required behavior / Необхідна поведінка

### UA
Поля `state` і `status` повинні відображати фінальний стан пристрою:

Пріоритет:
1. якщо `offline_since != null` → `offline`
2. якщо `online_since != null` → `online`
3. якщо `idle_since != null` → `idle`
4. fallback → `unknown`

### EN
`state` and `status` must reflect final resolved device state:

Priority:
1. if `offline_since != null` → `offline`
2. if `online_since != null` → `online`
3. if `idle_since != null` → `idle`
4. fallback → `unknown`

---

## Implementation requirements / Вимоги

### UA

Заборонено:
- визначати статус лише через `arp_status`
- перебивати `offline` значенням `idle`

Потрібно:
- використовувати session/timestamp-based логіку
- синхронізувати `state`, `status` з backend state

### EN

Do NOT:
- derive status only from `arp_status`
- override `offline` with `idle`

Must:
- use session/timestamp-based logic
- keep `state`, `status` aligned with backend state

---

## Suggested pseudo-code / Псевдокод

```python
if device.offline_since is not None:
    state = "offline"
elif device.online_since is not None:
    state = "online"
elif device.idle_since is not None:
    state = "idle"
else:
    state = "unknown"

device.state = state
device.status = state
```

---

## Scope / Межі задачі

### UA
НЕ потрібно:
- змінювати frontend
- змінювати timeout логіку
- змінювати event system

Потрібно:
- виправити лише API response mapping

### EN
Do NOT:
- modify frontend
- modify timeout logic
- modify event system

Must:
- fix API response mapping only

---

## Logging / Логування

### EN only
- `API state mapping: resolved offline for MAC XX:XX`
- `API state mapping: prevented idle override for MAC XX:XX`

---

## Acceptance criteria / Критерії

### UA
- Якщо `offline_since != null` → API повертає `offline`
- `idle` більше не перебиває `offline`
- `state` і `status` завжди однакові
- UI автоматично починає показувати правильний статус
- дані API консистентні

### EN
- If `offline_since != null` → API returns `offline`
- `idle` no longer overrides `offline`
- `state` and `status` always match
- UI automatically displays correct state
- API data is consistent

---

## Notes / Примітки

### UA
- це ключовий баг синхронізації даних
- після виправлення UI почне працювати без змін

### EN
- this is a critical data consistency bug
- fixing it will automatically fix UI behavior
