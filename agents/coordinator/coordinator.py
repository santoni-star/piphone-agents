#!/usr/bin/env python3
"""
coordinator.py — CLI точка входу для агента-координатора.

Використання:
    piphone                        # якщо встановлено через pip
    python3 -m agents.coordinator.coordinator
    python3 agents/coordinator/coordinator.py
    >>> де я зараз
    >>> /help  — список команд
    >>> /exit  — вихід

Архітектура:
    AgentLoop (plan → execute → check)
      ├── Cactus Needle (емуляція) — миттєво для простих команд
      └── LLM (opencode-zen) — для складних запитів
"""

from __future__ import annotations
import logging
from typing import Optional

from core import AgentLoop, AgentContext, registry
from core.llm_client import LLMConfig
from guests import whatsapp, telegram, sms, phone, youtube, maps, gps, system, notes

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s %(message)s",
)


class Coordinator(AgentLoop):
    """
    Координатор — агент для виконання команд через Android Intents.

    Працює через той самий agent_loop.py (plan → execute → check).
    Додає:
    - CLI-інтерфейс (заміна для APK у Phase 0-1)
    - Обробку спеціальних команд (/help, /exit)
    - Відображення Intent у зручному форматі
    """

    def __init__(self):
        llm_config = None
        try:
            llm_config = LLMConfig(provider="opencode-zen")
        except Exception as e:
            print(f"⚠️ LLM не налаштовано. Працює тільки Cactus: {e}")

        super().__init__(llm_config=llm_config)
        self.running = True

    # ─── CLI ──────────────────────────────────────────────

    HELP_TEXT = """
    Доступні команди:

    Telegram    → @username текст
    WhatsApp    → 380991234567 текст
    SMS         → 380991234567 текст
    Дзвінок     → зателефонуй 380991234567
    YouTube     → увімкни dQw4w9WgXcQ
    YouTube     → знайди відео prodigy girls
    Карти       → знайди кав'ярні поруч
    Маршрут     → проклади маршрут до Києва
    GPS         → де я зараз
    Wi-Fi       → відкрий вайфай
    Bluetooth   → відкрий блютуз
    Батарея     → який заряд
    Ліхтарик    → увімкни ліхтарик
    Нотатка     → запам'ятай купити молоко

    Спеціальні:
    /actions    → список доступних дій
    /help       → ця довідка
    /exit       → вихід
    """

    def get_input(self) -> str:
        """Отримати команду від користувача."""
        try:
            return input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            return "/exit"

    def send_output(self, text: str):
        """Відповісти користувачеві."""
        if text:
            print()
            print(text)
            print()

    def handle_special(self, cmd: str) -> bool:
        """Обробити спеціальну команду. Повертає True якщо оброблено."""
        cmd = cmd.lower()

        if cmd in ("/exit", "/quit", "/q"):
            self.running = False
            print("До побачення!")
            return True

        if cmd in ("/help", "/h"):
            print(self.HELP_TEXT)
            return True

        if cmd == "/actions" or cmd == "/list":
            available = registry.list_safe()
            print(f"\nДоступні дії ({len(available)}):")
            for a in available:
                print(f"  {a['name']:<35} {a['description']}")
            print()
            return True

        if cmd in ("/plugins", "/guests"):
            for name, plugin in registry.plugins.items():
                n_actions = len(plugin.actions)
                print(f"  {name:<15} v{plugin.version}  ({n_actions} дій)")
            print()
            return True

        return False

    # ─── Основний цикл ────────────────────────────────────

    def run_cli(self):
        """Запустити CLI-інтерфейс координатора."""
        print()
        print("🧠 PiPhone Coordinator v0.1")
        print("=" * 40)
        print("  /help — список команд")
        print("  /exit — вихід")
        print()

        while self.running:
            try:
                query = self.get_input()

                if not query:
                    continue

                # Спеціальні команди
                if query.startswith("/"):
                    self.handle_special(query)
                    continue

                # Агентний цикл
                self.run(query)

            except KeyboardInterrupt:
                self.running = False
                print("\nДо побачення!")
            except Exception as e:
                print(f"\n❌ Помилка: {e}\n")


def main():
    """Точка входу для pip-пакета."""
    coordinator = Coordinator()
    coordinator.run_cli()


if __name__ == "__main__":
    main()
