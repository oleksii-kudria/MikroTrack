# TASK-017 - Project structure and container layout (app + web, no DB)

## Мета

Підготувати поточний репозиторій MikroTrack до запуску у 2 контейнерах без використання окремої бази даних:

- `mikrotrack-app` - collector, snapshot persistence, event storage, API
- `mikrotrack-web` - Web UI (timeline)

Storage лишається файловим:

- snapshots → JSON
- events → JSONL

---

## Поточний стан репозиторію

У репозиторії вже є:

- один контейнер `mikrotrack-app`
- `docker-compose.yml`
- `docker/app/Dockerfile`
- flat-структура Python-коду в `app/`
- конфігурація через `.env`
- snapshot persistence через `app/persistence.py`
- event-driven diff і запис у `events.jsonl` в межах `PERSISTENCE_PATH`

---

## Що потрібно зробити

### 1. Зберегти існуючу логіку collector без функціонального регресу

Під час реорганізації не ламати:

- `app/main.py`
- завантаження env-конфігурації з `app/config.py`
- поточний loop/once run mode
- snapshot persistence
- event-driven diff
- запис `events.jsonl`

Усі наявні можливості повинні залишитися працездатними після реорганізації.

---

### 2. Підготувати структуру проєкту до розділення app і web

Поточний flat layout у `app/` залишити працездатним, але підготувати репозиторій до окремого web-контейнера.

Цільова структура:

```text
MikroTrack/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── collector.py
│   ├── device_builder.py
│   ├── mikrotik_client.py
│   ├── persistence.py
│   ├── logging_config.py
│   ├── sanitizer.py
│   ├── errors.py
│   ├── exceptions.py
│   └── api/
│       ├── __init__.py
│       └── main.py
├── web/
│   ├── __init__.py
│   ├── main.py
│   ├── templates/
│   └── static/
├── docker/
│   ├── app/
│   │   └── Dockerfile
│   └── web/
│       └── Dockerfile
├── docs/
├── tasks/
├── tests/
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

---

### 3. Не переносити конфігурацію в YAML на цьому етапі

З урахуванням поточного репозиторію, конфігурація вже реалізована через `.env` та `app/config.py`.

На цій задачі НЕ потрібно:

- вводити `config/mikrotrack.yml`
- дублювати конфіг у YAML
- переписувати `load_config()` на новий формат

Потрібно:

- зберегти `.env`-підхід
- за потреби розширити `.env.example` новими змінними для API/Web
- не ламати існуючі змінні

---

### 4. Розширити `.env.example` для майбутнього API/Web

До існуючих env-змінних додати нові, необхідні для 2-контейнерної схеми.

Зберегти наявні змінні:

- `MIKROTIK_HOST`
- `MIKROTIK_PORT`
- `MIKROTIK_USERNAME`
- `MIKROTIK_PASSWORD`
- `MIKROTIK_USE_SSL`
- `MIKROTIK_SSL_VERIFY`
- `LOG_LEVEL`
- `PRINT_RESULT_TO_STDOUT`
- `RUN_MODE`
- `COLLECTION_INTERVAL`
- `PERSISTENCE_ENABLED`
- `PERSISTENCE_PATH`
- `PERSISTENCE_RETENTION_DAYS`
- `TZ`

Додати нові:

```env
API_ENABLED=true
API_HOST=0.0.0.0
API_PORT=8000
WEB_HOST=0.0.0.0
WEB_PORT=8080
BACKEND_API_URL=http://mikrotrack-app:8000
```

Якщо частина цих змінних поки не використовується напряму - це допустимо, але вони мають бути підготовлені для наступних задач.

---

### 5. Розділити відповідальність між контейнерами

#### `mikrotrack-app`

Повинен відповідати за:

- підключення до MikroTik
- збір DHCP/ARP
- побудову unified device model
- loop scheduler
- snapshot persistence
- event-driven diff
- event storage (`events.jsonl`)
- API для читання snapshots/events

#### `mikrotrack-web`

Повинен відповідати тільки за:

- web UI
- timeline page
- filters
- event details view

`mikrotrack-web` не повинен напряму читати `/data/snapshots` або `/data/events/events.jsonl`.
Взаємодія тільки через HTTP API контейнера `mikrotrack-app`.

---

### 6. Оновити `docker-compose.yml` під 2 контейнери

Поточний `docker-compose.yml` містить лише `mikrotrack-app`.

Потрібно оновити його так, щоб він запускав:

- `mikrotrack-app`
- `mikrotrack-web`

Вимоги:

- залишити `mikrotrack-app` як основний сервіс збору
- додати `mikrotrack-web`
- обидва сервіси повинні бути в одній compose network
- `mikrotrack-app` повинен мати persistent volume для `/data/snapshots`
- `mikrotrack-app` повинен зберігати `events.jsonl` там само, як і зараз
- `mikrotrack-web` повинен залежати від `mikrotrack-app`
- не додавати PostgreSQL, Redis, Nginx та інші зайві сервіси

Орієнтир:

```yaml
services:
  mikrotrack-app:
    container_name: mikrotrack-app
    build:
      context: .
      dockerfile: docker/app/Dockerfile
    env_file:
      - .env
    volumes:
      - /data/snapshots:/data/snapshots
    ports:
      - "8000:8000"

  mikrotrack-web:
    container_name: mikrotrack-web
    build:
      context: .
      dockerfile: docker/web/Dockerfile
    env_file:
      - .env
    depends_on:
      - mikrotrack-app
    ports:
      - "8080:8080"
