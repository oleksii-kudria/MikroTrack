# TASK-080 - Fix event serialization crash

## Опис

У системі MikroTrack diff логіка виявляє зміни між snapshot-ами, але після цього падає з помилкою `[DIFF_ERROR] Failed to process snapshots`, а файл `events.jsonl` не створюється.

Логи підтверджують, що події вже генеруються, наприклад:

```text
diff: detected change field=dhcp_comment mac=44:86:09:32:41:CF old=okudr-laptop new=okudr-laptop1
```

але після цього diff завершується помилкою до моменту запису `events.jsonl`.

Найімовірніша причина - одна або кілька подій містять значення, які не серіалізуються через `json.dumps(...)`, наприклад:
- `datetime`
- `set`
- `bytes`
- вкладені несеріалізуємі об'єкти
- інші нестандартні типи Python

Потрібно виправити серіалізацію events так, щоб:
- diff не падав
- проблемні значення безпечно нормалізувались
- помилка діагностувалась швидко через логи
- `events.jsonl` стабільно створювався при наявності events

---

## Що потрібно зробити

### 1. Додати safe serialization для events

Перед записом кожної події в `events.jsonl` потрібно гарантувати, що event повністю JSON-serializable.

Реалізувати helper, наприклад:

```python
def _make_json_safe(value: Any) -> Any:
    ...
```

Він повинен коректно обробляти:
- `datetime` -> `isoformat()`
- `set` / `tuple` -> `list`
- `bytes` -> UTF-8 string або repr
- `dict` -> рекурсивна нормалізація значень
- `list` -> рекурсивна нормалізація
- прості типи (`str`, `int`, `float`, `bool`, `None`) -> без змін
- інші типи -> `str(value)`

---

### 2. Нормалізувати весь event перед `json.dumps`

Перед записом в `_append_events()`:

```python
safe_event = _make_json_safe(event)
events_file.write(json.dumps(safe_event, ensure_ascii=False) + "\n")
```

---

### 3. Додати точне логування serialization errors

Якщо навіть після нормалізації конкретний event не серіалізується, лог повинен містити:
- event type
- MAC
- сам event або його safe preview
- повний stack trace

Приклад логів англійською:

```text
ERROR mikrotrack: Failed to serialize event event_type=FIELD_CHANGE mac=44:86:09:32:41:CF
ERROR mikrotrack: Event payload: {...}
```

І бажано:
```python
logger.exception(...)
```

---

### 4. Не ковтати справжню причину помилки без деталей

Зараз у логах видно лише:

```text
[DIFF_ERROR] Failed to process snapshots
```

Потрібно покращити діагностику:
- залишити high-level помилку
- але додати debug/exception лог з реальною причиною
- щоб наступного разу було видно stack trace, а не тільки загальне повідомлення

---

### 5. Перевірити, що `events.jsonl` створюється після виправлення

Після фіксу потрібно підтвердити:
- якщо diff виявив хоча б одну подію
- і серіалізація пройшла успішно
- файл `events.jsonl` створюється автоматично

---

## Логи та журнали подій

Усі логи і журнали подій - англійською.

Очікувані приклади:

```text
INFO mikrotrack: diff: detected change field=dhcp_comment mac=44:86:09:32:41:CF old=okudr-laptop new=okudr-laptop1
INFO mikrotrack: Events persisted: 1 -> /data/snapshots/events.jsonl
```

У випадку помилки:

```text
ERROR mikrotrack: Failed to serialize event event_type=FIELD_CHANGE mac=44:86:09:32:41:CF
ERROR mikrotrack: Event payload: {...}
Traceback ...
```

---

## Документація

Оновити документацію українською та англійською.

### UA
Описати:
- що events проходять safe serialization перед записом
- які типи значень нормалізуються
- як тепер виглядає діагностика serialization errors

### EN
Document:
- safe event serialization before JSONL persistence
- supported normalization rules for complex Python types
- improved diagnostics for serialization failures

---

## Врахування змін у логах та документації

У кожній задачі необхідно враховувати:
- зміни в логах/журналах подій, якщо це потрібно
- зміни в документації українською та англійською

Для цієї задачі це обов'язково.

---

## Критерії приймання

Задача вважається виконаною, якщо:

1. усі events проходять через safe normalization перед `json.dumps`
2. diff більше не падає на serialization problem
3. при наявності events створюється `events.jsonl`
4. у випадку помилки є детальний log з причиною і stack trace
5. документація оновлена українською та англійською
6. існуючі формати events не ламаються

---

## Очікуваний результат

- diff стабільно завершується без crash на serialization
- `events.jsonl` створюється при першому непорожньому diff
- проблемні типи даних більше не валять persistence
- діагностика стає прозорою і швидкою

---

## Додатково

Буде плюсом:
- додати unit tests для `_make_json_safe()` на випадки:
  - `datetime`
  - `set`
  - `tuple`
  - `bytes`
  - nested dict/list
  - unknown custom object
