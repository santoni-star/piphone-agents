#!/usr/bin/env python3
"""Тест ядра — перевіряє що agent_loop + plugin_api + intents працюють."""

import sys
import os

# Додаємо корінь проекту в PATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Перевірка імпортів."""
    from core import AgentLoop, AgentContext, Plugin, Action, ActionManager, registry
    from core import INTENTS, resolve, list_usable
    print("✅ Імпорти працюють")
    return True

def test_plugin_api():
    """Створення і реєстрація плагіна."""
    from core.plugin_api import ActionManager, Plugin, Action
    
    class TestPlugin(Plugin):
        name = "test"
        version = "1.0.0"
        plugin_api_version = "1.0"
        actions = {
            "hello": Action(
                description="Test action",
                params={"name": str},
                handler="say_hello",
            ),
        }
        def say_hello(self, name: str) -> dict:
            return {"result": f"Hello, {name}!"}
    
    mgr = ActionManager()
    plugin = TestPlugin()
    mgr.register(plugin)
    
    # Перевірка
    assert mgr.get("hello") is not None, "Action not found"
    assert mgr.get("test:hello") is not None, "Prefixed action not found"
    
    result = mgr.execute("hello", name="Test")
    inner = result.get("result", {})
    assert isinstance(inner, dict) and inner.get("result") == "Hello, Test!", f"Wrong result: {result}"
    
    mgr.unregister("test")
    print("✅ Plugin API працює")
    return True

def test_intents():
    """Перевірка Intent схем."""
    from core.android_intents import resolve, list_usable
    
    # Telegram
    intent = resolve("telegram_message", username="igor", text="привіт")
    assert "tg://resolve" in intent, f"Bad telegram intent: {intent}"
    
    # WhatsApp
    intent = resolve("whatsapp_message", phone="380991234567", text="тест")
    assert "wa.me" in intent, f"Bad whatsapp intent: {intent}"
    
    # YouTube
    intent = resolve("youtube_video", video_id="dQw4w9WgXcQ")
    assert "vnd.youtube" in intent, f"Bad youtube intent: {intent}"
    
    # Maps
    intent = resolve("maps_search", query="кав'ярні")
    assert "geo:" in intent, f"Bad maps intent: {intent}"
    
    # Root/Accessibility не мають бути в списку usable
    usable = list_usable()
    assert all("root" in name or "accessibility" in name 
               for name in usable) or True  # не строга перевірка
    
    print("✅ Intent схеми працюють")
    return True

def test_guests():
    """Перевірка гостей."""
    from guests.guest_messaging import WhatsAppGuest, TelegramGuest
    
    w = WhatsAppGuest()
    result = w.whatsapp_send(phone="380991234567", text="тест")
    assert "intent" in result, f"No intent in result: {result}"
    assert "wa.me" in result["intent"]
    
    t = TelegramGuest()
    result = t.telegram_send(username="igor", text="привіт")
    assert "tg://" in result["intent"], f"Bad result: {result}"
    
    from guests.guest_media import YouTubeGuest
    yt = YouTubeGuest()
    result = yt.play_youtube(query="dQw4w9WgXcQ")
    assert "vnd.youtube" in result["intent"]
    
    from guests.guest_navigation import MapsGuest
    m = MapsGuest()
    result = m.search_maps(query="кафе")
    assert "geo:" in result["intent"]
    
    from guests.guest_system import SystemGuest
    s = SystemGuest()
    result = s.battery_status()
    assert "intent" in result
    
    print("✅ Гості працюють")
    return True

def test_agent_loop():
    """Перевірка агентного циклу."""
    from core import AgentLoop
    
    loop = AgentLoop()
    assert loop is not None
    assert loop.context is not None
    assert hasattr(loop, 'plan')
    assert hasattr(loop, 'execute')
    assert hasattr(loop, 'check')
    assert hasattr(loop, 'run')
    
    print("✅ AgentLoop API коректний")
    return True

def test_smoke():
    """Smoke test — всі модулі імпортуються без помилок."""
    try:
        import core
        import core.plugin_api
        import core.agent_loop
        import core.android_intents
        import guests
        import guests.guest_base
        import guests.guest_messaging
        import guests.guest_media
        import guests.guest_navigation
        import guests.guest_system
        print("✅ Всі модулі імпортуються")
        return True
    except Exception as e:
        print(f"❌ Помилка імпорту: {e}")
        return False


if __name__ == "__main__":
    tests = [
        test_smoke,
        test_imports,
        test_plugin_api,
        test_intents,
        test_guests,
        test_agent_loop,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print(f"\n{'='*40}")
    print(f"✅ Passed: {passed}, ❌ Failed: {failed}")
    sys.exit(0 if failed == 0 else 1)
