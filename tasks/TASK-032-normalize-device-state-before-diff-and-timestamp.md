# TASK-032 - Normalize device state before diff and timestamp logic

## Контекст

У системі використовуються різні джерела стану пристрою:
- arp_status (reachable, delay, stale, failed, etc.)
- dhcp_status (bound, waiting, etc.)
- bridge_host_present

На даний момент у різних частинах коду використовується як raw статус (arp_status), так і агрегований (arp_state).

Це призводить до:
- флапінгу стану між poll
- некоректного визначення зміни стану
- неправильного оновлення timestamps

## Проблема

Raw значення (наприклад arp_status=delay → reachable → delay) можуть змінюватись, хоча фактичний стан пристрою не змінюється (він як був online, так і є).

Якщо ці значення використовуються в diff/timestamp логіці:
- система помилково фіксує зміну стану
- timestamps скидаються

## Мета

Всі рішення щодо:
- diff
- timestamps
- events

повинні базуватись ТІЛЬКИ на нормалізованому стані:
- online
- idle
- offline
- unknown

## Вимоги

### 1. Ввести єдине поле

```
fused_state = ["online", "idle", "offline", "unknown"]
```

Це єдине джерело істини для:
- diff
- timestamp logic
- event generation

---

### 2. Mapping правил

```
arp_status:
  reachable → online
  delay     → online
  probe     → online
  stale     → idle
  failed    → offline
  incomplete → offline
  unknown   → unknown
```

---

### 3. Використання в коді

Заборонено використовувати в логіці:
- arp_status
- dhcp_status
- raw flags

Дозволено:
- тільки fused_state

---

### 4. Diff logic

```
old_state = previous.fused_state
new_state = current.fused_state
```

І тільки це використовується для визначення:
- state_changed
- timestamp update

---

### 5. Debug logging

```
MAC=XX
arp_status=delay
fused_state=online
decision=normalized
```

---

## Очікуваний результат

- Відсутній флапінг state
- Стабільний diff
- Коректна робота timestamps
