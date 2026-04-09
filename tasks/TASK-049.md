# TASK-049 - Optimize device table refresh with partial row updates

## Overview / Опис

### UA
Необхідно оптимізувати оновлення таблиці пристроїв у розділі Devices.

Зараз при `Refresh now` та `Auto refresh` виконується повний ререндер таблиці. Це створює зайві DOM-операції, може викликати візуальне "миготіння" інтерфейсу та ускладнює відстеження реальних змін у списку пристроїв.

Потрібно змінити механізм оновлення так, щоб без повного перерендеру сторінки оновлювалися лише ті рядки таблиці, де дані реально змінилися.

### EN
Optimize device table refresh behavior in the Devices section.

Currently, `Refresh now` and `Auto refresh` trigger a full table re-render. This causes unnecessary DOM operations, may create visible UI flicker, and makes it harder to visually track real changes in the device list.

Update the refresh mechanism so that only rows with actual data changes are updated, without a full page or full table redraw.

---

## Goal / Мета

### UA
Зробити оновлення таблиці плавнішим, швидшим і зручнішим для оператора:
- без повного redraw таблиці
- без зайвого мерехтіння
- з оновленням лише змінених рядків
- із збереженням поточних фільтрів і single-column sorting

### EN
Make table refresh smoother, faster, and more operator-friendly:
- no full table redraw
- no unnecessary flicker
- update only changed rows
- preserve current filters and single-column sorting

---

## Core idea / Основна ідея

### UA
Ключ ідентифікації рядка - `MAC`.

Під час refresh потрібно:
1. отримати новий список device items
2. зіставити нові записи з поточними DOM-рядками по `MAC`
3. оновити лише змінені рядки
4. додати нові рядки для нових `MAC`
5. видалити рядки для `MAC`, яких більше немає
6. після цього застосувати поточні фільтри, сортування і правильний порядок рядків

### EN
The row identity key is `MAC`.

During refresh:
1. fetch the new device items list
2. match new records with existing DOM rows by `MAC`
3. update only changed rows
4. add new rows for new `MAC`s
5. remove rows for `MAC`s that no longer exist
6. then apply current filters, sorting, and correct row order

---

## Requirements / Вимоги

### 1. No full table redraw

#### UA
- Не використовувати повний `innerHTML` rebuild всієї таблиці при кожному refresh.
- Не створювати заново всі рядки, якщо більшість записів не змінилася.
- Оновлювати тільки конкретні DOM-елементи, де змінилися дані.

#### EN
- Do not rebuild the full table with `innerHTML` on every refresh.
- Do not recreate all rows if most records did not change.
- Update only the specific DOM elements whose data changed.

---

### 2. Row reconciliation by MAC

#### UA
Потрібно реалізувати reconcile/update логіку:
- `MAC` є primary key для відповідності device record ↔ table row
- якщо `MAC` вже існує:
  - порівняти старі та нові значення
  - оновити тільки ті cells, де дані змінилися
- якщо `MAC` новий:
  - створити новий рядок
- якщо `MAC` зник:
  - видалити рядок

#### EN
Implement reconciliation/update logic:
- `MAC` is the primary key for device record ↔ table row mapping
- if `MAC` already exists:
  - compare old and new values
  - update only changed cells
- if `MAC` is new:
  - create a new row
- if `MAC` disappeared:
  - remove the row

---

### 3. Preserve filtering and sorting

#### UA
Після partial update потрібно:
- застосувати активні фільтри
- застосувати поточне single-column sorting
- забезпечити правильний порядок рядків

Важливо:
- якщо внаслідок зміни status/assignment рядок більше не проходить фільтр, його треба приховати або прибрати з видимого набору
- якщо запис почав проходити фільтр після refresh, його треба показати
- якщо змінилось поле, за яким виконується active sorting, рядок повинен змінити свою позицію

#### EN
After partial update:
- apply active filters
- apply current single-column sorting
- preserve correct row order

Important:
- if a row no longer matches filters after refresh, it must be hidden or excluded from the visible set
- if a row starts matching filters after refresh, it must appear
- if the active sort field changed, the row position must be updated

---

### 4. Reuse DOM rows where possible

#### UA
- Якщо рядок вже існує, потрібно перевикористати наявний DOM node.
- Допускається перестановка existing rows у новому порядку.
- Не потрібно повністю знищувати та створювати заново всі рядки.

#### EN
- If a row already exists, reuse the existing DOM node.
- Reordering existing rows is allowed.
- Do not destroy and recreate all rows unnecessarily.

---

### 5. Stats and UI blocks refresh

#### UA
Після refresh також потрібно оновлювати:
- device statistics block
- active filters block, якщо його стан залежить від кількості/наявності результатів
- empty state, якщо після фільтрації немає записів

При цьому не потрібно оновлювати всю сторінку цілком.

#### EN
After refresh, also update:
- device statistics block
- active filters block, if its state depends on visible results
- empty state, if there are no rows after filtering

