# Logging policy

## 🇺🇦 Українською

Цей документ фіксує єдину policy для логів MikroTrack.

### Рівні логування

- `DEBUG`
  - внутрішні технічні деталі
  - деталі state-machine рішень
  - розширені diff/event details
  - payload/debug дані для розробки

- `INFO`
  - стабільний operational flow
  - start/finish ключових етапів циклу
  - runtime summary (збір даних, diff summary, snapshot saved)
  - expected runtime behavior (включно з optional capability skip)

- `WARNING`
  - часткові non-fatal проблеми
  - degraded behavior, коли цикл продовжується
  - потенційні ризики (наприклад low disk space)

- `ERROR`
  - реальні збої, які впливають на коректність циклу
  - persistence/diff/API failures, що потребують втручання

### Expected conditions (не аварія)

Ці кейси не повинні інтерпретуватись як critical incident:

- `Skipping optional resource /interface/wireless: unsupported on this device`
- `Persistence path may not be mounted to host`
- `[DIFF_SKIPPED] No previous snapshot found`
- `No events were persisted after serialization attempts` (warning; перевірити, але сервіс не впав)

### Real errors (потрібне втручання)

- `[DIFF_ERROR] Failed to process snapshots`
- `[PERSISTENCE_ERROR] ...`
- MikroTik connection/auth/TLS/protocol errors

### Практика читання логів

1. Починайте з `ERROR`, потім `WARNING`.
2. Для операційного стану перевіряйте `INFO`-потік:
   - `Application started`
   - `Collection cycle started`
   - `Collection cycle completed`
   - `Snapshot saved: ...`
   - `Retention cleanup done: ...`
3. Для діагностики деталей піднімайте `LOG_LEVEL=DEBUG`.

---

## 🇬🇧 English

This document defines the unified MikroTrack logging policy.

### Log levels

- `DEBUG`
  - internal technical details
  - state-machine decision details
  - extended diff/event details
  - development-oriented payload diagnostics

- `INFO`
  - stable operational flow
  - start/finish of key cycle stages
  - runtime summaries (collection counts, diff summary, snapshot saved)
  - expected runtime behavior (including optional capability skips)

- `WARNING`
  - partial non-fatal issues
  - degraded behavior while the cycle continues
  - potential risks (for example low disk space)

- `ERROR`
  - real failures impacting cycle validity
  - persistence/diff/API failures requiring intervention

### Expected conditions (not incidents)

These should not be treated as critical incidents:

- `Skipping optional resource /interface/wireless: unsupported on this device`
- `Persistence path may not be mounted to host`
- `[DIFF_SKIPPED] No previous snapshot found`
- `No events were persisted after serialization attempts` (warning; inspect, but service is still alive)

### Real errors (intervention needed)

- `[DIFF_ERROR] Failed to process snapshots`
- `[PERSISTENCE_ERROR] ...`
- MikroTik connection/auth/TLS/protocol errors

### Practical reading flow

1. Start with `ERROR`, then `WARNING`.
2. For operational status, verify the `INFO` flow:
   - `Application started`
   - `Collection cycle started`
   - `Collection cycle completed`
   - `Snapshot saved: ...`
   - `Retention cleanup done: ...`
3. Raise `LOG_LEVEL=DEBUG` for deep diagnostics.
