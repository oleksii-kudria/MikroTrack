# TASK-006: Маскування паролів у логах + оновлення README (error handling)

## Мета

Забезпечити безпечне логування:

- приховати пароль у логах
- санітизувати traceback
- не допустити витоку секретів
- додати опис типових помилок у README

---

## Контекст

Стороння бібліотека (routeros_api) повертає traceback з паролем:

/login =name=user =password=StrongPassword

Це необхідно маскувати.

---

## Що потрібно реалізувати

### 1. Створити sanitizer

Файл:

app/sanitizer.py

Функція:

sanitize(text: str) -> str

---

### 2. Маскування

Покрити:

=password=VALUE → =password=***

'password': 'VALUE' → 'password': '***'

"password": "VALUE" → "password": "***"

---

### 3. Оновити логування

- не логувати пароль
- не використовувати print()
- санітизувати debug output

---

### 4. Оновити main.py

Було:

logger.debug(..., exc_info=...)

Стало:

logger.debug("Raw exception: %s", sanitize(str(e.original_exception)))

---

### 5. Оновити README

Додати розділ:

## Troubleshooting

### Connection refused

Причина:
- api-ssl вимкнено
- неправильний порт
- firewall

Рішення:
- перевірити api-ssl
- перевірити порт 8729
- перевірити доступ

---

### SSL handshake failure

Причина:
- відсутній сертифікат
- сертифікат не призначено

Рішення:
- створити сертифікат
- призначити api-ssl

---

### Authentication failed

Причина:
- неправильний логін/пароль

Рішення:
- перевірити .env
- перевірити user

---

### Not allowed (9)

Причина:
- недостатньо прав

Рішення:
- policy=read,api

---

### Timeout

Причина:
- немає доступу до мережі

Рішення:
- перевірити IP
- перевірити firewall

---

ВАЖЛИВО:
README не повинен містити паролі або приклади з реальними секретами.

---

## Очікуваний результат

- пароль не з’являється у логах
- traceback безпечний
- README містить troubleshooting

---

## Критерії приймання

- sanitizer реалізовано
- лог без секретів
- README оновлено
- код простий

---

## Далі

TASK-007: ARP + об’єднання DHCP
