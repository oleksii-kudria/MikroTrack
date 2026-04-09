# TASK-051 - Fix idle timeout loop and enforce idle-to-offline transition

## Overview / Опис

### UA
Після впровадження `IDLE_TIMEOUT_SECONDS` виявлено дефект:
пристрої у стані `idle` не переходять у `offline` після перевищення timeout, а замість цього їх таймер циклічно скидається (00:00 → timeout → 00:00).

Потрібно виправити логіку так, щоб після перевищення timeout відбувався реальний перехід `idle → offline`, а не оновлення timestamp для `idle`.

### EN
After introducing `IDLE_TIMEOUT_SECONDS`, a defect was observed:
devices in `idle` do not transition to `offline` after timeout. Instead, their timer resets in a loop (00:00 → timeout → 00:00).

Fix the logic so that exceeding the timeout triggers a real `idle → offline` transition instead of resetting idle timestamps.

---

## Problem description / Опис проблеми

### UA
Поточна поведінка:
- пристрій у `idle`
- таймер доходить до timeout (наприклад 120 сек)
- таймер скидається на 00:00
- стан залишається `idle`
- цикл повторюється

Очікувана поведінка:
- після перевищення timeout стан змінюється на `offline`
- таймер більше не скидається
- починається відлік `offline_since`

### EN
Current behavior:
- device is in `idle`
- timer reaches timeout (e.g., 120 seconds)
- timer resets to 00:00
- state remains `idle`
- loop repeats

Expected behavior:
- after timeout is exceeded, state changes to `offline`
- timer does not reset
- `offline_since` timer starts

---

## Root cause hypothesis / Ймовірна причина

### UA
Ймовірно, при перевищенні timeout:
- оновлюється `state_changed_at`
- але `state` не змінюється на `offline`

Тобто виконується "refresh idle", а не "transition to offline".

### EN
Most likely, when timeout is exceeded:
- `state_changed_at` is updated
- but `state` is not changed to `offline`

This results in refreshing idle instead of transitioning to offline.

---

## Required behavior / Необхідна поведінка

### UA

При виконанні умови:

```
state == "idle"
AND idle_duration > IDLE_TIMEOUT_SECONDS
```

повинно виконуватися:

- `state = "offline"`
- `offline_since = now`
- `online_since = null`
- `state_changed_at = now`

І ця операція повинна виконуватися **один раз**, без повторних циклів.

### EN

When condition is met:

```
state == "idle"
AND idle_duration > IDLE_TIMEOUT_SECONDS
```

must perform:

- `state = "offline"`
- `offline_since = now`
- `online_since = null`
- `state_changed_at = now`

This transition must occur **once**, without repeated loops.

---

## Forbidden behavior / Заборонена поведінка

### UA
- не оновлювати `state_changed_at`, якщо стан не змінюється
- не залишати `state = idle` після перевищення timeout
- не створювати циклічний reset таймера

### EN
- do not update `state_changed_at` if state is not changing
- do not keep `state = idle` after timeout exceeded
- do not create timer reset loops

---

## Implementation requirements / Вимоги до реалізації

### UA

1. Перевірити гілку обробки idle timeout
2. Розділити логіку:
   - idle within timeout
   - idle timeout exceeded
3. Переконатися, що:
   - при exceeded виконується реальний state transition
4. Заборонити повторне виконання переходу:
   - якщо вже `offline`, не виконувати логіку idle timeout

### EN

1. Review idle timeout handling logic
2. Separate logic:
   - idle within timeout
   - idle timeout exceeded
3. Ensure:
   - exceeded branch performs real state transition
4. Prevent repeated transitions:
   - if already `offline`, skip idle timeout logic

---

## Suggested pseudo-code / Псевдокод

```python
if state == "idle":
    idle_duration = now - state_changed_at

    if idle_duration > IDLE_TIMEOUT_SECONDS:
        state = "offline"
        state_changed_at = now
        offline_since = now
        online_since = None
    else:
        # keep idle state, do nothing
```

---

## Edge cases / Крайні випадки

### UA
- якщо пристрій повернувся в `online` до timeout → нічого не змінюємо
- якщо вже `offline` → не застосовувати idle timeout логіку
- уникати подвійного transition в одному циклі

### EN
- if device returns to `online` before timeout → no change
- if already `offline` → skip idle timeout logic
- avoid double transitions in same cycle

---

## Logging / Логування

### EN only
- `Idle timeout exceeded for MAC XX:XX:XX:XX:XX:XX, switching to offline`
- `Skipping idle timeout, device already offline`
- `Idle within threshold for MAC XX:XX:XX:XX:XX:XX`

---

## Acceptance criteria / Критерії приймання

### UA
- idle більше не циклічно скидається
- після timeout пристрій переходить у `offline`
- таймер більше не перезапускається в idle
- online → idle → offline працює коректно
- offline → online запускає нову сесію
- немає повторних циклів переходу

### EN
- idle no longer resets in loop
- device transitions to `offline` after timeout
- timer does not restart in idle
- online → idle → offline works correctly
- offline → online starts new session
- no repeated transition loops

---

## Notes / Примітки

### UA
- це bugfix, а не нова фіча
- має бути реалізовано поверх TASK-050
- критично для коректності таймерів

### EN
- this is a bugfix, not a new feature
- must be implemented on top of TASK-050
- critical for correct timer behavior
