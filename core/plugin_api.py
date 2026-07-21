#!/usr/bin/env python3
"""
plugin_api.py — Plugin/API для гостей.

Кожен гість (плагін) реєструє свої дії в ActionManager.
Будь-який агент може використовувати будь-якого гостя.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class Action:
    """Одна дія, яку може виконати гість."""
    description: str
    params: dict[str, type]  # {"name": str}
    handler: str             # ім'я методу
    examples: list[str] = field(default_factory=list)
    requires_network: bool = False
    fallback_intent: str = ""
    requires_root: bool = False
    requires_accessibility: bool = False


class Plugin:
    """Базовий клас для всіх гостей."""
    name: str = "unnamed"
    version: str = "0.0.0"
    plugin_api_version: str = "1.0"
    description: str = ""
    actions: dict[str, Action] = {}

    def __post_init__(self):
        """Автоматично реєструється в глобальному реєстрі."""
        from core.action_manager import registry
        registry.register(self)


class ActionManager:
    """Реєстр усіх дій від усіх плагінів."""

    def __init__(self):
        self._actions: dict[str, tuple[Plugin, Action]] = {}
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin):
        """Зареєструвати плагін і всі його дії."""
        self._plugins[plugin.name] = plugin
        for name, action in plugin.actions.items():
            full_name = f"{plugin.name}:{name}"
            self._actions[full_name] = (plugin, action)
            # Також реєструємо скорочене ім'я (без префікса)
            if name not in self._actions:
                self._actions[name] = (plugin, action)

    def unregister(self, plugin_name: str):
        """Видалить плагін (для тестів)."""
        if plugin_name in self._plugins:
            plugin = self._plugins[plugin_name]
            for name in plugin.actions:
                full = f"{plugin_name}:{name}"
                self._actions.pop(full, None)
                self._actions.pop(name, None)
            del self._plugins[plugin_name]

    def get(self, name: str) -> Optional[Action]:
        """Отримати дію за ім'ям."""
        pair = self._actions.get(name)
        return pair[1] if pair else None

    def execute(self, action_name: str, **kwargs) -> dict:
        """Виконати дію."""
        pair = self._actions.get(action_name)
        if not pair:
            return {"error": f"Action '{action_name}' not found"}
        plugin, action = pair
        handler = getattr(plugin, action.handler, None)
        if not handler:
            return {"error": f"Handler '{action.handler}' not found in {plugin.name}"}
        # Фільтруємо kwargs: залишаємо тільки ті, що є в params
        valid_kwargs = {k: v for k, v in kwargs.items() if k in action.params}
        try:
            result = handler(**valid_kwargs)
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}

    def list(self, plugin_name: str = None) -> list[dict]:
        """Список усіх дій (для LLM промпту)."""
        result = []
        for name, (plugin, action) in sorted(self._actions.items()):
            if plugin_name and plugin.name != plugin_name:
                continue
            result.append({
                "name": name,
                "plugin": plugin.name,
                "description": action.description,
                "params": list(action.params.keys()),
                "requires_root": action.requires_root,
                "requires_accessibility": action.requires_accessibility,
            })
        return result

    @property
    def plugins(self) -> dict[str, Plugin]:
        return dict(self._plugins)


# Глобальний реєстр (синглтон)
registry = ActionManager()
