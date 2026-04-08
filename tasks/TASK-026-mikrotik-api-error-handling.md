# TASK-026 - Improve MikroTik API Error Handling & Diagnostics

## Опис (UA)

Поточна обробка помилок при підключенні до MikroTik API / API-SSL є некоректною та вводить в оману.

Приклад:
[UNEXPECTED_ERROR] Unexpected response from MikroTik API.

Реальна причина може бути:
- IP клієнта не дозволений у /ip service api-ssl
- неправильні credentials
- вимкнений сервіс api/api-ssl
- TLS / certificate проблеми

---

## Мета (UA)

1. Розділити типи помилок підключення
2. Покращити діагностику
3. Надати точні рекомендації користувачу
4. Оновити документацію (UA + EN)

---

## Error Categories (EN)

- connection_error
- tls_error
- authentication_failed
- access_denied
- api_protocol_error
- unexpected_response

---

## 1. Error Mapping Logic (UA)

```python
if connection_failed:
    error = "connection_error"

elif tls_failed:
    error = "tls_error"

elif auth_failed:
    error = "authentication_failed"

elif api_access_denied:
    error = "access_denied"

else:
    error = "api_protocol_error"
```

---

## 2. Access Denied Detection (UA)

Ознаки:
- TCP connection є
- API session не встановлена

Ймовірна причина:
- /ip service api-ssl address не містить IP клієнта

---

## 3. Error Messages (EN)

access_denied:
MikroTik API-SSL access denied.
Possible reasons:
- client IP not allowed

authentication_failed:
Authentication failed. Verify credentials.

tls_error:
TLS connection failed. Verify certificates.

connection_error:
Unable to connect. Check IP/port.

---

## 4. Logging Requirements (UA)

Логи повинні містити:
- тип помилки
- IP
- порт

Приклад:
ERROR: access_denied 192.168.36.1:8729

---

## 5. API Response (EN)

```json
{
  "error": "access_denied",
  "message": "MikroTik API-SSL access denied"
}
```

---

## 6. Вплив на журнали подій (UA)

- нові типи помилок
- зрозумілі логи

---

## 7. Вплив на документацію (UA + EN)

Українською:
- опис помилок
- troubleshooting

English:
- error descriptions
- troubleshooting guide

---

## 8. Acceptance Criteria (UA)

- помилки розділені
- access_denied визначається
- повідомлення зрозумілі
- документація двомовна

---

## Результат (UA)

Система коректно діагностує проблеми підключення
