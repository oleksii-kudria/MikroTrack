# Troubleshooting

## 🇺🇦 Українською

Нижче наведені категорії помилок MikroTik API, які повертає MikroTrack:

- `connection_error`
- `tls_error`
- `authentication_failed`
- `access_denied`
- `api_protocol_error`
- `unexpected_response`

### connection_error

Симптоми:

- неможливо підключитись до `MIKROTIK_HOST:MIKROTIK_PORT`
- timeout / connection refused / network unreachable

Перевірки:

- на MikroTik увімкнено `api` або `api-ssl`
- порт вказаний правильно (типово `8729` для `api-ssl`)
- firewall дозволяє вхідне з'єднання з collector host
- DNS/IP вказані коректно

### tls_error

Симптоми:

- помилка TLS handshake
- `certificate verify failed`
- `wrong version number` або інші SSL/TLS помилки

Перевірки:

- `MIKROTIK_USE_SSL=true`
- на MikroTik сертифікат призначений на `api-ssl`
- для self-signed сертифіката: `MIKROTIK_SSL_VERIFY=false` або правильна довіра до CA
- дата/час роутера коректні

### authentication_failed

Симптоми:

- логін відхилено
- authentication error у логах

Перевірки:

- `MIKROTIK_USERNAME` та `MIKROTIK_PASSWORD` правильні
- акаунт не вимкнено
- користувач має мінімум права `read`, `api`

### access_denied

Симптоми:

- TCP з'єднання встановлюється, але API сесія не ініціалізується
- помилка доступу або закриття сесії на етапі авторизації

Ймовірна причина:

- IP collector не входить у `/ip service api-ssl address`
- користувачу бракує політик для API

Виправлення:

- перевірити allow-list для `api-ssl`
- перевірити policy групи користувача (мінімум `read,api`)

### api_protocol_error

Симптоми:

- помилки протоколу RouterOS API
- несподіване завершення API-комунікації

Перевірки:

- сумісність версії RouterOS/API
- стабільність каналу зв'язку
- коректність налаштувань сервісу API

### unexpected_response

Симптоми:

- API відповідає у форматі, який не очікує колектор

Перевірки:

- перевірити RouterOS версію та доступність потрібних API ресурсів

### persistence errors

Симптоми:

- `[PERSISTENCE_ERROR]` у логах під час старту
- snapshot-файли не створюються у `PERSISTENCE_PATH`

Перевірки:

- директорія `PERSISTENCE_PATH` існує та доступна на запис
- Docker volume змонтований: `- /data/snapshots:/data/snapshots`
- на хості достатньо вільного місця (мінімум 50MB)
- користувач контейнера має права на директорію

---

## 🇬🇧 English

Below are the MikroTik API error categories returned by MikroTrack:

- `connection_error`
- `tls_error`
- `authentication_failed`
- `access_denied`
- `api_protocol_error`
- `unexpected_response`

### connection_error

Symptoms:

- cannot connect to `MIKROTIK_HOST:MIKROTIK_PORT`
- timeout / connection refused / network unreachable

Checks:

- MikroTik `api` or `api-ssl` service is enabled
- port is correct (default `8729` for `api-ssl`)
- firewall allows inbound connection from collector host
- DNS/IP configuration is correct

### tls_error

Symptoms:

- TLS handshake failure
- `certificate verify failed`
- `wrong version number` or other SSL/TLS failures

Checks:

- `MIKROTIK_USE_SSL=true`
- MikroTik has certificate assigned to `api-ssl`
- if using self-signed certificate, set `MIKROTIK_SSL_VERIFY=false` or trust CA properly
- router date/time are correct (important for certificate validation)

### authentication_failed

Symptoms:

- login rejected
- authentication error in logs

Checks:

- `MIKROTIK_USERNAME` and `MIKROTIK_PASSWORD` are correct
- account is not disabled
- user has enough policy rights (`read`, `api`)

### access_denied

Symptoms:

- TCP connection is established, but API session is not initialized
- access is denied or session closes during authorization

Likely causes:

- collector IP is not included in `/ip service api-ssl address`
- user does not have enough API policies

Fix:

- verify `api-ssl` allow-list includes collector IP
- verify user group policies include at least `read,api`

### api_protocol_error

Symptoms:

- RouterOS API protocol errors
- unexpected API communication interruption

Checks:

- RouterOS/API version compatibility
- network stability
- API service configuration correctness

### unexpected_response

Symptoms:

- API responds with a format that collector does not expect

Checks:

- verify RouterOS version and required API resources

### persistence errors

Symptoms:

- `[PERSISTENCE_ERROR]` in startup logs
- snapshots are not created in `PERSISTENCE_PATH`

Checks:

- `PERSISTENCE_PATH` exists and is writable
- Docker volume is mapped: `- /data/snapshots:/data/snapshots`
- host has enough free space (at least 50MB)
- container user has directory permissions
