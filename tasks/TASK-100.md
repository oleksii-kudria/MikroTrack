# TASK-100 - Generate and Commit Full Offline MAC Vendors Database

## Опис задачі

Наразі логіка визначення `mac_vendor` працює коректно, але локальна база
`app/data/mac_vendors.json` містить неповний або тестовий набір OUI записів.

В результаті `mac_vendor` визначається лише для невеликої кількості пристроїв.

Необхідно:
- згенерувати повну локальну базу MAC-вендорів з IEEE MA-L registry
- зберегти її у репозиторії
- забезпечити перевірку повноти бази під час startup
- зберегти offline-first підхід

---

## Ціль задачі

Після виконання задачі:

- після `git clone` система вже має повноцінну локальну базу
- runtime НЕ залежить від інтернету
- більшість реальних MAC адрес коректно отримують `mac_vendor`
- тестові або неповні бази виявляються автоматично

---

## Що необхідно реалізувати

### 1. Згенерувати повний mac_vendors.json

Використати:

python scripts/update_mac_vendors.py

Джерело:
- IEEE MA-L registry

Результат:
- production-ready app/data/mac_vendors.json

---

### 2. Додати файл у репозиторій

Закомітити:

app/data/mac_vendors.json

Файл повинен бути доступний одразу після:
- clone
- deploy
- restart

Runtime не повинен самостійно завантажувати IEEE registry.

---

### 3. Startup validation

Перевіряти:

- файл існує
- JSON валідний
- структура валідна
- vendors не порожній
- база не виглядає тестовою

Приклад:

if vendors_count < 10000:
    raise ValidationError(...)

---

## Логування (LOGGING)

Логи тільки англійською.

Успішне завантаження:
INFO mac_vendor_db: Loaded MAC vendors database, entries=XXXXX

Некоректна база:
ERROR mac_vendor_db: MAC vendors database looks incomplete

---

## Runtime behavior

Runtime НЕ повинен:
- робити HTTP requests
- автоматично оновлювати базу
- залежати від IEEE availability

---

## Вплив на документацію

Оновити документацію українською та англійською:

- README
- docs (якщо є)

Описати:
- джерело mac_vendors.json
- процес оновлення
- offline-first підхід

---

## Тести

1. повна база успішно завантажується
2. файл відсутній
3. файл пошкоджений
4. база занадто мала
5. startup validation працює

---

## Acceptance Criteria

1. Повний mac_vendors.json згенеровано
2. Файл закомічено в репозиторій
3. Runtime працює offline
4. Є startup validation
5. Неповна база виявляється
6. Логи англійською
7. Документація оновлена
8. Тести додані

---

## Обмеження

- без auto-download під час runtime
- без зовнішньої БД
- deterministic behavior
- offline-first

---

## Примітки

Автоматичне завантаження IEEE при старті застосунку НЕ реалізовувати.
