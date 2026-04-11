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
