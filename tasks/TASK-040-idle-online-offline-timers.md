# TASK-040 - Separate timers for Online, Idle, and Offline states

## Контекст

Наразі UI відображає:

- Online: <timer>
- Idle since: <time>
- Offline: <timer>

Але існує проблема:

- коли пристрій переходить у стан `idle`, основний таймер продовжує рахуватися як `Online`
- це не відображає реальну поведінку пристрою
- немає чіткого розділення часу для кожного стану

## Мета

Розділити таймери для кожного стану:

- Online
- Idle
- Offline

та відображати їх незалежно один від одного.

---

## Вимоги

### 1. Заміна тексту

Якщо:

```
state == "idle"
```

відображати:

```
Idle: <timer>
```

замість:

```
Online: <timer>
```

---

### 2. Окремі таймери

Ввести три незалежні поля:

```
online_since
idle_since
offline_since
```

---

### 3. Логіка переходів

#### a) online → idle

```
idle_since = now
```

- online_since НЕ змінюється
- idle timer починається з 0

---

#### b) idle → online

```
idle_since = null
```

- online_since НЕ змінюється
- пристрій повертається до тієї ж online сесії

---

#### c) online/idle → offline

```
offline_since = now
idle_since = null
```

---

#### d) offline → online

```
online_since = now
offline_since = null
```

---

### 4. Відображення в UI

#### Online

```
Online: 00:10:25
```

#### Idle

```
Idle: 00:02:15
```

#### Offline

```
Offline: 00:05:12
```

---

### 5. Tooltip (опціонально)

При наведенні:

```
Online since: 18:10
Idle since: 18:20
Offline since: 18:30
```

---

### 6. Acceptance Criteria

- при переході в idle таймер починається з 0
- текст змінюється з Online → Idle
- online_since не скидається при idle
- offline логіка працює як раніше
- UI чітко показує поточний стан

---

## Очікуваний результат

- оператор бачить реальний стан пристрою:
  - скільки він активний
  - коли він став idle
  - коли він офлайн

- покращується аналітика поведінки пристроїв
