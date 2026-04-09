# TASK-050 - Add idle timeout and transition to offline

## Overview / Опис

### UA
Необхідно виправити логіку визначення стану пристрою, щоб довготривалий стан `idle` не вважався безперервною online-сесією.

Зараз пристрій може залишатися у стані `idle` багато годин, а після повернення в `online` таймер продовжується так, ніби пристрій весь цей час не зникав із мережі. Для операторського UI це виглядає некоректно.

Потрібно додати timeout для `idle`, після якого пристрій автоматично переводиться в `offline`.

### EN
Fix device state logic so that long-lasting `idle` state is no longer treated as a continuous online session.

Currently, a device can remain `idle` for many hours, and when it returns to `online`, the timer continues as if the device never actually left the network. For an operator-facing UI, this is misleading.

Add an `idle` timeout after which the device must automatically transition to `offline`.

---

## Goal / Мета

### UA
Зробити state/session model ближчою до реальної поведінки мережевих пристроїв:
- `idle` = короткочасна неактивність
- довгий `idle` = `offline`
- повернення з такого стану в `online` повинно запускати нову online-сесію

### EN
Make the state/session model closer to real device behavior:
- `idle` = short inactivity window
- long `idle` = `offline`
- returning from that state to `online` must start a new online session

---

## Problem statement / Опис проблеми

### UA
Поточна модель:
- `online ↔ idle` не скидає `online_since`
- `idle` може тривати дуже довго
- у результаті пристрій, який фактично був вимкнений, після повернення в `online` виглядає так, ніби він не вимикався

Приклад:
- TV був `online`
- потім 16 годин був `idle`
- після ввімкнення став `online`
- таймер не обнулився

Це технічно консистентно з поточною логікою, але не відповідає операторському очікуванню.

### EN
Current model:
- `online ↔ idle` does not reset `online_since`
- `idle` may last for a very long time
- as a result, a device that was effectively powered off appears to have been continuously online

Example:
- TV was `online`
- then stayed `idle` for 16 hours
- after power on it became `online`
- timer did not reset

This is technically consistent with current logic, but does not match operator expectations.

---

## Required behavior / Необхідна поведінка

### Idle timeout

#### UA
Потрібно додати configurable timeout для стану `idle`.

Рекомендована назва:
- `IDLE_TIMEOUT_SECONDS`

Рекомендоване дефолтне значення:
- `900` секунд (`15` хвилин)

Правило:
- якщо пристрій перебуває у стані `idle` довше за `IDLE_TIMEOUT_SECONDS`, його потрібно автоматично перевести у стан `offline`

#### EN
Add a configurable timeout for `idle` state.

Recommended name:
- `IDLE_TIMEOUT_SECONDS`

Recommended default:
- `900` seconds (`15` minutes)

Rule:
- if a device stays in `idle` longer than `IDLE_TIMEOUT_SECONDS`, it must be automatically transitioned to `offline`

---

## State transition rules / Правила переходів стану

### UA

#### 1. Online → Idle
- як і зараз, коротка втрата активності переводить пристрій у `idle`
- `online_since` зберігається
- `state_changed_at` оновлюється

#### 2. Idle within timeout
- якщо пристрій ще в межах timeout, він залишається `idle`
- `online_since` не скидається

#### 3. Idle timeout exceeded
- якщо тривалість `idle` перевищила `IDLE_TIMEOUT_SECONDS`, стан треба змінити на `offline`
- `offline_since` потрібно встановити у момент переходу в `offline`
- `online_since` потрібно скинути в `null`
- `state_changed_at` потрібно оновити

#### 4. Offline → Online
- коли пристрій після цього знову з'являється як `online`
- стартує нова online-сесія:
  - `online_since = now`
  - `offline_since = null`
  - `state_changed_at = now`

#### 5. Idle → Online before timeout
- якщо пристрій повернувся в `online` до закінчення timeout
- це все ще та сама online-сесія
- `online_since` не скидається
- `state_changed_at` оновлюється

### EN

#### 1. Online → Idle
- as now, short activity loss moves the device into `idle`
- `online_since` is preserved
- `state_changed_at` is updated

#### 2. Idle within timeout
- if device is still within timeout window, it remains `idle`
- `online_since` is not reset

#### 3. Idle timeout exceeded
- if `idle` duration exceeds `IDLE_TIMEOUT_SECONDS`, state must change to `offline`
- `offline_since` must be set at the moment of transition to `offline`
- `online_since` must be reset to `null`
- `state_changed_at` must be updated

