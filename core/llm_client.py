#!/usr/bin/env python3
"""
llm_client.py — HTTP-клієнт для LLM (OpenRouter, DeepSeek, OpenCodeZen, будь-який OpenAI-сумісний).

Використання:
    client = LLMClient(provider="opencode-zen")
    response = client.chat("Привіт, розкажи жарт")
    print(response)

Підтримувані провайдери:
    - opencode-zen (безкоштовний, за замовчуванням)
    - deepseek (дешевий)
    - openrouter (багато моделей)
    - будь-який OpenAI-сумісний
"""

from __future__ import annotations
import json
import logging
import os
import re
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("llm_client")


# ─── Конфігурація провайдерів ────────────────────────────

PROVIDERS = {
    "opencode-zen": {
        "base_url": "https://api.opencode-zen.com/v1",
        "model": "deepseek-v4-flash-free",
        "api_key_env": "OPENCODE_ZEN_API_KEY",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "deepseek/deepseek-chat",
        "api_key_env": "OPENROUTER_API_KEY",
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "model": "claude-sonnet-4",
        "api_key_env": "ANTHROPIC_API_KEY",
    },
}


@dataclass
class LLMConfig:
    """Конфігурація LLM клієнта."""
    provider: str = "opencode-zen"
    model: str = ""
    api_key: str = ""
    base_url: str = ""
    temperature: float = 0.3
    max_tokens: int = 1024
    timeout: int = 30

    def __post_init__(self):
        # Якщо не вказано явно — беремо з конфігурації провайдера
        if not self.api_key and self.provider in PROVIDERS:
            cfg = PROVIDERS[self.provider]
            self.base_url = self.base_url or cfg["base_url"]
            self.model = self.model or cfg["model"]
            env_var = cfg["api_key_env"]
            self.api_key = os.environ.get(env_var, "")
        # Якщо base_url не вказано — OpenAI сумісний формат
        if not self.base_url:
            self.base_url = "https://api.openai.com/v1"


class LLMClient:
    """
    HTTP клієнт для OpenAI-сумісних API.

    Підтримує chat/completions у форматі OpenAI.
    """

    def __init__(self, config: Optional[LLMConfig] = None, **kwargs):
        if config:
            self.config = config
        else:
            self.config = LLMConfig(**kwargs)
        
        # Список повідомлень (історія діалогу)
        self.messages: list[dict] = []

    def chat(self, prompt: str, system: str = "") -> str:
        """
        Надіслати запит до LLM і отримати текстову відповідь.

        Args:
            prompt: Запит користувача
            system: Системний промпт (опціонально)

        Returns:
            Текст відповіді
        """
        # Формуємо повідомлення
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        # Додаємо історію, якщо є
        full_messages = self.messages + messages

        # Формуємо запит
        body = {
            "model": self.config.model,
            "messages": full_messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        # Надсилаємо
        response = self._post(
            f"{self.config.base_url}/chat/completions",
            body,
        )

        # Парсимо відповідь
        content = self._parse_response(response)
        
        # Зберігаємо історію
        self.messages.append({"role": "user", "content": prompt})
        self.messages.append({"role": "assistant", "content": content})

        return content

    def chat_structured(self, prompt: str, system: str = "",
                        schema: Optional[dict] = None) -> dict:
        """
        Надіслати запит і отримати структуровану відповідь (JSON).

        Args:
            prompt: Запит користувача
            system: Системний промпт
            schema: JSON схема для структурованого виводу

        Returns:
            dict з відповіддю
        """
        # Якщо є схема — додаємо вказівку в системний промпт
        if schema:
            schema_hint = (
                f"\n\nВІДПОВІДАЙ ТІЛЬКИ JSON ЗА ЦІЄЮ СХЕМОЮ:\n"
                f"{json.dumps(schema, indent=2, ensure_ascii=False)}\n"
                f"Без пояснень, без додаткового тексту."
            )
            system = system + schema_hint if system else schema_hint

        response = self.chat(prompt, system)

        # Спроба розпарсити JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Спробуємо знайти JSON у відповіді
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            return {"error": "Не вдалося розпарсити JSON", "raw": response}

    def reset(self):
        """Очистити історію діалогу."""
        self.messages = []

    # ─── Приватні методи ──────────────────────────────────

    def _post(self, url: str, body: dict) -> dict:
        """HTTP POST запит."""
        data = json.dumps(body).encode()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }
        
        req = urllib.request.Request(url, data=data, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            logger.error(f"HTTP {e.code}: {error_body}")
            return {
                "error": True,
                "code": e.code,
                "message": error_body,
            }
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"error": True, "message": str(e)}

    def _parse_response(self, response: dict) -> str:
        """Дістати текст з OpenAI-сумісної відповіді."""
        if response.get("error"):
            return f"[Помилка API: {response.get('message', 'невідома')}]"

        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return f"[Неочікуваний формат відповіді: {json.dumps(response)}]"


# ─── Зручна функція для швидкого запиту ──────────────────

def ask(prompt: str, provider: str = "opencode-zen", **kwargs) -> str:
    """Один запит до LLM. Створює клієнт, питає, повертає відповідь."""
    client = LLMClient(provider=provider, **kwargs)
    return client.chat(prompt)


if __name__ == "__main__":
    # Smoke test
    import sys
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Напиши 'OK' і більше нічого"
    print(f"Запит: {prompt}")
    print(f"Відповідь: {ask(prompt)}")
