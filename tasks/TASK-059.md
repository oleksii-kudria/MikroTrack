# TASK-059 - Fix idle timeout for PERM/static ARP devices

## Опис / Description

### UA
Виявлено проблему: пристрої з ARP статусом `permanent` (flags `SC`, badge `PERM`) не переходять у стан `offline` після перевищення `IDLE_TIMEOUT_SECONDS`, хоча відсутні в bridge (`bridge_host_present = false`) та неактивні.

Це призводить до ситуації, коли пристрій залишається у стані `idle` безкінечно.

### EN
Issue detected: devices with ARP status `permanent` (flags `SC`, badge `PERM`) do not transition to `offline` after exceeding `IDLE_TIMEOUT_SECONDS`, even when `bridge_host_present = false` and device is inactive.

This results in devices being stuck in `idle` state indefinitely.

---

## Поточна поведінка / Current behavior

### UA
- PERM пристрій переходить у `idle`
- після перевищення timeout:
  - НЕ переходить у `offline`
  - `idle_duration_seconds` продовжує зростати

### EN
- PERM device enters `idle`
- after timeout:
  - does NOT transition to `offline`
  - `idle_duration_seconds` keeps increasing

---

## Очікувана поведінка / Expected behavior

### UA

Якщо виконуються умови:
- `active = false`
- `bridge_host_present = false`
- `idle_duration_seconds >= IDLE_TIMEOUT_SECONDS`

ТО:
- `status = "offline"`
- `state = "offline"`
- `offline_since = now`
- `idle_since = null`
- `online_since = null`

НЕЗАЛЕЖНО від:
- `arp_status = permanent`
- `arp_flag = SC`
- наявності badge `PERM`

### EN

If conditions met:
- `active = false`
- `bridge_host_present = false`
- `idle_duration_seconds >= IDLE_TIMEOUT_SECONDS`

THEN:
- force transition to `offline`
- regardless of:
  - `arp_status = permanent`
  - `arp_flag = SC`
  - `PERM` badge

---

## Причина проблеми / Root cause hypothesis

### UA

Ймовірно в коді є логіка:
- яка виключає PERM записи з idle timeout
- або трактує `permanent` як "still present"

### EN

Likely cause:
- PERM devices excluded from timeout logic
- or `permanent` treated as presence evidence

---

## Backend changes

### UA

Знайти логіку:
- idle → offline transition
- додати явне правило:

```python
if not active and not bridge_host_present:
    if idle_duration_seconds >= IDLE_TIMEOUT_SECONDS:
        force_offline_transition()
```

ВАЖЛИВО:
- ця логіка має виконуватись ДО перевірок arp_status

### EN

Ensure timeout logic is applied BEFORE any ARP-specific conditions.

---

## Логи / Logs

### UA

Додати подію:
```
event_type: device_offline
reason: idle_timeout
```

для PERM пристроїв також.

### EN

Ensure logs include:
- device_offline with reason `idle_timeout` for PERM devices

---

## Документація / Documentation

### UA

Оновити:
- пояснення статусів
- уточнити що PERM ≠ always online

### EN

Update docs:
- clarify PERM does not prevent offline transition

---

## Acceptance criteria / Критерії приймання

### UA

- PERM пристрій переходить:
  - online → idle → offline
- timeout працює для всіх типів записів
- відсутні "завислі idle" записи
- коректні timestamps:
  - offline_since встановлюється

### EN

- PERM devices transition:
  - online → idle → offline
- timeout works for all device types
- no stuck idle states
- correct timestamps applied
