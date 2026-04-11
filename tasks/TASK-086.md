# TASK-086 - Define and document stable API contract for Web UI

## Опис

Перед переходом до Phase 2 необхідно зафіксувати стабільний API contract між backend (collector/API) та Web UI.

Зараз UI сильно залежить від структури snapshot/device model, але цей контракт не формалізований:
- які поля гарантовано присутні
- які можуть бути null
- які є derived
- які можуть змінюватися

Це створює ризик:
- поломки UI при зміні backend
- неочевидної поведінки при refactor
- дублювання логіки між frontend/backend

Ця задача вводить чіткий і документований API contract.

---

## Що потрібно зробити

### 1. Зафіксувати device schema (API response)

Описати всі поля, які повертає API для одного пристрою:

Категорії:

#### Core identity
- mac
- ip
- hostname

#### State
- status
- state_changed_at
- online_since
- idle_since
- offline_since

#### Last-known
- last_known_ip
- last_known_hostname
- ip_is_stale
- hostname_is_stale
- data_is_stale

#### Flags
- dhcp_flag
- arp_flag
- source
- has_dhcp_lease
- has_arp_entry

#### Derived/UI fields
- comments
- comments_badge
- badges
- entity_type
- active

---

### 2. Позначити тип кожного поля

Для кожного поля визначити:

- type (string, number, boolean, array, null)
- required / optional
- nullable (true/false)
- description

---

### 3. Розділити raw vs derived поля

Потрібно чітко позначити:

- raw (з collector)
- computed (з diff/state logic)
- UI helper fields

Це критично для подальшого розвитку API.

---

### 4. Визначити гарантії API

Backend повинен гарантувати:

- стабільну структуру відповіді
- однакові назви полів
- передбачувані null значення
- відсутність "іноді є / іноді нема" полів

---

### 5. Визначити поведінку для null значень

Наприклад:

- unknown → всі *_since = null
- offline → online_since = null
- ip відсутній → last_known_ip використовується

Це має бути описано явно.

---

### 6. Документувати sorting dependencies

UI sorting залежить від:

- status
- *_since
- hostname / ip

Потрібно зафіксувати:
- які поля використовуються для sorting
- які гарантуються backend

---

### 7. Документувати API endpoint

Описати:

- endpoint (наприклад `/api/devices`)
- формат відповіді
- приклад response

---

## Приклад device object

```json
{
  "mac": "AA:BB:CC:DD:EE:FF",
  "ip": "192.168.1.10",
  "hostname": "laptop",
  "status": "online",
  "online_since": "2026-04-10T19:00:00+00:00",
  "idle_since": null,
  "offline_since": null,
  "state_changed_at": "2026-04-10T19:00:00+00:00",
  "last_known_ip": "192.168.1.10",
  "ip_is_stale": false
}
```

---

## Логи

Усі логи англійською.

---

## Документація

Оновити:

### UA
- опис API contract
- пояснення полів
- гарантії

### EN
- API contract definition
- field descriptions
- guarantees

---

## Критерії приймання

1. задокументовано повний device schema
2. визначено типи полів
3. описано null behavior
4. розділено raw/derived/UI fields
5. описано API endpoint
6. документація UA + EN

---

## Очікуваний результат

- UI більше не залежить від "випадкових" змін backend
- API стає стабільним контрактом
- зменшується ризик регресій при Phase 2

---

## Додатково

Буде плюсом:
- оформити як OpenAPI / JSON schema
