# TASK-029 - Live timers and tooltip absolute timestamps in UI

## Опис (UA)

Поточний UI відображає час як статичний текст, що оновлюється тільки після poll колектора.

Проблеми:
- немає живого відліку
- значення "стрибають" раз на 60 сек
- немає нормального UX

---

## Мета (UA)

1. Live таймери
2. Tooltip з абсолютним часом
3. Використання raw timestamps
4. Незалежність від poll

---

## Data Input (EN)

```json
{
  "state": "online",
  "online_since": "2026-04-08T16:08:00+03:00",
  "state_changed_at": "2026-04-08T16:10:00+03:00",
  "offline_since": null
}
```

---

## 1. Live Timer Logic (UA)

Frontend рахує час сам:

- Date.now()
- raw timestamps

---

## 2. Display Rules (UA)

### online
Timer: від online_since  
Tooltip: Online since: HH:MM

### idle
Timer: від online_since  
Tooltip:
- Online since
- Idle since

### offline
Timer: від offline_since  
Tooltip: Offline since

### last change
Timer: від state_changed_at  
Tooltip: Last change

---

## 3. Формат (UA)

< 1h → MM:SS  
>= 1h → HH:MM:SS  
>= 1 day → "1 day ago"

---

## 4. Tooltip (UA)

При hover:

Online since: 16:08  
Last change: 16:10  

---

## 5. UI Behavior (UA)

- update кожну секунду
- без reload
- без API виклику

---

## 6. Rendering (EN)

```javascript
setInterval(() => {
  updateTimers()
}, 1000)
```

---

## 7. Constraints (UA)

- не використовувати formatted backend strings
- не перераховувати timestamps
- тільки raw значення

---

## 8. API Expectations (EN)

Backend MUST return:

- online_since
- state_changed_at
- offline_since

---

## 9. Документація (UA + EN)

UA:
- live timers
- tooltip behavior

EN:
- relative time rendering
- absolute timestamp tooltip

---

## 10. Acceptance Criteria (UA)

- таймер змінюється щосекунди
- немає "стрибань"
- tooltip показує абсолютний час
- коректний формат часу

---

## Результат (UA)

UI стає живим і зручним