Do this without redrawing the full page.

---

## Suggested implementation approach / Рекомендований підхід

### UA
Рекомендується перейти від повного `renderDevices(items)` до схеми на кшталт:

- `reconcileDevices(items)`
- `updateDeviceRow(row, oldItem, newItem)`
- `createDeviceRow(item)`
- `removeMissingRows(items)`
- `applyFiltersAndSorting()`

Тобто:
- окремо підтримувати cache/Map рядків за `MAC`
- окремо підтримувати current items state
- окремо виконувати reorder visible rows після refresh

### EN
Recommended approach instead of full `renderDevices(items)`:

- `reconcileDevices(items)`
- `updateDeviceRow(row, oldItem, newItem)`
- `createDeviceRow(item)`
- `removeMissingRows(items)`
- `applyFiltersAndSorting()`

That means:
- maintain a row cache/Map by `MAC`
- maintain current items state separately
- reorder visible rows after refresh

---

## Processing flow / Потік обробки

### UA
Після натискання `Refresh now` або спрацювання `Auto refresh`:

1. fetch new device items
2. compare with current in-memory device state
3. update existing rows where needed
4. add new rows
5. remove missing rows
6. apply filters
7. apply single-column sorting
8. reorder visible rows
9. update stats / empty state

### EN
After `Refresh now` or `Auto refresh`:

1. fetch new device items
2. compare with current in-memory device state
3. update existing rows where needed
4. add new rows
5. remove missing rows
6. apply filters
7. apply single-column sorting
8. reorder visible rows
9. update stats / empty state

---

## Scope / Межі задачі

### UA
У цій задачі НЕ потрібно:
- змінювати backend
- змінювати API
- впроваджувати WebSocket
- впроваджувати SSE
- змінювати логіку визначення статусів
- змінювати логіку assignment
- змінювати логіку фільтрів або single-column sorting, окрім інтеграції їх у partial refresh pipeline

### EN
This task must NOT:
- modify backend
- modify API
- add WebSocket
- add SSE
- modify status determination logic
- modify assignment logic
- modify filtering or single-column sorting logic, except integrating them into the partial refresh pipeline

---

## Logging / Логування

### UA
Якщо додаються технічні логи, вони повинні бути англійською мовою.

### EN
If technical logs are added, they must be in English.

Recommended examples:
- `Device refresh: fetched 19 items`
- `Device refresh: updated row for MAC 50:FF:20:7D:0E:0E`
- `Device refresh: added row for MAC 9A:A1:33:D0:AB:FA`
- `Device refresh: removed row for MAC 20:37:A5:87:2A:13`
- `Device refresh: reordered visible rows`
- `Device refresh: stats updated`

---

## User-facing behavior / Поведінка для користувача

### UA
Після refresh користувач повинен бачити:
- мінімальні візуальні зміни
- без повного "миготіння" таблиці
- лише ті рядки змінюються, де справді є зміни в даних
- поточний tab, фільтри і сортування зберігаються

### EN
After refresh, the user should see:
- minimal visual disruption
- no full table flicker
- only rows with real data changes update
- current tab, filters, and sorting remain preserved

---

## Acceptance criteria / Критерії приймання

### UA
- Повний redraw таблиці при кожному refresh більше не використовується.
- Рядки зіставляються по `MAC`.
- Якщо дані рядка не змінилися, його DOM node не перевідтворюється без потреби.
- Нові `MAC` додаються як нові rows.
- Відсутні `MAC` видаляються.
- Змінені rows оновлюються частково, без повного rebuilding всієї таблиці.
- Поточні фільтри та single-column sorting зберігаються після refresh.
- Порядок рядків після refresh правильний.
- Stats block оновлюється після refresh.
- Empty state працює коректно.
- Refresh now та Auto refresh обидва використовують partial update pipeline.

### EN
- Full table redraw is no longer used on every refresh.
- Rows are matched by `MAC`.
- If a row did not change, its DOM node is not unnecessarily recreated.
- New `MAC`s are added as new rows.
- Missing `MAC`s are removed.
- Changed rows are updated partially, without rebuilding the full table.
- Current filters and single-column sorting are preserved after refresh.
- Row order remains correct after refresh.
- Stats block updates after refresh.
- Empty state works correctly.
- Both Refresh now and Auto refresh use the partial update pipeline.

---

## Notes / Примітки

### UA
- Основна мета - зробити refresh візуально спокійним і технічно акуратним.
- Це підготовчий крок до ще більш "живого" UI, але без переходу на WebSocket/SSE.
- Не ускладнювати рішення надмірно - потрібен практичний, підтримуваний підхід.

### EN
- The main goal is to make refresh visually calm and technically clean.
- This is a preparation step toward a more live UI, but without moving to WebSocket/SSE yet.
- Do not overcomplicate the solution - use a practical, maintainable approach.
