# TASK-074 - Preserve last known IP and hostname for offline devices (DHCP expired)

## Контекст

Сценарій:

1. Пристрій (наприклад iPhone) підключається до мережі
2. Отримує:
   - MAC: 6E:7B:C9:CC:5A:81
   - IP: 192.168.101.12
   - hostname: iPhone
3. Через деякий час відключається → переходить в `offline`
4. Пізніше DHCP сервер видаляє lease
5. У новому snapshot:
   - `ip = ""`
   - `hostname = ""`
   - зникає корисна інформація

---

## Проблема

Після видалення DHCP lease:

- втрачається IP
- втрачається hostname
- у UI залишається тільки MAC + offline

Це ускладнює:
- аналіз
- ідентифікацію пристрою
- історію підключень

---

## Мета задачі

Забезпечити збереження останніх відомих значень:

- `ip`
- `hostname`

для пристроїв у статусі `offline`, навіть після зникнення DHCP запису.

---

## Що потрібно зробити

### 1. Зберігати last known values

Якщо у новому snapshot:

```
ip == "" OR hostname == ""
```

але у попередньому snapshot були значення:

- використовувати попередні значення як fallback

---

### 2. Ввести нові поля (рекомендовано)

Додати:

```
last_known_ip
last_known_hostname
```

або використовувати існуючі поля з маркером

---

### 3. Логіка збереження

При обробці snapshot:

```
if device is offline:
    if current.ip is empty:
        device.ip = previous.ip
        mark as "stale"

    if current.hostname is empty:
        device.hostname = previous.hostname
        mark as "stale"
```

---

### 4. Додати маркер "stale data"

Щоб користувач розумів, що дані не актуальні:

#### Варіанти:
- badge:
  ```
  [STALE]
  ```
- або:
  ```
  IP (last known)
  ```
- або сірий/приглушений колір

---

## Вимоги до UI

### 1. Відображення

Якщо дані збережені:

- показувати IP та hostname
- додати візуальний індикатор:
  - сірий текст
  - або badge `STALE`
  - або tooltip

---

### 2. Tooltip (рекомендовано)

Hover:

```
Last seen IP before DHCP lease expired
```

---

## Вимоги до логування

(англійською)

Додати:

- `Preserving last known IP for MAC ...`
- `Preserving last known hostname for MAC ...`
- `Marking device data as stale`

---

## Вимоги до тестування

### Сценарій 1 - DHCP lease зник

1. пристрій online
2. має IP + hostname
3. переходить offline
4. DHCP видаляє запис

Очікування:
- IP зберігається
- hostname зберігається
- є маркер "stale"

---

### Сценарій 2 - нове підключення

1. пристрій знову online
2. отримує новий IP

Очікування:
- IP оновлюється
- маркер "stale" зникає

---

### Сценарій 3 - відсутність попередніх даних

- якщо даних не було → нічого не підставляти

---

## Вимоги до документації

Оновити (UA + EN):

- пояснення last known data
- поведінка при DHCP expiration
- опис маркеру "stale"

---

## Критерії приймання

- IP не зникає після DHCP expiration
- hostname не зникає
- є візуальний маркер
- дані оновлюються при новому підключенні
- немає регресії для online пристроїв

---

## Очікуваний результат

offline пристрій виглядає так:

```
iPhone
192.168.101.12   [STALE]
offline
```

і користувач розуміє, що це останні відомі дані
