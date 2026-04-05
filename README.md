# MikroTrack

## 🇺🇦 Українською

MikroTrack підключається до MikroTik через RouterOS `api-ssl` (порт `8729`), збирає DHCP leases та ARP записи, збагачує модель пристрою і повертає JSON.

### Швидкий старт

1. Створіть `.env` файл:

```bash
cp .env.example .env
```

2. Заповніть параметри доступу до MikroTik.
3. Запустіть сервіс:

```bash
docker compose up --build
```

### Змінні середовища

- `MIKROTIK_HOST` — адреса MikroTik.
- `MIKROTIK_PORT` — порт API SSL (`8729` за замовчуванням).
- `MIKROTIK_USERNAME` — користувач MikroTik.
- `MIKROTIK_PASSWORD` — пароль користувача.
- `MIKROTIK_USE_SSL` — увімкнути SSL (`true` за замовчуванням).
- `MIKROTIK_SSL_VERIFY` — перевіряти TLS-сертифікат (`false` за замовчуванням).
- `LOG_LEVEL` — рівень логування (`INFO` за замовчуванням).
- `PRINT_RESULT_TO_STDOUT` — друк JSON у stdout (`true` за замовчуванням).
- `RUN_MODE` — режим (`once` або `loop`, за замовчуванням `once`).
- `COLLECTION_INTERVAL` — інтервал циклічного збору в секундах (`60` за замовчуванням).

### Device Model

MikroTrack будує єдину модель пристрою з DHCP + ARP:

- базові поля: `mac_address`, `ip_address`, `host_name`, `source`
- коментарі: `dhcp_comment`, `arp_comment`
- стани: `dhcp_status`, `arp_status`
- прапори: `dhcp_flags`, `arp_flags`
- похідні поля: `arp_type`, `created_by`

#### DHCP status

- `waiting` — очікує на підтвердження/видачу
- `offered` — адресу запропоновано клієнту
- `bound` — адресу видано та активна прив’язка

#### DHCP dynamic

- `true` — динамічний lease, створений DHCP сервером
- `false` — статичний lease

#### ARP status

- `reachable` — хост доступний
- `stale` — запис застаріває
- `failed` — не вдалося підтвердити доступність
- `incomplete` — неповний ARP запис

#### ARP flags

- `dynamic` — динамічний ARP запис
- `dhcp` — запис походить з DHCP
- `complete` — ARP запис повний
- `published` — published/proxy ARP
- `invalid` — недійсний запис
- `disabled` — запис вимкнений

### Scheduler / Continuous Collection

У режимі `loop` MikroTrack працює безперервно, не зупиняється на помилках і продовжує наступну ітерацію після логування помилки.

---

## 🇬🇧 English

MikroTrack connects to MikroTik using RouterOS `api-ssl` (port `8729`), collects DHCP leases and ARP entries, enriches the device model, and returns JSON output.

### Quick start

1. Create `.env`:

```bash
cp .env.example .env
```

2. Fill in MikroTik access settings.
3. Run the service:

```bash
docker compose up --build
```

### Environment variables

- `MIKROTIK_HOST` — MikroTik address.
- `MIKROTIK_PORT` — API SSL port (`8729` by default).
- `MIKROTIK_USERNAME` — MikroTik username.
- `MIKROTIK_PASSWORD` — MikroTik password.
- `MIKROTIK_USE_SSL` — enable SSL (`true` by default).
- `MIKROTIK_SSL_VERIFY` — verify TLS certificate (`false` by default).
- `LOG_LEVEL` — logging level (`INFO` by default).
- `PRINT_RESULT_TO_STDOUT` — print JSON to stdout (`true` by default).
- `RUN_MODE` — mode (`once` or `loop`, default `once`).
- `COLLECTION_INTERVAL` — loop interval in seconds (`60` by default).

### Device Model

MikroTrack builds a single enriched device model from DHCP + ARP:

- base fields: `mac_address`, `ip_address`, `host_name`, `source`
- comments: `dhcp_comment`, `arp_comment`
- statuses: `dhcp_status`, `arp_status`
- flags: `dhcp_flags`, `arp_flags`
- derived fields: `arp_type`, `created_by`

#### DHCP status

- `waiting` — waiting for confirmation/assignment
- `offered` — address offered to a client
- `bound` — address is assigned and active

#### DHCP dynamic

- `true` — dynamic lease created by DHCP server
- `false` — static lease

#### ARP status

- `reachable` — host is reachable
- `stale` — entry is aging
- `failed` — reachability confirmation failed
- `incomplete` — incomplete ARP entry

#### ARP flags

- `dynamic` — dynamic ARP entry
- `dhcp` — entry comes from DHCP
- `complete` — ARP entry is complete
- `published` — published/proxy ARP entry
- `invalid` — invalid entry
- `disabled` — entry is disabled

### Scheduler / Continuous Collection

In `loop` mode, MikroTrack continuously collects data, logs errors, and keeps running on the next iteration.
