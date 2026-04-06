# 👉 TASK-014: Надійність збереження (Storage robustness & validation)

## 🎯 Мета

Покращити надійність механізму збереження (persistence) та додати перевірки, щоб уникнути втрати даних.

ВАЖЛИВО:
- Текст задачі — українською
- Логи та повідомлення — англійською
- Документація — українською та англійською

---

## 📦 Обсяг задачі

- Перевірка шляху збереження
- Автоматичне створення директорії
- Перевірка прав доступу
- Перевірка вільного місця
- Покращене логування
- Оновлення документації

---

## ⚙️ Вимоги

### 1. Перевірка шляху

[PERSISTENCE_ERROR] Persistence path is not writable or does not exist  
Recommendation: Verify volume mapping and directory permissions on host

---

### 2. Автостворення директорії

[PERSISTENCE_ERROR] Failed to create persistence directory  
Recommendation: Check permissions or create directory manually on host

---

### 3. Перевірка запису

[PERSISTENCE_ERROR] Persistence path is not writable  
Recommendation: Check filesystem permissions and Docker volume mapping

---

### 4. Перевірка місця

[LOW_DISK_SPACE] Available disk space is low (<50MB)  
Recommendation: Clean up old snapshots or increase storage

---

### 5. Логування

Persistence enabled: true  
Persistence path: /data/snapshots  

---

### 6. Попередження про volume

WARNING: Persistence path may not be mounted to host  
Recommendation: Verify docker-compose volume mapping

---

## 🐳 Docker

```yaml
volumes:
  - /data/snapshots:/data/snapshots
```

---

## 📚 Документація

### English:
- What is persistence path
- Container vs host
- Volume config

### Українською:
- Що таке PERSISTENCE_PATH
- Різниця контейнер/хост
- Як налаштувати volume

---

## ✅ Критерії

- Є перевірка шляху
- Є помилки з рекомендаціями
- Є логування
- Документація EN + UA
