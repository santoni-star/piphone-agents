"""
core.__init__ — імпортує всі ключові компоненти ядра.
"""
from core.agent_loop import AgentLoop, AgentContext
from core.action_manager import Action, Plugin, ActionManager, registry
from core.cactus_adapter import CactusAdapter, CactusResult
from core.llm_client import LLMClient, LLMConfig, ask
from core.android_intents import INTENTS, resolve, list_usable

__all__ = [
    # Agent loop
    "AgentLoop", "AgentContext",
    # Action system
    "Action", "Plugin", "ActionManager", "registry",
    # Cactus Needle
    "CactusAdapter", "CactusResult",
    # LLM
    "LLMClient", "LLMConfig", "ask",
    # Android Intents
    "INTENTS", "resolve", "list_usable",
]
