# TASK-004: Покращення журналів подій та обробки помилок (User-friendly logging)

## Мета

Покращити обробку помилок при підключенні до MikroTik API (api-ssl):

- додати класифікацію типових помилок
- формувати зрозумілі повідомлення англійською мовою
- додати рекомендації для користувача
- пояснювати, що саме не працює

---

## Контекст

Зараз при помилках виводиться stack trace, який складно читати.

Потрібно додати шар, який:

- аналізує exception
- визначає тип проблеми
- формує user-friendly повідомлення

---

## Що потрібно реалізувати

### 1. Створити модуль обробки помилок

Файл:

app/errors.py

Функціонал:

- приймає exception
- повертає структуру:

{
    "error_code": "STRING",
    "message": "Human readable message",
    "recommendation": "What user should do"
}

---

### 2. Реалізувати обробку типових помилок

#### 1. Connection refused

Message:
Failed to connect to MikroTik API SSL: TCP connection was refused.

Recommendation:
Verify that api-ssl is enabled, correct port is used, and firewall allows access.

---

#### 2. Connection timeout

Message:
Connection to MikroTik API SSL timed out.

Recommendation:
Verify network connectivity, IP address, and allowed address list.

---

#### 3. SSL handshake failure

Message:
Failed to establish SSL/TLS session with MikroTik API SSL.

Recommendation:
Verify certificate is generated and assigned to api-ssl service.

---

#### 4. SSL certificate verification failed

Message:
SSL certificate verification failed.

Recommendation:
Verify certificate validity or disable verification for lab environments.

---

#### 5. Invalid username or password

Message:
Authentication failed for MikroTik user.

Recommendation:
Verify username and password.

---

#### 6. Insufficient permissions (not allowed (9))

Message:
User does not have sufficient permissions for API access.

Recommendation:
Ensure user group has 'read' and 'api' policies.

---

#### 7. DHCP fetch failed

Message:
Connected to MikroTik, but failed to retrieve DHCP leases.

Recommendation:
Verify read access and DHCP configuration.

---

#### 8. Empty DHCP result

Message:
No DHCP leases were returned.

Recommendation:
Verify DHCP server is running and has active leases.

---

#### 9. Unexpected response

Message:
Unexpected response from MikroTik API.

Recommendation:
Verify RouterOS compatibility and API response.

---

### 3. Інтеграція в mikrotik_client.py

- перехоплювати exception
- викликати errors.py
- логувати:
    - message
    - recommendation

Stack trace залишити (debug або error)

---

### 4. Формат логів

Приклад:

2026-04-05 ERROR MikroTikClient: Failed to establish SSL/TLS session with MikroTik API SSL.
Recommendation: verify certificate is generated and assigned to api-ssl service.

---

### 5. Оновити main.py

- при помилці виводити user-friendly повідомлення
- завершувати виконання коректно

---

## Обмеження

НЕ потрібно:

- змінювати архітектуру
- додавати нові сервіси
- додавати БД
- змінювати collector логіку

---

## Очікуваний результат

При будь-якій помилці користувач бачить:

- зрозуміле повідомлення
- рекомендацію

без необхідності аналізувати stack trace

---

## Критерії приймання

- створено errors.py
- реалізовано класифікацію помилок
- лог містить message + recommendation
- підтримано всі основні сценарії помилок
- код простий і читабельний

---

## Далі

TASK-005: ARP + об’єднання DHCP
