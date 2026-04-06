# TASK-020 - Fix Devices API fetch (Docker networking issue)

## Мета

Виправити помилку у вкладці Devices:

Unable to load devices: TypeError: Failed to fetch

Причина:
frontend (browser) не може звернутись до backend через docker service name (mikrotrack-app).

---

## Опис проблеми

Зараз frontend виконує запит типу:

http://mikrotrack-app:8000/api/devices

Це працює тільки всередині Docker мережі.

Browser (Chrome у Windows) не бачить docker hostname → fetch падає.

---

## Що потрібно зробити

### 1. Замінити backend URL для browser

Всі client-side fetch запити повинні використовувати:

http://localhost:8000

або відносний шлях:

/api/devices

---

### 2. Виправити конфігурацію frontend

Якщо використовується env:

Змінити:

BACKEND_API_URL=http://mikrotrack-app:8000

на:

BACKEND_API_URL=http://localhost:8000

---

### 3. Оновити fetch у frontend коді

Було:

fetch("http://mikrotrack-app:8000/api/devices")

Має бути:

fetch("http://localhost:8000/api/devices")

або:

fetch("/api/devices")

---

### 4. (Опціонально - рекомендовано) Додати proxy через web container

Щоб уникнути hardcode localhost:

- web контейнер проксіює /api → mikrotrack-app:8000
- frontend використовує тільки:

fetch("/api/devices")

---

### 5. Перевірити docker-compose

Backend повинен мати відкритий порт:

ports:
  - "8000:8000"

---

### 6. Перевірити доступність API

З Windows:

http://localhost:8000/api/devices

повинен відкриватися у браузері

---

## Важливі вимоги

- не використовувати docker service name у browser fetch
- не ламати існуючий API
- Devices tab має працювати без помилки fetch

---

## Definition of Done

- вкладка Devices завантажує дані без помилки
- fetch більше не падає
- API доступний через localhost:8000
- Devices UI відображає список пристроїв
