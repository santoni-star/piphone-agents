package com.piphone.agents.core

data class CactusResult(
    val action: String,
    val args: Map<String, Any?> = emptyMap(),
    val confidence: Float,
    val source: String = "cactus"
)
