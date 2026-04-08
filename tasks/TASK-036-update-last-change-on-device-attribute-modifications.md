# TASK-036 - Update Last change on device attribute modifications (not only state)

## Контекст

Наразі поле `Last change` (state_changed_at) оновлюється лише при зміні стану:
- online ↔ offline
- online ↔ idle (частково)

Виявлена проблема:
- зміни атрибутів пристрою (ARP static/PERM, коментар, flags DC→SC, badges)
НЕ оновлюють `Last change`
- виняток: окремі пристрої (наприклад тільки ARP/manual) оновлюються

## Симптоми

- MAC `20:37:A5:87:2A:13`:
  - додано ARP comment
  - змінено ARP на static (PERM)
  - flags змінено (DC → SC)
  - `Last change` НЕ оновився

- MAC `40:7F:5F:17:6C:2A`:
  - `Last change` оновлюється

## Проблема

Логіка оновлення `state_changed_at` залежить тільки від:
```
old_state != new_state
```

Але НЕ враховує зміну суттєвих атрибутів пристрою.

## Мета

Оновлювати `Last change` при будь-якій суттєвій зміні aggregated device.

## Вимоги

### 1. Визначити набір суттєвих змін

Вважати зміною:

- arp_type (dynamic ↔ static)
- arp_flags
- dhcp_is_dynamic
- badges (наприклад PERM)
- dhcp_comment
- arp_comment
- host_name
- primary_ip
- source (набір джерел)
- interface_name

---

### 2. Виявлення змін

```
device_changed = any(field_old != field_new for field in tracked_fields)
```

---

### 3. Оновлення Last change

```
if old_state != new_state:
    apply_transition_rules()

elif device_changed:
    state_changed_at = now

elif timestamps_missing:
    initialize_missing_timestamps()

else:
    preserve
```

---

### 4. Debug logging

```
MAC=20:37:A5:87:2A:13
state=online → online
device_changed=true
changed_fields=[arp_type, badges, arp_comment]
decision=device_change_update_timestamp
state_changed_at=now
```

---

### 5. Acceptance Criteria

- зміна ARP dynamic → static оновлює `Last change`
- додавання PERM badge оновлює `Last change`
- зміна коментаря оновлює `Last change`
- state transition працює як раніше
- idle логіка не ламається

---

## Очікуваний результат

`Last change` відображає:
- або зміну стану
- або будь-яку суттєву зміну пристрою

UI більше не вводить в оману, коли пристрій змінився, але час не оновився.
