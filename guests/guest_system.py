"""guest_system.py — Системні дії: Wi-Fi, ліхтарик, батарея, нотатки."""

from core.action_manager import Plugin, Action, registry
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
            examples=["відкрий вайфай"],
        ),
        "open_bluetooth": Action(
            description="Відкрити налаштування Bluetooth",
            params={},
            handler="bluetooth_settings",
            examples=["відкрий блютуз"],
        ),
        "get_battery": Action(
            description="Рівень заряду батареї",
            params={},
            handler="battery_status",
            examples=["який заряд батареї"],
        ),
        "toggle_flashlight": Action(
            description="Увімкнути/вимкнути ліхтарик",
            params={"state": bool},
            handler="flashlight",
            examples=["увімкни ліхтарик"],
        ),
    }

    def wifi_settings(self) -> dict:
        return {"intent": resolve("wifi_settings")}

    def bluetooth_settings(self) -> dict:
        return {"intent": resolve("bluetooth_settings")}

    def battery_status(self) -> dict:
        return {"intent": resolve("battery_info")}

    def flashlight(self, state: bool) -> dict:
        return {"method": "flashlight",
                "args": {"state": state},
                "note": "Через CameraManager API"}


class NotesGuest(Plugin):
    name = "notes"
    version = "1.0.0"
    plugin_api_version = "1.0"
    description = "Створення нотаток"

    actions = {
        "create_note": Action(
            description="Створити нову нотатку (Google Keep)",
            params={"text": str},
            handler="new_note",
            examples=["запам'ятай купити молоко"],
        ),
    }

    def new_note(self, text: str) -> dict:
        return {
            "intent": resolve("keep_new_note"),
            "clipboard": text,
            "note": "Текст у буфері обміну.",
        }


system = SystemGuest()
notes = NotesGuest()
