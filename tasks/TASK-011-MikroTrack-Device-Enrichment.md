# TASK-011: Enrich device model (DHCP + ARP flags, comments, statuses) + bilingual README

## Мета

Розширити модель пристрою для отримання більш повної картини мережі:

- додати DHCP flags та status
- додати ARP flags та status
- додати comments (DHCP + ARP)
- сформувати багату модель пристрою перед persistence
- оновити README (українська + англійська)

---

## Контекст

Зараз модель пристрою містить базові поля:
- MAC
- IP
- hostname

Цього недостатньо для:
- аналізу стану мережі
- розуміння походження запису
- подальшого збереження (persistence)

---

## Що потрібно реалізувати

### 1. Оновити DHCP collector

Файл:
app/collector.py

Додати поля:

- comment
- status
- dynamic
- expires-after (optional)
- last-seen (optional)

Нормалізувати:

{
    "mac_address": "...",
    "ip_address": "...",
    "host_name": "...",
    "comment": "...",
    "status": "bound",
    "dynamic": True
}

---

### 2. Оновити ARP collector

Додати поля:

- comment
- status
- dynamic
- dhcp
- complete
- disabled
- invalid
- published

Нормалізувати:

{
    "mac_address": "...",
    "ip_address": "...",
    "interface": "...",
    "comment": "...",
    "status": "reachable",
    "dynamic": True,
    "dhcp": False,
    "complete": True,
    "disabled": False,
    "invalid": False,
    "published": False
}

---

### 3. Оновити device_builder.py

Об’єднати DHCP + ARP і сформувати:

{
    "mac_address": "...",
    "ip_address": "...",
    "host_name": "...",

    "dhcp_comment": "...",
    "arp_comment": "...",

    "dhcp_status": "...",
    "arp_status": "...",

    "dhcp_flags": {
        "dynamic": True
    },

    "arp_flags": {
        "dynamic": True,
        "dhcp": False,
        "complete": True,
        "disabled": False,
        "invalid": False,
        "published": False
    },

    "source": ["dhcp", "arp"]
}

---

### 4. Додати derived поля (optional, але бажано)

- arp_type:
    - dynamic
    - static
- created_by:
    - dhcp / manual

---

### 5. Логування

INFO:
- DHCP enriched records count
- ARP enriched records count

DEBUG:
- приклад enriched запису
- merge логіка

---

## README update (обов'язково)

README має бути двомовний:

### 🇺🇦 Українською
### 🇬🇧 English

---

### Додати розділ:

## Device Model

Описати:

- що таке DHCP status:
    - waiting
    - offered
    - bound

- що означає DHCP dynamic

- що таке ARP status:
    - reachable
    - stale
    - failed
    - incomplete

- що означають ARP flags:
    - dynamic
    - dhcp
    - complete
    - published
    - invalid
    - disabled

---

### Структура README

README.md:

## 🇺🇦 Українською

(опис)

---

## 🇬🇧 English

(same content in English)

---

## Очікуваний результат

- модель пристрою значно багатша
- видно походження даних
- готово до persistence

---

## Критерії приймання

- DHCP flags додані
- ARP flags додані
- comments додані
- модель пристрою оновлена
- README двомовний
- код простий і зрозумілий

---

## Далі

TASK-012: Persistence (збереження результатів)
