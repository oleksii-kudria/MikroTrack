# TASK-043 - Add multi-column sorting and shorten state time column label

## Overview / Опис

### UA
Необхідно додати підтримку сортування по декількох стовпцях (multi-column sorting) у таблиці пристроїв, а також скоротити назву стовпця `Session / state time`.

### EN
Implement multi-column sorting for the devices table and shorten the `Session / state time` column label.

---

## Requirements / Вимоги

### Multi-column sorting

#### UA
- Підтримати сортування по 2 і більше полях.
- Перший клік по заголовку - звичайне сортування.
- `Shift + click` - додає поле як наступний ключ сортування.
- Повторний клік - змінює напрямок (`ASC` / `DESC`).
- Додати можливість скидання сортування (clear sort).
- Сортування має бути стабільним (stable sort).

#### EN
- Support sorting by multiple columns.
- First click applies single-column sorting.
- `Shift + click` adds another sort key.
- Re-click toggles direction (`ASC` / `DESC`).
- Provide a way to clear sorting.
- Sorting must be stable.

---

## Status sorting / Сортування статусів

### UA
Кастомний порядок:

ASC:
- online
- idle
- unknown
- offline

DESC:
- offline
- unknown
- idle
- online

### EN
Custom order:

ASC:
- online
- idle
- unknown
- offline

DESC:
- offline
- unknown
- idle
- online

---

## State time sorting / Сортування часу стану

### UA
- ASC - найменший таймер зверху
- DESC - найбільший таймер зверху
- null або '-' завжди внизу

### EN
- ASC - smallest timer first
- DESC - largest timer first
- null or '-' values must always stay at the bottom

---

## Column rename / Перейменування стовпця

### UA
- `Session / state time` → `State time`

### EN
- Rename `Session / state time` to `State time`

---

## UI behavior / Поведінка UI

### UA
- Показувати порядок сортування:
  - Status [1]
  - State time [2]
- Не змінювати backend логіку

### EN
- Show sort priority:
  - Status [1]
  - State time [2]
- Do not modify backend logic

---

## Examples / Приклади

### UA
- Status ASC + State time ASC
- Status ASC + Hostname ASC
- Assignment ASC + IP ASC + MAC ASC

### EN
- Status ASC + State time ASC
- Status ASC + Hostname ASC
- Assignment ASC + IP ASC + MAC ASC

---

## Notes / Примітки

### UA
- Не змінювати існуючу логіку станів
- Сортування лише на frontend

### EN
- Do not break existing state logic
- Sorting must be frontend-only
