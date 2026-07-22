package com.piphone.agents.core

import android.util.Log

interface ActionPlugin {
    val name: String
    val version: String
    val description: String
    val actions: Map<String, Action>
    suspend fun execute(actionName: String, args: Map<String, Any?>): Map<String, Any?>
}

class ActionManager {
    private val actions = mutableMapOf<String, Pair<ActionPlugin, Action>>()
    private val plugins = mutableMapOf<String, ActionPlugin>()

    fun register(plugin: ActionPlugin) {
        plugins[plugin.name] = plugin
        for ((name, action) in plugin.actions) {
            actions["${plugin.name}:$name"] = Pair(plugin, action)
            if (!actions.containsKey(name)) {
                actions[name] = Pair(plugin, action)
            }
        }
        Log.i("ActionManager", "Registered '${plugin.name}' with ${plugin.actions.size} actions")
    }

    fun unregister(name: String) {
        plugins.remove(name)?.let { plugin ->
            for (actionName in plugin.actions.keys) {
                actions.remove("$name:$actionName")
                actions.remove(actionName)
            }
        }
    }

    fun get(name: String): Action? = actions[name]?.second

    fun listSafe(): List<Map<String, String>> = actions
        .filter { (_, pair) ->
            !pair.second.requiresRoot && !pair.second.requiresAccessibility
        }
        .map { (name, pair) ->
            mapOf(
                "name" to name,
                "plugin" to pair.first.name,
                "description" to pair.second.description
            )
        }

    suspend fun execute(actionName: String, args: Map<String, Any?>): Map<String, Any?> {
        val pair = actions[actionName] ?: return mapOf("error" to "Action '$actionName' not found")
        val (plugin, action) = pair
        val validArgs = args.filterKeys { it in action.params }
        return try {
            val result = plugin.execute(action.name, validArgs)
            if (result.containsKey("error") || result.containsKey("exception")) {
                result
            } else {
                mapOf<String, Any>("result" to result)
            }
        } catch (e: Exception) {
            Log.e("ActionManager", "Error executing '$actionName'", e)
            mapOf<String, Any>("error" to (e.message ?: "Unknown error"))
        }
    }

    val pluginCount: Int get() = plugins.size
    val actionCount: Int get() = actions.size
}

// Global registry (singleton)
object Registry {
    val instance = ActionManager()
}
