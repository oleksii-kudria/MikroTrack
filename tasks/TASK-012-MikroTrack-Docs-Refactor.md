# TASK-012: Refactor README and introduce docs structure

## Мета

Переробити структуру документації проєкту:

- спростити README (зробити його “landing page”)
- винести технічну документацію в docs/
- чітко позиціонувати сервіс як collector

---

## Контекст

Зараз README:

- перевантажений деталями
- змішує різні типи інформації
- складний для нових користувачів

---

## Що потрібно реалізувати

### 1. Переробити README.md

README має містити:

#### 1.1 Опис проєкту

MikroTrack is a lightweight network monitoring collector for MikroTik.

Collects:
- DHCP leases
- ARP table

Builds:
- unified device model

---

#### 1.2 Архітектура (коротко)

- collector only
- no persistence (yet)
- no API
- no UI

---

#### 1.3 Quick Start

git clone  
cp .env.example .env  
docker compose up --build  

---

#### 1.4 Основні параметри

LOG_LEVEL  
RUN_MODE  
COLLECTION_INTERVAL  
PRINT_RESULT_TO_STDOUT  

---

#### 1.5 Documentation section

Посилання на docs:

- MikroTik setup → docs/mikrotik-setup.md
- Device model → docs/device-model.md
- Scheduler → docs/scheduler.md
- Troubleshooting → docs/troubleshooting.md

---

### 2. Створити структуру docs/

docs/
  mikrotik-setup.md
  device-model.md
  scheduler.md
  troubleshooting.md
  architecture.md

---

### 3. docs/device-model.md

Описати:

- DHCP fields
- ARP fields
- flags
- status
- приклад JSON

---

### 4. docs/scheduler.md

Описати:

- RUN_MODE
- COLLECTION_INTERVAL
- loop vs once

---

### 5. docs/troubleshooting.md

Описати:

- connection refused
- ssl error
- authentication failed
- not allowed (9)

---

### 6. docs/architecture.md

Описати:

- collector (current)
- storage (future)
- API (future)
- UI (future)

---

### 7. README має бути двомовний

Структура:

## 🇺🇦 Українською

## 🇬🇧 English

---

## Очікуваний результат

- README короткий і зрозумілий
- docs містить всю деталізацію
- структура виглядає як production-ready проєкт

---

## Критерії приймання

- README спрощено
- docs створено
- README містить посилання на docs
- документація двомовна
- структура чиста і логічна

---

## Далі

TASK-013: Persistence (JSON snapshots)
