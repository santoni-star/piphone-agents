#!/usr/bin/env python3
"""
android_intents.py — База Android Intent схем.

Кожен Intent — це рядок, який можна передати в:
    am start -a ACTION -d "intent_string"
або через Android startActivity(Intent).

Поповнюється тільки додаванням. Старі записи не змінюються.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class IntentScheme:
    """Одна Intent схема."""
    action: str          # ACTION_VIEW, ACTION_SEND, etc.
    intent: str          # "https://wa.me/{phone}?text={text}"
    package: str = ""    # com.google.android.youtube, etc.
    description: str = ""
    requires_root: bool = False
    requires_accessibility: bool = False


# ─── БАЗА INTENT СХЕМ ────────────────────────────────────
# Key: ім'я дії → IntentScheme
# ТІЛЬКИ ДОДАВАТИ. Не змінювати і не видаляти.

INTENTS: dict[str, IntentScheme] = {

    # ── Комунікація ───────────────────────────────────────

    "telegram_message": IntentScheme(
        action="android.intent.action.VIEW",
        intent="tg://resolve?domain={username}&text={text}",
        description="Відкрити Telegram чат з повідомленням",
    ),
    "telegram_open": IntentScheme(
        action="android.intent.action.VIEW",
        intent="tg://resolve?domain={username}",
        description="Відкрити Telegram чат/канал",
    ),
    "whatsapp_message": IntentScheme(
        action="android.intent.action.VIEW",
        intent="https://wa.me/{phone}?text={text}",
        description="Відкрити WhatsApp з текстом повідомлення",
    ),
    "whatsapp_open": IntentScheme(
        action="android.intent.action.VIEW",
        intent="https://wa.me/{phone}",
        description="Відкрити WhatsApp чат",
    ),
    "sms_send": IntentScheme(
        action="android.intent.action.VIEW",
        intent="sms:{phone}?body={text}",
        description="Відкрити SMS з текстом",
    ),
    "phone_call": IntentScheme(
        action="android.intent.action.VIEW",
        intent="tel:{phone}",
        description="Зателефонувати на номер",
    ),

    # ── YouTube ───────────────────────────────────────────

    "youtube_video": IntentScheme(
        action="android.intent.action.VIEW",
        intent="vnd.youtube:{video_id}",
        package="com.google.android.youtube",
        description="Відкрити конкретне YouTube відео",
    ),
    "youtube_search": IntentScheme(
        action="android.intent.action.VIEW",
        intent="https://www.youtube.com/results?search_query={query}",
        description="Пошук на YouTube",
    ),

    # ── Карти та навігація ────────────────────────────────

    "maps_directions": IntentScheme(
        action="android.intent.action.VIEW",
        intent="google.navigation:q={lat},{lon}",
        description="Прокласти маршрут до координат",
    ),
    "maps_search": IntentScheme(
        action="android.intent.action.VIEW",
        intent="geo:0,0?q={query}",
        description="Пошук місць на Google Картах",
    ),
    "maps_coords": IntentScheme(
        action="android.intent.action.VIEW",
        intent="geo:{lat},{lon}?q={label}",
        description="Показати координати на мапі",
    ),

    # ── Система ───────────────────────────────────────────

    "wifi_settings": IntentScheme(
        action="android.settings.WIFI_SETTINGS",
        intent="",
        description="Відкрити налаштування Wi-Fi",
    ),
    "bluetooth_settings": IntentScheme(
        action="android.settings.BLUETOOTH_SETTINGS",
        intent="",
        description="Відкрити налаштування Bluetooth",
    ),
    "battery_info": IntentScheme(
        action="android.intent.action.BATTERY_CHANGED",
        intent="",
        description="Отримати інформацію про батарею",
    ),

    # ── Нотатки ───────────────────────────────────────────

    "keep_new_note": IntentScheme(
        action="android.intent.action.VIEW",
        intent="https://keep.google.com/new",
        description="Створити нову нотатку в Google Keep",
    ),

    # ── Контакти ──────────────────────────────────────────

    "contacts_open": IntentScheme(
        action="android.intent.action.VIEW",
        intent="content://contacts/people/",
        description="Відкрити контакти",
    ),
}


def resolve(name: str, **kwargs) -> str:
    """
    Отримати готовий Intent рядок з підставленими аргументами.

    Приклад:
        resolve("telegram_message", username="igor", text="привіт")
        → "tg://resolve?domain=igor&text=привіт"
    """
    scheme = INTENTS.get(name)
    if not scheme:
        return ""
    if scheme.requires_root or scheme.requires_accessibility:
        return ""  # не використовуємо
    try:
        return scheme.intent.format(**kwargs)
    except KeyError:
        # Перевіряємо чи не треба TODO
        if "{" in scheme.intent:
            return scheme.intent  # повертаємо шаблон
        return scheme.intent


def list_usable() -> list[str]:
    """Список Intent схем, які працюють без root/Accessibility."""
    return [
        name for name, s in sorted(INTENTS.items())
        if not s.requires_root and not s.requires_accessibility
    ]
