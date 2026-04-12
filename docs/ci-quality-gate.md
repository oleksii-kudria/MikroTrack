# CI quality gate / CI quality gate

## 🇺🇦 Українською

### Що перевіряє CI

Workflow `.github/workflows/ci.yml` запускає 4 jobs:

1. `lint`
   - `ruff check app` (backend lint)
   - `ruff check web` (frontend lint)
   - `ruff check tests` (test lint)
   - `ruff format --check app web tests` (formatting check)
2. `backend-tests`
   - backend unit/regression tests для diff/state/datetime/mac/persistence-related поведінки.
3. `frontend-tests`
   - UI/web regression tests (`sorting`, `mode`, `filters`, `summary`, `unknown`, empty/null поведінка).
4. `quality-gate`
   - агрегує попередні jobs через `needs` і проходить лише якщо всі critical checks успішні.

### Коли запускається

CI запускається автоматично на:

- `push` у `main`
- `push` у `develop`
- кожен `pull_request`

### Як локально повторити ті самі перевірки

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt ruff

ruff check app
ruff check web
ruff check tests
ruff format --check app web tests

PYTHONPATH=. pytest -q \
  tests/test_diff.py \
  tests/test_snapshot_diff.py \
  tests/test_state_logic.py \
  tests/test_datetime.py \
  tests/test_mac_index.py \
  tests/test_device_flags.py \
  tests/test_api_session_timing.py \
  tests/test_errors.py

PYTHONPATH=. pytest -q \
  tests/test_ui_regression.py \
  tests/test_web_timeline.py
```

### Мінімальний quality gate перед merge

Перед merge вважається мінімально обов'язковим:

- lint green
- formatting check green
- backend-tests green
- frontend-tests green

Якщо будь-який із цих кроків падає — зміни не готові до merge.

### Pre-commit alignment з CI baseline

У репозиторії додано `.pre-commit-config.yaml` з hooks, що покривають CI baseline для lint/format:

- `ruff` (`app`, `web`, `tests`)
- `ruff-format` (`app`, `web`, `tests`)

Також додані базові text/yaml sanity checks:

- `trailing-whitespace`
- `end-of-file-fixer`
- `check-yaml`
- `check-added-large-files`
- `check-merge-conflict`

Швидке налаштування:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

`--no-verify` використовуйте лише як виняток.

### Formatting baseline (одноразове вирівнювання)

Якщо CI падає на `ruff format --check ...` через "історичні" файли, які були створені до увімкнення hooks:

```bash
ruff format .
git add .
git commit -m "chore: apply repository-wide formatting baseline"
```

Після такого baseline-коміту локальна перевірка та CI мають поводитися однаково (`local == CI`).

---

## 🇬🇧 English

### What CI validates

The `.github/workflows/ci.yml` workflow runs 4 jobs:

1. `lint`
   - `ruff check app` (backend lint)
   - `ruff check web` (frontend lint)
   - `ruff check tests` (test lint)
   - `ruff format --check app web tests` (formatting check)
2. `backend-tests`
   - backend unit/regression tests for diff/state/datetime/mac/persistence-related behavior.
3. `frontend-tests`
   - UI/web regression tests (`sorting`, `mode`, `filters`, `summary`, `unknown`, empty/null behavior).
4. `quality-gate`
   - aggregates previous jobs via `needs` and passes only when all critical checks pass.

### When it runs

CI runs automatically on:

- `push` to `main`
- `push` to `develop`
- every `pull_request`

### How to run the same checks locally

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt ruff

ruff check app
ruff check web
ruff check tests
ruff format --check app web tests

PYTHONPATH=. pytest -q \
  tests/test_diff.py \
  tests/test_snapshot_diff.py \
  tests/test_state_logic.py \
  tests/test_datetime.py \
  tests/test_mac_index.py \
  tests/test_device_flags.py \
  tests/test_api_session_timing.py \
  tests/test_errors.py

PYTHONPATH=. pytest -q \
  tests/test_ui_regression.py \
  tests/test_web_timeline.py
```

### Minimal quality gate before merge

A change is merge-ready only when all of the following are green:

- lint
- formatting check
- backend-tests
- frontend-tests

If any of these steps fails, the change is not ready to merge.

### Pre-commit alignment with the CI baseline

The repository now includes `.pre-commit-config.yaml` with hooks aligned to the CI lint/format baseline:

- `ruff` (`app`, `web`, `tests`)
- `ruff-format` (`app`, `web`, `tests`)

It also includes basic text/yaml sanity checks:

- `trailing-whitespace`
- `end-of-file-fixer`
- `check-yaml`
- `check-added-large-files`
- `check-merge-conflict`

Quick setup:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Use `--no-verify` only as an exception.

### Formatting baseline (one-time normalization)

If CI fails on `ruff format --check ...` because of legacy files created before hooks were enabled:

```bash
ruff format .
git add .
git commit -m "chore: apply repository-wide formatting baseline"
```

After this baseline commit, local checks and CI should behave the same (`local == CI`).
