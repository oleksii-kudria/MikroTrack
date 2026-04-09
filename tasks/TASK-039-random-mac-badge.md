# TASK-039 - Add RANDOM badge with highest priority

## Контекст

У системі використовуються semantic badges:
- PERM
- STATIC
- DYNAMIC
- COMPLETE (для ARP-only)

Додатково виявлено важливий кейс:
- пристрої з рандомними MAC-адресами (наприклад iOS/Android privacy MAC)

Ці пристрої можуть:
- виглядати як STATIC або навіть PERM
- але по факту не є стабільними ідентифікаторами

## Мета

Додати нову semantic badge:

```
RANDOM
```

яка має найвищий пріоритет і перекриває всі інші типи.

---

## Вимоги

### 1. Визначення random MAC

Використати перевірку:

```
locally administered bit = 1
```

Тобто MAC:
- другий найменш значущий біт першого октета = 1

Приклад:

```
02:xx:xx:xx:xx:xx → random
```

---

### 2. Пріоритет badge

Оновити пріоритет:

```
RANDOM > PERM > STATIC > DYNAMIC > COMPLETE
```

---

### 3. Логіка

```
if is_random_mac(mac):
    badge = "RANDOM"

elif arp_is_static:
    badge = "PERM"

elif dhcp_is_static:
    badge = "STATIC"

elif dhcp_is_dynamic:
    badge = "DYNAMIC"

elif arp_only and arp_flags == "DC":
    badge = "COMPLETE"

else:
    no badge
```

---

### 4. Важливо

Навіть якщо:

- DHCP static
- ARP static
- PERM логіка

але MAC random → завжди:

```
RANDOM
```

---

### 5. Відображення

```
[RANDOM]
```

Рекомендований колір:
- жовтий / помаранчевий (щоб виділявся як нестабільний)

---

### 6. Acceptance Criteria

- random MAC завжди має badge RANDOM
- RANDOM перекриває PERM/STATIC/DYNAMIC
- правильне визначення locally administered MAC
- UI чітко відображає нестабільні пристрої

---

## Очікуваний результат

Оператор одразу бачить:
- що пристрій використовує random MAC
- що його не можна вважати стабільним ідентифікатором

Це особливо важливо для:
- мобільних пристроїв
- guest мереж
- безпекового аналізу
