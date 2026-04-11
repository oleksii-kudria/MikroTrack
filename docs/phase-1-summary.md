# Phase 1 Summary and System Boundaries

## 🇺🇦 Українською

## Мета документа

Цей документ фіксує Phase 1 як завершений baseline перед стартом Phase 2:

- що вже реалізовано і вважається стабільним;
- які межі системи в Phase 1;
- які обмеження та відомі edge cases потрібно враховувати;
- що можна розширювати у Phase 2 без ризику зламати стабільне ядро.

---

## Що реалізовано в Phase 1

### 1) Collector (DHCP, ARP, Bridge Host)

Collector читає дані з RouterOS API і нормалізує три ключові джерела:

- DHCP leases;
- ARP table;
- Bridge host table.

Це формує пасивний, неінвазивний шар спостереження за мережею.

### 2) Unified device model

Дані агрегуються у єдину модель пристрою з MAC як стабільним ключем і консолідацією DHCP/ARP/Bridge сигналів.

### 3) Event-driven diff

Після кожного snapshot виконується deterministic diff проти попереднього стану та генеруються події змін.

### 4) Persistence (snapshots + events.jsonl)

Реалізовано локальне збереження у файловому форматі:

- snapshots (`*.json`);
- append-only стрічка подій (`events.jsonl`).

### 5) Timezone-aware datetime

Система працює з timezone-consistent timestamp-ами для snapshot/event рівня та API-відповідей.

### 6) Last-known fields

Для offline-пристроїв підтримується last-known identity:

- `last_known_ip`;
- `last_known_hostname`;
- stale-ознаки для безпечного відображення історично відомих значень.

### 7) Web UI (filters, mode, sorting)

Web UI надає:

- таблицю пристроїв;
- режими відображення;
- фільтрацію;
- predictable сортування;
- live-таймери/статусні індикатори.

### 8) API (devices endpoint)

API вже має endpoint для device-представлення (`/api/devices`) зі стабільною структурою відповіді для UI/інтеграцій.

---

## System boundaries (Phase 1)

### ЩО входить у систему

- пасивний збір даних із MikroTik (без активного probing);
- локальне збереження snapshot + event журналу;
- відображення актуального стану та базової динаміки змін через API/UI.

### ЩО НЕ входить у систему

- активне сканування мережі (port scan, active probing);
- deep network discovery за межами доступних router таблиць;
- SIEM-рівень аналітики/кореляції/детекції загроз;
- correlation між різними мережами/сайтами як єдиним multi-site graph.

---

## Обмеження Phase 1

- Сильна залежність від доступності/якості даних MikroTik RouterOS API.
- Немає окремої historical DB: зберігання лише у JSON/JSONL.
- Точність state detection обмежена якістю ARP/DHCP/Bridge сигналів.
- Можливі часові прогалини між snapshot-ами (polling nature).
- Семантика деяких станів (наприклад stale/permanent) може відрізнятися залежно від поведінки конкретного роутера.

---

## Гарантії системи (Phase 1 contract)

- deterministic diff для однакових вхідних даних;
- стабільний snapshot schema для поточної моделі;
- відсутність crash на serialization/persistence шляху за валідних даних;
- timezone-consistent timestamps по всьому pipeline;
- predictable UI sorting при однаковому наборі даних.

---

## Відомі edge cases

- DHCP lease expiration може прибирати активні DHCP-атрибути до фактичного зникнення пристрою з L2.
- ARP stale entries можуть тривалий час виглядати як «не зовсім offline».
- `unknown` state можливий при неповних або суперечливих сигналах.
- Wireless-specific telemetry у Phase 1 не підтримується як окремий шар.
- Можливі mixed timestamp formats у legacy-даних під час міграцій/оновлень.

---

## Baseline для Phase 2

### Що безпечно розширювати

- нові read-only джерела сигналів (без порушення MAC-keyed моделі);
- додаткові API read endpoints;
- UI-аналітику/фільтри/візуалізації поверх існуючого schema;
- сервісні інструменти експорту/репортингу.

### Що не чіпати без явного рефакторингу

- базову state machine (`online`/`idle`/`offline`/`unknown`);
- snapshot/event format контракти;
- deterministic diff правила;
- timestamp contract (`state_changed_at`, `online_since`, `offline_since`, last-known поля).

### Де можливі breaking changes

- зміни device schema або імен ключових полів;
- зміни semantics існуючих state/flags/badges;
- зміни API-відповіді `/api/devices` без versioning;
- перехід з файлового storage на DB без migration compatibility layer.

---

## Ключові пов'язані документи

- `docs/architecture.md`
- `docs/device-model.md`
- `docs/storage.md`
- `docs/api-contract.md`

---

## 🇬🇧 English

## Purpose

This document freezes Phase 1 as a completed baseline before Phase 2 starts:

- what is implemented and considered stable;
- what is inside and outside system scope;
- which limitations and edge cases are known;
- what can be extended in Phase 2 without breaking the stable core.

---

## Implemented in Phase 1

1. **Collector** for DHCP, ARP, and Bridge Host data.
2. **Unified device model** keyed by MAC.
3. **Event-driven diff** between consecutive snapshots.
4. **Persistence layer** with snapshot JSON files and append-only `events.jsonl`.
5. **Timezone-aware datetime handling** across pipeline/API.
6. **Last-known fields** for offline identity continuity.
7. **Web UI** with filters, modes, sorting, and live state timers.
8. **API devices endpoint** (`/api/devices`) with stable consumer-facing shape.

---

## Phase 1 system boundaries

### In scope

- passive network observation via MikroTik tables;
- local persistence of snapshots and events;
- state exposure through API and Web UI.

### Out of scope

- active scanning/probing;
- deep discovery beyond router-provided tables;
- SIEM-grade analytics and threat correlation;
- cross-network (multi-site) correlation graph.

---

## Phase 1 limitations

- Depends on MikroTik RouterOS API availability and data quality.
- No dedicated historical DB (JSON/JSONL storage only).
- State detection precision is bounded by source signal quality.
- Snapshot polling can introduce temporal gaps.
- Some state semantics (for example stale/permanent behavior) may vary by router behavior.

---

## System guarantees (Phase 1 contract)

- deterministic diff for identical input snapshots;
- stable snapshot schema within current contract;
- no serialization-path crashes for valid input payloads;
- timezone-consistent timestamps;
- predictable UI sorting for equal datasets.

---

## Known edge cases

- DHCP lease expiration can remove DHCP attributes before a device fully disappears from L2 activity.
- ARP stale entries may delay clear offline interpretation.
- `unknown` state may appear when signals are incomplete/contradictory.
- Wireless-specific telemetry is not supported as a dedicated source in Phase 1.
- Mixed legacy timestamp formats may appear during upgrades/migrations.

---

## Phase 2 baseline guidance

### Safe extension areas

- add read-only signal sources without breaking the MAC-keyed model;
- add read APIs on top of current contracts;
- extend UI analytics/filters/visualizations;
- add export/reporting helpers.

### Areas requiring explicit refactoring first

- core state machine semantics;
- snapshot/event contract formats;
- deterministic diff rules;
- timestamp/session contract.

### Potential breaking-change zones

- device schema/key renaming;
- semantics changes for current states/flags/badges;
- `/api/devices` response shape changes without versioning;
- storage backend migration without compatibility/migration layer.
