#!/usr/bin/env python3
"""
action_manager.py — Реєстр дій та інструментів.

Центральне місце, де реєструються всі дії від усіх плагінів-гостей.
Будь-який агент (Координатор, Секретар, Проактивний) бере дії звідси.

ActionManager — це singleton. registry — глобальний екземпляр.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

logger = logging.getLogger("action_manager")


@dataclass
class Action:
    """Одна дія, яку може виконати плагін."""
    description: str
    params: dict[str, type]
    handler: str               # Ім'я методу в плагіні
    plugin_name: str = ""      # Заповнюється автоматично при реєстрації
    examples: list[str] = field(default_factory=list)
    requires_network: bool = False
    fallback_intent: str = ""
    requires_root: bool = False
    requires_accessibility: bool = False


# ─── Відкладений реєстратор ──────────────────────────────
_registry_ref = None

def _set_registry(reg):
    global _registry_ref
    _registry_ref = reg

def _get_registry():
    return _registry_ref


class Plugin:
    """Базовий клас для всіх плагінів-гостей."""
    
    name: str = "unnamed"
    version: str = "0.0.0"
    plugin_api_version: str = "1.0"
    description: str = ""
    actions: dict[str, Action] = {}

    def __init__(self):
        self._register_actions()
        # Автореєстрація в глобальному реєстрі
        r = _get_registry()
        if r is not None:
            r.register(self)

    def _register_actions(self):
        """Автоматично проставляє plugin_name в кожній дії."""
        for name, action in self.actions.items():
            action.plugin_name = self.name

    def get_handler(self, action_name: str) -> Optional[Callable]:
        """Знайти метод-обробник для дії."""
        action = self.actions.get(action_name)
        if not action:
            return None
        return getattr(self, action.handler, None)


class ActionManager:
    """Реєстр усіх дій від усіх плагінів."""

    def __init__(self):
        self._actions: dict[str, tuple[Plugin, Action]] = {}
        self._plugins: dict[str, Plugin] = {}

    # ─── Реєстрація ───────────────────────────────────────

    def register(self, plugin: Plugin) -> None:
        """Зареєструвати плагін і всі його дії."""
        self._plugins[plugin.name] = plugin
        for name, action in plugin.actions.items():
            # Повне ім'я: "telegram:send_message"
            full_name = f"{plugin.name}:{name}"
            self._actions[full_name] = (plugin, action)
            # Скорочене ім'я (без префікса), якщо не зайнято
            if name not in self._actions:
                self._actions[name] = (plugin, action)
        logger.info(f"Зареєстровано плагін '{plugin.name}' "
                     f"з {len(plugin.actions)} діями")

    def register_from_path(self, module_path: str) -> Optional[str]:
        """
        Зареєструвати плагін з Python-файлу.
        Шукає клас, що наслідує Plugin, у вказаному модулі.

        Args:
            module_path: 'guests.guest_messaging' або '/abs/path/file.py'

        Returns:
            Ім'я плагіна або None
        """
        try:
            import importlib
            spec = importlib.util.spec_from_file_location(
                module_path.replace('/', '.'),
                module_path if module_path.endswith('.py') 
                else module_path.replace('.', '/') + '.py'
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module_path
        except Exception as e:
            logger.warning(f"Не вдалося завантажити {module_path}: {e}")
        return None

    def unregister(self, plugin_name: str) -> bool:
        """Видалити плагін (для тестів)."""
        if plugin_name in self._plugins:
            plugin = self._plugins[plugin_name]
            for name in plugin.actions:
                full = f"{plugin_name}:{name}"
                self._actions.pop(full, None)
                self._actions.pop(name, None)
            del self._plugins[plugin_name]
            return True
        return False

    # ─── Отримання дій ────────────────────────────────────

    def get(self, name: str) -> Optional[Action]:
        """Отримати дію за ім'ям."""
        pair = self._actions.get(name)
        return pair[1] if pair else None

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Отримати плагін за ім'ям."""
        return self._plugins.get(name)

    def list(self, plugin_name: Optional[str] = None) -> list[dict]:
        """
        Список усіх зареєстрованих дій.

        Args:
            plugin_name: Фільтр за плагіном (опціонально)

        Returns:
            Список словників з описами дій
        """
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
                "requires_network": action.requires_network,
            })
        return result

    def list_safe(self) -> list[dict]:
        """Список дій, які не потребують root/Accessibility."""
        filtered = []
        for name, (plugin, action) in sorted(self._actions.items()):
            if not action.requires_root and not action.requires_accessibility:
                filtered.append({
                    "name": name,
                    "plugin": plugin.name,
                    "description": action.description,
                })
        return filtered

    # ─── Виконання ────────────────────────────────────────

    def execute(self, action_name: str, **kwargs) -> dict:
        """
        Виконати дію.

        Args:
            action_name: Ім'я дії ("telegram:send_message" або "send_message")
            **kwargs: Аргументи для дії

        Returns:
            {"result": ...} або {"error": ...}
        """
        pair = self._actions.get(action_name)
        if not pair:
            return {"error": f"Дію '{action_name}' не знайдено. "
                             f"Доступні: {list(self._actions.keys())[:10]}..."}

        plugin, action = pair
        handler = getattr(plugin, action.handler, None)
        if not handler:
            return {"error": f"Обробник '{action.handler}' не знайдено "
                             f"в плагіні '{plugin.name}'"}

        # Фільтруємо: тільки ті параметри, що є в описі дії
        valid_kwargs = {k: v for k, v in kwargs.items() if k in action.params}

        try:
            result = handler(**valid_kwargs)
            return {"result": result}
        except Exception as e:
            logger.exception(f"Помилка виконання '{action_name}': {e}")
            return {"error": str(e)}

    # ─── Властивості ──────────────────────────────────────

    @property
    def plugins(self) -> dict[str, Plugin]:
        return dict(self._plugins)

    @property
    def action_count(self) -> int:
        return len(self._actions)

    def __repr__(self) -> str:
        return (f"ActionManager("
                f"плагінів={len(self._plugins)}, "
                f"дій={len(self._actions)})")


# ─── Глобальний реєстр (singleton) ────────────────────────
registry = ActionManager()
_set_registry(registry)