#### 4. Offline → Online
- when the device later appears as `online`
- a new online session starts:
  - `online_since = now`
  - `offline_since = null`
  - `state_changed_at = now`

#### 5. Idle → Online before timeout
- if device returns to `online` before timeout expires
- it is still the same online session
- `online_since` is preserved
- `state_changed_at` is updated

---

## Time model expectations / Очікування щодо таймерів

### UA
Після впровадження timeout:
- короткий `idle` не повинен ламати поточну online-сесію
- довгий `idle` повинен завершувати online-сесію
- при поверненні після довгого `idle` таймер `online` повинен стартувати заново

### EN
After timeout is implemented:
- short `idle` must not break the current online session
- long `idle` must end the online session
- when device returns after long `idle`, the online timer must start from zero again

---

## Suggested implementation logic / Рекомендована логіка реалізації

### UA
Потрібно враховувати не лише raw state (`idle`), а й тривалість перебування в ньому.

Логіка на високому рівні:

1. визначити raw device state
2. якщо raw state = `idle`
3. перевірити, скільки часу минуло від `state_changed_at` або окремого timestamp початку idle
4. якщо timeout перевищено:
   - нормалізувати state до `offline`
5. далі застосувати session-aware transition rules

### EN
Consider not only raw state (`idle`), but also how long the device has remained in it.

High-level flow:

1. determine raw device state
2. if raw state = `idle`
3. check elapsed time since `state_changed_at` or a dedicated idle-start timestamp
4. if timeout is exceeded:
   - normalize state to `offline`
5. then apply session-aware transition rules

---

## Configuration / Конфігурація

### UA
Додати новий параметр конфігурації:

- `IDLE_TIMEOUT_SECONDS`

Вимоги:
- читати з `.env`
- мати дефолтне значення
- валідовувати як додатне ціле число
- використовувати в collector/state logic

### EN
Add new configuration parameter:

- `IDLE_TIMEOUT_SECONDS`

Requirements:
- read from `.env`
- provide default value
- validate as a positive integer
- use in collector/state logic

---

## Scope / Межі задачі

### UA
У цій задачі потрібно:
- змінити backend/state logic
- оновити session-aware transitions
- додати конфігураційний параметр
- за потреби оновити документацію

Не потрібно:
- змінювати frontend layout
- додавати нові UI badge
- змінювати sorting/filtering
- додавати WebSocket/SSE

### EN
This task must:
- update backend/state logic
- update session-aware transitions
- add configuration parameter
- update documentation if needed

This task must NOT:
- change frontend layout
- add new UI badges
- modify sorting/filtering
- add WebSocket/SSE

---

## Logging / Логування

### UA
Усі технічні логи повинні бути англійською мовою.

### EN
All technical logs must be in English.

Recommended examples:
- `Idle timeout exceeded for MAC AA:BB:CC:DD:EE:FF, forcing state to offline`
- `New online session started for MAC AA:BB:CC:DD:EE:FF`
- `Device remained idle within timeout for MAC AA:BB:CC:DD:EE:FF`

---

## Acceptance criteria / Критерії приймання

### UA
- Додано `IDLE_TIMEOUT_SECONDS`
- Довгий `idle` більше не може тривати необмежено довго
- Після перевищення timeout пристрій переходить у `offline`
- `online_since` скидається при такому переході
- `offline_since` встановлюється коректно
- Якщо пристрій повернувся в `online` після timeout, стартує нова online-сесія
- Якщо пристрій повернувся в `online` до timeout, стара online-сесія зберігається
- Таймери в UI після цього поводяться коректно без змін frontend логіки
- Existing short idle behavior is preserved

### EN
- `IDLE_TIMEOUT_SECONDS` is added
- Long `idle` can no longer last indefinitely
- After timeout is exceeded, device transitions to `offline`
- `online_since` is reset on that transition
- `offline_since` is set correctly
- If device returns to `online` after timeout, a new online session starts
- If device returns to `online` before timeout, the old online session is preserved
- UI timers behave correctly afterward without frontend changes
- Existing short idle behavior is preserved

---

## Notes / Примітки

### UA
- Це важливе виправлення семантики станів, а не просто UI покращення
- Мета - зробити `online` таймер правдивим для реального операторського сценарію
- Не потрібно ламати концепцію короткого `idle`; потрібно лише обмежити її в часі

### EN
- This is an important state semantics fix, not just a UI improvement
- The goal is to make the `online` timer truthful for real operator workflows
- Do not remove short `idle`; only limit it in time
