# TASK-093 - Apply repository-wide formatting baseline and align CI with pre-commit

## Опис

Після впровадження CI (TASK-091) та pre-commit hooks (TASK-092) виявлено, що CI продовжує падати через існуючі неформатовані файли в репозиторії.

Причина:
- pre-commit працює тільки для нових комітів
- існуючий код ще не приведений до єдиного форматування
- CI використовує `ruff format --check`, що падає, якщо є невідформатовані файли

Потрібно зробити одноразове вирівнювання всього репозиторію (formatting baseline) і узгодити локальні та CI перевірки.

---

## Що потрібно зробити

### 1. Застосувати форматування до всього репозиторію

Локально виконати:

```bash
ruff format .
```

---

### 2. Закомітити formatting baseline

```bash
git add .
git commit -m "chore: apply repository-wide formatting baseline"
git push
```

Важливо:
- це окремий commit
- без змішування з функціональними змінами

---

### 3. Переконатися, що CI проходить

Після push:

- `ruff format --check` не падає
- CI pipeline повністю зелений

---

### 4. Узгодити pre-commit і CI

Перевірити:

- pre-commit використовує ті самі інструменти (ruff, ruff-format)
- CI перевіряє ті самі правила
- немає розбіжностей між локальною і CI поведінкою

Мета:

local == CI

---

### 5. Додати рекомендацію для розробників

Перед push виконувати:

```bash
pre-commit run --all-files
```

або:

```bash
ruff format .
```

---

## Документація

### UA
- пояснення formatting baseline
- як уникати CI failures

### EN
- formatting baseline explanation
- how to keep CI green

---

## Врахування змін у логах та документації

Для цієї задачі:
- оновити документацію (developer workflow)

---

## Критерії приймання

1. виконано `ruff format .`
2. створено окремий commit
3. CI проходить без formatting errors
4. pre-commit і CI узгоджені
5. документація оновлена

---

## Очікуваний результат

- репозиторій має єдиний стиль форматування
- CI більше не падає через старі файли
- нові зміни автоматично відповідають стандарту
- developer workflow стає стабільним

---

## Додатково

Буде плюсом:
- додати `.editorconfig`
- зафіксувати стиль у CONTRIBUTING.md
