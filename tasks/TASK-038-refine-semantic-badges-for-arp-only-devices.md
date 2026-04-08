# TASK-038 - Refine semantic badges for ARP-only devices

## Контекст

Після впровадження semantic badges:
- PERM
- STATIC
- DYNAMIC

виявлено, що логіка добре працює для DHCP-based пристроїв, але недостатньо точно відображає ARP-only записи.

Поточна проблема:
- якщо DHCP запис відсутній, але є ARP
- пристрою може ставитись `DYNAMIC`, хоча це створює зайвий шум
- для ARP-only записів потрібна окрема, більш точна логіка

## Мета

Уточнити правила відображення semantic badges для записів, у яких:
- DHCP відсутній
- є тільки ARP дані

## Вимоги

### 1. DHCP-based логіка залишається без змін

Для пристроїв з DHCP:

```python
if arp_is_static:
    badge = "PERM"
elif dhcp_is_static:
    badge = "STATIC"
elif dhcp_is_dynamic:
    badge = "DYNAMIC"
```

---

### 2. ARP-only логіка

Якщо DHCP запис відсутній:

#### a) ARP flags = DC

Показувати:

```text
COMPLETE
```

---

#### b) ARP flags = D only

Не показувати жодної semantic badge.

Тобто:

```text
(no badge)
```

---

#### c) ARP static without DHCP

Якщо ARP запис статичний і DHCP відсутній:

```text
PERM
```

---

### 3. Заборонено

Не використовувати для ARP-only записів автоматично:

- DYNAMIC
- STATIC

якщо DHCP відсутній

---

### 4. Acceptance Criteria

- ARP-only + DC → badge `COMPLETE`
- ARP-only + D → без badge
- ARP-only + static → badge `PERM`
- DHCP-based логіка не змінюється
- UI не перевантажений зайвими мітками

---

## Очікуваний результат

Semantic badges стають точнішими:
- для DHCP-based клієнтів лишаються `PERM / STATIC / DYNAMIC`
- для ARP-only пристроїв:
  - `COMPLETE`
  - `PERM`
  - або без badge

UI залишається чистим, але краще передає сенс запису.
