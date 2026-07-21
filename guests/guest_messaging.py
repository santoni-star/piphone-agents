"""guest_messaging.py — WhatsApp, Telegram, SMS, Phone дії."""

from core.plugin_api import Plugin, Action, registry
from core.android_intents import resolve, INTENTS


class WhatsAppGuest(Plugin):
    name = "whatsapp"
    version = "1.0.0"
    plugin_api_version = "1.0"
    description = "Взаємодія з WhatsApp через Intents"

    actions = {
        "send_message": Action(
            description="Відкрити WhatsApp з готовим повідомленням",
            params={"phone": str, "text": str},
            handler="whatsapp_send",
            examples=["напиши 380991234567 привіт"],
            requires_network=True,
            fallback_intent="https://wa.me/{phone}?text={text}",
        ),
        "open_chat": Action(
            description="Відкрити чат WhatsApp",
            params={"phone": str},
            handler="whatsapp_open",
            requires_network=True,
        ),
    }

    def whatsapp_send(self, phone: str, text: str) -> dict:
        return {"intent": resolve("whatsapp_message", phone=phone, text=text)}

    def whatsapp_open(self, phone: str) -> dict:
        return {"intent": resolve("whatsapp_open", phone=phone)}


class TelegramGuest(Plugin):
    name = "telegram"
    version = "1.0.0"
    plugin_api_version = "1.0"
    description = "Взаємодія з Telegram через Intents"

    actions = {
        "send_message": Action(
            description="Відкрити Telegram з готовим повідомленням",
            params={"username": str, "text": str},
            handler="telegram_send",
            examples=["напиши @igor привіт"],
            requires_network=True,
            fallback_intent="tg://resolve?domain={username}&text={text}",
        ),
        "open_chat": Action(
            description="Відкрити чат/канал Telegram",
            params={"username": str},
            handler="telegram_open",
            requires_network=True,
        ),
    }

    def telegram_send(self, username: str, text: str) -> dict:
        return {"intent": resolve("telegram_message", username=username, text=text)}

    def telegram_open(self, username: str) -> dict:
        return {"intent": resolve("telegram_open", username=username)}


class SMSGuest(Plugin):
    name = "sms"
    version = "1.0.0"
    plugin_api_version = "1.0"
    description = "Відправка SMS"

    actions = {
        "send_sms": Action(
            description="Відкрити SMS з готовим текстом",
            params={"phone": str, "text": str},
            handler="sms_send",
            examples=["відправ sms 380991234567 буду о 6"],
        ),
    }

    def sms_send(self, phone: str, text: str) -> dict:
        return {"intent": resolve("sms_send", phone=phone, text=text)}


class PhoneGuest(Plugin):
    name = "phone"
    version = "1.0.0"
    plugin_api_version = "1.0"
    description = "Телефонні дзвінки"

    actions = {
        "make_call": Action(
            description="Зателефонувати на номер",
            params={"phone": str},
            handler="phone_call",
            examples=["зателефонуй мамі", "подзвони 380991234567"],
        ),
    }

    def phone_call(self, phone: str) -> dict:
        return {"intent": resolve("phone_call", phone=phone)}


# ─── Автореєстрація ──────────────────────────────────────
whatsapp = WhatsAppGuest()
telegram = TelegramGuest()
sms = SMSGuest()
phone = PhoneGuest()
