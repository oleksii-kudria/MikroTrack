# TASK-033 - Ensure stable device identity by MAC across all sources

## Контекст

Aggregated device формується з кількох джерел:
- dhcp
- arp
- bridge_host

Склад джерел може змінюватись між poll:
- ["dhcp","arp","bridge_host"]
- ["dhcp","arp"]
- ["arp"]

## Проблема

Якщо merge логіка залежить від source:
- один і той самий MAC може трактуватись як новий device
- timestamps скидаються
- state history втрачається

## Мета

Забезпечити стабільну ідентичність пристрою незалежно від джерел даних.

## Вимоги

### 1. Єдиний ключ

```
device_identity = mac_address
```

ТІЛЬКИ MAC використовується для:
- merge
- diff
- timestamps

---

### 2. Заборонено

Заборонено використовувати для identity:
- source
- dhcp presence
- arp presence
- bridge_host presence

---

### 3. Merge логіка

```
previous_device = find_by_mac(mac_address)
```

Навіть якщо:
- змінився source
- зник bridge_host
- немає dhcp

це той самий device

---

### 4. Source changes НЕ впливають

```
old.source != new.source → НЕ новий device
```

---

### 5. Timestamp preservation

Якщо MAC той самий:

```
preserve timestamps
```

---

### 6. Debug logging

```
MAC=XX
old_source=["dhcp","arp","bridge_host"]
new_source=["dhcp","arp"]
identity=preserved
```

---

## Очікуваний результат

- Один MAC = один device
- Відсутні "нові" пристрої при зміні source
- Timestamps стабільні між poll
