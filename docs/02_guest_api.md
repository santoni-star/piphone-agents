# Guest API — Як писати плагіни-гостей

## Базова структура

Кожен «гість» — це Python-файл у `guests/` або окремий пакет.

```python
from core.plugin_api import Plugin, Action

class MyGuest(Plugin):
    name = "my_guest"           # унікальне ім'я
    version = "1.0.0"           # семвер
    plugin_api_version = "1.0"  # версія API, з якою сумісний
    description = "Що робить цей гість"
```

## Дії (Actions)

Кожна дія — це словник з:

| Поле | Тип | Опис |
|---|---|---|
| `description` | str | Що робить дія (для LLM) |
| `params` | dict | Параметри: `{"ім'я": тип}` |
| `handler` | str | Ім'я методу в класі |
| `examples` | list[str] | Приклади запитів |
| `requires_network` | bool | Чи треба інтернет |
| `fallback_intent` | str | Android Intent якщо основний метод не спрацював |

### Приклад:

```python
actions = {
    "play_youtube": Action(
        description="Відкрити YouTube та увімкнути відео за назвою або ID",
        params={"query": str},
        handler="youtube_play",
        examples=[
            "увімкни prodigy girls на YouTube",
            "відкрий відео dQw4w9WgXcQ",
        ],
        requires_network=True,
        fallback_intent="https://youtu.be/",
    ),
    
    "get_location": Action(
        description="Отримати поточне місцезнаходження (одноразово)",
        params={},
        handler="location_once",
        requires_network=True,
    ),
}
```

## Методи

Кожен handler приймає аргументи згідно `params`:

```python
def youtube_play(self, query: str) -> dict:
    """
    Повертає словник з одним із:
    - {"intent": "android-intent-string"}  — виконати Android Intent
    - {"text": "відповідь"}                 — просто відповісти
    - {"action": "ім'я", "args": {...}}    — виконати іншу дію
    - {"error": "причина"}                  — помилка
    """
    if is_youtube_id(query):
        return {"intent": f"vnd.youtube:{query}"}
    else:
        video_id = search_youtube(query)
        return {"intent": f"vnd.youtube:{video_id}"}
```

## Реєстрація

```python
# В кінці файлу
guest = MyGuest()  # автоматично реєструється при імпорті
```

Або вручну:

```python
from core.action_manager import registry
from guests.guest_messaging import WhatsAppGuest, TelegramGuest

registry.register(WhatsAppGuest())
registry.register(TelegramGuest())
```

## Найкращі практики

1. **Не залежте від конкретного агента** — гість має працювати з будь-яким
2. **Використовуйте Intents** — це єдиний спосіб без root
3. **Не використовуйте Accessibility** — воно заблоковане на Xiaomi/Oppo/Huawei
4. **Документуйте приклади** — вони потрібні LLM/Cactus для розуміння
5. **Версіонуйте** — зміни в API = нова версія
6. **Intent fallback** — завжди майте запасний Intent

## Вбудовані гості

| Модуль | Гості |
|---|---|
| `guest_messaging.py` | WhatsApp, Telegram, SMS, Phone |
| `guest_media.py` | YouTube, Music Player |
| `guest_navigation.py` | Google Maps, GPS |
| `guest_notes.py` | Google Keep, Reminders, Calendar |
| `guest_system.py` | Wi-Fi, Flashlight, Battery, Volume |

## Створення нового гостя (шаблон)

```python
"""guest_example.py - Приклад для створення нового гостя."""

from core.plugin_api import Plugin, Action

class ExampleGuest(Plugin):
    name = "example"
    version = "0.1.0"
    plugin_api_version = "1.0"
    description = "Приклад гостя для документації"
    
    actions = {
        "hello": Action(
            description="Каже привіт",
            params={"name": str},
            handler="say_hello",
            examples=["скажи привіт Андрію"],
        ),
    }
    
    def say_hello(self, name: str) -> dict:
        return {"text": f"Привіт, {name}!"}

guest = ExampleGuest()
```