```

Volume mapping можна адаптувати, якщо потрібно винести events в окремий каталог, але без зміни файлової моделі storage.

---

### 7. Зберегти сумісність з поточним Dockerfile для app

У репозиторії вже є `docker/app/Dockerfile`, який:

- використовує `python:3.12-slim`
- копіює `requirements.txt`
- встановлює залежності
- копіює `app/`
- запускає `python -m app.main`

Потрібно:

- не ламати поточний спосіб запуску collector
- за потреби розширити Dockerfile для API-запуску
- не переносити startup logic у shell-обгортки без реальної потреби

Якщо буде додано API в той самий app-контейнер, стартовий механізм має бути продуманий так, щоб не втратити поточний scheduler/collector behavior.

---

### 8. Додати окремий Dockerfile для web

Створити `docker/web/Dockerfile`.

Вимоги:

- окремий контейнер для web
- простий запуск web-додатка
- web повинен вміти звертатись до `http://mikrotrack-app:8000`
- не додавати базу даних
- не монтувати snapshots/events напряму в web-контейнер

---

### 9. Підготувати мінімальний каркас API у backend

У рамках цієї задачі потрібно підготувати базове місце для майбутнього API шару.

Мінімум:

- створити `app/api/`
- підготувати entrypoint для майбутніх endpoint'ів
- не реалізовувати повний функціонал timeline тут
- не ламати поточний collector flow

Ця задача готує основу під наступні задачі по API та Web UI.

---

### 10. Підготувати мінімальний каркас web-додатка

У рамках цієї задачі потрібно підготувати базову структуру `web/`:

- `web/main.py`
- `web/templates/`
- `web/static/`

Без складної логіки.

Це лише підготовка структури для наступної задачі з timeline UI.

---

## Важливі вимоги

- не використовувати окрему БД
- не замінювати JSON/JSONL storage на SQL storage
- не переписувати поточний collector з нуля
- не ламати існуючі env-змінні
- не змінювати базову collector логіку без потреби
- web тільки через API, без прямого читання persistence files
- зберегти сумісність з поточним репозиторієм і його layout

---

## Очікуваний результат

Після виконання задачі репозиторій повинен:

- залишатися працездатним як collector
- мати готову основу під 2-контейнерний запуск
- містити `mikrotrack-app` і `mikrotrack-web`
- мати окремий Dockerfile для web
- мати оновлений `docker-compose.yml`
- мати підготовлений каркас `app/api/`
- мати підготовлений каркас `web/`
- зберігати snapshots/events у файловому вигляді без БД

---

## Definition of Done

Задача вважається виконаною, якщо:

- оновлено `docker-compose.yml` під 2 контейнери
- додано `docker/web/Dockerfile`
- збережено працездатність `docker/app/Dockerfile`
- створено `app/api/` як основу для backend API
- створено `web/` як основу для frontend
- `.env.example` розширено новими змінними для API/Web
- поточний collector запуск не зламаний
- база даних не додана
- JSON snapshots і `events.jsonl` залишились основним storage
