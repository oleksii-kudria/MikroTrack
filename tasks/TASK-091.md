# TASK-091 - Add CI pipeline for tests, lint, and baseline quality checks

## Опис

Перед переходом до Phase 2 потрібно додати базовий CI pipeline для MikroTrack.

Зараз у проєкті вже з'являються:
- unit tests
- UI regression tests
- стабілізована логіка diff/state/persistence
- documentation baseline

Але без CI залишається високий ризик:
- зламати diff або datetime logic
- зламати UI sorting / filters / mode
- зламати API/UI contract
- внести неконсистентні зміни без швидкого сигналу

Ця задача не додає новий функціонал. Її мета - створити мінімальний, але корисний CI pipeline, який автоматично перевіряє якість змін перед Phase 2.

---

## Що потрібно зробити

### 1. Додати CI workflow

Потрібно додати CI configuration для репозиторію.

Якщо репозиторій використовує GitHub, рекомендований варіант:
- GitHub Actions

Наприклад:
- `.github/workflows/ci.yml`

---

### 2. Запуск backend tests

CI має запускати backend tests, щонайменше:

- unit tests для diff/state/mac/datetime logic
- tests для persistence / serialization
- інші критичні tests, якщо вони вже існують

Мета:
- будь-яка поломка critical backend behavior має ловитися автоматично

---

### 3. Запуск UI tests

CI має запускати web/UI tests, щонайменше:

- sorting
- mode
- filters
- summary
- `unknown` behavior
- empty/null handling

---

### 4. Додати lint / formatting checks

Потрібно додати мінімально корисні quality checks.

Для backend:
- lint
- basic formatting check

Для frontend:
- lint
- якщо є formatter check - додати його теж

Інструмент можна обрати відповідно до стеку проєкту, але він має бути реалістичним і не надто важким.

---

### 5. Додати fail-fast baseline checks

CI повинен clearly fail якщо:
- тести не пройшли
- lint не пройшов
- critical build/test step не виконався

---

### 6. Перевірити reproducible install steps

CI workflow має включати чіткі install/setup кроки:
- backend dependencies
- frontend dependencies
- test commands
- lint commands

Мета:
- локальний запуск і CI запуск повинні бути максимально схожими

---

### 7. Документувати локальний запуск тих самих checks

Потрібно описати, як локально запустити той самий мінімум перевірок, що й у CI.

Наприклад:
- backend tests
- frontend tests
- lint
- повний CI-equivalent check sequence

---

### 8. Зробити pipeline мінімальним, але корисним

CI не повинен бути перевантаженим.

На цьому етапі достатньо:
- tests
- lint
- baseline validation

Не потрібно додавати складний release pipeline, deployment automation або heavy matrix, якщо це ще не потрібно.

---

## Логи та журнали подій

Усі CI messages, job names і user-facing log messages - англійською.

Назви jobs повинні бути зрозумілі, наприклад:
- `backend-tests`
- `frontend-tests`
- `lint`

---

## Документація

Оновити документацію українською та англійською.

Описати:
- що перевіряє CI
- коли він запускається
- як локально повторити ті самі перевірки
- що вважати мінімальним quality gate перед merge

---

## Врахування змін у логах та документації

У кожній задачі необхідно враховувати:
- зміни в логах/журналах подій, якщо це потрібно
- зміни в документації українською та англійською

Для цієї задачі це обов'язково.

---

## Критерії приймання

Задача вважається виконаною, якщо:

1. додано CI workflow configuration
2. CI запускає backend tests
3. CI запускає UI tests
4. CI запускає lint / formatting checks
5. pipeline падає при test/lint failure
6. локальні команди для повторення CI documented
7. документація оновлена українською та англійською

---

## Очікуваний результат

- базовий quality gate працює автоматично
- критичні регресії ловляться до merge
- перед Phase 2 проєкт отримує мінімальний, але зрілий CI foundation

---

## Додатково

Буде плюсом:
- cache dependencies
- split jobs для швидшого feedback
- status badge у README
