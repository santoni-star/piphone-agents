"""
plugin_api.py — зворотно сумісний імпорт.
Усі нові розробки використовують core.action_manager напряму.
"""
from core.action_manager import Plugin, Action, ActionManager, registry

__all__ = ["Plugin", "Action", "ActionManager", "registry"]
