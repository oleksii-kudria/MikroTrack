# TASK-057 - Add BRIDGE badge for devices detected only via bridge host

## Overview / Опис

### UA
Необхідно додати нову мітку `BRIDGE` у колонку Assignment для пристроїв, які визначені виключно через bridge (L2), без наявності записів у ARP та DHCP.

Це дозволить оператору чітко розуміти джерело появи пристрою в системі.

### EN
Add a new `BRIDGE` badge in the Assignment column for devices detected only via bridge (L2), without ARP or DHCP presence.

This helps operators understand the source of device detection.

---

## Conditions / Умови

### UA

Мітка `BRIDGE` додається ТІЛЬКИ якщо:

- `has_arp_entry = false`
- `has_dhcp_lease = false`
- `bridge_host_present = true`

### EN

`BRIDGE` badge is added ONLY if:

- `has_arp_entry = false`
- `has_dhcp_lease = false`
- `bridge_host_present = true`

---

## Exclusions / Виключення

### UA

НЕ додавати `BRIDGE`, якщо:

- є ARP запис
- є DHCP lease
- або обидва

### EN

Do NOT add `BRIDGE` if:

- ARP entry exists
- DHCP lease exists
- or both

---

## Backend changes / Зміни backend

### UA

У логіці формування badges:

```python
if not has_arp_entry and not has_dhcp_lease and bridge_host_present:
    badges.append("BRIDGE")
```

### EN

In badge generation logic:

```python
if not has_arp_entry and not has_dhcp_lease and bridge_host_present:
    badges.append("BRIDGE")
```

---

## Frontend changes / Зміни frontend

### UA

- Відобразити `BRIDGE` як звичайний badge
- Додати tooltip:

`BRIDGE - Device detected only via bridge (no ARP, no DHCP)`

### EN

- Render `BRIDGE` as standard badge
- Add tooltip:

`BRIDGE - Device detected only via bridge (no ARP, no DHCP)`

---

## Filtering / Фільтрація

### UA

- Клік по `BRIDGE` повинен фільтрувати список
- Працює разом з іншими фільтрами

### EN

- Clicking `BRIDGE` filters devices
- Works with other filters

---

## Acceptance criteria / Критерії приймання

### UA

- `BRIDGE` з’являється тільки при виконанні умов
- не з’являється в інших випадках
- коректно відображається в UI
- працює фільтрація
- не ламає існуючі badges

### EN

- `BRIDGE` appears only under correct conditions
- not shown otherwise
- correctly rendered in UI
- filtering works
- does not break existing badges

---

## Notes / Примітки

### UA

- `BRIDGE` означає L2 presence без IP-рівня
- важливо для діагностики “невидимих” пристроїв

### EN

- `BRIDGE` represents L2-only presence
- useful for detecting devices without IP visibility
