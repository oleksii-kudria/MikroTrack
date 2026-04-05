# MikroTrack DHCP Collector

Сервіс підключається до MikroTik через RouterOS API, отримує DHCP leases і виводить результат у форматі JSON.

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
- `MIKROTIK_PORT` — порт API (`8728` для `api`, `8729` для `api-ssl`).
- `MIKROTIK_USERNAME` — користувач MikroTik.
- `MIKROTIK_PASSWORD` — пароль користувача.
- `LOG_LEVEL` — рівень логування (`INFO` за замовчуванням).

## Налаштування MikroTik

### 1. Дозволити доступ до API лише з IP сервера

Приклад (замінити IP):

```routeros
/ip service set api address=192.168.1.100/32
```

або якщо потрібно `api-ssl`:

```routeros
/ip service set api-ssl address=192.168.1.100/32
```

### 2. Створити користувача для MikroTrack

```routeros
/user group add name=mikrotrack policy=read,!write,!policy,!test,!password,!sniff,!sensitive,!romon
/user add name=mikrotrack password=StrongPassword group=mikrotrack
```

### 3. Перевірити доступ

З сервера:

```bash
telnet MIKROTIK_IP 8728
```

або

```bash
nc -vz MIKROTIK_IP 8728
```

### 4. Рекомендації безпеки

- використовувати окремого користувача;
- не використовувати `admin`;
- обмежити доступ по IP;
- по можливості використовувати `api-ssl` (`8729`).
