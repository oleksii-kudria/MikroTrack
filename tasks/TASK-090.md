# TASK-090 - Add UI regression tests for sorting, filters, mode, and summary behavior

## Опис

Перед переходом до Phase 2 потрібно додати мінімальний набір UI regression tests для найбільш критичної поведінки Web UI.

Після останніх змін UI вже має складну, але важливу логіку:

- mode (`End` / `All`)
- filters
- summary
- single-column sorting
- default sorting
- special handling for `unknown`
- залежність UI від стабільної backend/device schema

Ця логіка вже кілька разів змінювалась, тому без regression tests існує високий ризик знову зламати:
- сортування
- summary counts
- mode visibility
- filter behavior
- `unknown` ordering

Ця задача вводить мінімальний набір UI tests для захисту ключової поведінки перед Phase 2.

---

## Що потрібно зробити

### 1. Додати UI regression test framework

Якщо вже є тестовий стек для web UI - використати його.

Якщо немає, додати мінімально достатній варіант для перевірки UI behavior, наприклад:
- unit/component tests
- або integration tests для table/toolbar logic

Мета:
- перевіряти поведінку UI
- не тестувати все підряд
- покрити саме найбільш критичну логіку

---

### 2. Тести для default sorting

Перевірити, що коли explicit sorting не обрано, порядок такий:

1. `online`
2. `idle`
3. `offline`
4. `unknown`

Усередині груп:
- `online` -> `online_since`
- `idle` -> `idle_since`
- `offline` -> `offline_since`
- `unknown` -> alphabetical only

Очікування:
- порядок стабільний
- `unknown` не намагається сортуватися по даті

---

### 3. Тести для explicit single-column sorting

Перевірити:
- ascending
- descending

Для мінімум таких колонок:
- hostname / name
- ip
- status
- time-related column (якщо sortable)

Очікування:
- активне лише одне сортування
- multi-column sorting не виникає
- повторний клік циклічно змінює state `none -> asc -> desc`

---

### 4. Тести для mode (`End` / `All`)

Перевірити:

#### End mode
- приховує `BRIDGE`
- приховує `COMPLETE`
- приховує `INTERFACE`
- приховує `unknown`

#### All mode
- показує всі записи

Очікування:
- dataset реально змінюється
- summary рахується правильно для mode dataset

---

### 5. Тести для summary behavior

Перевірити, що:

- `Devices: X | ...` залежить тільки від current mode dataset
- summary НЕ залежить від active filters
- filters впливають тільки на rows in table
- mode впливає і на summary, і на rows

Це дуже критична поведінка.

---

### 6. Тести для filters

Перевірити:

- активний filter зменшує таблицю
- summary не змінюється
- `Clear` прибирає filters
- filter badge clickable
- direct badge remove працює, якщо це вже реалізовано

---

### 7. Тести для `unknown`

Окремо перевірити:

- `unknown` hidden in End mode
- `unknown` visible in All mode
- `unknown` default ordering only alphabetical
- відсутність fallback до time sorting

---

### 8. Тести для empty/null values

Перевірити:
- `online_since = null`
- `idle_since = null`
- `offline_since = null`
- порожній hostname
- порожній ip

Очікування:
- UI не падає
- sorting deterministic
- rows render стабільно

---

### 9. Тести для contract assumptions

Мінімально перевірити, що UI коректно працює з полями:
- `status`
- `state_changed_at`
- `online_since`
- `idle_since`
- `offline_since`
- `last_known_ip`
- `last_known_hostname`
- stale flags

Це повинно допомогти вловити регресії API/UI contract.

---

## Логи та журнали подій

Усі user-facing тексти та test-related messages - англійською.

---

## Документація

Оновити документацію українською та англійською.

Описати:
- які UI behaviors покриті regression tests
- як запускати ці тести
- які сценарії вважаються критичними

---

## Врахування змін у логах та документації

У кожній задачі необхідно враховувати:
- зміни в логах/журналах подій, якщо це потрібно
- зміни в документації українською та англійською

Для цієї задачі потрібно оновити документацію по тестах.

---

## Критерії приймання

Задача вважається виконаною, якщо:

1. додано UI regression tests framework або використано наявний
2. є тести для default sorting
3. є тести для explicit single-column sorting
4. є тести для mode (`End` / `All`)
5. є тести для summary behavior
6. є тести для filters
7. є окремі тести для `unknown`
8. є перевірка empty/null scenarios
9. документація оновлена українською та англійською

---

## Очікуваний результат

- критична поведінка UI захищена від регресій
- sorting / filters / mode / summary більше не ламаються непомітно
- перед Phase 2 фронтова частина стає значно стабільнішою

---

## Додатково

Буде плюсом:
- додати test dataset fixtures
- винести reusable helper для rendering table with mocked API payload
