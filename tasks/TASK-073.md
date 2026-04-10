# TASK-073 - Refactor toolbar layout to logical flow (Filters → Mode → Summary → Actions)

## Контекст

Після впровадження TASK-071/072 toolbar став функціонально правильним, але порядок елементів не оптимальний з точки зору UX.

Обраний варіант: **Filters → Mode → Summary → Actions**

Також важливе уточнення:

> Значення `Devices:` НЕ повинно залежати від filters  
> Воно повинно залежати ТІЛЬКИ від обраного режиму (End / All)

---

## Мета задачі

- впорядкувати toolbar згідно логічного UX-потоку
- розділити:
  - filters (впливають на список)
  - mode (визначає dataset)
  - summary (відображає dataset)
- прибрати логічну плутанину

---

## Цільовий layout

```
[ ONLINE ] [ STATIC ]  Clear ✕   |   [ End | All ]   Devices: X | 🟢x 🟡x 🟣x 🔴x   |   ⇅ ⟳   Auto [ON]
```

---

## Логіка блоків

### 1. Filters (ліворуч)
```
[ ONLINE ] [ STATIC ]  Clear ✕
```

- впливають тільки на відображення списку
- НЕ впливають на Devices summary

---

### 2. Mode (після filters)
```
[ End | All ]
```

- визначає dataset
- впливає на:
  - список пристроїв
  - Devices summary

---

### 3. Devices summary (після Mode)

```
Devices: X | 🟢x 🟡x 🟣x 🔴x
```

---

## ⚠️ ВАЖЛИВЕ ПРАВИЛО

Devices summary:

### НЕ залежить від filters

Filters:
- ONLINE
- STATIC
- RANDOM
- і т.д.

НЕ повинні змінювати:

```
Devices: X
```

---

## Залежність тільки від Mode

### Mode = End
```
Devices = кількість End devices
```

### Mode = All
```
Devices = кількість ВСІХ devices
```

---

## Приклад

### Mode = End + Filters = ONLINE
```
Devices: 10   ← (ВСІ End devices)
таблиця: 3 записи (бо filter)
```

---

### Mode = All + Filters = OFFLINE
```
Devices: 41   ← (ВСІ devices)
таблиця: 27 записів (бо filter)
```

---

## 4. Actions (праворуч)

```
⇅ ⟳   Auto [ON]
```

- Sort
- Refresh
- Auto toggle

---

## Що потрібно зробити

### 1. Перерозташувати toolbar

Було:
```
Filters | Actions | Mode | Summary
```

Має бути:
```
Filters | Mode | Summary | Actions
```

---

### 2. Відокремити summary від filters

Переконатись, що:

```
summary = dataset (mode)
НЕ = filtered dataset
```

---

### 3. Перевірити data flow

```
Mode → визначає dataset
Filters → фільтрують UI
Summary → показує dataset
```

---

### 4. Вирівнювання

- один рядок
- рівні відступи
- логічні блоки

---

## Вимоги до UX

- логіка читається зліва направо
- filters не впливають на summary
- mode впливає на summary
- швидке розуміння стану системи

---

## Вимоги до тестування

### 1. Filters НЕ впливають на summary
- змінити filters
- Devices НЕ змінюється

---

### 2. Mode впливає на summary
- End → одне значення
- All → інше значення

---

### 3. Комбінації

- End + filters
- All + filters

Summary має змінюватись тільки при зміні Mode

---

### 4. Layout

- всі елементи в один ряд
- правильний порядок

---

## Вимоги до документації

Оновити (UA + EN):

- опис toolbar flow
- опис ролі Mode
- опис ролі Filters
- пояснення summary logic

---

## Критерії приймання

- toolbar у порядку: Filters → Mode → Summary → Actions
- summary не залежить від filters
- summary залежить від Mode
- UI виглядає логічно та передбачувано
- немає regression

---

## Очікуваний результат

Інтерфейс працює як:

```
Filters → уточнюють список
Mode → визначає дані
Summary → показує загальну картину
Actions → керують поведінкою
```
