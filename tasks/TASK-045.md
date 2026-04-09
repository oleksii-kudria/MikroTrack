# TASK-045 - Replace multi-column sorting with single-column sorting

## Overview / Опис

### UA
Необхідно прибрати multi-column sorting у таблиці пристроїв та залишити лише single-column sorting.

Поточна реалізація multi-sort ускладнює поведінку UI та створює плутанину для користувача. У цій задачі потрібно спростити логіку сортування так, щоб у будь-який момент активним був лише один sort key.

### EN
Remove multi-column sorting from the devices table and keep only single-column sorting.

The current multi-sort implementation makes the UI behavior more complex and confusing for the user. This task simplifies sorting so that only one sort key can be active at any time.

---

## Goal / Мета

### UA
Зробити сортування простим, передбачуваним і стабільним:
- один активний стовпець сортування
- зрозумілі індикатори
- стандартний цикл `ASC -> DESC -> no sort`
- клік по іншому стовпцю замінює попереднє сортування

### EN
Make sorting simple, predictable, and stable:
- one active sort column
- clear indicators
- standard `ASC -> DESC -> no sort` cycle
- clicking another column replaces the previous sorting

---

## Requirements / Вимоги

### Single-column sorting behavior

#### UA
- Повністю прибрати multi-sort logic.
- У таблиці може бути активним лише один sort key одночасно.
- Клік по sortable заголовку повинен циклічно змінювати стан:
  - перший клік -> `ASC`
  - другий клік -> `DESC`
  - третій клік -> `no active sorting`
- Клік по іншому sortable стовпцю повністю скидає попередній sort key і активує новий стовпець у стані `ASC`.
- Не використовувати `Shift + click` для сортування.
- Якщо старий multi-sort код ще існує, його потрібно прибрати або повністю відключити.

#### EN
- Fully remove multi-sort logic.
- Only one sort key may be active at a time.
- Clicking a sortable header must cycle through:
  - first click -> `ASC`
  - second click -> `DESC`
  - third click -> `no active sorting`
- Clicking another sortable column must fully reset the previous sort key and activate the new column as `ASC`.
- Do not use `Shift + click` for sorting.
- If old multi-sort code still exists, it must be removed or fully disabled.

---

## Sort indicators / Індикатори сортування

### UA
- Залишити лише прості індикатори:
  - `↕` - неактивне сортування
  - `↑` - `ASC`
  - `↓` - `DESC`
- Прибрати індикатори пріоритету multi-sort:
  - `[1]`
  - `[2]`
  - `[3]`
- Індикатори повинні коректно оновлюватися після кожного кліку.

### EN
- Keep only simple indicators:
  - `↕` - inactive sorting
  - `↑` - `ASC`
  - `↓` - `DESC`
- Remove multi-sort priority indicators:
  - `[1]`
  - `[2]`
  - `[3]`
- Indicators must update correctly after every click.

---

## Supported columns / Підтримувані стовпці

### UA
Single-column sorting має залишитися доступним для всіх поточних sortable стовпців:
- `MAC`
- `IP`
- `Hostname`
- `Comments`
- `Assignment`
- `Status`
- `State time`

### EN
Single-column sorting must remain available for all current sortable columns:
- `MAC`
- `IP`
- `Hostname`
- `Comments`
- `Assignment`
- `Status`
- `State time`

---

## Sorting rules / Правила сортування

### Status

#### UA
Для `Status` зберегти кастомний порядок:

ASC:
- `online`
- `idle`
- `unknown`
- `offline`

DESC:
- `offline`
- `unknown`
- `idle`
- `online`

#### EN
Keep custom order for `Status`:

ASC:
- `online`
- `idle`
- `unknown`
- `offline`

DESC:
- `offline`
- `unknown`
- `idle`
- `online`

### State time

#### UA
Для `State time`:
- `ASC` - менший timer зверху
- `DESC` - більший timer зверху
- пусті значення або `-` повинні залишатися внизу

#### EN
For `State time`:
- `ASC` - smaller timer first
- `DESC` - larger timer first
- empty values or `-` must stay at the bottom

### Other columns

#### UA
Для текстових і числових полів зберегти поточну логіку comparator'ів, якщо вона працює коректно.

#### EN
For text and numeric columns, keep the current comparator logic if it already works correctly.

---

## Scope / Межі задачі

### UA
У цій задачі змінюється тільки логіка single-column sorting у frontend.

Не потрібно:
- додавати нові фільтри
- робити клікабельні badge-фільтри
- змінювати backend
- змінювати API
- змінювати визначення статусів
- змінювати класифікацію assignment
- додавати multi-sort назад

### EN
This task only updates single-column sorting logic in the frontend.

Do not:
- add new filters
- add clickable badge filters
- modify backend
- modify API
- modify status determination logic
- modify assignment classification logic
- reintroduce multi-sort

---

## Logging / Логування

### UA
Якщо додаються логи, вони повинні бути англійською мовою.

### EN
If any logs are added, they must be in English.

Recommended examples:
- `Sorting applied: key=status direction=asc`
- `Sorting applied: key=session direction=desc`
- `Sorting cleared`

---

## User-facing text / Текст для користувача

### UA
Усі тексти в UI повинні залишатися англійською мовою.

### EN
All user-facing UI texts must remain in English.

Examples:
- `Clear sort`
- `Loading devices...`
- `No devices found`

---

## Acceptance criteria / Критерії приймання

### UA
- Multi-column sorting повністю прибрано.
- У будь-який момент активне лише одне сортування.
- `Shift + click` більше не використовується для сортування.
- Індикатори `[1]`, `[2]`, `[3]` більше не відображаються.
- Клік по sortable стовпцю працює за циклом `ASC -> DESC -> no sort`.
- Клік по іншому sortable стовпцю замінює попереднє сортування.
- Single-column sorting працює для всіх поточних sortable колонок.
- Існуючі правила сортування для `Status` і `State time` не зламані.
- Backend та current state/session logic залишаються без змін.

### EN
- Multi-column sorting is fully removed.
- Only one active sorting rule exists at any time.
- `Shift + click` is no longer used for sorting.
- `[1]`, `[2]`, `[3]` indicators are no longer displayed.
- Clicking a sortable column follows the `ASC -> DESC -> no sort` cycle.
- Clicking another sortable column replaces the previous sorting.
- Single-column sorting works for all current sortable columns.
- Existing sorting rules for `Status` and `State time` remain intact.
- Backend and current state/session logic remain unchanged.

---

## Notes / Примітки

### UA
- Це підготовчий крок перед окремими задачами на фільтрацію.
- Основна мета - зробити поведінку таблиці простою та стабільною.
- Не ускладнювати рішення прихованими shortcut-комбінаціями.

### EN
- This is a preparation step before separate filtering tasks.
- The main goal is to make table behavior simple and stable.
- Do not complicate the solution with hidden shortcut-based interactions.
