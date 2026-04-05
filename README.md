# MikroTrack DHCP Collector

Сервіс підключається до MikroTik через RouterOS `api-ssl` (порт `8729`), отримує DHCP leases і виводить результат у форматі JSON.

## Швидкий старт

1. Створіть `.env` файл на основі прикладу:

```bash
cp .env.example .env
```

2. Заповніть параметри доступу до MikroTik у `.env`.

3. Запустіть застосунок:

```bash
docker compose up --build
```

## Змінні середовища

- `MIKROTIK_HOST` — адреса MikroTik.
- `MIKROTIK_PORT` — порт API SSL (`8729` за замовчуванням).
- `MIKROTIK_USERNAME` — користувач MikroTik.
- `MIKROTIK_PASSWORD` — пароль користувача.
- `MIKROTIK_USE_SSL` — увімкнути SSL (`true` за замовчуванням).
- `MIKROTIK_SSL_VERIFY` — перевіряти TLS-сертифікат (`false` за замовчуванням).
- `LOG_LEVEL` — рівень логування (`INFO` за замовчуванням).

## Налаштування MikroTik

### 1. Увімкнути api-ssl

```routeros
/ip service enable api-ssl
```

### 2. Обмежити доступ до api-ssl лише з IP сервера

Приклад (замінити IP на адресу вашого сервера):

```routeros
/ip service set api-ssl address=192.168.1.100/32
```

### 3. Створити групу та користувача для MikroTrack

```routeros
/user group add name=mikrotrack policy=read,api
/user add name=mikrotrack password=StrongPassword group=mikrotrack
```

### 4. Згенерувати сертифікат для api-ssl (якщо ще немає)

```routeros
/certificate add name=api-cert common-name=mikrotik
/certificate sign api-cert
/ip service set api-ssl certificate=api-cert
```

Перевірка:

```routeros
/certificate print
/ip service print detail where name=api-ssl
```

### 5. Перевірити доступ

З сервера:

```bash
nc -vz MIKROTIK_IP 8729
```

### 6. Рекомендації безпеки

- використовувати окремого користувача;
- не використовувати `admin`;
- обмежити доступ по IP;
- використовувати тільки `api-ssl` (`8729`).
