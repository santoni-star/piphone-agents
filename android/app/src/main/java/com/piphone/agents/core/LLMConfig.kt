package com.piphone.agents.core

data class LLMConfig(
    val provider: String = "opencode-zen",
    val model: String = "deepseek-v4-flash-free",
    val apiKey: String = "",
    val baseUrl: String = "https://api.opencode-zen.com/v1",
    val temperature: Double = 0.3,
    val maxTokens: Int = 1024
)
