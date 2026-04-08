# TASK-024 - Online Detection using Bridge Host + ARP Fusion

## Опис (UA)

Поточна логіка визначення Online/Offline базується лише на ARP, що є недостатнім у випадках:
- статичних ARP записів (permanent)
- клієнтів за сторонніми точками доступу (TP-Link, інші AP)
- відсутності ARP активності при фактичному підключенні

У таких сценаріях ARP не відображає реальний стан пристрою.

---

## Мета (UA)

Реалізувати точне визначення Online/Offline через об'єднання (fusion):

1. ARP (L3 сигнал)
2. Bridge Host table (L2 присутність)

---

## Definitions (EN)

### ARP
- status: reachable, stale, delay, probe, failed, incomplete, permanent

### Bridge Host
- mac
- interface
- last-seen (optional)

---

## 1. Джерела даних (UA)

Система ПОВИННА використовувати:

- /ip arp
- /interface bridge host

---

## 2. Evidence Model (EN)

```python
device.evidence = {
    "arp_status": ...,
    "bridge_host_present": True/False,
    "bridge_host_last_seen": timestamp (optional)
}
```

---

## 3. Основна логіка визначення Online (UA)

```python
if arp.status == "reachable":
    state = "online"

elif bridge_host_present:
    state = "online"

elif arp.status in ["stale", "delay", "probe"]:
    state = "idle"

elif arp.status in ["failed", "incomplete"]:
    state = "offline"

elif arp.status == "permanent":
    if bridge_host_present:
        state = "online"
    else:
        state = "permanent"

else:
    state = "unknown"
```

---

## 4. Важливі правила (UA)

- bridge host = L2 presence (ключовий сигнал)
- ARP reachable = найвищий пріоритет
- permanent НЕ означає online
- bridge host може містити застарілі записи

---

## 5. Freshness (UA) [Optional]

```python
if bridge_host_present and last_seen < 60:
    state = "online"
else:
    state = "idle"
```

---

## 6. UI Requirements (UA)

- ONLINE → green
- IDLE → gray
- OFFLINE → red
- PERMANENT → gray + badge PERM

---

## 7. Events (EN)

System MUST generate:

- device_online
- device_offline
- device_idle
- evidence_changed

Example:

```json
{
  "type": "device_online",
  "mac": "20:37:A5:87:2A:13",
  "reason": "bridge_host_detected",
  "timestamp": "..."
}
```

---

## 8. Вплив на журнали подій (UA)

НЕОБХІДНО:

- додати поле reason:
  - arp_reachable
  - bridge_host_detected
- логувати зміну стану пристрою

---

## 9. Вплив на документацію (UA)

Оновити:

- Device state logic
- Online detection rules
- Data sources (ARP + Bridge Host)

---

## 10. Acceptance Criteria (UA)

- пристрій за TP-Link визначається як online
- permanent + bridge_host → online
- відсутні false offline
- відсутні false online при відсутності evidence

---

## Результат (UA)

Система коректно визначає Online стан:
- незалежно від типу підключення
- без активного сканування
- тільки на основі пасивних даних
