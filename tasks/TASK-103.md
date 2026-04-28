# TASK-103 - Display mac_vendor under hostname in device table UI

## Опис задачі

Поле `mac_vendor` вже присутнє у unified device model та API, але наразі не відображається в UI.

Необхідно додати відображення `mac_vendor` у таблиці пристроїв таким чином, щоб інтерфейс залишався компактним та читабельним.

Прийняте рішення:
- НЕ додавати окрему колонку `Vendor`
- НЕ перевантажувати колонку `MAC`
- показувати `mac_vendor` другим рядком під `Hostname`

---

## Ціль задачі

Після виконання задачі оператор повинен швидко розуміти:

- хто виробник пристрою
- чи це endpoint
- чи це потенційний network device
- чи це IoT пристрій
- чи hostname відсутній, але vendor допомагає ідентифікувати пристрій

---

## Поточний вигляд

Зараз колонка:

`Hostname`

показує:

```text
IPHONE-okudr
DESKTOP-FEDV38V
Galaxy-Tab-A8
-
```

---

## Новий вигляд

Колонка `Hostname` повинна виглядати так:

```text
IPHONE-okudr
Apple, Inc.
```

```text
DESKTOP-FEDV38V
Intel Corporate
```

```text
-
TP-Link Technologies
```

---

## UI правила

### Якщо `mac_vendor != null`

Показувати:

- другим рядком
- дрібнішим шрифтом
- muted / gray text
- без окремих badge

---

### Якщо `mac_vendor == null`

Нічого не показувати.

Відображати лише hostname.

---

### Якщо `is_random_mac == true`

Vendor НЕ показувати.

Причина:
- random MAC може вводити в оману
- vendor lookup для random MAC менш надійний

---

## UI стилізація

Рекомендовано:

- smaller font
- muted text color
- без сильного контрасту

Наприклад:

```css
font-size: 12px;
color: #6b7280;
```

Стиль має відповідати поточному UI.

---

## Responsive behavior

Необхідно переконатися:

- таблиця не стає ширшою
- layout не ламається на ноутбуках
- mobile/tablet view не деградує

---

## Sorting behavior

Поточне сортування по `Hostname` не змінювати.

Vendor НЕ повинен впливати на поточний sorting logic.

---

## Search behavior

Поточний search/filter logic не змінювати в межах цієї задачі.

Пошук по vendor буде окремою задачею при необхідності.

---

## Вплив на API

Змін в API НЕ потрібно.

Поле вже існує.

---

## Вплив на журнали подій (LOGGING)

Змін у logging не потрібно.

Логи залишаються англійською.

---

## Вплив на документацію

Необхідно оновити документацію українською та англійською.

Описати:

- де відображається `mac_vendor`
- чому vendor не показується для random MAC
- як це допомагає в ідентифікації пристроїв

Оновити:
- README
- UI documentation (якщо є)

---

## Тести

Необхідно додати або оновити UI тести:

1. hostname + vendor
2. hostname без vendor
3. hostname `-` + vendor
4. random MAC → vendor hidden
5. layout не ламається

---

## Acceptance Criteria

1. `mac_vendor` відображається під hostname
2. Vendor показується лише якщо значення існує
3. Vendor не показується для random MAC
4. Таблиця не стає ширшою
5. Layout залишається читабельним
6. API не змінюється
7. Документація оновлена (UA + EN)
8. Тести оновлені

---

## Обмеження

- не додавати нову колонку
- не додавати нові badge
- не змінювати sorting
- не змінювати search logic
