# TASK-071 - Redesign top toolbar into a single-row compact layout with segmented mode control

## Контекст

Поточний toolbar у верхній частині сторінки містить:

- Active filters (Status, Assignment)
- кнопку Clear
- кнопки Sort / Refresh
- Mode (dropdown)
- Auto toggle
- Devices summary

Проблеми:

- елементи розташовані не в один ряд
- Mode використовує dropdown (зайвий клік)
- UI виглядає як форма, а не як dashboard toolbar
- слабка ієрархія (важко швидко сканувати)

---

## Мета задачі

Переробити toolbar у **компактний однорядковий layout**, який:

- читається зліва направо
- не містить dropdown для Mode
- має чітке логічне групування
- оптимізований для швидкої роботи (1-клік UX)

---

## Цільовий layout

Toolbar повинен бути в **один рядок** та умовно поділений на 3 блоки:

[ Filters ]   |   [ Actions ]   |   [ View controls + Summary ]

---

## Що потрібно зробити

### 1. Переробити Mode → Segmented Control

Було:
Mode [ End devices ▼ ]

Має бути:
[ End devices | All ]

або коротко:
[ End | All ]

Вимоги:
- активний варіант підсвічений
- один клік для перемикання
- без dropdown
- значення за замовчуванням: End devices

---

### 2. Active filters → Pills

Було:
Status: offline
Assignment: RANDOM

Має бути:
[ 🔴 Offline ] [ 🎯 RANDOM ]

Вимоги:
- кожен фільтр — окремий pill/badge
- кольори відповідають статусам
- компактний вигляд

---

### 3. Clear → lightweight button

Було:
[ Clear X ]

Має бути:
Clear ✕

Вимоги:
- виглядає як link/button, а не primary action
- не перевантажує toolbar
- hover підсвічення

---

### 4. Sort / Refresh → уніфікувати

Поточний стан:
[⇅] [⟳]

Вимоги:
- однаковий стиль кнопок
- tooltip:
  - ⇅ → "Sort"
  - ⟳ → "Refresh"
- компактні (icon-only)

---

### 5. Devices summary → компактний вигляд

Було:
Devices: 41 | 🟢 12 | 🟡 0 | 🟣 2 | 🔴 27

Має бути:
41 | 🟢12 🟡0 🟣2 🔴27

---

### 6. Auto → toggle switch

Було:
Auto ☑

Має бути:
Auto [ ON ]

або toggle switch

---

### 7. Вирівнювання в один рядок

Всі елементи повинні:

- знаходитися в одному горизонтальному рядку
- мати consistent spacing
- не переноситися (окрім дуже вузьких екранів)

---

## Логічне групування

Ліва частина:
[ 🔴 Offline ] [ 🎯 RANDOM ]   Clear ✕

Центр:
⇅  ⟳

Права частина:
[ End | All ]   Auto [ON]   41 | 🟢12 🟡0 🟣2 🔴27

---

## Критерії приймання

- toolbar в один рядок
- dropdown Mode прибраний
- використовується segmented control
- filters у вигляді pills
- UI виглядає компактно та читабельно
- немає регресії функціоналу

---

## Очікуваний результат

[ 🔴 Offline ] [ 🎯 RANDOM ]  Clear ✕   |   ⇅ ⟳   |   [ End | All ]  Auto [ON]   41 | 🟢12 🟡0 🟣2 🔴27
