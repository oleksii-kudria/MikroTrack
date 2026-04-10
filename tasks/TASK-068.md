# TASK-068 - Fix false reconnect for PERM devices (offline → idle → online loop)

## Контекст

Після виправлення логіки `online_since` з’явилась нова проблема для пристроїв з бейджем `PERM` (ARP static / permanent):

- пристрій фізично відключений від мережі
- коректно переходить:
  - `online → idle → offline`
- але далі без реального підключення:
  - переходить у `online`
- при кожному циклі:
  - `online_since` скидається на поточний час
  - таймер починається з `00:00`

---

## Симптоми

У snapshot:

- `bridge_host_present = false`
- `arp_status = permanent`
- `arp_state = offline`

Але при цьому:

- `status = online`
- `online_since = now`
- `active = true`

Це означає, що система створює **хибний reconnect**.

---

## Корінь проблеми

У `app/persistence.py` в `_sanitize_presence_transition()` є правило:

```python
if prev == "offline" and curr == "idle":
    curr = "online"
```

Це правило:

- перетворює `offline → idle` у `offline → online`
- працює для всіх типів пристроїв

Але для `PERM`:

- `idle` означає відсутність активності
- не означає повернення пристрою в мережу

У результаті:

```text
offline → idle → online (помилково)
```

замість:

```text
offline → idle → offline
```

---

## Що потрібно зробити

### 1. Обмежити правило `offline → idle → online`

Змінити логіку:

### Було:
```python
if prev == "offline" and curr == "idle":
    curr = "online"
```

### Має бути:

Правило застосовується ТІЛЬКИ якщо є реальна ознака повернення пристрою:

- `bridge_host_present == true`
- або ARP статус став активним (`reachable`, `complete`)
- або інший валідний сигнал присутності

---

### 2. Заборонити reconnect для PERM без evidence

Для пристроїв:

- `arp_status == "permanent"`
- `bridge_host_present == false`

заборонити:

```text
offline → online
```

якщо немає нових ознак активності.

---

### 3. Узгодити стани

Гарантувати:

Якщо:

- `arp_state = offline`
- `bridge_host_present = false`

то:

```text
status = offline
active = false
```

---

## Вимоги до логування

Логи англійською.

Додати:

- `Skipping false reconnect for PERM device MAC ...`
- `PERM device remains offline due to lack of bridge_host evidence`

---

## Вимоги до тестування

### Сценарій 1 - PERM без bridge_host

1. online
2. idle
3. offline
4. новий цикл без підключення

Очікування:
- пристрій залишається `offline`
- `online_since` НЕ змінюється
- reconnect НЕ відбувається

---

### Сценарій 2 - PERM з реальним reconnect

1. offline
2. bridge_host_present = true

Очікування:
- `online`
- новий `online_since`

---

### Сценарій 3 - dynamic пристрій

Перевірити, що:

- поведінка не змінюється
- `idle` може перейти в `online` як і раніше

---

## Вимоги до документації

Оновити (UA + EN):

- пояснення, що `PERM` не означає онлайн
- опис ролі `bridge_host_present`
- опис умов reconnect

---

## Критерії приймання

- PERM пристрій не повертається в online без реального підключення
- `online_since` не скидається циклічно
- немає false reconnect
- dynamic пристрої працюють без змін

---

## Очікуваний результат

Система працює коректно:

```text
online → idle → offline → offline
```

і тільки при реальному підключенні:

```text
offline → online
```

без хибних сесій та reset таймера
