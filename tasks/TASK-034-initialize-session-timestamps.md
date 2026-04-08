# TASK-034 - Initialize session timestamps for devices with missing values

## Контекст

Після реалізації TASK-031 timestamps (online_since, offline_since, state_changed_at)
повинні зберігатись між poll.

Однак виявлено проблему:
- для більшості пристроїв timestamps залишаються null
- навіть якщо пристрій має стабільний стан (online/idle/offline)

Це призводить до:
- у UI відображається "Online: -"
- відсутня історія сесії
- некоректна аналітика

## Проблема

Timestamps ініціалізуються тільки в окремих сценаріях (наприклад для manual/ARP devices),
але не для всіх aggregated devices.

Зокрема:
- devices з source=["dhcp","arp","bridge_host"] не отримують timestamps
- перший стабільний стан не фіксується

## Мета

Гарантувати, що кожен device з визначеним станом має timestamps,
навіть якщо це перший snapshot або вони були відсутні.

## Вимоги

### 1. Ініціалізація для online / idle

Якщо:

```
fused_state in ["online", "idle"]
AND online_since is null
```

то:

```
online_since = now
```

Додатково:

```
if state_changed_at is null:
    state_changed_at = now
```

---

### 2. Ініціалізація для offline

Якщо:

```
fused_state == "offline"
AND offline_since is null
```

то:

```
offline_since = now
```

Додатково:

```
if state_changed_at is null:
    state_changed_at = now
```

---

### 3. НЕ перезаписувати існуючі значення

```
if online_since != null:
    DO NOT override

if offline_since != null:
    DO NOT override

if state_changed_at != null:
    DO NOT override
```

---

### 4. Незалежність від source

Логіка має працювати для всіх device незалежно від:

- created_by
- source (dhcp, arp, bridge_host, manual)
- entity_type (client, router, etc.)

---

### 5. Виключення (опціонально)

Для:

```
entity_type == "interface"
```

можна:
- не ініціалізувати timestamps
або
- залишити як є (за рішенням)

---

### 6. Debug logging

```
MAC=XX
state=online
online_since=null → initialized
state_changed_at=null → initialized
```

---

## Очікуваний результат

- У всіх активних пристроїв є online_since
- У всіх offline пристроїв є offline_since
- В UI більше немає "Online: -"
- Стабільна історія сесій
