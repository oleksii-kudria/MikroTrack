# TASK-009: Scheduler / Loop execution (циклічний збір даних)

## Мета

Реалізувати механізм періодичного збору даних:

- запуск у режимі one-shot або loop
- керування інтервалом через .env
- стабільна робота контейнера як сервісу
- базова обробка помилок (retry/backoff)

---

## Контекст

Зараз застосунок виконується один раз і завершується.

Необхідно:
→ перетворити його на сервіс, який регулярно збирає дані

---

## Що потрібно реалізувати

### 1. Додати змінні в .env

Оновити `.env.example`:

RUN_MODE=loop
COLLECTION_INTERVAL=60

---

### 2. Оновити config.py

Додати:

- RUN_MODE (str): "once" або "loop"
- COLLECTION_INTERVAL (int, секунди)

Значення за замовчуванням:

RUN_MODE=once  
COLLECTION_INTERVAL=60  

---

### 3. Оновити main.py

Реалізувати логіку:

def run_once():
    # існуюча логіка збору DHCP + ARP
    pass

if RUN_MODE == "once":
    run_once()
else:
    while True:
        run_once()
        time.sleep(COLLECTION_INTERVAL)

---

### 4. Додати логування

INFO:

- Starting in LOOP mode (interval=60s)
- Starting collection cycle
- Collection finished
- Sleeping for X seconds

DEBUG:

- start/end кожного кроку
- час виконання (optional)

---

### 5. Обробка помилок у loop

ВАЖЛИВО:

- сервіс не повинен падати при помилці

Приклад:

while True:
    try:
        run_once()
    except Exception as e:
        logger.error("Collection failed: %s", e)
    time.sleep(COLLECTION_INTERVAL)

---

### 6. Retry/backoff (мінімальний)

Додати:

- при помилці → коротший sleep (наприклад 10 сек)
- при успіху → стандартний інтервал

---

### 7. Graceful shutdown

Обробити SIGTERM / SIGINT:

- коректно завершити цикл
- закрити з’єднання

---

## README update (обов'язково)

Додати в README розділ:

## Scheduler / Continuous Collection

MikroTrack can run either as a one-time execution or as a continuous monitoring service.

### Configuration

RUN_MODE=loop  
COLLECTION_INTERVAL=60  

### Parameters

- RUN_MODE:
  - once - run once and exit
  - loop - continuous execution

- COLLECTION_INTERVAL:
  - interval in seconds
  - recommended: 60

### Behavior

- In loop mode, MikroTrack continuously collects DHCP + ARP data
- Service does not stop on errors
- Errors are logged and next iteration continues

### Notes

- ARP data is short-lived
- Recommended interval: 60 seconds

---

## Очікуваний результат

docker compose up

→ контейнер працює постійно  
→ кожні N секунд виконується збір  

---

## Критерії приймання

- підтримується режим once і loop
- інтервал керується через .env
- сервіс не падає при помилці
- логування відповідає TASK-007
- README оновлено
- graceful shutdown працює

---

## Далі

TASK-010: Persistence (збереження результатів у файл або БД)
