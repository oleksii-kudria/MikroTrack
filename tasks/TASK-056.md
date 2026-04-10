# TASK-056 - Handle bridge_host loss and trigger state downgrade from online

## Overview / Опис

### UA
У поточній реалізації пристрій переходить у стан `online`, коли з'являється `bridge_host_present = true`, але НЕ переходить у інший стан, коли цей прапорець зникає.

Це призводить до ситуації, коли:
- пристрій фізично відсутній у мережі
- але залишається у стані `online`
- не запускається `idle` або `offline` логіка
- не працює `IDLE_TIMEOUT`

Потрібно реалізувати обробку втрати `bridge_host` як тригер для перерахунку стану.

### EN
Currently, device transitions to `online` when `bridge_host_present = true`, but does NOT transition out when this flag becomes false.

This leads to:
- device no longer present in network
- but still marked as `online`
- idle/offline logic not triggered
- `IDLE_TIMEOUT` not working

Need to handle `bridge_host` loss as a trigger for state recalculation.

---

## Problem description / Опис проблеми

### UA

Приклад:

```
bridge_host_present: true → false
arp_status: permanent
```

Фактична поведінка:
```
state = online (залишається)
```

Очікування:
```
state → idle або offline
```

### EN

Example:

```
bridge_host_present: true → false
arp_status: permanent
```

Actual:
```
state = online (unchanged)
```

Expected:
```
state → idle or offline
```

---

## Root cause / Причина

### UA
Відсутній обробник переходу:
```
bridge_host_present: true → false
```

Система реагує тільки на появу bridge host, але не на його зникнення.

### EN
Missing handler for transition:
```
bridge_host_present: true → false
```

System reacts only to presence, not to loss.

---

## Required behavior / Необхідна поведінка

### UA

При зміні:
```
bridge_host_present: true → false
```

Потрібно:
1. Запустити перерахунок стану
2. Оцінити інші джерела (ARP, DHCP)
3. Перевести пристрій у:
   - `idle` (якщо є слабкі ознаки)
   - `offline` (якщо немає evidence)

### EN

On change:
```
bridge_host_present: true → false
```

Must:
1. Trigger state recalculation
2. Evaluate other evidence (ARP, DHCP)
3. Transition device to:
   - `idle` (weak evidence)
   - `offline` (no evidence)

---

## Suggested logic / Рекомендована логіка

```python
if bridge_host_present:
    state = "online"

elif arp_status in ["stale", "delay", "probe"]:
    state = "idle"

elif arp_status in ["failed", "incomplete", "unknown"]:
    state = "offline"

else:
    state = "unknown"
```

---

## Event handling / Обробка подій

### UA

Додати обробку:
- `bridge_host_lost` (або через `evidence_changed`)

При втраті:
- викликати `recalculate_device_state()`
- генерувати:
  - `state_changed`
  - `device_idle` або `device_offline`
  - `session_ended` (якщо було online)

### EN

Add handling:
- `bridge_host_lost` (or via `evidence_changed`)

On loss:
- call `recalculate_device_state()`
- emit:
  - `state_changed`
  - `device_idle` or `device_offline`
  - `session_ended` (if was online)

---

## Scope / Межі задачі

### UA
НЕ потрібно:
- змінювати frontend
- змінювати API формат
- змінювати timeout логіку

Потрібно:
- змінити backend state machine

### EN
Do NOT:
- modify frontend
- modify API format
- modify timeout logic

Must:
- update backend state machine

---

## Acceptance criteria / Критерії приймання

### UA
- При втраті `bridge_host` пристрій не залишається `online`
- Відбувається перехід у `idle` або `offline`
- Генеруються відповідні події
- `online_since` скидається
- `idle_since` або `offline_since` встановлюється
- `IDLE_TIMEOUT` починає працювати

### EN
- On `bridge_host` loss device does not remain `online`
- Device transitions to `idle` or `offline`
- Proper events are generated
- `online_since` cleared
- `idle_since` or `offline_since` set
- `IDLE_TIMEOUT` starts working

---

## Notes / Примітки

### UA
- Це критичний баг, що ламає модель сесій
- Впливає на всі downstream механізми (таймери, UI, аналітику)

### EN
- Critical bug breaking session model
- Affects timers, UI, and analytics
