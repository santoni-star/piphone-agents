# Архітектура PiPhone Agents

## 1. Спільне ядро (Core)

Усі агенти будуються на одному ядрі. Ядро не знає про конкретних агентів — воно надає механізми.

```
┌──────────────────────────────────────────────────────────────┐
│                      CORE (ядро)                              │
├──────────────────────────────────────────────────────────────┤
│  agent_loop.py     │  action_manager.py  │  tool_registry.py  │
│  plugin_api.py     │  llm_client.py      │  cactus_adapter.py │
│  android_intents.py│  memory.py          │  config.py         │
└──────────────────────────────────────────────────────────────┘
```

### 1.1 Агентний цикл (`agent_loop.py`)

Усі агенти використовують однаковий цикл:

```python
class AgentLoop:
    """
    plan  → execute → check  → (повтор або відповідь)

    plan:     LLM отримує запит, вирішує що робити
    execute:  виконує дію (Intent, shell, API)
    check:    перевіряє результат, вирішує чи треба ще крок
    """
```

Цей цикл не змінюється між агентами. Змінюється тільки те, **як отримується запит** (текст, голос, фон) і **як відповідає агент** (екран, TTS, сповіщення).

### 1.2 Plugin API (`plugin_api.py`)

Головний механізм розширення. Кожен «гість» — це плагін, який реєструє свої дії:

```python
class Plugin:
    name: str
    actions: dict[str, Action]  # назва → дія
    
    def register(self, registry: ActionManager):
        for name, action in self.actions.items():
            registry.add(name, action, plugin=self)
```

### 1.3 Cactus Needle Adapter (`cactus_adapter.py`)

Адаптер для голки кактуса (26M параметрів). Працює локально, без інтернету.

```
Запит → Cactus Needle (26M) → ім'я дії + аргументи
        Якщо > 75% впевненості → виконуємо
        Якщо < 75% → передаємо LLM (cloud)
```

## 2. Архітектура агентів

```
┌──────────────────────────────────────────────────────────────┐
│                        CORE                                   │
│          agent_loop | plugin_api | cactus | intents            │
└───────────────────────┬──────────────────────────────────────┘
                        │
          ┌─────────────┼─────────────┐
          ↓             ↓             ↓
┌─────────────────┐ ┌────────────┐ ┌──────────────┐
│   Coordinator   │ │  Secretary │ │  Proactive    │
│                 │ │            │ │              │
│ Тригер: текст   │ │ Тригер:   │ │ Тригер: час  │
│         голос   │ │  Bluetooth │ │         подія │
│ Вихід:  екран  │ │  вихід:    │ │  вихід:       │
│         TTS    │ │  TTS       │ │  сповіщення   │
└─────────────────┘ └────────────┘ └──────────────┘
          │                │               │
          └────────────────┼───────────────┘
                           ↓
               ┌──────────────────────┐
               │      Guests          │
               │  (плагіни-гості)     │
               │  WhatsApp, Telegram,  │
               │  YouTube, Maps, GPS,  │
               │  Notes, Calendar,     │
               │  System, ...          │
               └──────────────────────┘
```

## 3. Зворотна сумісність

Кожен новий агент або плагін **гарантовано сумісний** зі старими, тому що:

| Рівень | Як гарантується |
|---|---|
| **Plugin API** | Версіонується. `plugin_api_version` у кожного плагіна |
| **Core** | Ядро не змінює публічні інтерфейси. Нове тільки додається |
| **Intents** | База Intents тільки розширюється. Старі записи не змінюються |
| **Cactus Needle** | Адаптер тримає стару схему виклику |
| **Agent Loop** | Той самий `plan → execute → check` для всіх |

### Правило зворотної сумісності:
> **Можна додавати — не можна змінювати або видаляти публічні API.**

Порушення цього правила фатальне, тому ми тестуємо кожен PR:
```
Plugin X   + Core v1.0 → працює ✅
Plugin X   + Core v2.0 → працює ✅ (нове ядро сумісне зі старими плагінами)
Plugin X v2 + Core v1.0 → працює ✅ (новий плагін сумісний зі старим ядром)
```

## 4. Як плагін стає гостем

```python
from core.plugin_api import Plugin, Action

class WhatsAppGuest(Plugin):
    name = "whatsapp"
    version = "1.0.0"
    plugin_api_version = "1.0"
    
    actions = {
        "send_message": Action(
            description="Надіслати WhatsApp повідомлення",
            params={"phone": str, "text": str},
            handler="whatsapp_send"
        ),
        "open_chat": Action(
            description="Відкрити WhatsApp чат",
            params={"phone": str},
            handler="whatsapp_open"
        ),
    }
    
    def whatsapp_send(self, phone: str, text: str) -> dict:
        # wa.me/380XXXXXXXXX?text=...
        return {"intent": f"https://wa.me/{phone}?text={text}"}
    
    def whatsapp_open(self, phone: str) -> dict:
        return {"intent": f"https://wa.me/{phone}"}
```

Будь-який агент (Координатор, Секретар, Проактивний) може використовувати цього гостя — він не прив'язаний до конкретного агента.

## 5. Дорожня карта розширення

```
Фаза 1: Ядро + Coordinator + базові гості
Фаза 2: Секретар (голосовий інтерфейс)
Фаза 3: Проактивний (фонові тригери)
Фаза 4: Community гості (відкритий API)
```

Кожна фаза зворотно сумісна з попередньою.
