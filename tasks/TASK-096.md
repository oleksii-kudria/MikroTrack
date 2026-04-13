# TASK-096 - Offline MAC Vendors Database (mac_vendors.json)

## Опис задачі

Необхідно реалізувати підтримку локальної бази MAC-вендорів (OUI) у вигляді файлу:

app/data/mac_vendors.json

Система повинна працювати offline-first, без залежності від зовнішніх API під час runtime.

Також необхідно забезпечити:
- перевірку існування та валідності файлу при старті застосунку
- можливість оновлення файлу окремою дією
- стабільну інтеграцію з існуючою логікою визначення mac_vendor

---

## Що необхідно реалізувати

### 1. Додати офлайн файл у репозиторій

Створити файл:
app/data/mac_vendors.json

Файл повинен містити базову офлайн-версію бази OUI.

### Вимоги до формату

{
  "version": 1,
  "updated_at": "2026-04-13T12:00:00+03:00",
  "source": "offline snapshot",
  "vendors": {
    "001122": "Vendor A",
    "AABBCC": "Vendor B",
    "D850E6": "Apple, Inc."
  }
}

Правила:
- ключі - OUI (6 hex символів)
- верхній регістр
- без ':' або '-'
- значення - строка

---

### 2. Завантаження файлу при старті

- перевірити наявність файлу
- завантажити JSON
- провалідувати структуру
- зберегти в пам’яті

Логування (EN):
INFO mac_vendor_db: Loaded MAC vendors database
ERROR mac_vendor_db: mac_vendors.json not found
ERROR mac_vendor_db: invalid JSON format

---

### 3. Валідація

- файл існує
- валідний JSON
- vendors - dict
- ключі валідні OUI
- значення string

---

### 4. Lookup

get_vendor(mac: str) -> Optional[str]

- нормалізація MAC
- пошук по OUI
- якщо немає -> None

---

### 5. Оновлення

scripts/update_mac_vendors.py

- оновлення вручну
- атомарний запис

---

### 6. Fallback

- якщо немає оновлення -> використовувати офлайн файл

---

## Logging

- тільки англійською
- без шуму

---

## Документація

Оновити README (UA + EN):
- опис mac_vendors.json
- як оновлювати

---

## Тести

- валідний файл
- файл відсутній
- битий JSON
- lookup

---

## Acceptance Criteria

1. Є mac_vendors.json
2. Є завантаження
3. Є валідація
4. Є логування
5. Є lookup
6. Є update script
7. Offline runtime
8. Тести
9. Документація

---

## Обмеження

- без зовнішніх API
- JSON only
- deterministic
- offline-first
