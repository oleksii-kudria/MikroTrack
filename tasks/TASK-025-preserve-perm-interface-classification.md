# TASK-025 - Preserve PERM badge and classify interface MACs

## Опис (UA)

Поточна реалізація має дві проблеми:

1. Badge `PERM` зникає при переході пристрою в стан online
2. У список пристроїв потрапляють MAC адреси інтерфейсів MikroTik без коректної ідентифікації

---

## Мета (UA)

1. Зберігати `PERM` як badge незалежно від стану пристрою
2. Додати класифікацію об'єктів:
   - client
   - interface
3. Коректно відображати MAC інтерфейсів з підписом

---

## Definitions (EN)

### Device State
- online
- idle
- offline
- unknown

### Badges
- PERM
- INTERFACE
- LINK-LOCAL

### Entity Type
- client
- interface

---

## 1. Preserve PERM (UA)

`PERM` НЕ є state.

НЕПРАВИЛЬНО:

```python
state = "PERM"
```

ПРАВИЛЬНО:

```python
device.state = "online"
device.badges.append("PERM")
```

---

## 2. Rules for PERM (UA)

- якщо ARP status = permanent → додати badge `PERM`
- badge НЕ зникає при зміні state
- badge існує незалежно від online/offline

---

## 3. Entity Classification (UA)

Додати поле:

```python
device.entity_type = "client" | "interface"
```

---

## 4. Interface Detection (UA)

MAC вважається `interface`, якщо:

- MAC збігається з MAC локального інтерфейсу MikroTik
- MAC знайдений у списку:
  - /interface print
  - /interface bridge print
  - /interface vlan print
  - /interface wireless print

---

## 5. Interface Metadata (UA)

```python
device.entity_type = "interface"
device.interface_name = "ether3"
device.badges.append("INTERFACE")
```

---

## 6. Client Detection (UA)

MAC вважається `client`, якщо:

- є DHCP lease
- є ARP запис
- MAC не належить локальному інтерфейсу

---

## 7. UI Requirements (UA)

### Client

```text
● online   PERM
```

---

### Interface

```text
● unknown   INTERFACE   ether3
```

або

```text
INTERFACE: ether3
```

---

## 8. Important Rules (UA)

- badges НЕ впливають на state
- state визначається окремо
- interface MAC НЕ видаляються зі списку
- interface MAC повинні бути чітко позначені

---

## 9. Events (EN)

System MUST generate:

- entity_type_detected
- interface_detected

Example:

```json
{
  "type": "interface_detected",
  "mac": "AA:BB:CC:DD:EE:FF",
  "interface": "ether3",
  "timestamp": "..."
}
```

---

## 10. Вплив на журнали подій (UA)

НЕОБХІДНО:

- додати entity_type у всі події
- додати interface_name (якщо є)

---

## 11. Вплив на документацію (UA)

Оновити:

- Device model
- UI logic
- ARP/DHCP interpretation

---

## 12. Acceptance Criteria (UA)

- PERM badge не зникає при online
- interface MAC позначаються як INTERFACE
- interface MAC мають ім'я інтерфейсу
- відсутні false client записи
- UI відображає state + badges

---

## Результат (UA)

Система:

- зберігає PERM як атрибут
- відрізняє клієнтів від інтерфейсів
- коректно відображає структуру мережі
