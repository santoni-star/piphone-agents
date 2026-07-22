package com.piphone.agents.core

import android.util.Log

/**
 * PiPhone Agent Loop — direct port of agent_loop.py
 *
 * plan() → classify → execute() → check() → respond()
 */
class AgentLoop(
    private val cactus: CactusAdapter,
    private val llm: LLMClient?,
    private val actions: ActionManager
) {
    companion object {
        private const val TAG = "AgentLoop"
        private const val CONFIDENCE_THRESHOLD = 0.75f
        private const val MAX_RETRIES = 3
    }

    /**
     * Main entry point: process a natural language query
     */
    suspend fun run(query: String): String {
        Log.i(TAG, "Processing: $query")
        var lastError = ""
        var attempts = 0

        while (attempts < MAX_RETRIES) {
            attempts++

            // 1. PLAN — classify intent using cactus or LLM
            val planResult = plan(query)
            Log.i(TAG, "Plan: action=${planResult.action}, args=${planResult.args}, confidence=${planResult.confidence}")

            // 2. EXECUTE — run the action
            val executeResult = execute(planResult)
            Log.i(TAG, "Execute: $executeResult")

            // 3. CHECK — verify result
            if (check(executeResult)) {
                // 4. RESPOND — format response
                return respond(executeResult)
            }

            // Check for repeated error (infinite loop prevention)
            val error = executeResult["error"] as? String
                ?: executeResult["exception"] as? String
            if (error != null) {
                if (error == lastError) {
                    Log.w(TAG, "Same error repeated, stopping retry: $error")
                    return "❌ Помилка: $error"
                }
                lastError = error
            }

            if (attempts >= MAX_RETRIES) {
                return "❌ Не вдалося виконати після $MAX_RETRIES спроб. Остання помилка: $lastError"
            }

            // Retry with LLM fallback for plan refinement
            if (planResult.confidence < CONFIDENCE_THRESHOLD && llm != null) {
                val llmPlan = planWithLLM(query)
                if (llmPlan != null) {
                    // Continue loop with new plan from LLM
                    val llmResult = execute(llmPlan)
                    if (check(llmResult)) {
                        return respond(llmResult)
                    }
                    val llmError = llmResult["error"] as? String
                    if (llmError != null && llmError == lastError) break
                }
            }
        }

        return "❌ Перевищено ліміт спроб. Спробуй переформулювати запит."
    }

    /**
     * PLAN — classify intent using Cactus adapter (keyword matching)
     */
    private suspend fun plan(query: String): PlanResult {
        // Step 1: Try cactus (keyword matching)
        val cactusResult = cactus.analyze(query)

        if (cactusResult != null && cactusResult.confidence >= CONFIDENCE_THRESHOLD) {
            // Validate required parameters
            val action = actions.get(cactusResult.action)
            if (action != null) {
                val missingParams = action.params.keys.filter { param ->
                    param !in cactusResult.args || cactusResult.args[param] == null
                }
                if (missingParams.isEmpty()) {
                    return PlanResult(
                        action = cactusResult.action,
                        args = cactusResult.args,
                        confidence = cactusResult.confidence,
                        source = "cactus"
                    )
                }
                Log.i(TAG, "Cactus match $cactusResult but missing params: $missingParams")
            }
        }

        // Step 2: Try LLM for planning
        if (llm != null) {
            val llmPlan = planWithLLM(query)
            if (llmPlan != null) {
                return llmPlan
            }
        }

        // Step 3: Return cactus result (if any) even with low confidence
        if (cactusResult != null) {
            return PlanResult(
                action = cactusResult.action,
                args = cactusResult.args,
                confidence = cactusResult.confidence,
                source = "cactus"
            )
        }

        // Step 4: Unknown command
        return PlanResult(
            action = "system:unknown",
            args = emptyMap(),
            confidence = 0f,
            source = "fallback"
        )
    }

    /**
     * PLAN with LLM — structured JSON planning output
     */
    private suspend fun planWithLLM(query: String): PlanResult? {
        val availableActions = actions.listSafe()
        val system = buildString {
            appendLine("Ти — PiPhone Agent. Ти отримуєш запит і маєш визначити, яку дію виконати.")
            appendLine()
            appendLine("Доступні дії (action_name: description):")
            for (a in availableActions) {
                appendLine("  - ${a["name"]}: ${a["description"]}")
            }
            appendLine()
            appendLine("Якщо жодна дія не підходить, відповідай: {\"action\": \"chat\", \"args\": {\"text\": \"твій текст\"}}")
            appendLine()
            appendLine("Відповідай ТІЛЬКИ JSON без пояснень. Формат:")
            appendLine("{\"action\": \"назва_дії\", \"args\": {\"парам\": \"значення\"}}")
        }
        val prompt = "Користувач: $query\n\nЯку дію виконати?"

        val response = llm?.chat(prompt, system) ?: return null
        Log.i(TAG, "LLM plan response: $response")

        // Parse JSON from response
        val json = try {
            val jsonStr = response
                .substringAfter("{")
                .substringBeforeLast("}")
            org.json.JSONObject("{$jsonStr}")
        } catch (e: Exception) {
            Log.w(TAG, "Failed to parse LLM response as JSON: $response")
            return null
        }

        val actionName = json.optString("action", "") ?: return null
        if (actionName == "chat") {
            return PlanResult(
                action = "system:chat",
                args = mapOf(
                    "text" to (json.optJSONObject("args")?.optString("text") ?: "...")
                ),
                confidence = 0.9f,
                source = "llm"
            )
        }

        val args = mutableMapOf<String, Any?>()
        json.optJSONObject("args")?.keys()?.forEach { key ->
            args[key] = json.optJSONObject("args")?.opt(key)
        }

        return PlanResult(
            action = actionName,
            args = args,
            confidence = 0.85f,
            source = "llm"
        )
    }

    /**
     * EXECUTE — run action via ActionManager
     */
    private suspend fun execute(plan: PlanResult): Map<String, Any?> {
        if (plan.action == "system:unknown") {
            val suggestions = if (llm != null) {
                llm.chat(
                    prompt = "Користувач сказав: '${plan.args["query"] ?: ""}'. Поясни, що я можу зробити. Я вмію: надсилати повідомлення (telegram, whatsapp, sms), дзвонити, шукати відео, прокладати маршрути, керувати ліхтариком. Відповідай українською, коротко.",
                    system = "Ти — PiPhone, голосовий асистент. Відповідай коротко (<100 символів)."
                )
            } else {
                "Не розумію. Спробуй: \"напиши telegram @user привіт\", \"увімкни ліхтарик\", \"де я зараз?\", \"знайди відео cats\"."
            }
            return mapOf("text" to suggestions)
        }

        if (plan.action == "system:chat") {
            val text = plan.args["text"] as? String ?: "..."
            if (llm != null) {
                val response = llm.chat(
                    prompt = text,
                    system = "Ти — PiPhone, україномовний асистент. Відповідай коротко і дружньо."
                )
                return mapOf("text" to response)
            }
            return mapOf("text" to text)
        }

        return actions.execute(plan.action, plan.args)
    }

    /**
     * CHECK — verify action result, true = success
     */
    private fun check(result: Map<String, Any?>): Boolean {
        if (result.containsKey("error")) return false
        if (result.containsKey("exception")) return false
        return true
    }

    /**
     * RESPOND — format result to human-readable string
     */
    private fun respond(result: Map<String, Any?>): String {
        if (result.containsKey("error")) {
            return "❌ ${result["error"]}"
        }
        if (result.containsKey("text")) {
            return result["text"] as? String ?: "✅ Готово"
        }
        if (result.containsKey("intent")) {
            return "✅ Відкриваю..."
        }
        return "✅ Готово"
    }
}

/**
 * Internal plan representation
 */
data class PlanResult(
    val action: String,
    val args: Map<String, Any?>,
    val confidence: Float,
    val source: String
)
