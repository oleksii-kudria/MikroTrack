# UI Regression Tests / UI Regression тести

## 🇺🇦 Українською

Цей набір тестів захищає критичну поведінку Web UI перед Phase 2.

### Що покрито

- **Default sorting**: `online -> idle -> offline -> unknown`; для `unknown` використовується лише alphabetical ordering.
- **Explicit single-column sorting**: `hostname`, `ip`, `status`, `session` для напрямків `asc/desc`.
- **Sort cycle**: `none -> asc -> desc -> none`.
- **Mode behavior**:
  - `End`: приховує `BRIDGE`, `COMPLETE`, `INTERFACE`, `unknown`.
  - `All`: показує весь dataset.
- **Summary behavior**: summary рахується від mode dataset і не залежить від active filters.
- **Filters behavior**: filters зменшують таблицю; `Clear` повертає всі рядки.
- **Unknown behavior**: видимість залежно від mode + відсутність fallback до time sorting.
- **Empty/null stability**: порожні `hostname`, `ip`, `*_since` не ламають deterministic sorting.
- **Hostname + vendor rendering**:
  - `mac_vendor` показується другим рядком під `Hostname` (compact/muted style).
  - для `is_random_mac=true` vendor приховується.
  - відсутній `mac_vendor` не додає другий рядок.
  - порожній hostname відображається як `-`, vendor все одно може бути показаний.
- **Contract assumptions**: перевірка обов'язкових полів UI/API contract (`status`, `state_changed_at`, `online_since`, `idle_since`, `offline_since`, `last_known_ip`, `last_known_hostname`, stale flags).

### Як запускати

```bash
pytest -q tests/test_ui_regression.py
```

Або повний набір:

```bash
pytest -q
```

---

## 🇬🇧 English

This test set protects critical Web UI behavior before Phase 2.

### Covered behaviors

- **Default sorting**: `online -> idle -> offline -> unknown`; `unknown` uses alphabetical ordering only.
- **Explicit single-column sorting**: `hostname`, `ip`, `status`, `session` in `asc/desc` directions.
- **Sort cycle**: `none -> asc -> desc -> none`.
- **Mode behavior**:
  - `End`: hides `BRIDGE`, `COMPLETE`, `INTERFACE`, `unknown`.
  - `All`: shows the full dataset.
- **Summary behavior**: summary is calculated from the mode dataset and is not affected by active filters.
- **Filters behavior**: filters reduce table rows; `Clear` restores all rows.
- **Unknown behavior**: mode visibility + no fallback to time-based sorting.
- **Empty/null stability**: empty `hostname`, `ip`, and `*_since` values do not break deterministic sorting.
- **Hostname + vendor rendering**:
  - `mac_vendor` is shown as a second line under `Hostname` (compact/muted style).
  - vendor is hidden when `is_random_mac=true`.
  - missing `mac_vendor` does not add a second line.
  - empty hostname is rendered as `-`, while vendor may still be shown.
- **Contract assumptions**: required UI/API fields are checked (`status`, `state_changed_at`, `online_since`, `idle_since`, `offline_since`, `last_known_ip`, `last_known_hostname`, stale flags).

### How to run

```bash
pytest -q tests/test_ui_regression.py
```

Or run the full suite:

```bash
pytest -q
```
