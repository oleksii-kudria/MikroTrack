# TASK-003: Перехід на api-ssl та оновлення README і Python-клієнта

## Мета

- перейти на використання тільки api-ssl (8729)
- виправити права користувача (read,api)
- оновити README
- додати підтримку SSL у Python-клієнті

---

## Що потрібно реалізувати

### 1. Оновити README

Прибрати використання api (8728).

Використовувати тільки api-ssl (8729).

---

### 2. Налаштування MikroTik

#### Увімкнення api-ssl

/ip service enable api-ssl

---

#### Обмеження доступу

/ip service set api-ssl address=YOUR_SERVER_IP/32

---

#### Створення групи

/user group add name=mikrotrack policy=read,api

---

#### Створення користувача

/user add name=mikrotrack password=StrongPassword group=mikrotrack

---

### 3. Генерація сертифіката (ВАЖЛИВО)

Якщо сертифікат відсутній:

#### Створити сертифікат

/certificate add name=api-cert common-name=mikrotik

---

#### Підписати сертифікат

/certificate sign api-cert

---

#### Призначити сертифікат до api-ssl

/ip service set api-ssl certificate=api-cert

---

#### Перевірити

/certificate print

/ip service print detail where name=api-ssl

---

### 4. Оновити .env.example

MIKROTIK_HOST=
MIKROTIK_PORT=8729
MIKROTIK_USERNAME=
MIKROTIK_PASSWORD=
MIKROTIK_USE_SSL=true
MIKROTIK_SSL_VERIFY=false
LOG_LEVEL=INFO

---

### 5. Оновити Python-клієнт

- використовувати SSL
- використовувати порт 8729
- підтримка ssl_verify
- логування SSL

---

### 6. Перевірка

nc -vz MIKROTIK_IP 8729

---

## Очікуваний результат

docker compose up --build

- підключення через api-ssl
- отримання DHCP

---

## Критерії приймання

- працює api-ssl
- README оновлено
- є інструкція генерації сертифіката
- Python клієнт працює через SSL

---

## Далі

TASK-004: ARP + об’єднання DHCP
