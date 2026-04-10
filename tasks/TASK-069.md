# TASK-069 - Preserve offline_since for PERM devices while remaining offline

## Контекст

Після виконання TASK-068 поведінка для PERM пристроїв покращилась:

- більше немає хибного переходу `offline → online`
- статус `offline` відображається коректно

Але з’явилась нова проблема:

- при кожному оновленні snapshot:
  - `offline_since` інколи перезаписується
  - `state_changed_at` оновлюється
  - таймер (`offline_duration_seconds`) скидається на `00:00`

---

## Симптоми

Пристрій:

- фізично відключений
- стабільно знаходиться у стані `offline`

Але:

- `offline_since` змінюється кожні ~30 секунд
- `offline_duration_seconds` починається заново

---

## Корінь проблеми

Для PERM пристроїв:

- `_derive_device_state()` може повертати `idle`
- додаткова логіка перетворює це в `offline`

У результаті:

offline (previous) → idle (raw) → offline (normalized)

Система трактує це як новий перехід:

online/idle → offline

хоча насправді стан не змінювався.

---

## Що потрібно зробити

### 1. Заборонити повторний transition у offline

Додати перевірку:

if previous_effective_state == "offline" and merge_current_state == "offline":
    # НЕ новий transition

---

### 2. Зберігати попередні timestamps

У цьому випадку потрібно:

device["state_changed_at"] = previous_state_changed_at
device["offline_since"] = previous_offline_since

---

### 3. Не запускати блок transition

Гарантувати, що при:

offline → offline

НЕ виконується логіка:

device["offline_since"] = now_iso
device["state_changed_at"] = now_iso

---

## Вимоги до логування

(англійською)

Додати:

- Device remains offline, preserving offline_since for MAC ...
- Skipping offline transition, state unchanged

---

## Вимоги до тестування

### Сценарій 1 - стабільний offline

1. пристрій offline
2. кілька циклів snapshot

Очікування:
- `offline_since` НЕ змінюється
- `state_changed_at` НЕ змінюється
- `offline_duration_seconds` зростає

---

### Сценарій 2 - PERM пристрій

- ARP = permanent
- без bridge_host

Очікування:
- стабільний offline
- без reset таймера

---

### Сценарій 3 - реальний reconnect

1. offline
2. device online

Очікування:
- новий `online_since`
- новий `state_changed_at`

---

## Вимоги до документації

Оновити (UA + EN):

- опис того, що offline є стабільним станом
- пояснення, що offline не повинен “перезапускатись”
- опис правил session boundary

---

## Критерії приймання

- `offline_since` більше не скидається при кожному циклі
- `offline_duration_seconds` росте стабільно
- немає повторних transition у той самий стан
- PERM пристрої поводяться стабільно
- reconnect працює коректно

---

## Очікуваний результат

Система працює так:

online → idle → offline → offline → offline

і тільки при реальному підключенні:

offline → online

Без повторного створення offline-сесії та без reset таймера
