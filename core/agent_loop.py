#!/usr/bin/env python3
"""
agent_loop.py — спільний агентний цикл для всіх PiPhone агентів.

plan → execute → check → (repeat or respond)

Цей цикл НЕ ЗМІНЮЄТЬСЯ між агентами.
Змінюється тільки: як отримується запит, як виконуються дії, як відповідається.
"""

from __future__ import annotations
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Callable

logger = logging.getLogger("agent_loop")


@dataclass
class AgentContext:
    """Контекст виконання — передається через увесь цикл."""
    query: str                     # Початковий запит користувача
    history: list[dict] = field(default_factory=list)
    max_steps: int = 10
    step: int = 0
    response: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class AgentLoop:
    """
    Базова реалізація агентного циклу.

    Підкласи можуть перевизначати:
    - get_input()    — як отримати запит (текст, голос, сповіщення)
    - send_output()  — як відповісти (текст, TTS, сповіщення)
    - execute_action() — як виконати дію (Intent, shell, API)
    """

    def __init__(self, llm_client=None, action_manager=None, cactus=None):
        self.llm = llm_client
        self.actions = action_manager
        self.cactus = cactus  # Cactus Needle adapter
        self.context = AgentContext(query="")

    # ─── Інтерфейс для підкласів ──────────────────────────

    def get_input(self) -> str:
        """Отримати запит від користувача. Перевизначити в підкласі."""
        return input(">>> ")

    def send_output(self, text: str):
        """Відповісти користувачеві. Перевизначити в підкласі."""
        print(text)

    def execute_action(self, action_name: str, args: dict) -> dict:
        """
        Виконати дію.
        Повертає: {"result": ...} або {"error": ...}
        """
        if self.actions:
            action = self.actions.get(action_name)
            if action:
                return action.execute(**args)
        return {"error": f"Action '{action_name}' not found"}

    # ─── Основний цикл ────────────────────────────────────

    def plan(self, query: str, context: AgentContext) -> dict:
        """
        Крок 1: Визначити що робити.
        - Якщо Cactus Needle впевнений (> 75%) — використати його
        - Інакше — запитати LLM
        """
        if self.cactus:
            result = self.cactus.analyze(query)
            if result and result.get("confidence", 0) >= 0.75:
                logger.info(f"Cactus: {result['action']} ({result['confidence']:.0%})")
                return result

        # LLM планування
        if self.llm:
            prompt = self._build_prompt(query, context)
            response = self.llm.chat(prompt)
            return json.loads(response)

        return {"action": "reply", "args": {"text": "Не можу визначити дію"}}

    def execute(self, plan: dict, context: AgentContext) -> dict:
        """Крок 2: Виконати заплановану дію."""
        action = plan.get("action", "reply")
        args = plan.get("args", {})

        if action == "reply":
            return {"result": args.get("text", "")}
        
        if action == "compound":
            # Кілька дій поспіль
            results = []
            for sub_action in args.get("steps", []):
                r = self.execute_action(sub_action["name"], sub_action.get("args", {}))
                results.append(r)
            return {"result": results}

        return self.execute_action(action, args)

    def check(self, plan: dict, result: dict, context: AgentContext) -> bool:
        """Крок 3: Перевірити чи достатньо, або треба ще крок."""
        if "error" in result and context.step < context.max_steps:
            return True  # спробувати ще раз
        if result.get("requires_followup"):
            return True
        return False

    def run(self, query: Optional[str] = None) -> str:
        """Повний цикл: plan → execute → check → (повтор або відповідь)."""
        self.context = AgentContext(query=query or self.get_input())
        
        while self.context.step < self.context.max_steps:
            self.context.step += 1
            
            # Plan
            plan = self.plan(self.context.query, self.context)
            self.context.history.append({"type": "plan", "plan": plan})
            
            # Execute
            result = self.execute(plan, self.context)
            self.context.history.append({"type": "result", "result": result})
            
            # Check
            if not self.check(plan, result, self.context):
                break
        
        # Формуємо відповідь
        self.context.response = self._format_response(self.context)
        self.send_output(self.context.response)
        return self.context.response

    def _build_prompt(self, query: str, context: AgentContext) -> str:
        """Побудувати промпт для LLM."""
        available_actions = self.actions.list() if self.actions else []
        return json.dumps({
            "task": "Визнач що робити з цим запитом. Вибери дію з доступних.",
            "query": query,
            "available_actions": available_actions,
            "history": context.history[-3:],
            "format": {
                "action": "ім'я_дії",
                "args": {"ключ": "значення"}
            }
        })

    def _format_response(self, context: AgentContext) -> str:
        """Сформувати підсумкову відповідь."""
        last = context.history[-1] if context.history else {}
        if last.get("type") == "result":
            result = last.get("result", {})
            if "result" in result:
                return str(result["result"])
            if "error" in result:
                return f"❌ {result['error']}"
        return "Готово."


# ─── Приклад використання ─────────────────────────────────

if __name__ == "__main__":
    # Smoke test
    loop = AgentLoop()
    output = loop.run("Привіт, це тест")
    print(f"Відповідь: {output}")
    print(f"Історія: {len(loop.context.history)} кроків")
