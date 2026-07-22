package com.piphone.agents.core

data class Action(
    val name: String,
    val description: String,
    val params: Map<String, Class<*>> = emptyMap(),
    val handlerName: String = "",
    val examples: List<String> = emptyList(),
    val requiresNetwork: Boolean = false,
    val requiresRoot: Boolean = false,
    val requiresAccessibility: Boolean = false
)
