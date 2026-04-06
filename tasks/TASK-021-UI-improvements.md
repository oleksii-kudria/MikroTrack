# TASK-021 - UI Improvements (Flags + Status + Comments)

## Мета
Покращити читабельність UI в розділі Devices шляхом:
- компактного відображення flags/state
- заміни active/inactive на індикатор
- уніфікації відображення коментарів DHCP/ARP

---

## 1. Compact flags/state visualization

### Проблема
Flags/state відображаються у вигляді тексту в декілька рядків.

### Рішення
Відображати всі flags в одну строку у вигляді badge/іконок.

### Mapping

source:
- dhcp → [DHCP]
- arp → [ARP]
- dhcp+arp → [DHCP] [ARP]

lease:
- dynamic → [D]
- static → [S]

dhcp status:
- bound → [B]
- unknown → [U]

arp:
- dynamic → [AD]
- complete → [C]
- dynamic+complete → [AD+C]

### Кольори

- DHCP → синій
- ARP → фіолетовий/сірий
- D → жовтий
- S → синій
- B → зелений
- U → сірий
- AD → оранжевий

### Tooltip

Кожен badge має tooltip з повним значенням.

---

## 2. Replace active/inactive with status dot

### Проблема
active/inactive займає місце і повільно читається.

### Рішення

Замінити на кольорову точку:

- зелена → active
- червона → inactive

### Вимоги

- розмір 6-10px
- border-radius: 50%
- tooltip:
  - active
  - inactive

### Розташування

Перед MAC:

● 6E:40:D3:A9:1A:D3

---

## 3. Comments visualization (DHCP / ARP)

### Проблема
Коментарі відображаються як текст:

dhcp: MKT-spor-petrov

### Рішення

Замінити на badge/іконку:

- DHCP comment → [DHCP: text]
- ARP comment → [ARP: text]

### Якщо коментар однаковий:

[DHCP+ARP: text]

---

## Definition of Done

- flags/state в одну строку
- використані badge/іконки
- кольори застосовані
- tooltip реалізований
- active/inactive замінено на точку
- коментарі DHCP/ARP у вигляді badge
