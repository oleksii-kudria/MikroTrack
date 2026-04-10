# TASK-078 - Extended Diff Tracking

## Опис (UA)

Необхідно розширити механізм diff у системі MikroTrack для фіксації ВСІХ змін стану пристрою та його атрибутів між snapshot'ами.

Поточна реалізація фокусується лише на базових змінах стану (online/idle/offline), але для повноцінного відображення історії у web UI потрібно відслідковувати всі суттєві зміни.

Ця задача вводить розширений diff (extended diff), який дозволить будувати повну історію життєвого циклу пристрою.

---

## Description (EN)

Extend the diff mechanism in MikroTrack to track ALL changes in device state and attributes between snapshots.

The current implementation focuses mainly on state transitions, but to provide a complete network visibility in the UI, the system must detect and store all meaningful changes.

This task introduces extended diff tracking to support full device lifecycle history.

---

## Що потрібно зробити (UA)

Розширити diff логіку таким чином, щоб фіксувалися зміни у наступних полях:

- state (online / idle / offline)
- IP address
- hostname
- DHCP lease type (dynamic ↔ static)
- DHCP presence (lease exists / removed)
- DHCP flags
- ARP flags
- comment (DHCP / ARP)
- source (яке джерело дало дані: DHCP / ARP / bridge host)

Для кожної зміни:
- визначити старе значення (previous)
- визначити нове значення (current)
- згенерувати подію

---

## What needs to be done (EN)

Extend diff logic to detect changes in:

- state (online / idle / offline)
- IP address
- hostname
- DHCP lease type (dynamic ↔ static)
- DHCP presence (exists / removed)
- DHCP flags
- ARP flags
- comment (DHCP / ARP)
- source (data origin: DHCP / ARP / bridge host)

For each change:
- detect previous value
- detect current value
- generate an event

---

## Формат події (Event Format)

Event MUST contain:

- device_mac
- field_name
- previous_value
- current_value
- timestamp

Example:

```
event_type=FIELD_CHANGE
device_mac=AA:BB:CC:DD:EE:FF
field=ip
previous=192.168.1.10
current=192.168.1.25
timestamp=2026-04-10T10:15:30
```

---

## Правила (Rules)

1. Подія генерується ТІЛЬКИ якщо значення змінилось
2. Якщо значення однакові - подія НЕ створюється
3. None → value або value → None також вважається зміною
4. Snapshot без змін НЕ повинен генерувати події
5. Timer (online_since, idle_since, offline_since) НЕ вважається зміною для event

---

## Logs (EN)

All logs MUST be in English.

Examples:

```
INFO diff: detected change field=ip mac=AA:BB:CC:DD:EE:FF old=192.168.1.10 new=192.168.1.25
INFO diff: detected change field=state mac=AA:BB:CC:DD:EE:FF old=idle new=online
WARNING diff: missing field hostname for mac=AA:BB:CC:DD:EE:FF
```

---

## Журнали подій (UA)

У логах повинно бути:

- чітке поле яке змінилось
- MAC пристрою
- старе та нове значення
- без зайвого шуму

---

## Вплив на документацію (Documentation impact)

### UA

Необхідно оновити документацію:
- опис diff логіки
- опис формату подій
- приклади подій

### EN

Update documentation:
- diff logic description
- event format
- event examples

---

## Врахування змін (Important)

При реалізації задачі ОБОВ'ЯЗКОВО врахувати:

- оновлення логів (англійською)
- оновлення документації (UA + EN)
- сумісність з існуючими snapshot'ами
- відсутність breaking changes

---

## Результат (Expected Result)

- система фіксує всі зміни стану пристрою
- кожна зміна генерує окрему подію
- UI може відобразити повну історію пристрою
- diff стає deterministic та прозорим

---

## Додатково (Optional)

- групування подій в рамках одного snapshot
- додавання event_type (STATE_CHANGE / FIELD_CHANGE)
