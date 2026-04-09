# TASK-052 - Fix UI state mapping to use fused_state as primary source

## Overview / Опис

### UA
У поточній реалізації UI відображає стан пристрою (Status) не на основі `fused_state`, а через похідні значення (`arp_status`, `arp_state`), що призводить до некоректного відображення.

В результаті:
- backend правильно визначає `offline`
- API повертає `fused_state = offline`
- але UI показує `idle`

Потрібно виправити мапінг стану в UI так, щоб **основним джерелом істини був `fused_state`**.

### EN
Currently, the UI displays device state (Status) not based on `fused_state`, but using derived values (`arp_status`, `arp_state`), which leads to incorrect display.

As a result:
- backend correctly determines `offline`
- API returns `fused_state = offline`
- but UI shows `idle`

Fix UI state mapping so that **`fused_state` is the primary source of truth**.

---

## Problem description / Опис проблеми

### UA

Приклад:

```
fused_state = "offline"
arp_status = "stale"
```

Очікування:
```
Status = offline
```

Фактична поведінка:
```
Status = idle
```

Причина:
- UI інтерпретує `arp_status = stale` як `idle`
- ігноруючи `fused_state`

### EN

Example:

```
fused_state = "offline"
arp_status = "stale"
```

Expected:
```
Status = offline
```

Actual:
```
Status = idle
```

Reason:
- UI maps `arp_status = stale` to `idle`
- ignoring `fused_state`

---

## Required behavior / Необхідна поведінка

### UA

- UI повинен використовувати `fused_state` як primary source
- `arp_status` та інші поля можуть використовуватись тільки як fallback
- якщо `fused_state` заданий → він має повністю визначати статус

### EN

- UI must use `fused_state` as the primary source
- `arp_status` and other fields should be fallback only
- if `fused_state` is present → it must fully determine the status

---

## Implementation requirements / Вимоги до реалізації

### Current (incorrect)

```javascript
function getStatus(device) {
  if (device.arp_status === "stale") return "idle";
  if (device.arp_status === "reachable") return "online";
  if (device.arp_status === "unknown") return "unknown";
}
```

### Required (correct)

```javascript
function getStatus(device) {
  if (device.fused_state) {
    return device.fused_state;
  }

  // fallback only if fused_state missing
  if (device.arp_status === "stale") return "idle";
  if (device.arp_status === "reachable") return "online";
  if (device.arp_status === "unknown") return "unknown";

  return "unknown";
}
```

---

## UI mapping rules / Правила відображення

### UA

| fused_state | UI Status |
|------------|----------|
| online     | online   |
| idle       | idle     |
| offline    | offline  |
| unknown    | unknown  |

### EN

| fused_state | UI Status |
|------------|----------|
| online     | online   |
| idle       | idle     |
| offline    | offline  |
| unknown    | unknown  |

---

## Scope / Межі задачі

### UA
НЕ потрібно:
- змінювати backend
- змінювати API
- змінювати state machine
- змінювати timeout логіку

Потрібно:
- виправити тільки frontend mapping

### EN
Do NOT:
- modify backend
- modify API
- modify state machine
- modify timeout logic

Must:
- fix frontend mapping only

---

## Logging / Логування

### EN only
- `UI state mapping: using fused_state=offline for MAC XX:XX:XX:XX`
- `UI fallback mapping used for MAC XX:XX:XX:XX`

---

## Acceptance criteria / Критерії приймання

### UA
- Якщо `fused_state = offline`, UI показує `offline`
- Якщо `fused_state = idle`, UI показує `idle`
- `arp_status` більше не перебиває `fused_state`
- Таймери відповідають правильному стану
- Поведінка UI відповідає backend/API
- Всі існуючі фільтри і сортування працюють без змін

### EN
- If `fused_state = offline`, UI shows `offline`
- If `fused_state = idle`, UI shows `idle`
- `arp_status` no longer overrides `fused_state`
- Timers match correct state
- UI behavior matches backend/API
- Existing filters and sorting continue to work

---

## Notes / Примітки

### UA
- Це критичний баг синхронізації UI та backend
- Після виправлення UI буде відображати реальний стан мережі

### EN
- This is a critical UI/backend consistency bug
- After fix, UI will reflect actual network state
