# TASK-054 - Compact devices toolbar and move global device stats to top-right

## Overview / Опис

### UA
Необхідно покращити layout верхньої частини сторінки Devices:
- прибрати зайвий заголовок
- винести глобальну статистику пристроїв у правий верхній кут
- зробити toolbar компактним (в один ряд)
- замінити текстові кнопки на іконки там, де це доречно

### EN
Improve the Devices page header layout:
- remove redundant header
- move global device stats to top-right
- make toolbar compact (single row)
- replace verbose buttons with icons where appropriate

---

## 1. Remove "Devices ℹ️"

### UA
- Повністю прибрати блок "Devices ℹ️"
- Назва "Devices" вже присутня у вкладках — дублювання не потрібне

### EN
- Remove "Devices ℹ️" block entirely
- "Devices" already exists in tabs — duplication not needed

---

## 2. Move global device stats to top-right

### UA
Перенести блок:
Devices: N | 🟢 online | 🟡 idle | ⚪ unknown | 🔴 offline

В правий верхній кут сторінки.

Важливо:
- значення НЕ змінюються при застосуванні фільтрів
- показують повний стан мережі (всі devices)
- не залежать від visible rows

### EN
Move block:
Devices: N | 🟢 online | 🟡 idle | ⚪ unknown | 🔴 offline

To the top-right corner.

Important:
- values must NOT change with filters
- represent full dataset
- not based on visible rows

---

## 3. Single-row toolbar

### UA
Об’єднати в один ряд:

- Active filters
- Clear filters
- Clear sort
- Refresh
- Auto refresh

Toolbar має бути компактним і не розбиватись на кілька рядків без необхідності.

### EN
Combine into single row:

- Active filters
- Clear filters
- Clear sort
- Refresh
- Auto refresh

Toolbar must stay compact and avoid multi-line layout.

---

## 4. Replace buttons with icons

### UA

Замінити текстові кнопки:

- Clear sort → icon + tooltip
- Refresh now → icon + tooltip
- Auto refresh → compact toggle

Tooltip:
- повинні бути англійською

### EN

Replace buttons:

- Clear sort → icon + tooltip
- Refresh now → icon + tooltip
- Auto refresh → compact toggle

Tooltips must be in English.

---

## 5. Active filters behavior

### UA
- Показувати тільки якщо є активні фільтри
- Вигляд:
  [Status: online] [Assignment: PERM] [Clear ✕]

- Якщо фільтрів немає:
  - або ховати блок
  - або залишити максимально компактним

### EN
- Show only when filters exist
- Format:
  [Status: online] [Assignment: PERM] [Clear ✕]

- If no filters:
  - hide block
  - or keep minimal layout

---

## Scope / Межі задачі

### UA
НЕ потрібно:
- змінювати backend
- змінювати логіку фільтрів
- змінювати логіку сортування

Потрібно:
- змінити тільки UI layout і presentation

### EN
Do NOT:
- modify backend
- modify filtering logic
- modify sorting logic

Must:
- update UI layout only

---

## Acceptance criteria / Критерії приймання

### UA
- "Devices ℹ️" прибрано
- stats винесені у правий верхній кут
- stats не змінюються при фільтрації
- toolbar в один ряд
- кнопки замінені на іконки
- tooltips англійською
- Active filters відображається тільки при наявності

### EN
- "Devices ℹ️" removed
- stats moved to top-right
- stats not affected by filters
- toolbar is single-row
- buttons replaced with icons
- tooltips in English
- Active filters shown only when present

---

## Notes / Примітки

### UA
- основна мета — зменшити візуальний шум і зробити UI операторським
- focus на компактність та швидке сприйняття

### EN
- goal is to reduce visual noise and improve operator UX
- focus on compactness and readability
