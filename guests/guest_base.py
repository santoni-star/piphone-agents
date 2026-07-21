"""guest_base.py — базовий клас для всіх гостей."""

from core.plugin_api import Plugin, Action


class GuestBase(Plugin):
    """
    Базовий клас для всіх гостей.
    Додатковий рівень валідації та допоміжних методів над Plugin.
    """

    requires_explicit_enable: bool = False
    """Деякі гості (GPS, Calendar) вимагають явного ввімкнення."""

    def validate_params(self, action: Action, **kwargs) -> tuple[bool, str]:
        """Перевірити чи всі обов'язкові параметри присутні."""
        for param_name in action.params:
            if param_name not in kwargs:
                return False, f"Missing required param: {param_name}"
        return True, "OK"

    def validate_intent(self, name: str, **kwargs) -> bool:
        """
        Перевірити чи Intent спрацює перед виконанням.
        Наприклад: чи є WhatsApp встановлений, чи є інтернет.
        """
        return True

    def safe_execute(self, action_name: str, **kwargs) -> dict:
        """Безпечне виконання з валідацією."""
        action = self.actions.get(action_name)
        if not action:
            return {"error": f"Action '{action_name}' not found in {self.name}"}

        valid, msg = self.validate_params(action, **kwargs)
        if not valid:
            return {"error": msg}

        handler = getattr(self, action.handler, None)
        if not handler:
            return {"error": f"Handler '{action.handler}' not found"}

        try:
            result = handler(**kwargs)
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}
