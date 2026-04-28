# TASK-102 - Improve IEEE OUI updater diagnostics and prevent invalid vendor data

## Опис задачі

Після виконання `python3 scripts/update_mac_vendors.py` зафіксовано проблему:

```text
INFO mac_vendor_update: Downloading IEEE OUI registry
ERROR mac_vendor_update: Failed to download data
```

Поточне повідомлення не містить причину помилки: HTTP status, DNS error, SSL error, timeout, URL або інші деталі.

Також у `app/data/mac_vendors.json` виявлено некоректні placeholder-значення замість реальних назв вендорів:

```json
{
  "vendors": {
    "000000": "IEEE MA-L Vendor 00000",
    "000001": "IEEE MA-L Vendor 00001"
  }
}
```

Це означає, що файл не можна вважати production-ready базою MAC-вендорів.

Необхідно виправити updater, покращити діагностику помилок та додати перевірки, які не дозволять записати згенеровані placeholder-дані у `app/data/mac_vendors.json`.

---

## Поточний стан

Файл:

```text
scripts/update_mac_vendors.py
```

вже містить:
- URL за замовчуванням `https://standards-oui.ieee.org/oui/oui.csv`
- функцію `download_registry`
- парсинг CSV/TXT
- валідацію OUI
- атомарний запис JSON

Але в блоці обробки помилок download зараз логування занадто загальне:

```text
ERROR mac_vendor_update: Failed to download data
```

Цього недостатньо для діагностики.

---

## Що необхідно реалізувати

### 1. Покращити логування помилок download

Необхідно логувати конкретну причину помилки.

Приклади очікуваних логів:

```text
ERROR mac_vendor_update: Failed to download IEEE OUI registry: url=https://standards-oui.ieee.org/oui/oui.csv, error=<details>
ERROR mac_vendor_update: IEEE OUI registry returned HTTP error: status=403, reason=Forbidden, url=...
ERROR mac_vendor_update: IEEE OUI registry download timeout: timeout=20.0s, url=...
ERROR mac_vendor_update: IEEE OUI registry DNS/connection error: error=<details>, url=...
```

Логи повинні залишатися англійською мовою.

---

### 2. Логувати параметри запуску updater

На старті додати INFO/DEBUG повідомлення з основними параметрами:

```text
INFO mac_vendor_update: Starting MAC vendors update, source_url=..., output=..., timeout=...
```

Не логувати секрети, якщо в майбутньому зʼявляться авторизаційні параметри.

---

### 3. Логувати результат download

Після успішного завантаження додати інформацію:

```text
INFO mac_vendor_update: IEEE OUI registry downloaded, bytes=XXXXX
```

За можливості також логувати:
- HTTP status
- content-type
- charset

---

### 4. Покращити логування parsing

Після парсингу додати:

```text
INFO mac_vendor_update: IEEE OUI registry parsed, entries=XXXXX
```

Якщо CSV не містить очікуваних колонок, логувати назви колонок:

```text
ERROR mac_vendor_update: Unsupported IEEE CSV header, fields=[...]
```

---

### 5. Заборонити placeholder vendor names

Необхідно додати sanity-check, який забороняє записувати значення типу:

```text
IEEE MA-L Vendor 00000
IEEE MA-L Vendor 00001
IEEE MA-L Vendor 12345
```

Якщо такі значення виявлені у великій кількості або як системний шаблон, updater має завершуватися з помилкою і НЕ перезаписувати `app/data/mac_vendors.json`.

Приклад логу:

```text
ERROR mac_vendor_update: Placeholder vendor names detected, aborting update
```

---

### 6. Перевірити реальні назви вендорів

Після генерації бази необхідно перевірити, що у vendors є реальні назви організацій.

Мінімальні sanity-checks:
- vendors не порожній
- vendors_count >= мінімального порогу
- vendor name не є placeholder
- vendor name не генерується з OUI
- у базі є очікувані відомі вендори, наприклад Apple

