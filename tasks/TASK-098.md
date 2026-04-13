# TASK-098 - MAC Vendor DB Loader (startup + validation)

## Опис задачі

Необхідно реалізувати модуль завантаження та використання локальної бази MAC-вендорів:

app/data/mac_vendors.json

Цей модуль використовується під час runtime та працює тільки з локальним файлом.

---

## Що необхідно реалізувати

### 1. Модуль

app/services/mac_vendor_db.py

Функціонал:
- завантаження JSON
- валідація структури
- доступ до lookup функції

---

### 2. Завантаження при старті

- перевірка існування файлу
- парсинг JSON
- кешування в пам'яті

Логування (EN):
INFO mac_vendor_db: Loaded MAC vendors database
ERROR mac_vendor_db: mac_vendors.json not found
ERROR mac_vendor_db: invalid structure

---

### 3. Валідація

- vendors є dict
- ключі відповідають OUI
- значення string

---

### 4. Lookup

get_vendor(mac: str)

- нормалізація MAC
- пошук по OUI
- повертає vendor або None

---

### 5. Поведінка при помилках

- при відсутності файлу → контрольована помилка
- при битому JSON → лог + stop або fallback

---

## Logging

- тільки англійською
- мінімальний шум

---

## Документація

Оновити README (UA + EN):
- опис mac_vendor_db
- як працює lookup

---

## Тести

- файл існує
- файл відсутній
- битий JSON
- lookup

---

## Acceptance Criteria

1. Є mac_vendor_db.py
2. Є завантаження при старті
3. Є валідація
4. Є lookup
5. Є логування
6. Є тести
7. Оновлена документація

---

## Обмеження

- тільки локальний JSON
- без зовнішніх API
- deterministic
