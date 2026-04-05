# TASK-001: Bootstrap репозиторію та базовий запуск через Docker Compose

## Мета

Створити базову структуру проєкту MikroTrack та забезпечити запуск застосунку через Docker Compose.

Це перший крок розробки.  
На цьому етапі ми НЕ реалізуємо логіку роботи з MikroTik або БД.

---

## Контекст

MikroTrack - це локальний інструмент пасивного моніторингу мережі.

Основні принципи:

- local-first
- запуск на Linux через Docker
- мінімалізм
- маленькі ітерації

---

## Що потрібно реалізувати

### 1. Структура репозиторію

Створити базову структуру:

.
├── app/
│   ├── __init__.py
│   └── main.py
├── docker/
│   └── app/
│       └── Dockerfile
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md

---

### 2. Мінімальний Python-застосунок

Файл: `app/main.py`

Вимоги:

- використовувати logging
- при запуску вивести:
  - "MikroTrack started"
  - "MikroTrack stopped"
- завершуватись без помилок

---

### 3. Dockerfile

Файл: `docker/app/Dockerfile`

Вимоги:

- базовий image: python:3.12-slim
- робоча директорія: /app
- копіювання коду
- встановлення залежностей
- запуск через python -m app.main

---

### 4. docker-compose.yml

Файл: `docker-compose.yml`

Вимоги:

- один сервіс: mikrotrack-app
- build з docker/app/Dockerfile
- використання .env
- зрозуміла назва контейнера
- проста конфігурація без зайвих параметрів

---

### 5. Конфігурація через .env

Файл: `.env.example`

APP_ENV=development  
LOG_LEVEL=INFO  
TZ=Europe/Kyiv  

---

### 6. .gitignore

Додати:

__pycache__/  
*.pyc  
.env  
.venv/  

---

### 7. requirements.txt

Порожній файл (поки без залежностей)

---

### 8. README.md

Короткий опис:

- що це стартовий каркас MikroTrack
- як створити .env
- як запустити

Приклад:

cp .env.example .env  
docker compose up --build  

---

## Обмеження

На цьому етапі НЕ використовувати:

- PostgreSQL
- FastAPI
- MikroTik API
- NetFlow
- кілька сервісів
- складну архітектуру

---

## Очікуваний результат

Команда:

docker compose up --build

має:

- зібрати Docker image
- запустити контейнер
- вивести лог:

MikroTrack started

- завершитись без помилок

---

## Критерії приймання

- створена структура репозиторію
- є Dockerfile
- є docker-compose.yml
- контейнер збирається
- контейнер запускається
- використовується logging
- є .env.example
- є README
- код простий і читабельний

---

## Додатково

Структура має бути підготовлена для наступних задач:

- додавання конфігурації
- MikroTik client
- collector DHCP
