# TASK-070 - Remove special handling for PERM and unify state logic

## Контекст

Поточна логіка для пристроїв з бейджем `PERM` (ARP `permanent`) створює зайву складність та призводить до серії багів:

- хибні переходи `offline -> online`
- циклічний reset `online_since`
- циклічний reset `offline_since`
- неузгодженість між `arp_state`, `fused_state`, `status`, `active`
- окремі special-case правила, які ускладнюють підтримку коду

З практичної точки зору `PERM` означає лише те, що запис ARP є статичним / permanent.  
Це має бути **metadata**, а не окрема поведінка state machine.

---

## Мета задачі

Прибрати special handling для `PERM` у backend-логіці та перевести його в звичайний `STATIC`-тип запису без окремих правил для життєвого циклу станів.

---

## Цільова модель

### 1. ARP тип = metadata
Тип ARP-запису (`dynamic`, `static`, `permanent`) повинен використовуватись:
- для відображення в UI
- для badge/flags
- для технічної інформації

Але НЕ повинен:
- впливати на session lifecycle
- змінювати state transitions
- створювати special-case для reconnect/offline

### 2. Єдина state machine для всіх пристроїв

Стан визначається однаково для всіх:

- `online` - є валідна ознака присутності
- `idle` - немає нової активності, але ще не timeout
- `offline` - timeout / відсутність evidence

### 3. Джерела істини для presence
Визначення стану повинно базуватись на реальних ознаках присутності, а не на типі ARP запису:

- `bridge_host_present`
- валідний ARP status / evidence
- timeout rules
- session timestamps

---

## Що потрібно зробити

### 1. Прибрати special-case для `arp_status == "permanent"`

Знайти і прибрати всі місця, де `permanent` обробляється окремо як логічний special-case.

Зокрема перевірити:
- `app/persistence.py`
- `app/arp_logic.py`
- `app/api/main.py`
- інші місця, де є:
  - `arp_status == "permanent"`
  - `"PERM"`
  - окрема логіка для static/permanent ARP

### 2. Прибрати вплив PERM на state machine

Заборонити таку поведінку:
- `permanent -> idle` тільки тому, що запис permanent
- `offline -> idle -> online` через special-case rules
- окремий reconnect logic лише для PERM

### 3. Замінити PERM на STATIC як metadata

У відображенні та badges:

- замість `PERM` використовувати `STATIC`  
або
- залишити технічне поле `permanent` внутрішньо, але badge для користувача відображати як `STATIC`

Рекомендовано:
- у UI та API використовувати єдину термінологію `STATIC`
- не створювати окрему user-facing категорію `PERM`

### 4. Уніфікувати логіку визначення state

Переглянути `_derive_device_state()` та пов’язані функції.

Очікування:
- тип ARP запису не змінює логіку стану сам по собі
- state залежить лише від presence evidence

### 5. Уніфікувати логіку transition

Правила переходів повинні бути однаковими для всіх пристроїв:

- `online -> idle`
- `idle -> offline`
- `offline -> online`

Без special-case для:
- `PERM`
- `permanent`
- static ARP

### 6. Перевірити узгодженість API

Після змін:
- `status`
- `flags.state`
- `arp_state`
- `active`
- `online_since`
- `offline_since`

не повинні суперечити одне одному.

---

## Вимоги до логування

Усі логи англійською.

Додати або оновити логи так, щоб було видно:

- що `permanent` більше не впливає на state logic
- що пристрій обробляється загальними правилами
- що STATIC використовується як metadata

Приклади:
- `ARP permanent entry is treated as STATIC metadata for MAC ...`
- `State resolved using generic presence rules for MAC ...`

---

## Вимоги до журналів подій

Перевірити та за потреби оновити генерацію подій:

- `state_changed`
- `session_started`
- `session_ended`
- `device_online`
- `device_idle`
- `device_offline`

Очікування:
- події не повинні залежати від PERM special-case
- послідовність подій повинна бути однаковою для static і dynamic записів

У цій задачі обов’язково врахувати, чи потрібні зміни:
- в журнали подій
- у генерацію подій
- у назви / metadata подій, якщо там фігурує `PERM`

---

## Вимоги до API / UI

### API
Перевірити, що API повертає:
- узгоджений `status`
- коректні timers
- `STATIC` як metadata замість `PERM`, якщо це обраний формат

### UI
Перевірити:
- badge / label
- фільтрацію
- сортування
- відображення details

Очікування:
- користувач бачить `STATIC`, а не `PERM`
- логіка інтерфейсу не залежить від старого PERM special-case

---

## Вимоги до тестування

### Сценарій 1 - static/permanent запис без bridge_host
1. пристрій online
2. bridge host зникає
3. далі idle
4. далі offline

Очікування:
- жодного хибного reconnect
- timers не скидаються циклічно

### Сценарій 2 - static/permanent запис з реальним reconnect
1. offline
2. пристрій реально повертається
3. з’являється валідна ознака присутності

Очікування:
- новий `online_since`
- коректний `session_started`

### Сценарій 3 - dynamic ARP
Перевірити, що динамічні записи працюють без regression.

### Сценарій 4 - API consistency
Перевірити, що:
- `status`
- `flags.state`
- `arp_state`
- `active`

узгоджені між собою.

### Сценарій 5 - UI metadata
Перевірити, що badge відображається як `STATIC`, якщо це новий user-facing формат.

---

## Вимоги до документації

Оновити документацію українською та англійською.

Оновити:
- опис state machine
- опис presence evidence
- опис ARP metadata
- пояснення, що `permanent` / static ARP більше не має special behavior
- опис того, як тепер відображається `STATIC`

У цій задачі обов’язково врахувати, чи потрібні зміни:
- в документацію
- в приклади API
- в опис UI badge/flags
- в опис журналів подій

---

## Критерії приймання

Задача вважається виконаною, якщо:

- special-case логіка для `PERM` прибрана
- `permanent` більше не впливає на state machine
- `STATIC` використовується як metadata / user-facing label
- немає false reconnect
- немає циклічного reset `online_since`
- немає циклічного reset `offline_since`
- API повертає узгоджені значення
- UI коректно показує STATIC badge
- тести покривають static і dynamic сценарії
- документація оновлена українською та англійською

---

## Очікуваний результат

Система працює з єдиною моделлю станів для всіх пристроїв:

online -> idle -> offline -> online

де:
- тип ARP запису є metadata
- `STATIC` не має special behavior
- presence / timers / session lifecycle працюють однаково для всіх типів пристроїв
