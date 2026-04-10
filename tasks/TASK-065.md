# TASK-065 - Fix session timer inconsistency for PERM ARP and prioritize events over snapshot in API

## Контекст

Після виконання TASK-064 проблема зі скиданням таймера частково залишилась.

Поточна ситуація:
- для звичайних (dynamic) ARP записів:
  - перехід `offline -> online` коректно створює нову сесію
  - `online_since` скидається
- для статичних ARP записів (`PERM`):
  - події (`events.jsonl`) фіксують правильну послідовність:
    - `DEVICE_OFFLINE`
    - `STATE_CHANGED`
    - `SESSION_ENDED`
    - `DEVICE_ONLINE`
    - `STATE_CHANGED`
    - `SESSION_STARTED`
  - але в API / UI:
    - `online_since` НЕ скидається
    - таймер продовжує попередню сесію

---

## Виявлені проблеми

### 1. API ігнорує новіші дані з events

У `app/api/main.py`:
- timestamps (`online_since`, `idle_since`, `offline_since`) з events використовуються ТІЛЬКИ як fallback
- якщо в snapshot є значення — воно не замінюється навіть якщо events новіші

Результат:
- навіть при правильному `SESSION_STARTED` API може віддавати старий `online_since`

---

### 2. Неузгодженість логіки для ARP status = permanent

У різних частинах системи `permanent` інтерпретується по-різному:

- `app/arp_logic.py`:
  - `fused_device_state()` → `permanent` → `unknown`
- `app/persistence.py`:
  - `_recalculate_state_on_bridge_host_loss()` → `permanent` → `idle`

Результат:
- з’являються переходи типу:
  - `online -> idle -> unknown -> online`
- це ламає session lifecycle
- впливає на reset таймерів

---

## Що потрібно зробити

### 1. Пріоритет events над snapshot у API

У `app/api/main.py` змінити логіку формування session timestamps:

#### Поточна логіка (неправильна)
- events використовуються тільки якщо snapshot не має значення

#### Нова логіка (обов’язкова)
- якщо в `session_by_mac` є дані
- і `event.state_changed_at >= snapshot.state_changed_at`
→ використовувати значення з events

Оновити:
- `state_changed_at`
- `online_since`
- `idle_since`
- `offline_since`

#### Очікувана поведінка
- `SESSION_STARTED` завжди оновлює `online_since`
- snapshot НЕ може “перебити” новішу подію

---

### 2. Уніфікувати логіку для ARP status = permanent

Необхідно привести всю систему до єдиного правила:

#### Рекомендована модель:
- `permanent + bridge_host_present = true` → `online`
- `permanent + bridge_host_present = false` → `idle`

#### Заборонено:
- повертати `unknown` для `permanent`

#### Де внести зміни:
- `app/arp_logic.py`
- `app/persistence.py` (перевірити відповідність)
- за потреби `app/api/main.py`

---

### 3. Забезпечити коректний session lifecycle

Після змін система повинна працювати стабільно:

```text
online → idle → offline → online
```

Без переходів через:
```text
unknown
```

Особливо для `PERM` пристроїв.

---

## Вимоги до логування

Логи — англійською.

Додати повідомлення:
- `API: overriding snapshot session timestamps with newer event data for MAC ...`
- `PERM state normalized to idle/online for MAC ...`

---

## Вимоги до журналів подій

Перевірити, що:
- `SESSION_STARTED` завжди відповідає новому `online_since`
- `SESSION_ENDED` закриває попередню сесію

Якщо потрібно:
- уточнити порядок або типи подій

---

## Вимоги до тестування

Додати тести:

### 1. PERM reconnect
- ARP = permanent
- `online -> offline -> online`
- перевірити:
  - новий `online_since`
  - таймер = ~0

### 2. Snapshot vs events conflict
- snapshot має старий `online_since`
- events мають новий `SESSION_STARTED`
- API повинен повернути новий timestamp

### 3. No unknown state for PERM
- перевірити, що `unknown` не з’являється у lifecycle

---

## Вимоги до документації

Оновити документацію:

### Українською та англійською:
- пояснити логіку `permanent`
- описати пріоритет events над snapshot
- описати reset таймерів

---

## Критерії приймання

Задача виконана, якщо:

- API використовує найновіші дані з events
- `online_since` коректно скидається після reconnect
- для `PERM` немає `unknown` станів
- session lifecycle стабільний
- тести покривають сценарії
- документація оновлена

---

## Очікуваний результат

- reconnect для всіх типів пристроїв (включно з PERM) створює нову сесію
- таймер починається з `00:00`
- API і UI показують коректний стан
