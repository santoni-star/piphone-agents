# План робіт

## Фаза 0: Фундамент (тиждень 1)

**Мета:** Запустити ядро і довести що агентний цикл + Cactus Needle + Intents працюють.

```
[ ] core/agent_loop.py        — базовий цикл plan → execute → check
[ ] core/llm_client.py        — HTTP-клієнт для OpenRouter/DeepSeek
[ ] core/android_intents.py   — база відомих Intent схем
[ ] core/cactus_adapter.py    — заглушка для Cactus Needle
[ ] core/action_manager.py    — реєстр дій
[ ] core/plugin_api.py        — базовий Plugin клас
[ ] tests/test_loop.py        — тест що цикл працює
```

**Перевірка успіху:**
```bash
python3 -c "from core.agent_loop import AgentLoop; print('OK')"
```

---

## Фаза 1: Координатор MVP (тиждень 2)

**Мета:** Перший APK, який приймає текст, виконує Intents, відповідає.

```
[ ] agents/coordinator/       — Kotlin APK обгортка
[ ] agents/coordinator/
    app/src/main/java/...    — MainActivity + AgentService
[ ] guests/guest_messaging.py — WhatsApp, Telegram, SMS
[ ] guests/guest_media.py    — YouTube
[ ] guests/guest_navigation.py — Maps, GPS
[ ] guests/guest_system.py   — Wi-Fi, Flashlight, Battery
[ ] tests/test_coordinator.py — smoke test
```

**Базові команди, які мають працювати:**
- «Напиши Колі в Telegram: буду через 10 хв»
- «Проклади маршрут до вокзалу»
- «Увімкни ліхтарик»
- «Яка погода в Києві?»
- «Знайди та увімкни [відео] на YouTube»

---

## Фаза 2: Cactus Needle (тиждень 3)

**Мета:** Підключити Cactus Needle як локальний reflex шар.

```
[ ] core/cactus_adapter.py    — реальна інтеграція через JNI/ONNX
[ ] core/cactus_adapter.py    — логіка confidence threshold
[ ] tests/test_cactus.py      — порівняння Cactus vs LLM
```

**Механіка:**
```
Запит → Cactus Needle (0.1s)
  ├── > 75% → виконуємо (без інтернету)
  └── < 75% → LLM (5-30s)
```

---

## Фаза 3: Секретар (тиждень 4)

**Мета:** Голосовий асистент для Bluetooth-гарнітури.

```
[ ] core/voice_pipeline.py    — SpeechRecognizer + TextToSpeech
[ ] agents/assistant-secretary/ — APK секретаря
[ ] tests/test_voice.py        — тест голосового циклу
```

**Сценарій:**
```
🎤 «Напиши мамі що я скоро буду»
    → STT → LLM → Intent → TTS відповідь
```

---

## Фаза 4: Проактивний (тиждень 5-6)

**Мета:** Асистент, який сам пропонує дії за часом/подіями.

```
[ ] agents/assistant-proactive/ — APK
[ ] core/triggers.py            — AlarmManager, CalendarContract
[ ] core/notification_service.py — сповіщення
```

**Сценарій:**
```
7:30 → «Доброго ранку! На сьогодні: зустріч о 15:00.
        У вас 28% батареї. Нагадати про день народження тата?»
```

---

## Фаза 5: Екосистема (тиждень 7+)

**Мета:** Відкрити API для спільноти.

```
[ ] docs/04_contributing.md   — гайд для контриб'юторів
[ ] guest_template/           — шаблон для створення нових гостей
[ ] examples/                 — приклади використання
[ ] CI/tests                  — автоматичне тестування сумісності
```

---

## Як почати прямо зараз

```bash
# 1. Клонувати
git clone git@github.com:santoni-star/piphone-agents.git
cd piphone-agents

# 2. Встановити залежності
pip install requests

# 3. Запустити тест ядра
python3 -c "
from core.agent_loop import AgentLoop
from core.action_manager import registry
loop = AgentLoop(llm_provider='opencode-zen')
print('✅ Ядро працює')
"
```

Перша задача: зробити так, щоб цей тест проходив.
