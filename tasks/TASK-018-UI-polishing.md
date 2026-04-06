# TASK-018 - UI Polishing (Timeline)

## Мета

Покращити Web UI (timeline) для зручного використання мережевим інженером.

---

## Що потрібно зробити

### 1. Відображення MAC

- Вивести MAC у окрему колонку
- Не показувати "-"
- Брати значення з event.mac

---

### 2. Human-readable опис подій

Замість raw значень:

old_value → new_value

Показувати:

- DHCP lease changed from dynamic to static
- IP changed from X to Y
- Source changed from dhcp to arp

---

### 3. Raw JSON → collapse

- Details по замовчуванню приховані
- Кнопка "expand"
- JSON доступний для дебагу

---

### 4. Grouping подій

Групувати події по:
- MAC
- timestamp (±1 сек)

В рамках групи показувати список змін

---

### 5. Фільтри

Додати:

- filter by MAC
- filter by event_type

---

### 6. Сортування

- newest first (default)
- oldest first (optional)

---

### 7. Empty state

Якщо подій немає:

- показати "No events yet"

---

## Важливі вимоги

- UI не читає файли напряму
- тільки через API
- не ламати існуючу логіку

---

## Definition of Done

- MAC відображається
- події readable
- є expand/collapse
- є grouping
- є базові фільтри
