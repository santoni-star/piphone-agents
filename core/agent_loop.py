#!/usr/bin/env python3
"""
agent_loop.py — спільний агентний цикл для всіх PiPhone агентів.

plan → execute → check → (repeat or respond)

Архітектура:
  plan()     → Cactus Needle (якщо >75% впевненості) або LLM
  execute()  → ActionManager, Intent, shell, або текст
  check()    → перевірка чи треба ще крок (або повтор при помилці)
  respond()  → текст, TTS, або сповіщення (залежить від агента)

Змінювати цей файл не можна. Якщо треба змінити поведінку —
створіть підклас і перевизначте потрібний метод.
"""

from __future__ import annotations
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from core.action_manager import registry as actions
from core.llm_client import LLMClient, LLMConfig
from core.cactus_adapter import CactusAdapter, CactusResult

logger = logging.getLogger("agent_loop")


@dataclass
class AgentContext:
    """Контекст виконання — передається через увесь цикл."""
    query: str = ""
    history: list = field(default_factory=list)
    max_steps: int = 10
    step: int = 0
    response: str = ""
    last_action: Optional[dict] = None
    last_result: Optional[dict] = None


class AgentLoop:
    """
    Основний агентний цикл.

    Підкласи можуть перевизначати:
    - get_input()    — як отримати запит
    - send_output()  — як відповісти
    - execute_action() — як виконати дію
    """

    def __init__(self, llm_config: Optional[LLMConfig] = None,
                 cactus_path: str = ""):
        # LLM
        self.llm = None
        if llm_config is not None:
            self.llm = LLMClient(config=llm_config)
        else:
            try:
                self.llm = LLMClient(provider="opencode-zen")
            except Exception:
                logger.warning("LLM не налаштовано")

        # Cactus Needle
        self.cactus = CactusAdapter(model_path=cactus_path)

        # Контекст
        self.context = AgentContext()

    # ─── Інтерфейс для підкласів ──────────────────────────

    def get_input(self) -> str:
        """Отримати запит. Перевизначити для голосу/сповіщень."""
        return input(">>> ")

    def send_output(self, text: str):
        """Відповісти. Перевизначити для TTS/сповіщень."""
        print(f"\n{text}\n")

    def execute_action(self, action_name: str, args: dict) -> dict:
        """
        Виконати дію. Перевизначити для Android Intent виконання.

        За замовчуванням — через ActionManager.
        """
        return actions.execute(action_name, **args)

    # ─── Потік даних ──────────────────────────────────────

    def plan(self, query: str) -> dict:
        """
        Крок 1: Визначити що робити.

        Стратегія:
          1. Cactus Needle (якщо >75%) → миттєво
          2. LLM → якщо Cactus не впевнений
          3. fallback → відповісти текстом
        """
        # Крок 1: Cactus Needle (reflex)
        cactus_result = self.cactus.analyze(query)
        if cactus_result and cactus_result.confidence >= 0.75:
            logger.info(f"Cactus Needle: {cactus_result.action} "
                        f"({cactus_result.confidence:.0%})")
            return {
                "action": cactus_result.action,
                "args": cactus_result.args,
                "confidence": cactus_result.confidence,
                "source": "cactus",
            }

        # Крок 2: LLM
        if self.llm:
            plan = self._plan_with_llm(query)
            if plan and plan.get("action"):
                plan["source"] = "llm"
                return plan

        # Крок 3: Fallback
        return {
            "action": "reply",
            "args": {"text": f"Отримано: {query[:200]}..."
                     "\n(Базовий режим — Cactus не впізнав команду, "
                     "LLM недоступний)"},
            "source": "fallback",
        }

    def execute(self, plan: dict) -> dict:
        """
        Крок 2: Виконати заплановану дію.
        """
        action = plan.get("action", "reply")
        args = plan.get("args", {})

        logger.info(f"Виконую: {action} args={args}")

        # Спеціальні дії
        if action == "reply":
            return {"result": args.get("text", "")}
        
        if action == "compound":
            results = []
            for step in args.get("steps", []):
                r = self.execute_action(
                    step.get("name", ""),
                    step.get("args", {}),
                )
                results.append(r)
            return {"result": results, "completed": len(results)}

        # Звичайна дія → через ActionManager
        return self.execute_action(action, args)

    def check(self, plan: dict, result: dict) -> bool:
        """
        Крок 3: Перевірити чи треба ще крок.

        Повертає True, якщо треба повторити цикл (напр. при помилці).
        """
        if "error" in result and self.context.step < self.context.max_steps:
            logger.warning(f"Помилка: {result['error']}. Повтор...")
            return True
        if result.get("requires_followup"):
            return True
        return False

    def respond(self, result: dict) -> str:
        """
        Сформувати відповідь для користувача.
        """
        if "error" in result:
            return f"❌ {result['error']}"

        data = result.get("result", "")

        # dict → текст
        if isinstance(data, dict):
            # Якщо це Intent — показуємо що буде виконано
            if "intent" in data:
                intent = data["intent"]
                if intent:
                    return f"🔗 Відкриваю: {intent[:100]}"
                return "🔗 Посилання порожнє"
            return data.get("text", json.dumps(data, ensure_ascii=False))

        return str(data)

    # ─── Основний цикл ────────────────────────────────────

    def run(self, query: Optional[str] = None) -> str:
        """
        Повний агентний цикл.

        plan → execute → check → (повтор при помилці або respond)
        """
        self.context = AgentContext(query=query or self.get_input())
        
        if not self.context.query:
            return ""

        logger.info(f"Запит: {self.context.query}")

        while self.context.step < self.context.max_steps:
            self.context.step += 1
            logger.info(f"Крок {self.context.step}/{self.context.max_steps}")

            # Plan
            plan = self.plan(self.context.query)
            self.context.last_action = plan
            self.context.history.append({"step": self.context.step,
                                         "type": "plan", "plan": plan})
            logger.debug(f"План: {json.dumps(plan, ensure_ascii=False)}")

            # Execute
            result = self.execute(plan)
            self.context.last_result = result
            self.context.history.append({"step": self.context.step,
                                         "type": "result", "result": result})

            # Check — чи треба ще крок?
            if not self.check(plan, result):
                break

        # Формуємо і надсилаємо відповідь
        self.context.response = self.respond(self.context.last_result or {})
        self.send_output(self.context.response)
        return self.context.response

    # ─── Допоміжні ────────────────────────────────────────

    def _plan_with_llm(self, query: str) -> dict:
        """Попросити LLM визначити дію."""
        if not self.llm:
            return {}

        available = actions.list_safe()
        system = (
            "Ти — агент для Android. Твоя задача — визначити яку дію "
            "виконати за запитом користувача.\n\n"
            "Доступні дії:\n"
            + json.dumps(available, indent=2, ensure_ascii=False) +
            "\n\n"
            "Відповідай ТІЛЬКИ JSON без пояснень у форматі:\n"
            '{"action": "ім\'я_дії", "args": {"ключ": "значення"}}\n'
            'Якщо жодна дія не підходить: {"action": "reply", '
            '"args": {"text": "відповідь"}}'
        )

        schema = {
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "args": {"type": "object"},
            },
            "required": ["action", "args"],
        }

        response = self.llm.chat_structured(query, system, schema)
        if "error" not in response:
            return response
        return {}

    def reset(self):
        """Скинути стан агента."""
        self.context = AgentContext()
        if self.llm:
            self.llm.reset()
