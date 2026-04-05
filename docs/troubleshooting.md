# Troubleshooting

## 🇺🇦 Українською

## connection refused

Симптоми:

- неможливо підключитись до `MIKROTIK_HOST:MIKROTIK_PORT`
- socket error з "connection refused"

Перевірки:

- на MikroTik увімкнено `api-ssl`
- порт вказаний правильно (типово `8729`)
- firewall дозволяє вхідне з'єднання з collector host
- IP allow-list для сервісу MikroTik містить адресу collector

## ssl error

Симптоми:

- помилка TLS handshake
- certificate verify failed

Перевірки:

- `MIKROTIK_USE_SSL=true`
- на MikroTik сертифікат призначений на `api-ssl`
- для self-signed сертифіката: `MIKROTIK_SSL_VERIFY=false` або правильна довіра до CA
- дата/час роутера коректні

## authentication failed

Симптоми:

- логін відхилено
- authentication error у логах

Перевірки:

- `MIKROTIK_USERNAME` та `MIKROTIK_PASSWORD` правильні
- акаунт не вимкнено
- користувач має мінімум права `read`, `api`

## not allowed (9)

Симптоми:

- RouterOS API повертає `not allowed (9)`

Причина:

- користувачу бракує прав для запитаного path/command

Виправлення:

- перевірити policy групи (мінімум `read,api`)
- уникати надмірно обмеженої custom-групи
- перевірити доступ до команди напряму в RouterOS terminal

---

## 🇬🇧 English

## connection refused

Symptoms:

- cannot connect to `MIKROTIK_HOST:MIKROTIK_PORT`
- socket error with "connection refused"

Checks:

- MikroTik service `api-ssl` is enabled
- port is correct (default `8729`)
- firewall allows inbound connection from collector host
- IP allow-list on MikroTik service includes collector address

## ssl error

Symptoms:

- TLS handshake failure
- certificate verify failed

Checks:

- `MIKROTIK_USE_SSL=true`
- MikroTik has certificate assigned to `api-ssl`
- if using self-signed certificate, set `MIKROTIK_SSL_VERIFY=false` or trust CA properly
- router date/time are correct (important for certificate validation)

## authentication failed

Symptoms:

- login rejected
- authentication error in logs

Checks:

- `MIKROTIK_USERNAME` and `MIKROTIK_PASSWORD` are correct
- account is not disabled
- user has enough policy rights (`read`, `api`)

## not allowed (9)

Symptoms:

- RouterOS API returns `not allowed (9)`

Root cause:

- user lacks permissions for requested path/command

Fix:

- verify group policies include at least `read,api`
- avoid using over-restricted custom group
- test command access directly in RouterOS terminal
