# TASK-066 - Force timer reset for PERM devices on offline -> online transition

## Контекст

Після виконання TASK-064 та TASK-065 проблема зі скиданням таймера залишається для пристроїв з бейджем `PERM` (ARP static / permanent).

Поточна ситуація:

- Для dynamic ARP:
  - `offline -> online` → нова сесія
  - `online_since` коректно оновлюється

- Для PERM (static ARP):
  - події (`SESSION_STARTED`, `STATE_CHANGED`) генеруються коректно
  - `state_changed_at` оновлюється
  - але `online_since` НЕ оновлюється
  - таймер (`elapsed_seconds`) продовжує стару сесію

---

## Причина

Навіть після виправлень:
- persistence або API в окремих сценаріях не трактує reconnect як нову session boundary
- для `PERM` пристроїв це відбувається частіше через особливості ARP логіки (`permanent` статус)

У результаті:
- `offline -> online` не завжди запускає reset таймера

---

## Що потрібно зробити

### 1. Ввести явне правило для PERM

Для пристроїв з:
- `arp_status == "permanent"` АБО
- бейджем `"PERM"`

при переході:

```text
offline -> online
```

ОБОВ’ЯЗКОВО виконувати reset таймерів.

---

### 2. Примусовий reset session timestamps

При виконанні умови вище встановлювати:

```text
online_since = now
idle_since = null
offline_since = null
state_changed_at = now
```

Це має виконуватись незалежно від:
- попередніх значень у snapshot
- логіки derived/effective state
- bridge_host або ARP статусу

---

### 3. Реалізація

Основне місце:
- `app/persistence.py`
- функція `_apply_stable_timestamps()`

Додати логіку:

```python
is_perm_device = (
    normalize_arp_status(device.get("arp_status", "")) == "permanent"
    or "PERM" in [str(x).strip().upper() for x in device.get("badges", [])]
)

if previous_presence_state == "offline" and current_presence_state == "online" and is_perm_device:
    # force reset
```

---

### 4. Захист від повторного затирання

Перевірити, що:
- після встановлення нового `online_since`
- значення не перезаписується нижче в коді (merge / preserve блоки)

---

### 5. Узгодження з API

Перевірити `app/api/main.py`, що:
- новий `online_since` з snapshot НЕ замінюється старим значенням
- events не перетирають актуальні timestamps

---

## Вимоги до логування

Логи англійською.

Додати:

- `PERM reconnect detected for MAC XX:XX:XX:XX:XX:XX`
- `Forced session reset applied for PERM device`
- `online_since overridden due to PERM reconnect`

---

## Вимоги до журналів подій

Перевірити, що sequence подій залишається:

```text
DEVICE_OFFLINE
STATE_CHANGED
SESSION_ENDED

DEVICE_ONLINE
STATE_CHANGED
SESSION_STARTED
```

Нові події додавати не обов’язково, якщо логіка вже достатня.

---

## Вимоги до тестування

### 1. PERM reconnect
- ARP = permanent
- `offline -> online`
- перевірити:
  - новий `online_since`
  - `elapsed_seconds ≈ 0`

### 2. Regression
- dynamic ARP не ламається

### 3. Mixed scenario
- PERM + bridge_host
- PERM без bridge_host

---

## Вимоги до документації

Оновити документацію (UA + EN):

- опис special-case для PERM
- пояснення чому використовується force reset
- опис поведінки reconnect

---

## Критерії приймання

- для PERM пристроїв таймер завжди скидається при `offline -> online`
- `online_since` більше не переноситься зі старої сесії
- API повертає новий timer
- dynamic пристрої працюють як раніше
- логування відображає застосування правила

---

## Очікуваний результат

Система стабільно працює для всіх типів пристроїв:

```text
online -> idle -> offline -> online
```

де:
- кожен `offline -> online` = нова сесія
- таймер завжди починається з `00:00`
