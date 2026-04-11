# TASK-092 - Add pre-commit hooks for formatting and linting

## Опис

Після додавання CI pipeline виявилось, що частина перевірок падає не через логіку коду, а через локально не застосоване форматування або lint fixes.

Типовий сценарій:
- розробник змінює код
- локально тести можуть проходити
- CI падає на `ruff format --check` або lint step
- доводиться робити окремий "format-only" commit

Це зайвий шум і зайві ітерації.

Потрібно додати `pre-commit` hooks, щоб базові перевірки запускались локально перед commit і зменшували кількість дрібних CI failures.

---

## Що потрібно зробити

### 1. Додати pre-commit configuration

Створити файл:

- `.pre-commit-config.yaml`

Конфігурація має бути мінімальною, але корисною.

---

### 2. Додати hooks для Python lint/format

Потрібно додати hooks щонайменше для:

- `ruff`
- `ruff-format`

Мета:
- автоматично ловити lint issues
- автоматично застосовувати або перевіряти форматування до commit

---

### 3. Додати hooks для базових текстових/службових перевірок

Мінімально корисно додати hooks для:
- trailing whitespace
- end-of-file newline
- YAML validation
- large file / merge-conflict style sanity checks, якщо це доцільно

Не потрібно перевантажувати конфіг занадто великою кількістю hooks.

---

### 4. Узгодити hooks з CI

Pre-commit hooks мають відповідати тому, що вже перевіряє CI.

Мета:
- локальна перевірка ≈ CI baseline
- розробник ловить більшість дрібних проблем до push
- зменшується кількість "format-only" CI failures

---

### 5. Додати інструкцію з встановлення

Потрібно задокументувати:

- як встановити `pre-commit`
- як увімкнути hooks
- як запустити вручну для всього репозиторію

Наприклад:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

---

### 6. Додати інструкцію для bypass only when needed

Коротко описати, що bypass hooks має бути винятком, а не нормальним шляхом.

Не потрібно заохочувати постійний skip, але корисно згадати, що при потребі є `--no-verify`.

---

### 7. Перевірити, що hooks працюють на поточній структурі репозиторію

Потрібно перевірити, що конфіг коректно працює для:
- backend code
- web code
- tests
- docs / yaml files

---

## Логи та журнали подій

Усі user-facing тексти, comments і documentation - англійською.

---

## Документація

Оновити документацію українською та англійською.

Мінімально:
- README або окремий dev/setup section
- опис:
  - install
  - enable
  - run manually
  - relation to CI

---

## Врахування змін у логах та документації

У кожній задачі необхідно враховувати:
- зміни в логах/журналах подій, якщо це потрібно
- зміни в документації українською та англійською

Для цієї задачі основний фокус - документація і developer workflow.

---

## Критерії приймання

Задача вважається виконаною, якщо:

1. додано `.pre-commit-config.yaml`
2. hooks включають `ruff`
3. hooks включають `ruff-format`
4. додано базові text/yaml hygiene checks
5. pre-commit узгоджений з CI baseline
6. documented install and usage steps
7. документація оновлена українською та англійською

---

## Очікуваний результат

- дрібні formatting/lint issues ловляться до commit
- CI рідше падає на trivial formatting problems
- developer workflow стає швидшим і чистішим
- перед Phase 2 репозиторій отримує кращу локальну quality gate

---

## Додатково

Буде плюсом:
- додати section "recommended developer setup"
- додати приклад локальної команди для повної перевірки перед push
