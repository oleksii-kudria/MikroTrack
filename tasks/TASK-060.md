# TASK-060 - Apply idle timeout in API device state resolver

## Опис / Description

### UA
Виявлено проблему: `/api/devices` формує `status` / `state` для веб-інтерфейсу без урахування `IDLE_TIMEOUT_SECONDS`.

Через це пристрій може вже перевищити timeout у стані `idle`, але API все одно продовжує повертати `status = "idle"`, якщо в snapshot ще немає `offline_since`.

Це особливо помітно для пристроїв типу `PERM` / static ARP, але проблема насправді знаходиться в API state resolver.

### EN
Issue found: `/api/devices` builds `status` / `state` for the web UI without applying `IDLE_TIMEOUT_SECONDS`.

As a result, a device may already exceed idle timeout, but the API still returns `status = "idle"` if the snapshot does not yet contain `offline_since`.

This is especially visible for `PERM` / static ARP devices, but the actual problem is in the API state resolver.

---

## Проблема / Problem

### UA
Поточна логіка `_resolve_api_state()` у `app/api/main.py` працює так:

1. якщо `offline_since != null` → `offline`
2. якщо `idle_since != null` → `idle`
3. якщо `online_since != null` → `online`
4. інакше → `unknown`

Проблема:
- немає перевірки `IDLE_TIMEOUT_SECONDS`
- немає перевірки `bridge_host_present`
- немає примусового переходу `idle -> offline` на рівні API

### EN
Current `_resolve_api_state()` logic in `app/api/main.py` is:

1. if `offline_since != null` → `offline`
2. if `idle_since != null` → `idle`
3. if `online_since != null` → `online`
4. else → `unknown`

Problem:
- no `IDLE_TIMEOUT_SECONDS` check
- no `bridge_host_present` check
- no forced `idle -> offline` transition at API layer

---

## Очікувана поведінка / Expected behavior

### UA
API повинен повертати `offline`, якщо одночасно виконуються умови:

- `idle_since != null`
- `offline_since == null`
- `bridge_host_present == false`
- `now - idle_since >= IDLE_TIMEOUT_SECONDS`

У такому випадку:
- `status` має бути `offline`
- `flags.state` має бути `offline`
- `active = false`

Навіть якщо snapshot ще не містить `offline_since`.

### EN
API must return `offline` if all conditions are true:

- `idle_since != null`
- `offline_since == null`
- `bridge_host_present == false`
- `now - idle_since >= IDLE_TIMEOUT_SECONDS`

In that case:
- `status` must be `offline`
- `flags.state` must be `offline`
- `active = false`

Even if snapshot does not yet contain `offline_since`.

---

## Що треба змінити / Required changes

### UA

У `app/api/main.py`:

1. Додати читання `IDLE_TIMEOUT_SECONDS` з environment/config
2. Передавати в `_resolve_api_state()` додаткові параметри:
   - `idle_since`
   - `bridge_host_present`
   - `now`
   - `idle_timeout_seconds`
3. Додати перевірку timeout перед поверненням `idle`

Рекомендований пріоритет:

1. якщо `offline_since != null` → `offline`
2. якщо `idle_since != null` і timeout exceeded та `bridge_host_present == false` → `offline`
3. якщо `idle_since != null` → `idle`
4. якщо `online_since != null` → `online`
5. інакше → `unknown`

### EN

In `app/api/main.py`:

1. Read `IDLE_TIMEOUT_SECONDS` from environment/config
2. Pass additional parameters into `_resolve_api_state()`:
   - `idle_since`
   - `bridge_host_present`
   - `now`
   - `idle_timeout_seconds`
3. Add timeout check before returning `idle`

Recommended priority:

1. if `offline_since != null` → `offline`
2. if `idle_since != null` and timeout exceeded and `bridge_host_present == false` → `offline`
3. if `idle_since != null` → `idle`
4. if `online_since != null` → `online`
5. else → `unknown`

---

## Рекомендований псевдокод / Suggested pseudocode

```python
def _resolve_api_state(
    *,
    mac: str,
    offline_since: datetime | None,
    online_since: datetime | None,
    idle_since: datetime | None,
    bridge_host_present: bool,
    now: datetime,
    idle_timeout_seconds: int,
    fallback_state: str,
) -> str:
    if isinstance(offline_since, datetime):
        return "offline"

    if (
        isinstance(idle_since, datetime)
        and not bridge_host_present
        and int((now - idle_since).total_seconds()) >= idle_timeout_seconds
    ):
        return "offline"

    if isinstance(idle_since, datetime) and (
        not isinstance(online_since, datetime) or idle_since >= online_since
    ):
        return "idle"

    if isinstance(online_since, datetime):
        return "online"

    return "unknown"
```

---

## Межі задачі / Scope

### UA
Потрібно:
- змінити тільки API state resolver
- не змінювати frontend
- не змінювати web sorting / filtering
- не змінювати persistence diff logic в цій задачі

### EN
Must:
- update API state resolver only
- do not change frontend
- do not change web sorting / filtering
- do not change persistence diff logic in this task

---

## Логи / Logs

### UA
Якщо додаються логи, вони повинні бути англійською мовою.

### EN
If logs are added, they must be in English.

Recommended examples:
- `API idle timeout exceeded for MAC XX:XX:XX:XX:XX:XX, resolving state to offline`
- `API state mapping: resolved offline by timeout for MAC XX:XX:XX:XX:XX:XX`

---

## Документація / Documentation

### UA
Оновити документацію:
- пояснити, що API також застосовує timeout-захист для `idle`
- описати, чому `offline_since` може ще бути відсутнім у snapshot, але API вже повертає `offline`

### EN
Update documentation:
- explain that API also applies idle-timeout protection
- document why `offline_since` may still be absent in snapshot while API already returns `offline`

---

## Критерії приймання / Acceptance criteria

### UA
- `/api/devices` більше не тримає запис у `idle`, якщо timeout уже перевищено
- для `bridge_host_present = false` та `idle_since + timeout` API повертає `offline`
- `status`, `flags.state`, `active` стають консистентними
- PERM/static ARP пристрої більше не зависають у `idle` тільки через API mapping
- frontend автоматично починає показувати правильний статус без змін у UI коді

### EN
- `/api/devices` no longer keeps a record in `idle` after timeout is exceeded
- for `bridge_host_present = false` and `idle_since + timeout`, API returns `offline`
- `status`, `flags.state`, and `active` become consistent
- PERM/static ARP devices no longer get stuck in `idle` due to API mapping
- frontend automatically shows the correct state without UI code changes

---

## Примітки / Notes

### UA
- Це bugfix для API mapping layer
- Основна мета - зробити відповідь `/api/devices` ближчою до реального стану мережі навіть між snapshot transitions

### EN
- This is a bugfix for the API mapping layer
- Main goal: make `/api/devices` reflect real network state even between snapshot transitions
