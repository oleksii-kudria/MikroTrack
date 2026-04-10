# TASK-067 - Fix incorrect offline boundary detection causing stale `online_since`

## Контекст

Проблема:

- при переході `offline → online` таймер (`online_since`) інколи НЕ скидається
- особливо проявляється для пристроїв з бейджем `PERM`
- `events` показують коректний `SESSION_STARTED`
- але snapshot продовжує використовувати старий `online_since`

---

## Корінь проблеми

У функції:

app/persistence.py → _resolve_previous_effective_state()

логіка визначення offline-сесії занадто обережна:

has_valid_offline_boundary = previous_offline_since is not None and (
    previous_online_since is None or previous_offline_since >= previous_online_since
)

Через це:

- якщо `online_since` "залип" (старий)
- то навіть при наявності `offline_since`
- система НЕ вважає попередній стан `offline`

В результаті:

offline → online

перетворюється на:

online → online

і таймер не скидається

---

## Що потрібно зробити

### 1. Спрощення логіки offline boundary

### Було:

previous_offline_since = _parse_snapshot_timestamp(previous.get("offline_since"))
previous_online_since = _parse_snapshot_timestamp(previous.get("online_since"))

has_valid_offline_boundary = previous_offline_since is not None and (
    previous_online_since is None or previous_offline_since >= previous_online_since
)

### Має бути:

previous_offline_since = _parse_snapshot_timestamp(previous.get("offline_since"))

has_valid_offline_boundary = previous_offline_since is not None

---

### 2. Видалити залежність від `online_since`

Видалити рядок:

previous_online_since = _parse_snapshot_timestamp(previous.get("online_since"))

---

## Очікувана поведінка

Після змін:

- якщо у snapshot є `offline_since`
→ попередній стан ЗАВЖДИ вважається `offline`

Це гарантує:

offline → online → нова сесія

і:

"online_since": "now"

---

## Вимоги до логування

(англійською)

Лог має залишитись:

Previous snapshot contains offline_since for MAC XX, treating previous effective state as offline

---

## Вимоги до тестування

### Сценарій 1 - reconnect після offline

1. online
2. idle
3. offline (є offline_since)
4. online

Очікування:
- новий `online_since`
- `elapsed_seconds ≈ 0`

---

### Сценарій 2 - PERM пристрій

- ARP = permanent
- той самий сценарій

Очікування:
- нова сесія
- таймер НЕ тягнеться

---

### Сценарій 3 - regression

- online → idle → online (без offline)

Очікування:
- `online_since` НЕ змінюється

---

## Вимоги до документації

Оновити (UA + EN):

- опис того, що `offline_since` є джерелом істини для завершення сесії
- опис lifecycle:
  online → idle → offline → online

---

## Критерії приймання

- `online_since` більше не залипає після reconnect
- `offline → online` завжди створює нову сесію
- `PERM` пристрої працюють так само, як dynamic
- немає regression для idle

---

## Очікуваний результат

Стабільна модель:

online → idle → offline → online

де:

- `offline` = кінець сесії
- новий `online` = нова сесія
- таймер починається з 00:00
