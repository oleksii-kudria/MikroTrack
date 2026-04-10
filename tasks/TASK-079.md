# TASK-079 - Fix diff MAC indexing and ensure events.jsonl is generated

## Опис

Після останніх оновлень у MikroTrack snapshot-файли створюються коректно, але файл `events.jsonl` не з'являється навіть тоді, коли стан пристрою змінюється, наприклад `online -> offline`.

Під час перевірки виявлено, що snapshot-и містять поле:

```json
"mac": "6E:7B:C9:CC:5A:81"
```

але diff логіка в `app/persistence.py` індексує пристрої лише за полем:

```python
mac_address
```

Через це пристрої не потрапляють у `previous_by_mac` / `current_by_mac`, diff не бачить змін між snapshot-ами, список events залишається порожнім, а `events.jsonl` не створюється.

---

## Що потрібно зробити

### 1. Виправити індексацію пристроїв по MAC

У функції `_index_devices_by_mac()` додати підтримку обох варіантів поля:

- `mac_address`
- `mac`

Пріоритет:
1. `mac_address`
2. `mac`

Очікувана логіка:

```python
mac = str(device.get("mac_address") or device.get("mac") or "").strip().upper()
```

---

### 2. Додати захисне логування

Якщо у snapshot записі немає ні `mac_address`, ні `mac`, потрібно логувати warning англійською.

Приклад:

```text
WARNING persistence: skipping device without MAC key
```

Лог повинен допомогти швидко знаходити проблеми зі схемою snapshot-ів.

---

### 3. Перевірити генерацію events після виправлення

Після виправлення потрібно підтвердити, що при наявності двох snapshot-ів:

- у першому пристрій `online`
- у другому той самий пристрій `offline`

система:
- коректно зіставляє пристрій по MAC
- генерує події diff
- створює файл `events.jsonl`

---

### 4. Перевірити сумісність зі старими snapshot-ами

Реалізація має бути backward-compatible:
- якщо snapshot містить `mac_address` - все працює як раніше
- якщо snapshot містить `mac` - diff також працює
- якщо присутні обидва поля - використовувати `mac_address`

---

## Логи та журнали подій

Усі логи і журнали подій - англійською.

Додати або перевірити наявність корисних логів:

```text
INFO diff: detected change field=state mac=6E:7B:C9:CC:5A:81 old=online new=offline
INFO mikrotrack: Events persisted: 4 -> /data/snapshots/events.jsonl
WARNING persistence: skipping device without MAC key
```

---

## Документація

Оновити документацію українською та англійською.

### UA
Описати:
- підтримку `mac_address` і `mac` у snapshot schema
- причину, чому `events.jsonl` міг не створюватися
- що diff тепер підтримує обидва варіанти ключа MAC

### EN
Document:
- support for both `mac_address` and `mac` in snapshot schema
- root cause of missing `events.jsonl`
- updated diff behavior with MAC fallback support

---

## Врахування змін у логах та документації

У кожній задачі необхідно враховувати:
- зміни в логах/журналах подій, якщо це потрібно
- зміни в документації українською та англійською

Для цієї задачі це обов'язково.

---

## Критерії приймання

Задача вважається виконаною, якщо:

1. `_index_devices_by_mac()` підтримує `mac_address` та `mac`
2. при відсутності MAC у записі є warning лог
3. diff бачить зміни між snapshot-ами з полем `mac`
4. при реальному переході `online -> offline` створюється `events.jsonl`
5. документація оновлена українською та англійською
6. існуюча поведінка для `mac_address` не зламана

---

## Очікуваний результат

- diff коректно індексує пристрої незалежно від того, чи використовується `mac_address`, чи `mac`
- події знову генеруються
- `events.jsonl` створюється при першому непорожньому diff
- система стає стійкішою до змін snapshot schema

---

## Додатково

Буде плюсом:
- додати unit test для `_index_devices_by_mac()` на випадки:
  - тільки `mac_address`
  - тільки `mac`
  - обидва поля
  - відсутність обох полів
