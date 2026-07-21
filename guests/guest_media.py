"""guest_media.py — YouTube дії."""

import re
from core.action_manager import Plugin, Action, registry
from core.android_intents import resolve


def is_youtube_id(query: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9_-]{11}$', query))


class YouTubeGuest(Plugin):
    name = "youtube"
    version = "1.0.0"
    plugin_api_version = "1.0"
    description = "Взаємодія з YouTube"

    actions = {
        "play_video": Action(
            description="Увімкнути YouTube відео за ID або назвою",
            params={"query": str},
            handler="play_youtube",
            examples=["увімкни dQw4w9WgXcQ",
                       "знайди і увімкни prodigy girls"],
            requires_network=True,
            fallback_intent="https://youtu.be/{query}",
        ),
        "search_video": Action(
            description="Пошук відео на YouTube",
            params={"query": str},
            handler="search_youtube",
            requires_network=True,
        ),
    }

    def play_youtube(self, query: str) -> dict:
        if is_youtube_id(query):
            return {"intent": resolve("youtube_video", video_id=query)}
        return {"intent": resolve("youtube_search", query=query)}

    def search_youtube(self, query: str) -> dict:
        return {"intent": resolve("youtube_search", query=query)}


youtube = YouTubeGuest()
