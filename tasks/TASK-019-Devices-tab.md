# TASK-019 - Add Devices Tab to Web UI

## Мета

Додати нову вкладку "Devices" у Web UI, не змінюючи існуючу вкладку "Timeline".

Timeline залишається для перегляду історії подій.
Devices використовується для відображення поточного стану мережі.

---

## Що потрібно зробити

### 1. Додати вкладки у UI

Додати перемикач:

[ Timeline ] [ Devices ]

- Timeline - існуюча реалізація без змін
- Devices - нова вкладка

---

### 2. Реалізувати Devices view

Один рядок = один пристрій (по MAC)

---

### 3. Дані для Devices

Backend endpoint:

GET /api/devices

Повертає агрегований стан пристроїв

---

### 4. Поля для відображення

- MAC
- IP
- Hostname
- Comments (DHCP + ARP)
- Flags / state
- Last change (elapsed time)

---

### 5. Логіка коментарів

- тільки DHCP → "dhcp: text"
- тільки ARP → "arp: text"
- однакові → "dhcp arp: text"
- різні → окремі рядки

---

### 6. Flags / State

Показувати:

- source
- dynamic/static
- dhcp status
- arp flags
- active/inactive

---

### 7. Active / Inactive сортування

Порядок:

1. Active devices
2. Inactive devices

---

### 8. Elapsed time

Показувати:

- seconds / minutes / hours since last change

---

### 9. Auto refresh

Додати toggle:

Auto refresh ON/OFF

- ON → оновлення кожні N секунд
- OFF → ручне оновлення

---

## Важливі вимоги

- Timeline не змінювати
- Devices не використовує raw events
- тільки агрегований API
- не використовувати БД

---

## Definition of Done

- є вкладка Devices
- працює GET /api/devices
- відображається список пристроїв
- active зверху
- elapsed time працює
- є auto refresh
