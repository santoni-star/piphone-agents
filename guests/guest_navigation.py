"""guest_navigation.py — Google Maps, GPS."""

from core.action_manager import Plugin, Action, registry
from core.android_intents import resolve


class MapsGuest(Plugin):
    name = "maps"
    version = "1.0.0"
    plugin_api_version = "1.0"
    description = "Google Карти та навігація"

    actions = {
        "navigate_to": Action(
            description="Прокласти маршрут до координат",
            params={"lat": float, "lon": float},
            handler="navigate",
            examples=["проклади маршрут до 50.45,30.52"],
            requires_network=True,
        ),
        "search_places": Action(
            description="Пошук місць на мапі",
            params={"query": str},
            handler="search_maps",
            examples=["знайди кав'ярні поруч"],
            requires_network=True,
        ),
        "show_coords": Action(
            description="Показати координати на мапі",
            params={"lat": float, "lon": float, "label": str},
            handler="show_coords",
            requires_network=True,
        ),
    }

    def navigate(self, lat: float, lon: float) -> dict:
        return {"intent": resolve("maps_directions", lat=lat, lon=lon)}

    def search_maps(self, query: str) -> dict:
        return {"intent": resolve("maps_search", query=query)}

    def show_coords(self, lat: float, lon: float, label: str = "") -> dict:
        return {"intent": resolve("maps_coords", lat=lat, lon=lon, label=label)}


class GPSGuest(Plugin):
    name = "gps"
    version = "1.0.0"
    plugin_api_version = "1.0"
    description = "Одноразове отримання GPS (без фонового режиму)"

    actions = {
        "get_location_once": Action(
            description="Отримати поточне місцезнаходження (одноразово)",
            params={},
            handler="location_once",
            examples=["де я зараз"],
            requires_network=True,
        ),
    }

    def location_once(self) -> dict:
        return {
            "method": "gps_once",
            "note": "GPS на 5-10 секунд, потім вимикається"
        }


maps = MapsGuest()
gps = GPSGuest()
