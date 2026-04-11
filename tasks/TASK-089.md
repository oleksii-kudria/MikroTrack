# TASK-089 - Normalize logging policy and separate expected conditions from real errors

## Опис

Перед переходом до Phase 2 необхідно привести logging policy у MikroTrack до єдиного, передбачуваного стандарту.

Зараз логи вже дуже корисні, але в системі все ще є ризики:

- expected conditions інколи виглядають як помилки
- warning/error рівні можуть використовуватись непослідовно
- схожі ситуації можуть логуватись у різному стилі
- оператору інколи складно швидко відрізнити шум від реально критичної проблеми

Ця задача не додає новий функціонал. Її мета - зробити логи консистентними, практичними і зручними для експлуатації та діагностики.

---

## Що потрібно зробити

### 1. Визначити єдину logging policy

Потрібно документовано зафіксувати, що саме логувати як:

- `DEBUG`
- `INFO`
- `WARNING`
- `ERROR`

Має бути просте правило:

#### DEBUG
Для:
- внутрішніх технічних деталей
- trace/debug інформації
- розширених деталей diff
- внутрішніх рішень state machine
- службових details, які потрібні в основному розробнику

#### INFO
Для:
- нормального progress flow
- старту/завершення циклів
- summary
- expected runtime behavior
- важливих, але не помилкових operational messages

#### WARNING
Для:
- часткових проблем
- expected degraded behavior
- optional capability mismatch
- non-fatal conditions
- ситуацій, коли система продовжує працювати, але щось варто перевірити

#### ERROR
Для:
- реальних збоїв
- падіння ключового етапу
- ситуацій, коли результат циклу частково або повністю невалідний
- persistence/diff/API failures, які впливають на роботу системи

---

### 2. Відокремити expected conditions від real errors

Потрібно пройтися по ключових логах і привести їх до правильної категорії.

Приклади expected conditions:
- unsupported `/interface/wireless`
- відсутність optional data source
- перший запуск без попереднього snapshot
- відсутність events при відсутності змін

Ці ситуації не повинні виглядати як аварія.

---

### 3. Уніфікувати формат повідомлень

Потрібно привести логи до одного стилю:

- коротко
- технічно
- без двозначності
- без зайвого шуму
- з однаковою логікою формулювання

Бажано уникати випадкового змішування:
- plain English text
- bracket-style event labels
- різних стилів опису одних і тих самих сценаріїв

Потрібно або залишити нинішній стиль, або привести всі ключові повідомлення до одного шаблону.

---

### 4. Нормалізувати progress logs

Для основних runtime flows потрібно забезпечити стабільні INFO логи:

- application started
- collection cycle started
- data collected
- devices built
- diff processed
- snapshot saved
- retention cleanup done
- API started

Це має виглядати як передбачуваний operational flow.

---

### 5. Нормалізувати diff/error logs

Потрібно окремо перевірити логи для:

- diff summary
- diff skipped
- diff error
- event serialization issues
- persistence errors

Мета:
- щоби одразу було видно, що сталося
- щоби error logs містили суть проблеми
- щоби traceback/debug details були там, де вони реально потрібні

---

### 6. Нормалізувати collector capability logs

Для optional або platform-dependent resources:
- wireless interfaces
- unsupported API branches
- optional data collection

Потрібно мати єдину логіку:
- expected unsupported capability -> DEBUG/INFO
- real fetch problem -> WARNING/ERROR

---

### 7. Зменшити шум від повторюваних повідомлень

Якщо одне й те саме повідомлення з'являється дуже часто і не несе нової користі, потрібно оцінити:
- чи залишати його в INFO
- чи опустити в DEBUG
- чи агрегувати через summary
- чи логувати лише при зміні стану

Особливо це стосується:
- repeated offline preservation messages
- expected capability skips
- recurring stable-state messages

---

### 8. Оновити документацію по logging policy

Потрібно додати документацію українською та англійською:
- як читати логи
- що вважати expected behavior
- що вважати warning
- що вважати real error
- як використовувати log levels у runtime

---

## Логи та журнали подій

Усі логи та user-facing повідомлення - англійською.

Ця задача прямо стосується логів, тому потрібно перевірити:
- узгодженість message style
- правильне використання log levels
- відсутність misleading warnings/errors

---

## Документація

Оновити документацію українською та англійською.

Мінімально:
- `README.md` (за потреби короткий summary)
- `docs/troubleshooting.md`
- окремий розділ або документ про logging policy, якщо це доцільно

---

## Врахування змін у логах та документації

У кожній задачі необхідно враховувати:
- зміни в логах/журналах подій, якщо це потрібно
- зміни в документації українською та англійською

Для цієї задачі це є основною суттю.

---

## Критерії приймання

Задача вважається виконаною, якщо:

1. визначено і впроваджено єдину logging policy
2. expected conditions не виглядають як critical errors
3. warning/error використовуються послідовно
4. ключові runtime flows мають стабільні INFO logs
5. collector capability mismatch logs нормалізовані
6. шум від повторюваних повідомлень зменшений
7. документація оновлена українською та англійською

---

## Очікуваний результат

- логи стають більш чистими і передбачуваними
- оператору простіше бачити реальні проблеми
- expected runtime behavior не створює зайвої паніки
- система готова до Phase 2 з більш зрілою operational visibility

---

## Додатково

Буде плюсом:
- додати коротку таблицю `log level -> usage`
- додати приклади correct vs incorrect log classification
