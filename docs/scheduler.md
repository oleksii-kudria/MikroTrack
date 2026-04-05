# Scheduler

## 🇺🇦 Українською

MikroTrack підтримує два режими збору через змінні середовища.

## `RUN_MODE`

Дозволені значення:

- `once` — виконати один цикл і завершити процес
- `loop` — працювати безперервно з паузою між циклами

Значення за замовчуванням: `once`.

## `COLLECTION_INTERVAL`

Використовується лише у `loop` режимі.

- Одиниця: секунди
- Значення: пауза між завершенням попереднього циклу і стартом наступного
- Приклад: `COLLECTION_INTERVAL=60`

## Loop vs once

### Once mode

Підходить для:

- one-shot запуску (ручна перевірка)
- CI/CD або cron із зовнішнім планувальником

Поведінка:

1. підключення до MikroTik
2. збір DHCP + ARP
3. побудова unified model
4. вивід/логування результату (залежно від налаштувань)
5. завершення процесу

### Loop mode

Підходить для:

- always-on collector контейнера
- внутрішнього циклічного збору

Поведінка:

1. запуск циклу збору
2. обробка/логування можливих помилок
3. sleep на `COLLECTION_INTERVAL`
4. повторення наступної ітерації

---

## 🇬🇧 English

MikroTrack supports two collection modes controlled via environment variables.

## `RUN_MODE`

Allowed values:

- `once` — run one collection cycle and exit
- `loop` — run continuously with a pause between cycles

Default: `once`.

## `COLLECTION_INTERVAL`

Used only in `loop` mode.

- Unit: seconds
- Meaning: delay between the end of previous cycle and the start of next one
- Example: `COLLECTION_INTERVAL=60`

## Loop vs once

### Once mode

Use when you need:

- one-shot run (manual check)
- execution from CI/CD or cron with external scheduling

Behavior:

1. connect to MikroTik
2. collect DHCP + ARP
3. build unified model
4. print/log result (depending on settings)
5. exit process

### Loop mode

Use when you need:

- always-on collector container
- internal repeat schedule

Behavior:

1. run collection cycle
2. handle/log possible errors
3. sleep for `COLLECTION_INTERVAL`
4. continue next iteration
