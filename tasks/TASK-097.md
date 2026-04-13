# TASK-097 - MAC Vendors Update from IEEE (online → mac_vendors.json)

## Опис задачі

Необхідно реалізувати механізм оновлення локальної бази MAC-вендорів (mac_vendors.json)
шляхом завантаження даних з офіційного реєстру IEEE.

Оновлення виконується окремою дією (script / CLI / CI) та НЕ є частиною runtime.

---

## Що необхідно реалізувати

### 1. Скрипт оновлення

scripts/update_mac_vendors.py

Функціонал:
- завантажити дані з IEEE OUI registry
- обробити помилки мережі

Логування (EN):
INFO mac_vendor_update: Downloading IEEE OUI registry
ERROR mac_vendor_update: Failed to download data

---

### 2. Парсинг

- обробити CSV/TXT IEEE
- витягнути OUI + vendor

Нормалізація:
00-11-22 → 001122

---

### 3. JSON формат

{
  "version": 1,
  "updated_at": "ISO8601",
  "source": "ieee",
  "vendors": {
    "001122": "Vendor A"
  }
}

---

### 4. Валідація

- vendors не порожній
- ключі валідні
- значення string

---

### 5. Атомарний запис

- temp файл
- rename

---

### 6. Помилки

- не перезаписувати файл при помилці

---

## Logging

INFO mac_vendor_update: Vendors loaded
INFO mac_vendor_update: mac_vendors.json updated successfully

---

## Документація

README (UA + EN):
- як оновити
- приклад запуску

---

## Тести

- download OK
- download fail
- parse
- normalize
- save

---

## Acceptance Criteria

1. Є update script
2. Завантаження з IEEE
3. Парсинг
4. Нормалізація
5. Валідація
6. Атомарний запис
7. Логи
8. Тести
9. Документація

---

## Обмеження

- runtime без інтернету
- JSON only
- deterministic

---

## Примітки

- не хардкодити URL
- IEEE формат може змінюватись
