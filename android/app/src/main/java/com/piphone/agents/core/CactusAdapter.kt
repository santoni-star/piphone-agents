package com.piphone.agents.core

import android.util.Log
import java.util.regex.Pattern

class CactusAdapter(private val useEmulation: Boolean = true) {
    private var loaded = false

    data class PatternEntry(
        val pattern: Pattern,
        val actionName: String,
        val argsTemplate: Map<String, Any?>,  // "{1}" = group ref, "query" = whole query
        val confidence: Float
    )

    private val patterns = listOf(
        // ── Telegram ──
        PatternEntry(
            Pattern.compile("(?:напиши|відправ|надішли)\\s.*?(?:telegram|телеграм|тг)\\s*[:@]?\\s*(\\w+)\\s+(.+)", Pattern.CASE_INSENSITIVE),
            "telegram:send_message", mapOf("username" to "{1}", "text" to "{2}"), 0.8f
        ),
        // ── WhatsApp ──
        PatternEntry(
            Pattern.compile("(?:напиши|відправ|надішли)\\s.*?(?:whatsapp|ватсап|вацап)\\s*(\\d+)\\s+(.+)", Pattern.CASE_INSENSITIVE),
            "whatsapp:send_message", mapOf("phone" to "{1}", "text" to "{2}"), 0.8f
        ),
        // ── SMS ──
        PatternEntry(
            Pattern.compile("(?:напиши|відправ|надішли)\\s.*?sms\\s*(\\d+)\\s+(.+)", Pattern.CASE_INSENSITIVE),
            "sms:send_sms", mapOf("phone" to "{1}", "text" to "{2}"), 0.8f
        ),
        // ── Phone calls ──
        PatternEntry(
            Pattern.compile("(?:зателефонуй|подзвони|дзвінок)\\s*(?:\\w+\\s+)?(\\d+)", Pattern.CASE_INSENSITIVE),
            "phone:make_call", mapOf("phone" to "{1}"), 0.8f
        ),
        // ── YouTube ──
        PatternEntry(
            Pattern.compile("(?:увімкни|відкрий)\\s+(\\w{11})\\s*$", Pattern.CASE_INSENSITIVE),
            "youtube:play_video", mapOf("query" to "{1}"), 0.75f
        ),
        PatternEntry(
            Pattern.compile("знайди\\s+(?:відео|youtube|ютуб)\\s+(.+)", Pattern.CASE_INSENSITIVE),
            "youtube:search_video", mapOf("query" to "{1}"), 0.85f
        ),
        // ── Maps ──
        PatternEntry(
            Pattern.compile("(?:проклади|покажи|знайди)\\s.*?(?:маршрут|дорогу|шлях)", Pattern.CASE_INSENSITIVE),
            "maps:navigate_to", mapOf("lat" to 50.45, "lon" to 30.52), 0.75f
        ),
        PatternEntry(
            Pattern.compile("(?:де|знайди)\\s.*?(?:кав'ярн|ресторан|аптек|магазин)", Pattern.CASE_INSENSITIVE),
            "maps:search_places", mapOf("query" to null), 0.75f
        ),
        // ── GPS ──
        PatternEntry(
            Pattern.compile("де\\s+я\\s*(?:зараз|знаходжусь)?\\s*\\??$", Pattern.CASE_INSENSITIVE),
            "gps:get_location_once", emptyMap(), 0.85f
        ),
        // ── System ──
        PatternEntry(
            Pattern.compile("(?:увімкни|відкрий)\\s.*?(?:вайфай|wifi|Wi-Fi)", Pattern.CASE_INSENSITIVE),
            "system:open_wifi", emptyMap(), 0.9f
        ),
        PatternEntry(
            Pattern.compile("(?:увімкни|відкрий)\\s.*?(?:блютуз|bluetooth)", Pattern.CASE_INSENSITIVE),
            "system:open_bluetooth", emptyMap(), 0.9f
        ),
        PatternEntry(
            Pattern.compile("(?:який|скільки)\\s.*?(?:заряд|батарея|відсотків)", Pattern.CASE_INSENSITIVE),
            "system:get_battery", emptyMap(), 0.85f
        ),
        PatternEntry(
            Pattern.compile("(?:увімкни|включи)\\s.*?(?:ліхтарик|світло)", Pattern.CASE_INSENSITIVE),
            "system:toggle_flashlight", mapOf("state" to true), 0.85f
        ),
        PatternEntry(
            Pattern.compile("(?:вимкни|погаси)\\s.*?(?:ліхтарик|світло)", Pattern.CASE_INSENSITIVE),
            "system:toggle_flashlight", mapOf("state" to false), 0.85f
        ),
        // ── Notes ──
        PatternEntry(
            Pattern.compile("запам'ятай\\s+(.+)", Pattern.CASE_INSENSITIVE or Pattern.UNICODE_CHARACTER_CLASS),
            "notes:create_note", mapOf("text" to "{1}"), 0.8f
        ),
    )

    fun load(): Boolean {
        if (useEmulation) {
            Log.i("CactusAdapter", "Using keyword emulation (Phase 0-1)")
            loaded = true
            return true
        }
        Log.w("CactusAdapter", "Real ONNX model not yet integrated")
        return false
    }

    fun isLoaded(): Boolean = loaded

    fun analyze(query: String, availableActions: List<Map<String, String>>? = null): CactusResult? {
        if (!loaded) load()
        val queryLower = query.lowercase().trim()

        var best: CactusResult? = null

        for (entry in patterns) {
            val matcher = entry.pattern.matcher(queryLower)
            if (matcher.find()) {
                val resolvedArgs = mutableMapOf<String, Any?>()
                for ((key, value) in entry.argsTemplate) {
                    when {
                        value is String && value.startsWith("{") && value.endsWith("}") -> {
                            val idx = value.substring(1, value.length - 1).toIntOrNull()
                            if (idx != null && idx <= matcher.groupCount()) {
                                resolvedArgs[key] = matcher.group(idx) ?: value
                            }
                        }
                        value == null -> resolvedArgs[key] = query
                        else -> resolvedArgs[key] = value
                    }
                }

                val candidate = CactusResult(
                    action = entry.actionName,
                    args = resolvedArgs,
                    confidence = entry.confidence
                )

                if (best == null || candidate.confidence > best.confidence) {
                    best = candidate
                }
            }
        }

        return best?.takeIf { it.confidence >= 0.5f }
    }

    fun classify(query: String): Boolean {
        val result = analyze(query)
        return result != null && result.confidence >= 0.75f
    }
}
