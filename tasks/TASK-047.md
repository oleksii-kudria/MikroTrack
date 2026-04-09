# TASK-047 - UI for clickable filters and clear action

## Overview / Опис

### UA
Необхідно реалізувати UI для вже підготовленої логіки фільтрації пристроїв:
- клік по мітках у колонці `Assignment`
- клік по значеннях у колонці `Status`
- явний елемент скидання активних фільтрів

Ця задача стосується тільки frontend UI та взаємодії з уже існуючими змінними і функціями фільтрації.

### EN
Implement the UI for the prepared device filtering logic:
- click on badges in the `Assignment` column
- click on values in the `Status` column
- explicit clear action for active filters

This task is limited to frontend UI and interaction with the already existing filtering state and functions.

---

## Goal / Мета

### UA
Зробити фільтрацію швидкою та зручною для оператора:
- один клік по badge/status активує фільтр
- активні фільтри видно одразу
- скидання фільтрів очевидне і доступне
- без dropdown та без переходів між екранами

### EN
Make filtering fast and operator-friendly:
- one click on a badge/status activates a filter
- active filters are immediately visible
- clearing filters is obvious and accessible
- no dropdowns and no extra screens

---

## UI behavior / Поведінка UI

### 1. Clickable Assignment badges

#### UA
- Усі мітки в колонці `Assignment` повинні бути клікабельними.
- Клік по мітці повинен встановлювати `assignmentFilter`.
- Після кліку таблиця має бути перемальована з урахуванням фільтрації.
- Має працювати для:
  - `RANDOM`
  - `PERM`
  - `STATIC`
  - `DYNAMIC`
  - `COMPLETE`
  - `INTERFACE`

#### EN
- All badges in the `Assignment` column must be clickable.
- Clicking a badge must set `assignmentFilter`.
- After click, the table must re-render with filtered results.
- Must work for:
  - `RANDOM`
  - `PERM`
  - `STATIC`
  - `DYNAMIC`
  - `COMPLETE`
  - `INTERFACE`

---

### 2. Clickable Status values

#### UA
- Значення в колонці `Status` повинні бути клікабельними.
- Клік по статусу повинен встановлювати `statusFilter`.
- Після кліку таблиця має бути перемальована.
- Має працювати для:
  - `online`
  - `idle`
  - `unknown`
  - `offline`

#### EN
- Values in the `Status` column must be clickable.
- Clicking a status must set `statusFilter`.
- After click, the table must re-render.
- Must work for:
  - `online`
  - `idle`
  - `unknown`
  - `offline`

---

### 3. Combined filters

#### UA
- UI повинен підтримувати одночасно два активні фільтри:
  - `statusFilter`
  - `assignmentFilter`
- Якщо активні обидва, таблиця повинна показувати результат з AND логікою.

Приклад:
- click `online`
- click `PERM`

Результат:
- показати тільки `online + PERM`

#### EN
- UI must support two active filters at the same time:
  - `statusFilter`
  - `assignmentFilter`
- If both are active, table must show the AND-filtered result.

Example:
- click `online`
- click `PERM`

Result:
- show only `online + PERM`

---

## Active filters UI / Відображення активних фільтрів

### UA
Над таблицею потрібно показувати компактний блок активних фільтрів, наприклад:

- `Active filters`
- `Status: online`
- `Assignment: PERM`

Якщо активних фільтрів немає, блок можна:
- приховувати
- або показувати в неактивному стані

### EN
Show a compact active filters block above the table, for example:

- `Active filters`
- `Status: online`
- `Assignment: PERM`

If there are no active filters, the block may:
- be hidden
- or shown in an inactive state

---

## Clear filters action / Скидання фільтрів

### UA
- Додати явну кнопку або іконку `Clear filters`.
- Вона повинна скидати:
  - `statusFilter`
  - `assignmentFilter`
- Після натискання:
  - показується повний список пристроїв
  - active filters UI очищується
  - таблиця ререндериться без фільтрів

### EN
- Add an explicit `Clear filters` button or icon.
- It must reset:
  - `statusFilter`
  - `assignmentFilter`
