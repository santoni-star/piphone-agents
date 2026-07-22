package com.piphone.agents.actions

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.hardware.camera2.CameraManager
import android.os.Build
import android.provider.Settings
import androidx.core.content.ContextCompat
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
        val batteryIntent = context.registerReceiver(null, android.content.IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        val level = batteryIntent?.getIntExtra(android.os.BatteryManager.EXTRA_LEVEL, -1) ?: -1
        val scale = batteryIntent?.getIntExtra(android.os.BatteryManager.EXTRA_SCALE, 100) ?: 100
        val percent = if (level > 0) (level * 100 / scale) else -1
        if (percent > 0) {
            return mapOf("text" to "🔋 $percent%")
        }
        return mapOf("text" to "Не вдалося отримати рівень заряду")
    }

    private fun toggleFlashlight(args: Map<String, Any?>): Map<String, Any?> {
        val state = args["state"] as? Boolean ?: return mapOf("error" to "Missing state")
        return try {
            val cameraManager = context.getSystemService(Context.CAMERA_SERVICE) as CameraManager
            val cameraId = cameraManager.cameraIdList[0]
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                cameraManager.setTorchMode(cameraId, state)
            } else {
                return mapOf("error" to "Flashlight requires Android 6+")
            }
            mapOf("text" to (if (state) "🔦 Увімкнено" else "🔦 Вимкнено"))
        } catch (e: SecurityException) {
            mapOf("error" to "Немає дозволу CAMERA")
        } catch (e: Exception) {
            mapOf("error" to "Помилка: ${e.message}")
        }
    }
}
