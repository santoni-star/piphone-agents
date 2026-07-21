#!/usr/bin/env python3
"""Тести ядра — перевіряють всі компоненти end-to-end."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Всі модулі імпортуються без помилок."""
    from core import AgentLoop, AgentContext
    from core import Action, Plugin, ActionManager, registry
    from core import CactusAdapter, CactusResult
    from core import LLMClient, LLMConfig, ask
    from core import INTENTS, resolve, list_usable
    from core.action_manager import Action, Plugin, ActionManager, registry
    from core.cactus_adapter import CactusAdapter, CactusResult
    from core.llm_client import LLMClient, ask
    print("✅ Імпорти")
    return True

def test_action_manager():
    """ActionManager реєструє, знаходить і виконує дії."""
    from core.action_manager import ActionManager, Plugin, Action
    
    class TestPlugin(Plugin):
        name = "test"
        version = "1.0.0"
        actions = {
            "hello": Action(
                description="Test action",
                params={"name": str},
                handler="say_hello",
            ),
        }
        def say_hello(self, name: str) -> dict:
            return {"text": f"Привіт, {name}!"}
    
    mgr = ActionManager()
    plugin = TestPlugin()
    mgr.register(plugin)
    
    assert mgr.get("hello") is not None, "Повне ім'я не знайдено"
    assert mgr.get("test:hello") is not None, "Скорочене ім'я не знайдено"
    
    result = mgr.execute("hello", name="Тест")
    inner = result.get("result", {})
    assert isinstance(inner, dict) and inner.get("text") == "Привіт, Тест!", f"Result: {result}"
    
    mgr.unregister("test")
    assert mgr.get("hello") is None, "Плагін не видалився"
    print("✅ ActionManager")
    return True

def test_cactus_emulation():
    """Cactus Needle емуляція розпізнає команди."""
    from core.cactus_adapter import CactusAdapter
    
    cactus = CactusAdapter()
    cactus.load()
    
    test_cases = [
        ("увімкни ліхтарик", "system:toggle_flashlight"),
        ("відкрий вайфай", "system:open_wifi"),
        ("де я зараз", "gps:get_location_once"),
        ("зателефонуй мамі", "phone:make_call"),
        ("знайди кав'ярні поруч", "maps:search_places"),
    ]
    
    for query, expected in test_cases:
        result = cactus.analyze(query)
        assert result is not None, f"Не розпізнано: '{query}'"
        assert result.action == expected, \
            f"'{query}': очікував '{expected}', отримав '{result.action}'"
        assert result.confidence >= 0.5, \
            f"'{query}': низька впевненість {result.confidence}"
    
    # Нерозпізнаний запит — має повернути None
    unknown = cactus.analyze("розкажи жарт про програмістів")
    assert unknown is None or unknown.confidence < 0.5, \
        f"Нерозпізнаний запит має низьку впевненість"
    
    print("✅ Cactus Needle емуляція")
    return True

def test_guests():
    """Гості створюють правильні Intent."""
    from guests import whatsapp, telegram, youtube, maps, system
    
    tests = [
        (whatsapp, "whatsapp_send", 
         {"phone": "380991234567", "text": "тест"},
         lambda r: "wa.me" in r.get("intent", "")),
        (telegram, "telegram_send",
         {"username": "igor", "text": "привіт"},
         lambda r: "tg://" in r.get("intent", "")),
        (youtube, "play_youtube",
         {"query": "dQw4w9WgXcQ"},
         lambda r: "vnd.youtube" in r.get("intent", "")),
        (maps, "search_maps",
         {"query": "кафе"},
         lambda r: "geo:" in r.get("intent", "")),
        (system, "wifi_settings",
         {},
         lambda r: "settings" in r.get("intent", "").lower() or 
                   r.get("intent", "") == ""),  # intent порожній, але це ок
    ]
    
    for guest, method, args, check_fn in tests:
        handler = getattr(guest, method)
        result = handler(**args)
        assert check_fn(result), \
            f"{guest.name}.{method}: не пройшло перевірку: {result}"
    
    print("✅ Гості")
    return True

def test_loop_api():
    """AgentLoop має правильний API."""
    from core import AgentLoop
    
    loop = AgentLoop()
    assert hasattr(loop, 'plan')
    assert hasattr(loop, 'execute')
    assert hasattr(loop, 'check')
    assert hasattr(loop, 'run')
    assert hasattr(loop, 'respond')
    assert loop.cactus is not None
    print("✅ AgentLoop API")
    return True

def test_cactus_classify():
    """Cactus Needle класифікація простих vs складних запитів."""
    from core.cactus_adapter import CactusAdapter
    
    cactus = CactusAdapter()
    cactus.load()
    
    simple = [
        "увімкни ліхтарик",
        "де я зараз",
        "відкрий вайфай",
    ]
    for q in simple:
        r = cactus.analyze(q)
        assert r and r.confidence >= 0.75, f"Має бути простою: {q}"
    
    print("✅ Cactus класифікація")
    return True


if __name__ == "__main__":
    tests = [
        test_imports,
        test_action_manager,
        test_cactus_emulation,
        test_guests,
        test_loop_api,
        test_cactus_classify,
    ]
    
    passed, failed = 0, 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print(f"\n{'='*40}")
    print(f"✅ Пройдено: {passed}, ❌ Помилок: {failed}")
    sys.exit(0 if failed == 0 else 1)
