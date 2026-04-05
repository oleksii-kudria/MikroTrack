# TASK-008: ARP table + об’єднання DHCP (модель пристрою)

## Мета

Реалізувати базову модель пристрою шляхом об’єднання даних з:

- DHCP (ip → hostname)
- ARP (ip ↔ mac)

Результат:
→ отримати список реальних пристроїв у мережі

---

## Контекст

DHCP:
- показує лише клієнтів, які отримали IP

ARP:
- показує всі активні пристрої (включно зі статичними IP)

Разом:
→ повна картина мережі

---

## Що потрібно реалізувати

### 1. Отримання ARP

Файл:
app/collector.py

Функція:

def get_arp_entries(api) -> list[dict]:

Джерело:
"/ip/arp"

---

### 2. Нормалізація ARP

Перетворити:

- mac-address → mac_address
- address → ip_address

Результат:

{
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "ip_address": "192.168.88.10",
    "interface": "bridge"
}

---

### 3. Створити device_builder

Файл:
app/device_builder.py

Функція:

def build_devices(dhcp: list, arp: list) -> list[dict]:

---

### 4. Логіка об’єднання

Ключ:
→ mac_address

Правила:

- якщо MAC є в DHCP → беремо hostname
- якщо тільки ARP → hostname=""
- якщо IP різні:
    → використовувати ARP як актуальний

---

### 5. Формат результату

[
    {
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "ip_address": "192.168.88.10",
        "host_name": "laptop",
        "source": ["dhcp", "arp"]
    },
    {
        "mac_address": "11:22:33:44:55:66",
        "ip_address": "192.168.88.50",
        "host_name": "",
        "source": ["arp"]
    }
]

---

### 6. Оновити main.py

dhcp = get_dhcp_leases(api)
arp = get_arp_entries(api)
devices = build_devices(dhcp, arp)

---

### 7. Логування

INFO:
- ARP entries fetched: X
- Devices built: X

DEBUG:
- raw ARP count
- sample ARP entry
- merge steps

---

## Обмеження

НЕ потрібно:

- база даних
- API
- складна логіка дедуплікації

---

## Очікуваний результат

docker compose up

→ отримуєш список пристроїв, а не тільки DHCP

---

## Критерії приймання

- ARP отримується
- DHCP + ARP об’єднуються
- є список пристроїв
- код простий
- логування відповідає TASK-007

---

## Далі

TASK-009: Bridge host table + LLDP/MNDP
