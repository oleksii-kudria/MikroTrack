# TASK-012: Persistence (JSON snapshots) + bilingual docs

## Мета

Реалізувати збереження результатів збору даних (devices) у файл:

- зберігати snapshots у JSON
- керувати шляхом через .env
- додати підготовку директорії
- оновити README та docs (двомовність)

---

## Контекст

Зараз дані збираються, але не зберігаються.

Потрібно:
→ додати persistence як MVP (без БД)

---

## Що потрібно реалізувати

### 1. Додати змінні в .env

Оновити `.env.example`:

PERSISTENCE_ENABLED=true
PERSISTENCE_PATH=/data/snapshots
PERSISTENCE_RETENTION_DAYS=7

---

### 2. Оновити config.py

Додати:

- PERSISTENCE_ENABLED (bool)
- PERSISTENCE_PATH (str)
- PERSISTENCE_RETENTION_DAYS (int)

---

### 3. Створити persistence модуль

Файл:
app/persistence.py

Функція:

def save_snapshot(devices: list[dict]) -> None:

---

### 4. Формат збереження

Файли:

YYYY-MM-DDTHH-MM-SS.json

Приклад:

2026-04-05T23-10-00.json

---

### 5. Реалізація

- створити директорію якщо не існує
- записати JSON

with open(file, "w") as f:
    json.dump(devices, f, indent=2, ensure_ascii=False)

---

### 6. Retention

- видаляти файли старше N днів

---

### 7. Інтеграція в main.py

devices = run_once()

if config.persistence_enabled:
    save_snapshot(devices)

---

### 8. Логування

INFO:
- Snapshot saved: path
- Retention cleanup done

DEBUG:
- file size
- number of devices

---

## Docs update (обов'язково)

### 1. README (двомовний)

Додати розділ:

## Persistence

Опис:
- де зберігаються файли
- як увімкнути
- приклад

---

### 2. docs/storage.md (новий файл)

Описати:

#### 🇺🇦 Українською
- як працює persistence
- структура директорій
- приклад snapshot
- як підготувати директорію:

mkdir -p /data/snapshots
chmod 755 /data/snapshots

- якщо Docker:
  - volume mapping

#### 🇬🇧 English
(same content in English)

---

### 3. Всі docs повинні бути двомовні

Обов'язково:

- README
- docs/*

Структура:

## 🇺🇦 Українською
## 🇬🇧 English

---

## Очікуваний результат

- snapshots зберігаються у файли
- директорія створюється автоматично
- retention працює
- документація двомовна

---

## Критерії приймання

- persistence працює
- шлях задається через env
- retention працює
- docs оновлені
- README двомовний
- docs двомовні
- код простий

---

## Далі

TASK-013: Diff (порівняння snapshot)
