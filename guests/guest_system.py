"""guest_system.py — Системні дії: Wi-Fi, ліхтарик, батарея, гучність."""

from core.plugin_api import Plugin, Action, registry
from core.android_intents import resolve


class SystemGuest(Plugin):
    name = "system"
    version = "1.0.0"
    plugin_api_version = "1.0"
    description = "Системні дії Android"

    actions = {
        "open_wifi": Action(
            description="Відкрити налаштування Wi-Fi",
            params={},
            handler="wifi_settings",
            examples=["відкрий вайфай", "налаштування Wi-Fi"],
        ),
        "open_bluetooth": Action(
            description="Відкрити налаштування Bluetooth",
            params={},
            handler="bluetooth_settings",
            examples=["відкрий блютуз"],
        ),
        "get_battery": Action(
            description="Рівень заряду батареї та статус",
            params={},
            handler="battery_status",
            examples=["який заряд батареї", "скільки відсотків"],
        ),
        "toggle_flashlight": Action(
            description="Увімкнути або вимкнути ліхтарик (через CameraManager API)",
            params={"state": bool},
            handler="flashlight",
            examples=["увімкни ліхтарик", "вимкни світло"],
        ),
    }

    def wifi_settings(self) -> dict:
        return {"intent": resolve("wifi_settings")}

    def bluetooth_settings(self) -> dict:
        return {"intent": resolve("bluetooth_settings")}

    def battery_status(self) -> dict:
        return {"intent": resolve("battery_info")}

    def flashlight(self, state: bool) -> dict:
        return {
            "method": "flashlight",
            "args": {"state": state},
            "note": "Використовує CameraManager API (Android API 23+)"
        }


class NotesGuest(Plugin):
    name = "notes"
    version = "1.0.0"
    plugin_api_version = "1.0"
    description = "Створення нотаток та нагадувань"

    actions = {
        "create_note": Action(
            description="Створити нову нотатку (Google Keep або інший додаток)",
            params={"text": str},
            handler="new_note",
            examples=["запам'ятай купити молоко", "створи нотатку"],
        ),
    }

    def new_note(self, text: str) -> dict:
        """
        Створює нотатку через Google Keep Intent.
        Текст попередньо копіюється в буфер обміну.
        """
        return {
            "intent": resolve("keep_new_note"),
            "clipboard": text,
            "note": "Текст скопійовано в буфер. Вставте його в нотатку."
        }


system = SystemGuest()
notes = NotesGuest()
