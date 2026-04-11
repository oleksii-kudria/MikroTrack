# TASK-085 - Add minimal unit tests for critical diff and state logic

## Опис

Перед переходом до Phase 2 необхідно додати мінімальний набір unit tests для найбільш критичних частин системи MikroTrack.

Зараз логіка:
- event-driven diff
- timezone-aware datetime
- state transitions
- MAC fallback
- last-known fields

є складною і вже кілька разів ламалась при змінах.

Ця задача вводить базовий рівень тестів для запобігання регресіям.

---

## Що потрібно зробити

### 1. Додати test framework

Якщо ще не використовується:
- додати `pytest`

Структура:

```text
tests/
  test_diff.py
  test_datetime.py
  test_mac_index.py
  test_state_logic.py
```

---

### 2. Тести для MAC fallback

Перевірити:

- тільки `mac_address`
- тільки `mac`
- обидва поля
- відсутність обох

Очікування:
- індексація працює
- device не губиться
- warning лог при відсутності MAC

---

### 3. Тести для datetime logic

Критично перевірити:

- naive timestamp
- aware timestamp (`+00:00`)
- `Z` формат
- змішані snapshot-и

Очікування:
- немає exception
- `_idle_timeout_exceeded()` працює стабільно

---

### 4. Тести для state transitions

Сценарії:

- online → idle
- idle → offline
- online → offline
- offline → online

Перевірити:
- state
- state_changed_at
- відповідні *_since поля

---

### 5. Тести для extended diff

Перевірити генерацію:

- `FIELD_CHANGE`
- `state_changed`
- `IP_CHANGED`
- `HOSTNAME_CHANGED`

Очікування:
- події створюються
- містять правильні поля
- previous/current значення коректні

---

### 6. Тести для last-known fields

Сценарій:

- пристрій offline
- DHCP запис зник

Очікування:
- `last_known_ip` збережений
- `ip_is_stale=True`
- UI-ready поведінка

---

### 7. Тести для events serialization

Перевірити:

- datetime
- set
- tuple
- bytes
- nested dict

Очікування:
- `json.dumps` не падає
- дані нормалізуються

---

## Логи

Логи тестів не обов'язкові, але:

- не повинно бути traceback
- помилки повинні чітко показувати причину

---

## Документація

Оновити:

### UA
- як запускати тести
- які сценарії покриті

### EN
- how to run tests
- covered critical logic areas

---

## Критерії приймання

1. додано pytest
2. є тести для:
   - MAC fallback
   - datetime
   - state transitions
   - diff events
   - serialization
3. тести проходять (`pytest`)
4. немає crash у критичних сценаріях
5. документація оновлена

---

## Очікуваний результат

- критична логіка захищена від регресій
- нові зміни не ламають diff
- швидка діагностика проблем

---

## Додатково

Буде плюсом:
- додати CI запуск тестів
