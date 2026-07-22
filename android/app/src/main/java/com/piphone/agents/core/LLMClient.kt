package com.piphone.agents.core

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

class LLMClient(private val config: LLMConfig = LLMConfig()) {
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()

    suspend fun chat(prompt: String, system: String = ""): String = withContext(Dispatchers.IO) {
        val messages = JSONArray()
        if (system.isNotEmpty()) {
            messages.put(JSONObject().apply {
                put("role", "system")
                put("content", system)
            })
        }
        messages.put(JSONObject().apply {
            put("role", "user")
            put("content", prompt)
        })

        val bodyJson = JSONObject().apply {
            put("model", config.model)
            put("messages", messages)
            put("temperature", config.temperature)
            put("max_tokens", config.maxTokens)
        }

        val request = Request.Builder()
            .url("${config.baseUrl}/chat/completions")
            .header("Authorization", "Bearer ${config.apiKey}")
            .header("Content-Type", "application/json")
            .post(bodyJson.toString().toRequestBody(jsonMediaType))
            .build()

        try {
            val response = client.newCall(request).execute()
            val body = response.body?.string() ?: return@withContext "[Empty response]"
            val json = JSONObject(body)
            if (json.has("error")) {
                return@withContext "[API Error: ${json.getJSONObject("error").optString("message", "unknown")}]"
            }
            val choices = json.optJSONArray("choices")
            if (choices != null && choices.length() > 0) {
                choices.getJSONObject(0)
                    .getJSONObject("message")
                    .optString("content", "[No content]")
            } else {
                "[Unexpected response format]"
            }
        } catch (e: IOException) {
            Log.e("LLMClient", "Request failed", e)
            "[Network error: ${e.message}]"
        } catch (e: Exception) {
            Log.e("LLMClient", "Error", e)
            "[Error: ${e.message}]"
        }
    }

    suspend fun chatStructured(prompt: String, system: String = "", schema: JSONObject? = null): JSONObject? = withContext(Dispatchers.IO) {
        var finalSystem = system
        if (schema != null) {
            finalSystem += "\n\nВІДПОВІДАЙ ТІЛЬКИ JSON ЗА ЦІЄЮ СХЕМОЮ:\n${schema.toString(2)}\nБез пояснень, без додаткового тексту."
        }
        val response = chat(prompt, finalSystem)
        try {
            JSONObject(response)
        } catch (e: Exception) {
            // Try to extract JSON from response
            val match = Regex("\\{.*}").find(response.replace("\n", " "))
            try {
                match?.value?.let { JSONObject(it) }
            } catch (e2: Exception) {
                null
            }
        }
    }
}
