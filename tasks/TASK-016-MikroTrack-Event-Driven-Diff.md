# 👉 TASK-016: Event-driven Diff (фіксація змін стану мережі)

## 🎯 Мета

Реалізувати систему diff, яка фіксує КОЖНУ зміну стану пристрою та генерує події.

ВАЖЛИВО:
- Текст задачі — українською
- Логи та повідомлення — англійською
- Документація — українською та англійською

---

## 📦 Обсяг задачі

- Повний diff по атрибутах
- Генерація подій (events)
- Додавання timestamp
- Підготовка до web UI

---

## ⚙️ Вимоги

### 1. Основна логіка

Порівнювати два snapshot:
- попередній
- поточний

Primary key:
- mac_address

---

### 2. Типи подій

#### Presence

[NEW_DEVICE] New device detected: {ip} ({mac})  
[DEVICE_REMOVED] Device disappeared: {ip} ({mac})

---

#### IP / identity

[IP_CHANGED] Device IP changed: {mac} {old_ip} -> {new_ip}  
[HOSTNAME_CHANGED] Hostname changed: {mac} {old} -> {new}

---

#### DHCP

[DHCP_ADDED] DHCP lease appeared  
[DHCP_REMOVED] DHCP lease removed  
[DHCP_DYNAMIC_CHANGED] DHCP dynamic flag changed: {old} -> {new}  
[DHCP_STATUS_CHANGED] DHCP status changed  
[DHCP_COMMENT_CHANGED] DHCP comment changed

---

#### ARP

[ARP_ADDED] ARP entry appeared  
[ARP_REMOVED] ARP entry removed  
[ARP_DYNAMIC_CHANGED] ARP dynamic flag changed  
[ARP_FLAG_CHANGED] ARP flags changed

---

#### Source

[SOURCE_CHANGED] Device source changed: {old} -> {new}

---

#### Combined

[DEVICE_IP_ASSIGNMENT_CHANGED] IP assignment changed: dynamic -> static

---

### 3. Формат події

```json
{
  "timestamp": "2026-04-06T21:17:55",
  "event_type": "DHCP_DYNAMIC_CHANGED",
  "mac": "AA:BB:CC:DD:EE:FF",
  "old_value": true,
  "new_value": false
}
```

---

### 4. Логування

INFO:
- Diff summary

DEBUG:
- всі події

---

### 5. Збереження

Підготовка до:
- events.jsonl
- або окрема директорія events/

---

## 📚 Документація

### English:
- What is event-driven diff
- How events are generated

### Українською:
- Що таке event-driven diff
- Як формуються події

---

## 🧪 Тестування

- новий пристрій → NEW_DEVICE
- зміна IP → IP_CHANGED
- DHCP dynamic → static → DHCP_DYNAMIC_CHANGED
- DHCP → ARP only → SOURCE_CHANGED

---

## ✅ Критерії

- фіксується кожна зміна
- події містять timestamp
- логування працює
- документація EN + UA

---

## 🚀 Результат

Система відслідковує повну історію змін мережі
