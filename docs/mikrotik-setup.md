# MikroTrack – MikroTik Setup Guide (API-SSL + User + Certificate)

## 🇺🇦 Українською

### 1. Створення користувача

Створити окремого користувача для MikroTrack:

```bash
/user add name=mikrotrack password=StrongPassword group=read
```

Додати необхідні права:

```bash
/user group set read policy=read,api
```

> ⚠️ Не використовуй admin користувача

---

### 2. Увімкнення API-SSL

Вимкнути небезпечний API (без шифрування):

```bash
/ip service disable api
```

Увімкнути API-SSL:

```bash
/ip service enable api-ssl
/ip service set api-ssl port=8729
```

Обмежити доступ тільки з IP сервера:

```bash
/ip service set api-ssl address=192.168.36.100/32
```

---

### 3. Генерація сертифіката

Створити сертифікат:

```bash
/certificate add name=mikrotrack-cert common-name=mikrotik
```

Підписати сертифікат:

```bash
/certificate sign mikrotrack-cert
```

Перевірити статус (має бути "issued"):

```bash
/certificate print
```

---

### 4. Призначити сертифікат для API-SSL

```bash
/ip service set api-ssl certificate=mikrotrack-cert
```

---

### 5. Перевірка

```bash
/ip service print
```

Очікувано:

- api → disabled
- api-ssl → enabled (port 8729)

---

## 🇬🇧 English

### 1. Create user

Create a dedicated user for MikroTrack:

```bash
/user add name=mikrotrack password=StrongPassword group=read
```

Grant required permissions:

```bash
/user group set read policy=read,api
```

> ⚠️ Do not use admin account

---

### 2. Enable API-SSL

Disable insecure API:

```bash
/ip service disable api
```

Enable secure API:

```bash
/ip service enable api-ssl
/ip service set api-ssl port=8729
```

Restrict access to server IP only:

```bash
/ip service set api-ssl address=192.168.36.100/32
```

---

### 3. Generate certificate

Create certificate:

```bash
/certificate add name=mikrotrack-cert common-name=mikrotik
```

Sign certificate:

```bash
/certificate sign mikrotrack-cert
```

Verify status:

```bash
/certificate print
```

---

### 4. Assign certificate

```bash
/ip service set api-ssl certificate=mikrotrack-cert
```

---

### 5. Verification

```bash
/ip service print
```

Expected:

- api → disabled
- api-ssl → enabled (port 8729)

---

## Notes

- Replace `StrongPassword` with a secure password
- Replace `192.168.36.100` with your server IP
- Ensure firewall allows access to port 8729
- If you see `access_denied`, verify `/ip service api-ssl address` includes collector IP
- If you see `authentication_failed`, verify user credentials and policy (`read,api`)
