package com.piphone.agents.core

data class AgentContext(
    val query: String = "",
    val maxSteps: Int = 10,
    var step: Int = 0,
    var response: String = "",
    var lastAction: Map<String, Any?>? = null,
    var lastResult: Map<String, Any?>? = null
)
