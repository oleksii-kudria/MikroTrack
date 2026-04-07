# TASK-023 - ARP Status Mapping & Permanent Handling

## Опис (UA)

Необхідно реалізувати коректне відображення ARP статусів у derived стан пристрою.

Поточна проблема:
- статус "permanent" некоректно інтерпретується
- змішується поняття стану (online/offline) та типу запису

---

## Мета (UA)

1. Впровадити чітке мапування ARP статусів
2. Виділити "permanent" як окремий стан
3. Забезпечити коректне відображення в UI та подіях

---

## ARP Status Mapping (EN)

```python
if arp.status == "reachable":
    state = "online"

elif arp.status in ["stale", "delay", "probe"]:
    state = "idle"

elif arp.status in ["failed", "incomplete"]:
    state = "offline"

elif arp.status == "permanent":
    state = "permanent"

else:
    state = "unknown"
```

---

## Інтерпретація (UA)

- online → пристрій активний
- idle → пристрій неактивний, але запис валідний
- offline → пристрій недоступний
- permanent → статичний ARP запис (тип, а не стан)

ВАЖЛИВО:
permanent НЕ означає online або offline

---

## Data Model Changes (EN)

Add field:

```python
device.arp_state
device.arp_status
```

---

## UI Requirements (UA)

Для permanent:

- статус: окремий (наприклад "PERM")
- колір: gray або окремий стиль

Приклад:

PERM + idle/unknown не використовується — тільки PERM

---

## Events (EN)

System MUST generate:

- arp_status_changed
- arp_state_changed

Example:

```json
{
  "type": "arp_status_changed",
  "mac": "A8:3B:76:F4:27:27",
  "old_status": "reachable",
  "new_status": "permanent",
  "timestamp": "..."
}
```

---

## Вплив на журнали подій (UA)

- додати підтримку status=permanent
- не інтерпретувати permanent як online/offline

---

## Вплив на документацію (UA)

Оновити:
- ARP логіку
- Device state logic
- UI опис статусів

---

## Acceptance Criteria (UA)

- permanent обробляється окремо
- відсутні false online
- UI коректно відображає PERM
- події генеруються коректно

---

## Результат (UA)

Система чітко розділяє:
- стан пристрою
- тип ARP запису

та не вводить в оману користувача