- After click:
  - full device list is shown
  - active filters UI is cleared
  - table is re-rendered without filters

---

## Visual requirements / Візуальні вимоги

### UA
Елементи фільтрації повинні виглядати інтерактивно:
- `cursor: pointer`
- hover state
- активний фільтр має бути візуально виділений

Можливі підходи:
- інший border
- інший background
- stronger text color
- active chip style

### EN
Filterable elements must look interactive:
- `cursor: pointer`
- hover state
- active filter must be visually highlighted

Possible approaches:
- different border
- different background
- stronger text color
- active chip style

---

## Re-render behavior / Поведінка ререндеру

### UA
Після кожної дії:
- click on Assignment badge
- click on Status value
- click on Clear filters

має виконуватися стандартний пайплайн:
- full items list
- apply filters
- apply single-column sorting
- render filtered result

### EN
After every action:
- click on Assignment badge
- click on Status value
- click on Clear filters

the standard pipeline must run:
- full items list
- apply filters
- apply single-column sorting
- render filtered result

---

## Toggle behavior / Поведінка повторного кліку

### UA
Допускається один із двох варіантів:
1. клік по вже активному badge/status скидає відповідний фільтр
2. повторний клік нічого не змінює

Але в будь-якому випадку:
- має бути окремий `Clear filters`
- поведінка повинна бути однаковою і передбачуваною

### EN
One of these behaviors is acceptable:
1. clicking an already active badge/status clears that specific filter
2. repeated click does nothing

In all cases:
- there must be a separate `Clear filters`
- behavior must be consistent and predictable

---

## Scope / Межі задачі

### UA
У цій задачі НЕ потрібно:
- змінювати backend
- змінювати API
- змінювати sorting logic з TASK-045
- змінювати filtering core logic з TASK-046
- додавати dropdown filters
- додавати multi-sort

### EN
This task must NOT:
- modify backend
- modify API
- modify sorting logic from TASK-045
- modify core filtering logic from TASK-046
- add dropdown filters
- add multi-sort

---

## Logging / Логування

### UA
Якщо додаються логи, вони повинні бути англійською мовою.

### EN
If logs are added, they must be in English.

Recommended examples:
- `UI filter click: assignment=PERM`
- `UI filter click: status=online`
- `UI action: clear filters`

---

## User-facing text / Текст для користувача

### UA
Усі тексти в UI повинні бути англійською мовою.

### EN
All user-facing UI text must remain in English.

Recommended examples:
- `Active filters`
- `Clear filters`
- `No devices found`

---

## Acceptance criteria / Критерії приймання

### UA
- Усі badge у колонці `Assignment` клікабельні.
- Усі значення у колонці `Status` клікабельні.
- Клік по `Assignment` badge застосовує `assignmentFilter`.
- Клік по `Status` застосовує `statusFilter`.
- Одночасно можуть бути активні два фільтри.
- Працює AND логіка.
- Є явний `Clear filters`.
- Активні фільтри відображаються над таблицею.
- Після кліку таблиця оновлюється без перезавантаження сторінки.
- Single-column sorting продовжує працювати поверх відфільтрованого списку.
- Backend та current state/session logic не змінені.

### EN
- All badges in the `Assignment` column are clickable.
- All values in the `Status` column are clickable.
- Clicking an `Assignment` badge applies `assignmentFilter`.
- Clicking a `Status` value applies `statusFilter`.
- Two filters can be active at the same time.
- AND logic works.
- There is an explicit `Clear filters`.
- Active filters are shown above the table.
- The table updates after click without page reload.
- Single-column sorting continues to work on the filtered list.
- Backend and current state/session logic remain unchanged.

---

## Notes / Примітки

### UA
- Основна мета - зробити керування списком швидким і зрозумілим.
- Потрібно зберегти мінімалістичний вигляд таблиці.
- Не перевантажувати UI зайвими елементами.

### EN
- The main goal is to make list control fast and understandable.
- Keep the table visually minimal.
- Do not overload the UI with extra elements.