Приклад перевірки:

```python
assert any("Apple" in vendor for vendor in vendors.values())
```

Це не має бути єдиною перевіркою, але може бути додатковим smoke-test.

---

### 7. Не перезаписувати файл при будь-якій помилці

Якщо сталася помилка на етапі:
- download
- parsing
- validation
- sanity-check

існуючий `app/data/mac_vendors.json` не повинен бути змінений.

---

### 8. Додати підтримку локального input file

Для діагностики та роботи в середовищах без прямого доступу до IEEE додати параметр:

```bash
python3 scripts/update_mac_vendors.py --input-file /tmp/oui.csv
```

Поведінка:
- якщо `--input-file` заданий, download не виконується
- файл читається локально
- далі використовується та сама логіка parse / validate / write

Приклад логів:

```text
INFO mac_vendor_update: Loading IEEE OUI registry from local file, path=/tmp/oui.csv
```

---

### 9. Додати retry для download

Додати простий retry-механізм:

- кількість спроб: 3
- затримка між спробами: 2-5 секунд
- логувати номер спроби

Приклад:

```text
WARNING mac_vendor_update: Download attempt failed, attempt=1/3, error=...
```

---

## Вплив на журнали подій (LOGGING)

Необхідно врахувати зміни в журнали подій.

Всі нові повідомлення логів мають бути англійською мовою.

### Повинні бути додані логи:

- старт updater
- URL / output / timeout
- результат download
- причина download failure
- CSV fields при помилці parsing
- кількість parsed vendors
- причина validation failure
- detection placeholder vendor names
- success update

### Не потрібно:

- логувати кожен OUI
- логувати весь CSV payload
- логувати весь JSON

---

## Вплив на документацію

Необхідно оновити документацію українською та англійською.

Оновити README / docs:

### Українською:
- як оновити `app/data/mac_vendors.json`
- як перевірити доступність IEEE URL через `curl`
- як використати `--input-file`
- що робити, якщо download failed
- чому runtime не завантажує IEEE автоматично

### English:
- how to update `app/data/mac_vendors.json`
- how to test IEEE URL with `curl`
- how to use `--input-file`
- how to troubleshoot download failures
- why runtime does not download IEEE automatically

---

## Приклади команд для документації

```bash
python3 scripts/update_mac_vendors.py
```

```bash
python3 scripts/update_mac_vendors.py --timeout 60
```

```bash
curl -L https://standards-oui.ieee.org/oui/oui.csv -o /tmp/oui.csv
python3 scripts/update_mac_vendors.py --input-file /tmp/oui.csv
```

---

## Тести

Необхідно додати або оновити тести:

1. download success
2. download HTTP error
3. download timeout
4. DNS / connection error
5. local `--input-file`
6. valid IEEE CSV parsing
7. unsupported CSV header
8. empty vendors validation
9. placeholder vendor names detection
10. existing `mac_vendors.json` is not overwritten on failure
11. successful atomic write

---

## Acceptance Criteria

1. При download failure лог містить реальну причину помилки
2. Лог містить URL, timeout та output path
3. Успішний download логують з розміром payload
4. Parsing логують з кількістю vendor entries
5. Placeholder vendor names не можуть потрапити у production `mac_vendors.json`
6. При помилці існуючий `mac_vendors.json` не перезаписується
7. Додано `--input-file`
8. Додано retry для download
9. Додано/оновлено тести
10. Документація оновлена українською та англійською

---

## Обмеження

- runtime не повинен завантажувати IEEE registry
- online download дозволений тільки для updater script
- не додавати важких залежностей
- JSON формат `app/data/mac_vendors.json` не змінювати
- логи тільки англійською

---

## Примітки

Поточний файл `app/data/mac_vendors.json` з placeholder-значеннями виду `IEEE MA-L Vendor XXXXX` не повинен використовуватися як production база.

Перед комітом production версії потрібно переконатися, що `vendors` містить реальні назви організацій.
