"""guest_base.py — базовий клас для всіх гостей."""

from core.action_manager import Plugin, Action


class GuestBase(Plugin):
    """Базовий клас з додатковою валідацією."""

    requires_explicit_enable: bool = False

    def validate_params(self, action: Action, **kwargs) -> tuple[bool, str]:
        for param_name in action.params:
            if param_name not in kwargs:
                return False, f"Відсутній параметр: {param_name}"
        return True, "OK"

    def safe_execute(self, action_name: str, **kwargs) -> dict:
        action = self.actions.get(action_name)
        if not action:
            return {"error": f"Дія '{action_name}' не знайдена в {self.name}"}

        valid, msg = self.validate_params(action, **kwargs)
        if not valid:
            return {"error": msg}

        handler = self.get_handler(action_name)
        if not handler:
            return {"error": f"Обробник для '{action_name}' не знайдено"}

        try:
            result = handler(**kwargs)
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}
