# TASK-044 - Fix multi-column sort UX so additional columns are added without Shift

## Overview / Опис

### UA
Поточна реалізація сортування по декількох стовпцях у таблиці пристроїв працює лише через `Shift + click`. Для користувача це неочевидно та виглядає як помилка, тому що при звичайному кліку по іншому стовпцю попередній ключ сортування скидається.

Необхідно змінити UX сортування так, щоб додавання другого, третього та наступних полів працювало без `Shift`.

### EN
The current multi-column sorting implementation in the devices table only works with `Shift + click`. This is not obvious to the user and looks like a bug because a normal click on another column resets the previous sort key.

Update the sorting UX so that adding second, third, and further sort keys works without `Shift`.

---

## Goal / Мета

### UA
Зробити поведінку multi-column sorting інтуїтивною:
- перший клік додає перший ключ сортування
- клік по іншому стовпцю додає наступний ключ сортування
- повторний клік по вже активному стовпцю змінює напрямок
- третій клік по тому самому активному стовпцю видаляє його з ланцюжка сортування
- очищення всього сортування виконується окремою кнопкою `Clear sort`

### EN
Make multi-column sorting intuitive:
- first click adds the first sort key
- clicking another column adds the next sort key
- re-clicking an already active column toggles direction
- third click on the same active column removes it from the sort chain
- clearing the whole sort chain is done via the dedicated `Clear sort` button

---

## Current problem / Поточна проблема

### UA
Зараз логіка кліку по заголовках працює так:
- звичайний клік без `Shift` скидає поточний chain sort і залишає тільки один стовпець
- додавання наступних полів можливе лише через `Shift + click`

Через це користувач бачить поведінку як single-column sort, хоча в коді вже є часткова підтримка multi-sort.

### EN
Current header click logic works like this:
- normal click without `Shift` resets the current sort chain and keeps only one column
- adding more sort keys is only possible with `Shift + click`

As a result, the user experiences it as single-column sorting even though multi-sort is partially implemented in the code.

---

## Requirements / Вимоги

### Sorting UX

#### UA
- Прибрати залежність від `Shift + click` для додавання нових полів сортування.
- Звичайний клік по новому sortable стовпцю має додавати його в кінець `activeDeviceSorts`.
- Якщо стовпець уже присутній у `activeDeviceSorts`, повторні кліки повинні циклічно змінювати стан:
  - `asc`
  - `desc`
  - remove from sort chain
- `Clear sort` повинен повністю очищати `activeDeviceSorts`.
- Поведінка має бути однаковою для всіх sortable стовпців.

#### EN
- Remove dependency on `Shift + click` for adding new sort keys.
- A normal click on a new sortable column must append it to the end of `activeDeviceSorts`.
- If the column is already present in `activeDeviceSorts`, repeated clicks must cycle through:
  - `asc`
  - `desc`
  - remove from sort chain
- `Clear sort` must fully reset `activeDeviceSorts`.
- Behavior must be consistent for all sortable columns.

---

## Expected behavior / Очікувана поведінка

### UA
Приклад 1:
- click `Status` -> `Status ASC`
- click `State time` -> `Status ASC`, `State time ASC`
- click `Hostname` -> `Status ASC`, `State time ASC`, `Hostname ASC`

Приклад 2:
- click `Status` -> `ASC`
- click `Status` -> `DESC`
- click `Status` -> removed from chain

Приклад 3:
- click `Status`
- click `State time`
- click `Status`
Результат:
- `Status DESC`
- `State time ASC`

Порядок пріоритету повинен зберігатися:
- перший доданий стовпець = `[1]`
- другий доданий стовпець = `[2]`
- третій доданий стовпець = `[3]`

### EN
Example 1:
- click `Status` -> `Status ASC`
- click `State time` -> `Status ASC`, `State time ASC`
- click `Hostname` -> `Status ASC`, `State time ASC`, `Hostname ASC`

Example 2:
- click `Status` -> `ASC`
- click `Status` -> `DESC`
- click `Status` -> removed from chain

Example 3:
- click `Status`
- click `State time`
- click `Status`
Result:
- `Status DESC`
- `State time ASC`

Sort priority order must be preserved:
- first added column = `[1]`
- second added column = `[2]`
- third added column = `[3]`

---

## UI indicators / UI індикатори

### UA
- Залишити індикатори сортування у заголовках.
- Для активних полів показувати:
  - `↑[1]`
  - `↓[2]`
- Для неактивних полів показувати:
  - `↕`
- Індикатори повинні оновлюватися після кожного кліку та після `Clear sort`.

### EN
- Keep sorting indicators in the headers.
- For active fields display:
  - `↑[1]`
  - `↓[2]`
- For inactive fields display:
  - `↕`
- Indicators must update after every click and after `Clear sort`.

---

## Scope / Межі задачі

### UA
У цій задачі змінюється лише UX логіка multi-column sorting.
Не треба:
- змінювати backend
- змінювати comparator для статусів, IP або state time, якщо він уже працює коректно
- змінювати формат API
- змінювати layout таблиці

### EN
This task only updates the UX logic of multi-column sorting.
Do not:
- modify backend logic
- modify comparators for status, IP, or state time if they already work correctly
- modify API format
- modify table layout

---

## Logging / Логування

### UA
Логи в коді, якщо вони додаються, мають бути англійською мовою.

### EN
Any logs added in code must be in English.

Recommended examples:
- `Multi-sort: added key "status" with direction "asc"`
- `Multi-sort: toggled key "status" to "desc"`
- `Multi-sort: removed key "status"`
- `Multi-sort: cleared all sort keys`

---

## User-facing text / Текст для користувача

### UA
Усі повідомлення в UI повинні бути англійською мовою.

### EN
All user-facing UI messages must remain in English.

Examples:
- `Clear sort`
- `Loading devices...`
- `No devices found`

---

## Acceptance criteria / Критерії приймання

### UA
- Клік по іншому стовпцю більше не скидає попередній sort key.
- Multi-sort працює без `Shift`.
- Порядок сортування `[1]`, `[2]`, `[3]` відображається коректно.
- Повторні кліки по активному стовпцю циклічно змінюють `asc -> desc -> remove`.
- `Clear sort` очищає весь chain sort.
- Існуюче сортування по `Status`, `State time`, `IP`, `Hostname`, `MAC`, `Comments`, `Assignment` продовжує працювати.
- Не зламана існуюча логіка backend та session/state таймерів.

### EN
- Clicking another column no longer removes the previous sort key.
- Multi-sort works without `Shift`.
- Sort order `[1]`, `[2]`, `[3]` is rendered correctly.
- Repeated clicks on an active column cycle through `asc -> desc -> remove`.
- `Clear sort` clears the whole sort chain.
- Existing sorting for `Status`, `State time`, `IP`, `Hostname`, `MAC`, `Comments`, and `Assignment` continues to work.
- Existing backend and session/state timer logic remains intact.

---

## Notes / Примітки

### UA
- Простота та передбачуваність UX важливіші за підтримку прихованих shortcut-комбінацій.
- Якщо підтримка `Shift + click` уже є, її можна або повністю прибрати, або залишити як сумісну додаткову поведінку, але основний сценарій повинен працювати без `Shift`.
- Не ламати існуючу стабільність сортування.

### EN
- Simplicity and predictability of UX are more important than hidden shortcut-based behavior.
- If `Shift + click` support already exists, it may either be removed or kept as an optional compatible behavior, but the primary workflow must work without `Shift`.
- Do not break stable sorting behavior.
