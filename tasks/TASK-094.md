# TASK-094 - Pin tool versions and eliminate CI/local formatting drift

## Опис

Після впровадження CI, pre-commit hooks та formatting baseline проблема з `ruff format --check` продовжує повторюватись.

Типовий симптом:

```text
Would reformat: app/api/main.py
Would reformat: web/ui_regression.py
```

навіть після локального форматування і повторних спроб виправлення.

Це означає, що проблема вже не в самих файлах, а в дрейфі між локальним середовищем розробника та CI.

Найімовірніші причини:
- різні версії `ruff`
- різні line ending rules (`LF` / `CRLF`)
- відсутність єдиного pinned toolchain
- різна поведінка локального pre-commit і CI

Потрібно зафіксувати версії інструментів і усунути будь-який drift між local та CI.

---

## Що потрібно зробити

### 1. Зафіксувати версію `ruff`

Потрібно визначити одну робочу версію `ruff` і використовувати її всюди:

- у CI
- у pre-commit
- у локальних developer instructions

Не можна залишати floating/latest behavior.

---

### 2. Узгодити CI з pinned version

У CI workflow потрібно явно встановлювати конкретну версію `ruff`, наприклад:

```yaml
- name: Install ruff
  run: pip install ruff==X.Y.Z
```

Ту саму версію потрібно використовувати локально.

---

### 3. Узгодити pre-commit з тією ж версією

У `.pre-commit-config.yaml` потрібно використовувати ту саму pinned version `ruff`, що і в CI.

Мета:
- same formatter
- same rules
- same output

---

### 4. Зафіксувати formatting configuration

Якщо ще не зроблено, потрібно явно зафіксувати formatting-related settings у конфігурації проекту, наприклад у `pyproject.toml`.

Мінімально перевірити/задокументувати:
- line length
- quote style
- indent style
- target version (якщо потрібно)

Мета:
- жодної implicit behavior залежно від environment

---

### 5. Усунути line ending drift

Потрібно додати або перевірити `.gitattributes`, щоб у репозиторії був стабільний підхід до line endings.

Рекомендовано забезпечити:
- текстові файли в репозиторії з `LF`
- відсутність випадкових `CRLF` diffs, які можуть впливати на formatter/checks

---

### 6. Перевірити локально exactly-CI scenario

Потрібно задокументувати і перевірити локальну команду, яка повинна давати той самий результат, що і CI:

```bash
ruff format --check app web tests
```

і/або повний аналог CI-quality gate.

---

### 7. Додати debug guidance для future cases

У документації коротко описати, як діяти, якщо локально все "formatted", а CI каже `Would reformat`.

Наприклад, перевірки:
- `ruff --version`
- `pre-commit run --all-files`
- `git diff`
- line endings
- compare local vs CI tool versions

---

## Логи та журнали подій

Не застосовується напряму, але ця задача впливає на developer workflow та CI consistency.

Усі user-facing тексти і документація - англійською.

---

## Документація

Оновити документацію українською та англійською.

Описати:
- pinned `ruff` version
- relation between CI and pre-commit
- line ending policy
- local commands to reproduce CI formatting checks

Мінімально оновити:
- README / developer setup section
- pre-commit setup notes
- CI/dev workflow documentation

---

## Врахування змін у логах та документації

Для цієї задачі головний фокус:
- developer tooling consistency
- documentation updates

---

## Критерії приймання

Задача вважається виконаною, якщо:

1. `ruff` version pinned у CI
2. `ruff` version pinned у pre-commit
3. formatting config зафіксований у проекті
4. line ending policy зафіксована (`.gitattributes` або еквівалент)
5. local formatting checks повторюють CI behavior
6. documented troubleshooting for local/CI drift
7. документація оновлена українською та англійською

---

## Очікуваний результат

- локальне середовище і CI дають однаковий formatting result
- зникають recurring `Would reformat ...` failures без видимих змін у коді
- developer workflow стає передбачуваним
- formatting drift як клас проблем закривається перед Phase 2

---

## Додатково

Буде плюсом:
- додати `.editorconfig`
- зафіксувати recommended local Python/tool setup
- додати короткий "toolchain versions" section у документацію
