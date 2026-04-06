# 👉 TASK-015: Snapshot Diff (аналіз змін)

## 🎯 Мета

Реалізувати механізм порівняння snapshot'ів для виявлення змін у мережі.

ВАЖЛИВО:
- Текст задачі — українською
- Логи та повідомлення — англійською
- Документація — українською та англійською

---

## 📦 Обсяг задачі

- Завантаження попереднього snapshot
- Порівняння з поточним
- Виявлення змін
- Формування подій
- Логування результатів
- Оновлення документації

---

## ⚙️ Вимоги

### 1. Завантаження snapshot

- знайти попередній snapshot у директорії
- якщо немає — пропустити diff

Лог:

[DIFF_SKIPPED] No previous snapshot found

---

### 2. Порівняння даних

Порівнювати devices:

- MAC (primary key)
- IP
- hostname

---

### 3. Типи подій

#### Новий пристрій

[NEW_DEVICE] New device detected: {ip} ({mac})

#### Видалений пристрій

[DEVICE_REMOVED] Device disappeared: {ip} ({mac})

#### Зміна IP

[IP_CHANGED] Device IP changed: {mac} {old_ip} -> {new_ip}

#### Зміна hostname

[HOSTNAME_CHANGED] Hostname changed: {mac} {old} -> {new}

---

### 4. Логування

INFO:

Diff summary:
- new: X
- removed: X
- changed: X

DEBUG:

деталі кожної події

---

### 5. Обробка помилок

[DIFF_ERROR] Failed to process snapshots  
Recommendation: Verify snapshot format and integrity

---

## 📚 Документація

### English:
- What is snapshot diff
- How changes are detected

### Українською:
- Що таке diff snapshot
- Як визначаються зміни

---

## 🧪 Тестування

- запуск без snapshot → skip
- додати новий пристрій → NEW_DEVICE
- змінити IP → IP_CHANGED
- видалити пристрій → DEVICE_REMOVED

---

## ✅ Критерії

- diff працює коректно
- всі події логуються
- є summary
- документація EN + UA

---

## 🚀 Результат

Система починає відслідковувати зміни в мережі
