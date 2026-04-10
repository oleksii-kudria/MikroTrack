# TASK-081 - Fix naive/aware datetime mismatch in diff timeout logic

## Опис

У MikroTrack diff логіка продовжує падати навіть після виправлень запису events. Аналіз traceback показав точну причину:

```text
TypeError: can't subtract offset-naive and offset-aware datetimes
```

Проблема виникає у `_idle_timeout_exceeded()` під час обчислення:

```python
(now - idle_since).total_seconds()
```

де:
- `now` створюється як naive datetime (`datetime.now()`)
- `idle_since` може бути timezone-aware datetime після парсингу timestamp з timezone, наприклад `+00:00`

Через це diff падає ще до запису events, а `events.jsonl` не створюється.

---

## Що потрібно зробити

### 1. Уніфікувати всі datetime для diff логіки

Усі datetime, які використовуються в:
- `_generate_diff_events()`
- `_resolve_previous_effective_state()`
- `_idle_timeout_exceeded()`
- `_apply_stable_timestamps()`
- `_parse_snapshot_timestamp()`
- `_iso_timestamp()`

мають бути приведені до одного узгодженого формату.

Рекомендований варіант:
- використовувати timezone-aware datetime всюди
- бажано в UTC або через `astimezone()` з явною timezone

---

### 2. Виправити створення `now` у `_generate_diff_events()`

Зараз використовується:

```python
now = datetime.now()
```

Потрібно замінити на timezone-aware варіант, наприклад:

```python
now = datetime.now().astimezone()
```

або:

```python
from datetime import UTC, datetime
now = datetime.now(UTC)
```

---

### 3. Привести `_iso_timestamp()` до timezone-aware формату

Зараз нові timestamp-и створюються без гарантії єдиного timezone формату.

Потрібно зробити так, щоб нові значення:
- `state_changed_at`
- `online_since`
- `idle_since`
- `offline_since`
- event timestamps

завжди записувались в одному форматі, наприклад ISO 8601 з offset:

```text
2026-04-10T19:47:01+00:00
```

---

### 4. Перевірити `_parse_snapshot_timestamp()` на змішані формати

Функція повинна коректно обробляти:
- naive timestamps без timezone
- aware timestamps з `Z`
- aware timestamps з `+00:00`
- порожні значення
- некоректні значення

Важливо:
- на виході повинно бути узгоджене timezone-aware значення
- не можна повертати іноді naive, а іноді aware datetime

---

### 5. Забезпечити backward compatibility зі старими snapshot-ами

У системі вже є snapshot-и зі значеннями типу:

```text
2026-04-10T19:41:29
```

і можуть бути записи типу:

```text
2026-04-10T19:17:28+00:00
```

Після виправлення:
- старі snapshot-и мають продовжити читатись без падіння
- нові snapshot-и мають записуватись у єдиному timezone-aware форматі
- diff не повинен падати при змішаних старих і нових даних

---

### 6. Додати захисні тести

Додати unit tests для сценаріїв:

1. naive previous timestamp + aware now
2. aware previous timestamp + aware now
3. timestamp з `Z`
4. timestamp з `+00:00`
5. timestamp без timezone
6. idle timeout calculation не падає при змішаних старих snapshot-ах

---

## Логи та журнали подій

Усі логи і журнали подій - англійською.

Після виправлення:
- не повинно бути traceback з `offset-naive and offset-aware datetimes`
- diff повинен проходити до кінця
- якщо знайдені events, повинен створюватися `events.jsonl`

Очікувані приклади:

```text
INFO mikrotrack: Diff summary:
INFO mikrotrack: - events: 4
INFO mikrotrack: Events persisted: 4 -> /data/snapshots/events.jsonl
```

---

## Документація

Оновити документацію українською та англійською.

### UA
Описати:
- що всі internal timestamps у diff нормалізовані до timezone-aware формату
- що старі snapshot-и без timezone підтримуються
- що нові snapshot-и записуються в єдиному форматі

### EN
Document:
- all internal diff timestamps are normalized to timezone-aware datetime values
- legacy snapshots without timezone are supported
- new snapshots are persisted in a unified timezone-aware format

---

## Врахування змін у логах та документації

У кожній задачі необхідно враховувати:
- зміни в логах/журналах подій, якщо це потрібно
- зміни в документації українською та англійською

Для цієї задачі це обов'язково.

---

## Критерії приймання

Задача вважається виконаною, якщо:

1. diff більше не падає з помилкою `offset-naive and offset-aware datetimes`
2. `_idle_timeout_exceeded()` стабільно працює для старих і нових snapshot-ів
3. усі нові timestamp-и записуються в єдиному timezone-aware форматі
4. старі snapshot-и без timezone підтримуються без crash
5. при наявності events створюється `events.jsonl`
6. документація оновлена українською та англійською
7. додані unit tests на datetime compatibility

---

## Очікуваний результат

- diff стабільно працює на змішаних snapshot-ах
- timeout logic не падає через datetime mismatch
- `events.jsonl` нарешті створюється, якщо є події
- формат часу в системі стає передбачуваним і консистентним

---

## Додатково

Буде плюсом:
- додати helper типу `_now_aware()` для централізованого отримання поточного часу
- мінімізувати ручну роботу з tzinfo у різних місцях коду
