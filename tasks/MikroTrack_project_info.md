# MikroTrack - Passive Network Visibility Appliance for MikroTik

## 1. Концепція проєкту (основа)

**MikroTrack - це локальний апаратно-програмний комплекс для пасивного спостереження за мережею, інвентаризації пристроїв та виявлення аномалій у середовищах з MikroTik.**

Ключова ідея:
- ❗ **тільки пасивне спостереження**
- ❗ **жодного активного сканування**
- ❗ **локальне збереження даних (local-first)**
- ❗ **розгортання як "коробочного" рішення (appliance)**

---

## 2. Принципи системи

### 🔹 Passive-first
Система не виконує:
- Nmap
- ICMP sweep
- TCP/UDP scanning
- активне опитування кінцевих пристроїв

Система використовує лише:
- телеметрію MikroTik
- мережеві події
- NetFlow
- (у майбутньому) mirror traffic

---

### 🔹 Local-first
- всі дані зберігаються локально
- немає залежності від SaaS
- немає передачі даних у хмару
- підходить для закритих мереж

---

### 🔹 Appliance model
- готовий mini PC (MikroTrack Box)
- Linux + Docker
- мінімальне налаштування
- запуск "з коробки"

---

## 3. Архітектура розвитку

### 🔹 Етап 1 - 1 LAN + NetFlow (поточний)
- робота як passive observer
- збір даних з MikroTik
- аналіз поведінки через NetFlow

### 🔹 Етап 2 - 2 LAN (майбутнє)
- додавання sensor інтерфейсу
- mirror/SPAN
- passive packet analysis (DHCP, ARP, mDNS)

---

## 4. Джерела даних (пасивні)

### Основні:
- DHCP leases
- ARP table
- bridge host table
- neighbor discovery (MNDP/CDP/LLDP)

### Додаткові:
- NetFlow (ключовий на старті)
- Syslog
- SNMP

### Майбутні:
- mirrored traffic (через 2 LAN)

---

## 5. NetFlow як основний сенсор (Етап 1)

Використання:
- аналіз поведінки
- визначення "шлюзів"
- виявлення NAT
- виявлення аномалій

Обмеження:
- немає MAC
- немає DHCP
- немає L2

---

## 6. Функціональні можливості

### Інвентаризація:
- список пристроїв
- IP/MAC/hostname
- історія активності

### Random MAC detection:
- locally administered MAC
- поведінкова кореляція

### Rogue device detection:
- багато MAC за портом
- NetFlow поведінка
- LLDP/CDP/MNDP

---

## 7. Майбутнє розширення (2 LAN)

Додається:
- повний passive L2 аналіз
- DHCP detection (100%)
- mDNS/LLMNR/NetBIOS
- точна класифікація пристроїв

---

## 8. Компоненти системи

- Collector (MikroTik API + NetFlow)
- Flow Processor
- Enrichment Engine
- PostgreSQL
- Backend API
- Web UI

---

## 9. Веб-інтерфейс

- Active devices
- NetFlow analytics
- Random MAC
- Suspicious devices
- History

---

## 10. Розгортання

```
docker compose up -d
```

---

## 11. Підсумок

MikroTrack:
- не сканує мережу
- не створює шум
- не потребує агентів
- працює локально
- швидко розгортається

👉 Це **passive network intelligence система для MikroTik мереж**
