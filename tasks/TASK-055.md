# TASK-055 - Move unknown devices below offline and disable timers for unknown state

## Overview / Опис

### UA
Необхідно покращити поведінку записів зі статусом `unknown` у таблиці Devices:
- перемістити їх у самий низ списку (після `offline`)
- вимкнути відображення таймера для цього статусу

Це потрібно для зменшення шуму та правильного сприйняття стану мережі оператором.

### EN
Improve handling of `unknown` state devices in the Devices table:
- move them to the bottom (after `offline`)
- disable timer display for this state

This reduces noise and improves operator clarity.

---

## 1. Status ordering

### UA
Новий порядок статусів:

Default (ascending):
- online
- idle
- offline
- unknown

`unknown` завжди має бути в самому низу таблиці.

### EN
New status order:

Default (ascending):
- online
- idle
- offline
- unknown

`unknown` must always be rendered at the bottom.

---

## 2. Sorting behavior

### UA
- При сортуванні за статусом:
  - `unknown` завжди після `offline`
- При інших сортуваннях:
  - `unknown` не повинен "випливати" вище `offline`

### EN
- When sorting by status:
  - `unknown` always comes after `offline`
- For other sorting modes:
  - `unknown` should not appear above `offline`

---

## 3. Disable timer for unknown

### UA
Для записів зі статусом `unknown`:

- у колонці `State time` завжди показувати:
  `-`
- не запускати таймер
- не використовувати `state_changed_at` для обчислення часу

### EN
For `unknown` devices:

- in `State time` column always show:
  `-`
- do not run timer
- do not calculate time from `state_changed_at`

---

## 4. Tooltip behavior

### UA
- для `unknown` не показувати tooltip з часом
- можна додати коротке пояснення (опційно):
  `State is unknown`

### EN
- do not show time tooltip for `unknown`
- optional short message:
  `State is unknown`

---

## Scope / Межі задачі

### UA
НЕ потрібно:
- змінювати backend
- змінювати API
- змінювати state logic

Потрібно:
- змінити тільки frontend rendering та sorting behavior

### EN
Do NOT:
- modify backend
- modify API
- modify state logic

Must:
- update frontend rendering and sorting only

---

## Acceptance criteria / Критерії приймання

### UA
- `unknown` записи відображаються після `offline`
- `unknown` не перемішуються з іншими статусами
- у колонці `State time` для `unknown` показується `-`
- таймер не запускається для `unknown`
- UI не вводить в оману щодо часу стану
- інші статуси працюють без змін

### EN
- `unknown` devices are rendered after `offline`
- `unknown` does not mix with other states
- `State time` shows `-` for `unknown`
- no timer updates for `unknown`
- UI is not misleading
- other states work unchanged

---

## Notes / Примітки

### UA
- `unknown` не є повноцінним станом сесії
- таймер для нього не має сенсу
- пріоритет — читабельність і операторський UX

### EN
- `unknown` is not a full session state
- timer has no real meaning
- focus on clarity and operator UX
