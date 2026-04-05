# TASK-010: Fix stdout output in loop mode

## Мета

Виправити проблему, коли при:

PRINT_RESULT_TO_STDOUT=true  
RUN_MODE=loop  

→ результат (devices JSON) не виводиться у консоль.

---

## Контекст

Зараз:

- loop працює
- збір виконується
- логування є
- але результат не друкується

Причина:
- результат не повертається з run_once()
- або print виконується тільки в режимі once

---

## Що потрібно реалізувати

### 1. run_once() має повертати результат

Було:

def run_once():
    ...

Стало:

def run_once():
    dhcp = get_dhcp_leases(api)
    arp = get_arp_entries(api)
    devices = build_devices(dhcp, arp)
    return devices

---

### 2. Вивід у stdout для обох режимів

Оновити main.py:

if config.run_mode == "once":
    result = run_once()
    if config.print_result_to_stdout:
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
else:
    while True:
        result = run_once()

        if config.print_result_to_stdout:
            print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)

        time.sleep(config.collection_interval)

---

### 3. Додати flush=True

ВАЖЛИВО:

print(..., flush=True)

Щоб уникнути буферизації в Docker.

---

### 4. Перевірити parsing boolean

config.py:

def str_to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}

print_result_to_stdout = str_to_bool(
    os.getenv("PRINT_RESULT_TO_STDOUT", "true")
)

---

### 5. Логування

INFO:

- Result printed to stdout (optional)

DEBUG:

- size of output
- sample device

---

## Очікуваний результат

При:

PRINT_RESULT_TO_STDOUT=true  
RUN_MODE=loop  

→ кожну ітерацію в stdout виводиться JSON

---

## Критерії приймання

- stdout працює в once і loop
- немає дублювання
- є flush=True
- bool правильно парситься
- код простий

---

## Далі

TASK-011: Persistence (збереження результатів)
