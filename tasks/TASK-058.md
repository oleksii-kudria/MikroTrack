# TASK-058 - Перемикач режимів відображення (All vs End devices)

## Опис / Description

### UA
Необхідно додати перемикач (toggle) у toolbar, який дозволяє перемикатися між двома режимами відображення списку пристроїв:

- All — відображення всіх записів
- End devices only — відображення тільки кінцевих пристроїв

Мета — приховати технічні записи (bridge, interface, incomplete тощо) за замовчуванням та показувати оператору лише релевантні пристрої.

### EN
Add a toolbar toggle to switch between two display modes:

- All — show all records
- End devices only — show only end-user devices

Goal: hide technical/noisy records by default and present a clean operator-focused view.

---

## Поведінка / Behavior

### UA

### Режим All
- Показуються всі записи без обмежень

### Режим End devices only (за замовчуванням)
Приховувати записи, якщо виконується хоча б одна умова:

- Assignment = `BRIDGE`
- Assignment = `COMPLETE`
- Assignment = `INTERFACE`
- Status = `unknown`

### EN

### All mode
- Show all records

### End devices only (default)
Hide records if ANY condition matches:

- Assignment = `BRIDGE`
- Assignment = `COMPLETE`
- Assignment = `INTERFACE`
- Status = `unknown`

---

## UI / UX

### UA

- Розмістити toggle поруч із кнопками:
  - clear sorting
  - refresh
  - auto refresh
- Варіанти відображення:
  - `All / End devices`
  - або компактний toggle

- Додати tooltip:
  - `Show only end devices (hide BRIDGE, COMPLETE, INTERFACE, unknown)`

- За замовчуванням:
  - активний режим `End devices only`

### EN

- Place toggle near:
  - clear sorting
  - refresh
  - auto refresh

- Suggested labels:
  - `All / End devices`

- Tooltip:
  - `Show only end devices (hide BRIDGE, COMPLETE, INTERFACE, unknown)`

- Default:
  - `End devices only`

---

## Логіка обробки / Processing logic

### UA

Порядок обробки:

1. Отримати повний список пристроїв
2. Застосувати display mode filter
3. Застосувати активні фільтри (status / assignment)
4. Застосувати сортування
5. Відобразити

ВАЖЛИВО:
- статистика (Devices: X | 🟢 ...) НЕ повинна змінюватися
- вона рахується від повного набору даних

### EN

Processing order:

1. Load full dataset
2. Apply display mode filter
3. Apply active filters (status / assignment)
4. Apply sorting
5. Render

IMPORTANT:
- global stats must NOT change
- stats are based on full dataset

---

## Backend

### UA
Зміни НЕ потрібні.

### EN
No backend changes required.

---

## Frontend

### UA

- Додати state:
  - `displayMode = "all" | "end_devices"`
- Додати функцію фільтрації:
```js
function applyDisplayMode(items) {
  if (displayMode === "all") return items;

  return items.filter(item => {
    const status = normalizeStatus(item);
    const assignment = resolveAssignment(item);

    if (status === "unknown") return false;
    if (assignment === "BRIDGE") return false;
    if (assignment === "COMPLETE") return false;
    if (assignment === "INTERFACE") return false;

    return true;
  });
}
```

- Інтегрувати у pipeline перед applyDeviceFilters()

### EN

- Add state:
  - `displayMode = "all" | "end_devices"`

- Add filtering function (same as above)

---

## Логи / Logs

### UA

Зміни в журнали подій НЕ потрібні.

### EN

No changes required in logs.

---

## Документація / Documentation

### UA

Оновити документацію:
- описати новий режим відображення
- пояснити різницю між All та End devices only
- додати приклади

### EN

Update documentation:
- describe new display mode
- explain difference between All and End devices only
- add examples

---

## Acceptance criteria / Критерії приймання

### UA

- Є перемикач режимів у toolbar
- За замовчуванням активний режим `End devices only`
- У цьому режимі приховуються:
  - BRIDGE
  - COMPLETE
  - INTERFACE
  - unknown
- У режимі All видно всі записи
- Фільтри та сортування працюють коректно
- Статистика НЕ змінюється при перемиканні

### EN

- Toggle exists in toolbar
- Default mode is `End devices only`
- Hidden in this mode:
  - BRIDGE
  - COMPLETE
  - INTERFACE
  - unknown
- All mode shows everything
- Filters and sorting work correctly
- Stats are not affected by mode
