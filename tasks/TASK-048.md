# TASK-048 - Improve devices page layout and statistics display

## Overview / Опис

### UA
Необхідно покращити зовнішній вигляд сторінки Devices:
- прибрати зайвий текст і винести його в tooltip
- замінити технічні метрики (Loaded / Total) на корисну статистику
- змінити порядок вкладок (Devices / Timeline)
- покращити блок активних фільтрів
- зробити toolbar компактнішим

### EN
Improve the Devices page layout:
- remove unnecessary text and move it to a tooltip
- replace technical metrics (Loaded / Total) with useful statistics
- reorder tabs (Devices / Timeline)
- improve active filters block
- make toolbar more compact

---

## 1. Page description → Tooltip

### UA
- Прибрати текст:
  "Current aggregated network state grouped by MAC."
- Додати іконку ℹ️ поруч із заголовком
- При наведенні показувати цей текст у tooltip

### EN
- Remove text:
  "Current aggregated network state grouped by MAC."
- Add ℹ️ icon near header
- Show this text in tooltip on hover

---

## 2. Replace Loaded / Total with real stats

### UA
Замість:
- Loaded: X
- Total: X

Показувати:

Devices: N | 🟢 online | 🟡 idle | ⚪ unknown | 🔴 offline

Приклад:
Devices: 19 | 🟢 8 | 🟡 5 | ⚪ 0 | 🔴 6

### EN
Replace:
- Loaded: X
- Total: X

With:

Devices: N | 🟢 online | 🟡 idle | ⚪ unknown | 🔴 offline

Example:
Devices: 19 | 🟢 8 | 🟡 5 | ⚪ 0 | 🔴 6

---

## 3. Tabs order

### UA
Змінити порядок вкладок:

Було:
Timeline | Devices

Стало:
Devices | Timeline

- Devices повинна бути активною за замовчуванням

### EN
Change tabs order:

Before:
Timeline | Devices

After:
Devices | Timeline

- Devices must be default active tab

---

## 4. Active filters block

### UA
Покращити блок:

- Показувати тільки якщо є активні фільтри
- Формат:

Active filters:
[Status: online] [Assignment: PERM]   [Clear ✕]

- Якщо немає фільтрів → не показувати блок

### EN
Improve block:

- Show only if filters exist
- Format:

Active filters:
[Status: online] [Assignment: PERM]   [Clear ✕]

- Hide if no filters

---

## 5. Toolbar compact layout

### UA
Зробити toolbar компактнішим:

Було:
- розкидані елементи

Стало:

[Devices: stats]

[Active filters + Clear]

[Refresh] [Auto refresh]

### EN
Make toolbar compact:

Before:
- scattered elements

After:

[Devices stats]

[Active filters + Clear]

[Refresh] [Auto refresh]

---

## Scope / Межі задачі

### UA
НЕ потрібно:
- змінювати backend
- змінювати логіку фільтрів
- змінювати логіку сортування

### EN
Do NOT:
- modify backend
- modify filtering logic
- modify sorting logic

---

## Acceptance criteria / Критерії

### UA
- опис перенесений у tooltip
- Loaded / Total прибрані
- показується статистика по статусам
- Devices вкладка перша і активна
- Active filters показується тільки при наявності
- toolbar став компактнішим

### EN
- description moved to tooltip
- Loaded / Total removed
- status stats displayed
- Devices tab first and active
- Active filters shown only when needed
- toolbar more compact
