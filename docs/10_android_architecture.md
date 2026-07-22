# PiPhone Android APK — Архітектура

## Огляд

Повноцінний Android APK без Termux. Весь код — Kotlin + Jetpack Compose.
Агентний цикл, Cactus Needle, LLM клієнт — портовані з Python в Kotlin.

```
┌──────────────────────────────────────────────────────────────┐
│                    PiPhone Android APK                        │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                    UI Layer (Compose)                  │    │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────────┐ │    │
│  │  │  Chat    │  │  Bubble  │  │     Settings        │ │    │
│  │  │  Screen  │  │  Overlay │  │     Screen          │ │    │
│  │  └────┬─────┘  └────┬─────┘  └────────────────────┘ │    │
│  │       │              │                                │    │
│  └───────┴──────────────┴────────────────────────────────┘    │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                  Agent Layer (Core)                    │    │
│  │  ┌────────────────────────────────────────────────┐  │    │
│  │  │               AgentLoop (Kotlin)                │  │    │
│  │  │  plan() → execute() → check() → respond()      │  │    │
│  │  └──────────┬──────────┬───────────┬───────────────┘  │    │
│  │             │          │           │                    │    │
│  │  ┌──────────┴──────┐ ┌─┴────────┐ ┌┴──────────────┐  │    │
│  │  │  CactusAdapter  │ │LLMClient │ │ ActionManager  │  │    │
│  │  │  (ONNX/Emul)    │ │(OkHttp)  │ │  (Registry)    │  │    │
│  │  └─────────────────┘ └──────────┘ └───────┬────────┘  │    │
│  └────────────────────────────────────────────┼───────────┘    │
│                                               │                │
│  ┌────────────────────────────────────────────┼───────────┐    │
│  │          Actions Layer (Guests port)        │           │    │
│  │  ┌──────────┐ ┌────────┐ ┌──────────┐     │           │    │
│  │  │Messaging │ │ Media  │ │Navigatn │ ...  │           │    │
│  │  │Actions   │ │Actions │ │Actions   │      │           │    │
│  │  └──────────┘ └────────┘ └──────────┘      │           │    │
│  └────────────────────────────────────────────┼───────────┘    │
│                                               │                │
│  ┌────────────────────────────────────────────┼───────────┐    │
│  │         Android Native Layer               │           │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┘           │    │
│  │  │   STT    │ │   TTS    │ │  Android Intents         │    │
│  │  │(Recogn.) │ │(Engine)  │ │  (startActivity)          │    │
│  │  └──────────┘ └──────────┘ └──────────────────────────┘    │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │           Service Layer (Background)                   │    │
│  │  ┌────────────────┐  ┌──────────────────────────┐    │    │
│  │  │ AgentService   │  │ Notification + Bubble    │    │    │
│  │  │ (Foreground)   │  │ (Always-on listening)    │    │    │
│  │  └────────────────┘  └──────────────────────────┘    │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

## Компоненти

### 1. AgentLoop (Kotlin порт agent_loop.py)

```kotlin
class AgentLoop(
    private val cactus: CactusAdapter,
    private val llm: LLMClient?,
    private val actions: ActionManager
) {
    fun plan(query: String): Plan
    fun execute(plan: Plan): ActionResult
    fun check(plan: Plan, result: ActionResult): Boolean
    fun respond(result: ActionResult): String
    suspend fun run(query: String): String
}
```

### 2. CactusAdapter (Kotlin порт cactus_adapter.py)

Два режими:
- **Phase 0-1**: Keyword matching (той самий, що в Python)
- **Phase 2+**: ONNX Runtime (Cactus Needle 26M params)

### 3. LLMClient (Kotlin порт llm_client.py)

- OkHttp замість urllib
- OpenAI-сумісний API
- Підтримка structured output (JSON schema)

### 4. ActionManager (Kotlin порт action_manager.py)

- Реєстр дій
- Виконання через Android Intent API
- Плагінна система

### 5. Actions (порт guests/)

| Python | Kotlin | Механізм |
|---|---|---|
| guest_messaging.py | MessagingActions.kt | Intent.ACTION_VIEW (tel://, sms://, tg://, https://wa.me/) |
| guest_media.py | MediaActions.kt | YouTube intent (vnd.youtube:) |
| guest_navigation.py | NavigationActions.kt | Google Maps intent (geo:, google.navigation:) |
| guest_system.py | SystemActions.kt | Settings Intents + CameraManager |

### 6. Voice I/O

- **STT**: Android SpeechRecognizer (offline)
- **TTS**: Android TextToSpeech (offline)

### 7. UI

- **Chat Screen**: Compose, список повідомлень + поле вводу
- **Bubble Overlay**: плаваюча іконка поверх усіх додатків
- **Settings**: API ключ, мова, тема

### 8. Background Service

- Foreground Service з постійним сповіщенням
- Опціональне "завжди слухати" (через MediaRecorder + SpeechRecognizer)

## Маршрут даних

```
Голос/Текст → AgentLoop.plan()
    ├── CactusAdapter (>75%) → execute() → Intent/API
    └── LLMClient (<75%) → execute() → Intent/API
         ↓
    AgentLoop.check() → respond() → TTS/UI
```

## Відмінності від Python версії

| Аспект | Python/Termux | Kotlin APK |
|---|---|---|
| Runtime | Python + Termux | Kotlin + Android Runtime |
| Інтерфейс | CLI (input/print) | Compose UI + TTS + STT |
| Intents | URL схеми | Android Intent API |
| Фон | Немає | Foreground Service |
| Cactus | Keyword match | Keyword match + ONNX |
| LLM | urllib | OkHttp |
| Встановлення | git + pip | APK з магазину |
