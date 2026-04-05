# TASK-002: Підключення до MikroTik API та отримання DHCP leases

## Мета

Додати першу прикладну функціональність:

- підключення до MikroTik через API
- отримання DHCP leases
- виведення результату

---

## Що потрібно реалізувати

### 1. Оновити структуру

.
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── logging_config.py
│   ├── mikrotik_client.py
│   ├── collector.py
│   └── main.py
├── docker/
├── docker-compose.yml
├── requirements.txt
└── README.md

---

### 2. Конфігурація (.env)

Додати:

MIKROTIK_HOST=
MIKROTIK_PORT=8728
MIKROTIK_USERNAME=
MIKROTIK_PASSWORD=
LOG_LEVEL=INFO

---

### 3. MikroTik client

Реалізувати простий клієнт:

- підключення через API
- обробка помилок
- закриття з’єднання
- logging

---

### 4. DHCP collector

Функція повинна повертати:

[
    {
        "address": "192.168.88.10",
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "host_name": "laptop-01",
        "status": "bound",
        "server": "defconf"
    }
]

---

### 5. main.py

- ініціалізація логування
- завантаження конфіг
- підключення до MikroTik
- отримання DHCP
- логування кількості записів
- вивід JSON

---

### 6. requirements.txt

Додати бібліотеку для RouterOS API

---

## README (ВАЖЛИВО)

Додати розділ:

### Налаштування MikroTik

#### 1. Дозволити доступ до API лише з IP сервера

Приклад (замінити IP):

/ip service set api address=192.168.1.100/32

або якщо потрібно api-ssl:

/ip service set api-ssl address=192.168.1.100/32

---

#### 2. Створити користувача для MikroTrack

/user group add name=mikrotrack policy=read,!write,!policy,!test,!password,!sniff,!sensitive,!romon

/user add name=mikrotrack password=StrongPassword group=mikrotrack

---

#### 3. Перевірити доступ

З сервера:

telnet MIKROTIK_IP 8728

або

nc -vz MIKROTIK_IP 8728

---

#### 4. Рекомендації безпеки

- використовувати окремого користувача
- не використовувати admin
- обмежити доступ по IP
- по можливості використовувати api-ssl (8729)

---

## Обмеження

НЕ додавати:

- PostgreSQL
- FastAPI
- ARP
- NetFlow

---

## Очікуваний результат

docker compose up --build

- підключення до MikroTik
- отримання DHCP
- вивід JSON

---

## Критерії приймання

- працює підключення до MikroTik
- DHCP повертається
- є README з налаштуванням MikroTik
- код простий і зрозумілий

---

## Далі

TASK-003: ARP + об’єднання з DHCP
