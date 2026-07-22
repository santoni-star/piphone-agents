#!/usr/bin/env python3
"""
cactus_adapter.py — Адаптер для Cactus Needle (26M параметрів).

Cactus Needle — це pure-attention модель для function calling.
https://github.com/cactus-compute/needle

Архітектура адаптера:
  1. Спрощена емуляція (якщо модель не завантажена)
  2. Реальна інтеграція (через JNI/ONNX, коли модель доступна)

Проста емуляція працює через keyword matching — достатньо 
для Phase 0-1, поки не інтегровано реальну модель.
"""

from __future__ import annotations
import json
import logging
import re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("cactus_adapter")


@dataclass
class CactusResult:
    """Результат від Cactus Needle."""
    action: str           # Ім'я дії
    args: dict            # Аргументи дії
    confidence: float     # Впевненість (0.0 - 1.0)
    source: str = "cactus"  # "cactus" або "llm"


class CactusAdapter:
    """
    Адаптер для Cactus Needle.

    У Phase 0-1 використовує спрощену емуляцію.
    У Phase 2+ буде реальна інтеграція через ONNX/JNI.
    """

    def __init__(self, model_path: str = "", use_emulation: bool = True):
        self.model_path = model_path
        self._loaded = False
        self._use_emulation = use_emulation
        self._patterns: dict[str, list[dict]] = {}  # action → [{pattern, extract}]

    # ─── Завантаження моделі ──────────────────────────────

    def load(self) -> bool:
        """
        Завантажити Cactus Needle модель.
        Повертає True якщо модель завантажено, False якщо треба емуляція.
        """
        if self._use_emulation:
            logger.info("Cactus: використовується емуляція (Phase 0-1)")
            self._loaded = True
            return True

        # TODO: Phase 2 — реальне завантаження через ONNX
        # import onnxruntime
        # self._session = onnxruntime.InferenceSession(self.model_path)
        logger.warning("Cactus: реальна модель ще не інтегрована")
        return False

    def is_loaded(self) -> bool:
        return self._loaded

    # ─── Аналіз запиту ────────────────────────────────────

    def analyze(self, query: str, 
                available_actions: Optional[list[dict]] = None) -> Optional[CactusResult]:
        """
        Визначити яку дію виконати за запитом.

        Args:
            query: Запит користувача
            available_actions: Список доступних дій (якщо None — використовуємо вбудовані)

        Returns:
            CactusResult або None (якщо не впевнені)
        """
        if not self._loaded:
            self.load()

        query_lower = query.lower().strip()

        # Спрощена емуляція через ключові слова
        result = self._keyword_match(query_lower, available_actions)
        if result and result.confidence >= 0.5:
            return result

        # TODO: Phase 2 — реальний інференс через ONNX
        return None

    # ─── Емуляція (Phase 0-1) ─────────────────────────────

    def _keyword_match(self, query: str, 
                       available_actions: Optional[list[dict]] = None) -> Optional[CactusResult]:
        """Спрощене співставлення ключових слів для Phase 0-1."""

        # Шаблони: (ключові слова, дія, {аргументи}, впевненість)
        patterns = [
            # ── Telegram ──
            (r'(?:напиши|відправ|надішли)\s.*?(?:telegram|телеграм|тг)\s*[:@]?\s*(\w+)\s+(.+)', 
             "telegram:send_message", {"username": "{1}", "text": "{2}"}, 0.8),

            # ── WhatsApp ──
            (r'(?:напиши|відправ|надішли)\s.*?(?:whatsapp|ватсап|вацап)\s*(\d+)\s+(.+)',
             "whatsapp:send_message", {"phone": "{1}", "text": "{2}"}, 0.8),

            # ── SMS ──
            (r'(?:напиши|відправ|надішли)\s.*?sms\s*(\d+)\s+(.+)',
             "sms:send_sms", {"phone": "{1}", "text": "{2}"}, 0.8),

            # ── Дзвінки ──
            (r'(?:зателефонуй|подзвони|дзвінок)\s*(?:\w+\s+)?(\d+)',
             "phone:make_call", {"phone": "{1}"}, 0.8),
            (r'зателефонуй\s+(?:мамі|тату|мам|тат)',
             "phone:make_call", {"phone": "contact"}, 0.65),

            # ── YouTube ──
            (r'знайди\s+(?:відео|youtube|ютуб)\s+(.+)',
             "youtube:search_video", {"query": "{1}"}, 0.85),
            (r'(?:увімкни|відкрий|знайди)\s.*?(?:відео|youtube|ютуб)',
             "youtube:search_video", {"query": query}, 0.8),
            (r'(?:увімкни|відкрий)\s+(\w{11})\s*$',
             "youtube:play_video", {"query": "{1}"}, 0.75),

            # ── Карти ──
            (r'(?:проклади|покажи|знайди)\s.*?(?:маршрут|дорогу|шлях)',
             "maps:navigate_to", {"lat": 50.45, "lon": 30.52}, 0.75),
            (r'(?:де|знайди)\s.*?(?:кав\'ярн|ресторан|аптек|магазин)',
             "maps:search_places", {"query": query}, 0.75),

            # ── GPS ──
            (r'де\s+я\s*(?:зараз|знаходжусь)?\s*\??$',
             "gps:get_location_once", {}, 0.85),
            (r'(?:моє|поточн)\s*місце\s*(?:знаходження|розташування)',
             "gps:get_location_once", {}, 0.8),

            # ── Система ──
            (r'(?:увімкни|відкрий)\s.*?(?:вайфай|wifi|Wi-Fi)',
             "system:open_wifi", {}, 0.9),
            (r'(?:увімкни|відкрий)\s.*?(?:блютуз|bluetooth)',
             "system:open_bluetooth", {}, 0.9),
            (r'(?:який|скільки)\s.*?(?:заряд|батарея|відсотків)',
             "system:get_battery", {}, 0.85),
            (r'(?:увімкни|включи)\s.*?(?:ліхтарик|світло)',
             "system:toggle_flashlight", {"state": True}, 0.85),
            (r'(?:вимкни|погаси)\s.*?(?:ліхтарик|світло)',
             "system:toggle_flashlight", {"state": False}, 0.85),

            # ── Нотатки ──
            (r'запам\'ятай\s+(.+)',
             "notes:create_note", {"text": "{1}"}, 0.8),
            (r'(?:запиши|створи)\s.*?(?:нотатку|замітку|нагадування)\s+(.+)',
             "notes:create_note", {"text": "{1}"}, 0.75),
        ]

        best: Optional[CactusResult] = None
        
        for pattern, action_name, args_template, confidence in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                # Підставляємо аргументи з шаблону
                resolved_args = {}
                for key, val in args_template.items():
                    if isinstance(val, str) and val.startswith("{") and val.endswith("}"):
                        idx = int(val[1:-1])
                        resolved_args[key] = match.group(idx) if match.groups() else val
                    else:
                        resolved_args[key] = val

                # Додаємо повний текст для контексту
                if "query" in args_template and args_template["query"] == query:
                    pass  # query вже встановлено

                candidate = CactusResult(
                    action=action_name,
                    args=resolved_args,
                    confidence=confidence,
                )

                if not best or candidate.confidence > best.confidence:
                    best = candidate

        return best

    def classify(self, query: str) -> bool:
        """
        Перевірити чи Cactus Needle може обробити цей запит.
        True — модель впевнена, False — треба LLM.
        """
        result = self.analyze(query)
        return result is not None and result.confidence >= 0.75
