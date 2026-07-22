package com.piphone.agents.actions

import android.content.Context
import android.content.Intent
import android.provider.Settings
import com.piphone.agents.core.Action
import com.piphone.agents.core.ActionPlugin

class SystemActions(private val context: Context) : ActionPlugin {
    override val name = "system"
    override val version = "1.0.0"
    override val description = "System controls"

    override val actions = mapOf(
        "open_wifi" to Action(
            name = "open_wifi",
            description = "Відкрити налаштування Wi-Fi",
            params = emptyMap()
        ),
        "open_bluetooth" to Action(
            name = "open_bluetooth",
            description = "Відкрити налаштування Bluetooth",
            params = emptyMap()
        ),
        "get_battery" to Action(
            name = "get_battery",
            description = "Рівень заряду батареї",
            params = emptyMap()
        ),
        "toggle_flashlight" to Action(
            name = "toggle_flashlight",
            description = "Увімкнути/вимкнути ліхтарик",
            params = mapOf("state" to Boolean::class.java)
        )
    )

    override suspend fun execute(actionName: String, args: Map<String, Any?>): Map<String, Any?> {
        return when (actionName) {
            "open_wifi" -> openWifi()
            "open_bluetooth" -> openBluetooth()
            "get_battery" -> getBattery()
            "toggle_flashlight" -> toggleFlashlight(args)
            else -> mapOf("error" to "Unknown action: $actionName")
        }
    }

    private fun openWifi(): Map<String, Any?> {
        context.startActivity(
            Intent(Settings.ACTION_WIFI_SETTINGS).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
        )
        return mapOf("text" to "Відкриваю налаштування Wi-Fi")
    }

    private fun openBluetooth(): Map<String, Any?> {
        context.startActivity(
            Intent(Settings.ACTION_BLUETOOTH_SETTINGS).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
        )
        return mapOf("text" to "Відкриваю налаштування Bluetooth")
    }

    private fun getBattery(): Map<String, Any?> {
        return mapOf("text" to "Перевіряю батарею...", "method" to "battery_intent")
    }

    private fun toggleFlashlight(args: Map<String, Any?>): Map<String, Any?> {
        val state = args["state"] as? Boolean ?: return mapOf("error" to "Missing state")
        return mapOf(
            "method" to "flashlight",
            "state" to state,
            "text" to if (state) "🔦 Увімкнено" else "🔦 Вимкнено"
        )
    }
}
