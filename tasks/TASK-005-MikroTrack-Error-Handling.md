# TASK-005: Централізація обробки помилок та усунення дублювання логів

## Мета

Усунути дублювання повідомлень про помилки та зробити централізовану, зрозумілу обробку помилок.

Після виконання задачі:
- кожна помилка логуються тільки один раз
- немає дублювання message/recommendation
- немає print()
- stack trace виводиться контрольовано

---

## Контекст

Зараз помилка логується:

- у mikrotik_client.py
- у main.py
- додатково через print()

Це призводить до дублювання і "зашумлення" логів.

---

## Що потрібно реалізувати

### 1. Створити кастомний exception

Файл: app/exceptions.py

Створити клас:

class MikroTrackError(Exception):
    def __init__(self, error_code, message, recommendation, original_exception=None):
        self.error_code = error_code
        self.message = message
        self.recommendation = recommendation
        self.original_exception = original_exception
        super().__init__(message)

---

### 2. Оновити errors.py

- замість логування — тільки формувати структуру помилки
- повертати або використовувати дані для створення MikroTrackError

---

### 3. Оновити mikrotik_client.py

Змінити поведінку:

Замість:
- логування message
- логування recommendation
- логування traceback

Зробити:

- визначити тип помилки
- створити MikroTrackError
- підняти exception (raise)

ВАЖЛИВО:
- не логувати user-friendly повідомлення тут
- не викликати print()
- не дублювати логування

---

### 4. Оновити main.py

Тут має бути єдина точка логування помилок.

Логіка:

try:
    ...
except MikroTrackError as e:
    logger.error("[%s] %s", e.error_code, e.message)
    logger.error("Recommendation: %s", e.recommendation)
    logger.debug("Raw exception details", exc_info=e.original_exception)
    exit(1)

---

### 5. Прибрати print()

Заборонено використовувати print для помилок.

Весь вивід тільки через logging.

---

### 6. Контроль stack trace

Правила:

- ERROR — тільки message + recommendation
- DEBUG — traceback

Не можна виводити traceback більше одного разу.

---

## Очікуваний результат

При помилці лог виглядає так:

INFO Connecting to MikroTik 192.168.36.1:8729 (ssl=True)

ERROR [CONNECTION_REFUSED] Failed to connect to MikroTik API SSL: TCP connection was refused.
ERROR Recommendation: Verify that api-ssl is enabled, correct port is used, and firewall allows access.

(traceback тільки в debug режимі)

---

## Критерії приймання

- створено MikroTrackError
- помилки не дублюються
- немає print()
- logging централізований у main.py
- traceback виводиться один раз
- код простий і читабельний

---

## Далі

TASK-006: ARP + об’єднання DHCP
