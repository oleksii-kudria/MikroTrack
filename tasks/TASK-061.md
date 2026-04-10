# TASK-061 - Force ONLINE state when bridge_host is present

## Опис / Description

### UA
Після виправлення TASK-060 виявлено нову проблему:

Коли пристрій знову підключається до мережі (`bridge_host_present = true`), він переходить у стан `idle` замість `online`.

Це відбувається навіть якщо:
- пристрій фізично присутній у мережі
- є запис у bridge host
- `arp_state = "online"`

### EN
After TASK-060 fix, a new issue appeared:

When a device reconnects (`bridge_host_present = true`), it transitions to `idle` instead of `online`.

---

## Проблема / Problem

### UA
Логіка `_derive_device_state()` НЕ гарантує:

```
bridge_host_present = true → state = online
```

Через це:
- `idle_since` не скидається
- `online_since` не оновлюється
- API показує `idle`

---

## Очікувана поведінка / Expected behavior

### UA

```
bridge_host_present = true → ALWAYS online
```

---

## Що треба змінити / Required changes

### app/persistence.py

#### 1. В `_derive_device_state()`

```python
def _derive_device_state(device: dict[str, Any]) -> str:
    bridge_host_present = bool(device.get("bridge_host_present", False))

    if bridge_host_present:
        return "online"
```

#### 2. В `_apply_stable_timestamps()`

```python
if current_bridge_host_present:
    merge_current_state = "online"
```

---

## Критерії приймання / Acceptance criteria

- при появі `bridge_host_present = true` → `online`
- `idle_since` очищається
- `online_since` оновлюється
- API повертає `status = online`
