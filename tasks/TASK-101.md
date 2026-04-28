# TASK-101 - Fix Python 3.10 compatibility in update_mac_vendors.py

## Опис задачі

Скрипт:

`scripts/update_mac_vendors.py`

не працює в середовищах з Python 3.10 через використання:

from datetime import UTC

Під час запуску виникає помилка:

ImportError: cannot import name 'UTC' from 'datetime'

Причина:
`datetime.UTC` підтримується лише починаючи з Python 3.11.

MikroTrack повинен залишатися сумісним з Python 3.10+.

---

## Що необхідно виправити

Замінити:

from datetime import UTC, datetime

на:

from datetime import datetime, timezone

---

## Оновити використання datetime

Замінити:

datetime.now(UTC)

на:

datetime.now(timezone.utc)

---

## Вимоги

- забезпечити сумісність з Python 3.10
- не ламати існуючу логіку генерації updated_at
- зберегти UTC timestamps
- не змінювати формат output JSON

---

## Expected output

{
  "updated_at": "2026-04-28T10:53:29+00:00"
}

---

## Логування

Змін у логування не потрібно.

Логи залишаються англійською.

---

## Вплив на документацію

Якщо в документації зазначено Python requirements:
- оновити README
- вказати Python 3.10+ compatibility

Документація:
- українською
- англійською

---

## Тести

1. запуск на Python 3.10
2. запуск на Python 3.11+
3. перевірка updated_at

---

## Acceptance Criteria

1. Скрипт працює на Python 3.10
2. Скрипт працює на Python 3.11+
3. UTC timestamp формується коректно
4. JSON формат не змінено
5. Документація оновлена при необхідності

---

## Обмеження

- без зміни бізнес-логіки updater
- тільки compatibility fix
