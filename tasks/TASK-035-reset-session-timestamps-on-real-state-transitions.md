# TASK-035 - Reset session timestamps on real state transitions

## Контекст

Після реалізації TASK-034 timestamps почали ініціалізуватись для більшості пристроїв.

Однак виявлено нову проблему:
- якщо пристрій був у стані `offline`
- потім перейшов у `online`
- `online_since` НЕ ініціалізується заново
- `state_changed_at` НЕ оновлюється
- таймер продовжує рахуватись від попереднього offline періоду

Це означає, що система не створює нову session при реальному переході стану.

## Проблема

Поточна логіка, ймовірно, має такий недолік:
- якщо timestamps вже існують, вони preserve-яться
- навіть якщо `old_state != new_state`

Тобто правила `preserve` / `initialize missing timestamps`
спрацьовують раніше, ніж правила реального state transition.

## Мета

Забезпечити коректне скидання / перевстановлення session timestamps
при реальних змінах стану пристрою.

## Вимоги

### 1. Пріоритет логіки

Порядок застосування правил повинен бути таким:

```python
if old_state != new_state:
    apply_transition_rules()

elif timestamps_missing:
    initialize_missing_timestamps()

else:
    preserve_existing_timestamps()
```

Правила `state transition` мають вищий пріоритет, ніж:
- preserve
- initialize missing

---

### 2. Transition: offline -> online

Якщо:

```python
old_state == "offline"
new_state in ["online", "idle"]
```

то ОБОВ’ЯЗКОВО:

```python
online_since = now
state_changed_at = now
offline_since = None
```

---

### 3. Transition: online/idle -> offline

Якщо:

```python
old_state in ["online", "idle"]
new_state == "offline"
```

то ОБОВ’ЯЗКОВО:

```python
offline_since = now
state_changed_at = now
online_since = None
```

---

### 4. Transition: online <-> idle

Якщо:

```python
old_state in ["online", "idle"]
new_state in ["online", "idle"]
```

то:

```python
online_since = old.online_since
offline_since = None
```

`state_changed_at`:
- або оновлювати, якщо треба фіксувати перехід `online -> idle`
- або залишати старе значення, якщо `idle` вважається тією ж online session

Поточне рішення вибрати явно і зафіксувати в коді.

---

### 5. Заборонено

Заборонено зберігати попередні timestamps, якщо state реально змінився:

```python
old_state != new_state
```

Тобто такий сценарій неправильний:

```python
old_state = "offline"
new_state = "online"
decision = preserve_existing_timestamps
```

---

### 6. Debug logging

Додати логування рішення:

```text
MAC=B0:E4:5C:FD:BB:98
old_state=offline
new_state=online
old_online_since=null
old_offline_since=2026-04-08T...
decision=transition_offline_to_online
new_online_since=2026-04-08T...
new_offline_since=null
new_state_changed_at=2026-04-08T...
```

---

### 7. Acceptance Criteria

- при `offline -> online` таймер online починається заново
- при `offline -> online` `Last change` оновлюється
- при `online -> offline` таймер offline починається заново
- timestamps НЕ preserve-яться при реальному state transition
- проблема відтворена та виправлена на прикладі MAC `B0:E4:5C:FD:BB:98`

---

## Очікуваний результат

Система:
- коректно створює нову session при реальній зміні стану
- не продовжує таймер від попереднього offline/online періоду
- правильно оновлює `online_since`, `offline_since`, `state_changed_at`
