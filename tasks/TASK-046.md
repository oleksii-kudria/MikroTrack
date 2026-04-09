# TASK-046 - Device filtering logic (Status + Assignment)

## Overview / Опис

### UA
Необхідно реалізувати логіку фільтрації пристроїв у таблиці:
- фільтр по статусу (`Status`)
- фільтр по типу призначення (`Assignment`)

Ця задача включає лише логіку (state + functions), без UI взаємодії. UI (клік по бейджах, кнопка скидання) буде реалізований у наступній задачі.

### EN
Implement device filtering logic for the table:
- filter by `Status`
- filter by `Assignment`

This task includes logic only (state + functions), without UI interactions. UI (badge clicks, clear button) will be implemented in the next task.

---

## Goal / Мета

### UA
Створити просту, передбачувану і тестовану систему фільтрації:
- незалежні фільтри
- комбінування через AND
- застосування перед сортуванням

### EN
Create a simple, predictable, and testable filtering system:
- independent filters
- combined using AND logic
- applied before sorting

---

## Filter model / Модель фільтрації

### UA
Потрібно підтримати два фільтри:

- statusFilter: string | null
- assignmentFilter: string | null

Можливі значення:

Status:
- online
- idle
- unknown
- offline

Assignment:
- RANDOM
- PERM
- STATIC
- DYNAMIC
- COMPLETE
- INTERFACE

### EN
Support two filters:

- statusFilter: string | null
- assignmentFilter: string | null

Possible values:

Status:
- online
- idle
- unknown
- offline

Assignment:
- RANDOM
- PERM
- STATIC
- DYNAMIC
- COMPLETE
- INTERFACE

---

## Expected behavior / Очікувана поведінка

### UA

Case 1: без фільтрів  
→ показуються всі пристрої

Case 2: тільки statusFilter  
→ показати всі online

Case 3: тільки assignmentFilter  
→ показати всі PERM

Case 4: обидва фільтри  
→ показати тільки online + PERM

### EN

Case 1: no filters  
→ show all devices

Case 2: only statusFilter  
→ show all online

Case 3: only assignmentFilter  
→ show all PERM

Case 4: both filters  
→ show only online + PERM

---

## Implementation requirements / Вимоги до реалізації

### Core variables

let statusFilter = null;
let assignmentFilter = null;

---

### Filter function

function applyFilters(items) {
  return items.filter(item => {
    const status = normalizeStatus(item);
    const assignment = resolveAssignment(item);

    if (statusFilter && status !== statusFilter) return false;
    if (assignmentFilter && assignment !== assignmentFilter) return false;

    return true;
  });
}

---

## Processing order / Порядок обробки

items → applyFilters() → applySorting() → render()

---

## Edge cases / Крайні випадки

### UA
- без фільтрів → всі записи
- немає результатів → пустий список
- записи без assignment не проходять assignmentFilter

### EN
- no filters → all items
- no results → empty list
- no assignment → excluded when filtering by assignment

---

## Scope / Межі задачі

### UA
НЕ потрібно:
- UI
- клікабельні бейджі
- кнопки
- backend зміни
- sorting зміни

### EN
Do NOT:
- add UI
- add clickable badges
- modify backend
- modify sorting

---

## Acceptance criteria / Критерії приймання

### UA
- працюють обидва фільтри
- AND логіка
- виконується перед sorting
- не залежить від UI

### EN
- both filters work
- AND logic works
- applied before sorting
- independent from UI
