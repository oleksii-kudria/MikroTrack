# TASK-082 - Fix single-column sorting behavior in UI

## Опис

Після останніх змін у UI сортування пристроїв працює некоректно.

Потрібно виправити логіку сортування так, щоб вона працювала просто, передбачувано і лише по **одному вибраному стовпцю** у двох варіантах:

- ascending
- descending

Без multi-column sorting.
Без прихованих додаткових режимів сортування для користувача.

---

## Що потрібно зробити

### 1. Реалізувати сортування лише по одному стовпцю

У кожен момент часу може бути активне лише одне сортування:

- або по конкретному стовпцю ascending
- або по конкретному стовпцю descending
- або без явного вибору користувача - default sorting

Потрібно прибрати/не використовувати логіку, де одночасно комбінуються кілька активних user-selected sort fields.

---

### 2. Default sorting, якщо користувач не обрав сортування

Якщо explicit sorting не вибрано, використовувати default sorting:

1. `status` у такому порядку:
   - `online`
   - `idle`
   - `offline`
   - `unknown`

2. Усередині кожної групи:
   - для `online` - сортування по `online_since`
   - для `idle` - сортування по `idle_since`
   - для `offline` - сортування по `offline_since`
   - для `unknown` - тільки алфавітне сортування, бо дати відсутні

---

### 3. Правила сортування всередині статусних груп

#### online
Сортувати по `online_since`

#### idle
Сортувати по `idle_since`

#### offline
Сортувати по `offline_since`

#### unknown
Сортувати тільки алфавітно

Для `unknown` не треба намагатися будувати сортування по даті.

---

### 4. Явне user-selected sorting

Якщо користувач натиснув сортування по конкретному стовпцю, потрібно застосовувати тільки його:

- ascending
- descending

Без додаткового автоматичного другого user sort.

Допускається лише стабільний fallback для однакових значень, якщо він потрібен для консистентності рендеру, але він не повинен виглядати як друге сортування з точки зору користувача.

---

### 5. Алфавітне та зворотне сортування

Для sortable columns потрібно забезпечити два режими:

- alphabetical / ascending
- reverse / descending

Це означає:
- для тексту - A → Z і Z → A
- для чисел / duration / counts - від меншого до більшого і навпаки
- для дат - від старішого до новішого або навпаки, відповідно до UI semantics

---

### 6. Узгодити default sorting для статусів з часовими полями

Default sorting не повинен просто групувати по статусу. Усередині груп також потрібен стабільний другий порядок:

- `online` -> `online_since`
- `idle` -> `idle_since`
- `offline` -> `offline_since`
- `unknown` -> alphabetic

Це обов'язково.

---

## Вимоги до реалізації

### 1. Логіка має бути простою і deterministic

Потрібно уникати:
- неочевидних chained sort rules
- змішування explicit sorting і default sorting
- різної поведінки залежно від випадкових null/undefined значень

### 2. Null / empty values

Потрібно чітко обробляти пусті значення:
- якщо поле для сортування порожнє, запис має впорядковуватись стабільно
- для `unknown` не використовувати date sort fallback

### 3. Sorting state in UI

UI повинен чітко зберігати:
- немає explicit sorting
- ascending для конкретного стовпця
- descending для конкретного стовпця

Без додаткових прихованих станів.

---

## Очікувана поведінка

### Випадок 1 - користувач нічого не обрав
Тоді порядок має бути:

1. всі `online`
   - впорядковані по `online_since`
2. всі `idle`
   - впорядковані по `idle_since`
3. всі `offline`
   - впорядковані по `offline_since`
4. всі `unknown`
   - впорядковані алфавітно

---

### Випадок 2 - користувач обрав сортування по стовпцю
Тоді використовується лише це сортування:
- ascending
- descending

Default status sorting у цей момент не повинен нав'язуватись як основне user-visible правило.

---

## Логи та журнали подій

Усі логи та user-facing повідомлення - англійською.

Якщо в проекті вже є debug logs для UI/data sorting, оновити їх за потреби так, щоб вони відповідали новій логіці.

Приклади debug log, якщо такі використовуються:

```text
Sorting applied: column=status direction=asc mode=explicit
Sorting applied: column=default_status mode=default
Sorting fallback for unknown status: alphabetical
```

---

## Документація

Оновити документацію українською та англійською.

### UA
Описати:
- що підтримується лише single-column sorting
- як працює default sorting
- як сортуються `online`, `idle`, `offline`, `unknown`

### EN
Document:
- single-column sorting only
- default sorting behavior
- per-status fallback ordering
- alphabetical handling for `unknown`

---

## Врахування змін у логах та документації

У кожній задачі необхідно враховувати:
- зміни в логах/журналах подій, якщо це потрібно
- зміни в документації українською та англійською

Для цієї задачі це потрібно врахувати.

---

## Критерії приймання

Задача вважається виконаною, якщо:

1. UI підтримує лише single-column sorting
2. для обраного стовпця працюють два режими:
   - ascending
   - descending
3. якщо сортування не обрано, використовується default sorting:
   - `online`
   - `idle`
   - `offline`
   - `unknown`
4. усередині `online`, `idle`, `offline` сортування виконується по відповідних timestamp fields
5. для `unknown` використовується лише alphabetic sorting
6. поведінка стабільна для empty/null values
7. документація оновлена українською та англійською

---

## Очікуваний результат

- сортування в UI знову працює передбачувано
- користувач бачить лише один активний sort column
- default порядок відповідає реальній цінності для мережевого фахівця
- `unknown` більше не поводиться некоректно через відсутність дат

---

## Додатково

Буде плюсом:
- додати unit tests / UI tests для:
  - default sorting
  - explicit ascending sorting
  - explicit descending sorting
  - `unknown` alphabetical sorting
  - empty timestamp values
