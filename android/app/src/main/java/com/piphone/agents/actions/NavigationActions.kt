package com.piphone.agents.actions

import android.content.Context
import android.content.Intent
import android.net.Uri
import com.piphone.agents.core.Action
import com.piphone.agents.core.ActionPlugin

class NavigationActions(private val context: Context) : ActionPlugin {
    override val name = "navigation"
    override val version = "1.0.0"
    override val description = "Google Maps and GPS"

    override val actions = mapOf(
        "navigate_to" to Action(
            name = "navigate_to",
            description = "Прокласти маршрут",
            params = mapOf("lat" to Double::class.java, "lon" to Double::class.java),
            handlerName = "navigate"
        ),
        "search_places" to Action(
            name = "search_places",
            description = "Пошук місць на мапі",
            params = mapOf("query" to String::class.java),
            handlerName = "searchPlaces"
        ),
        "get_location" to Action(
            name = "get_location",
            description = "Отримати поточне місцезнаходження",
            params = emptyMap(),
            handlerName = "getLocation"
        )
    )

    override suspend fun execute(actionName: String, args: Map<String, Any?>): Map<String, Any?> {
        return when (actionName) {
            "navigate_to" -> navigate(args)
            "search_places" -> searchPlaces(args)
            "get_location" -> getLocation()
            else -> mapOf("error" to "Unknown action: $actionName")
        }
    }

    private fun navigate(args: Map<String, Any?>): Map<String, Any?> {
        val lat = args["lat"]?.toString()?.toDoubleOrNull() ?: 50.45
        val lon = args["lon"]?.toString()?.toDoubleOrNull() ?: 30.52
        val uri = Uri.parse("google.navigation:q=$lat,$lon")
        val intent = Intent(Intent.ACTION_VIEW, uri)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
        return mapOf("intent" to uri.toString())
    }

    private fun searchPlaces(args: Map<String, Any?>): Map<String, Any?> {
        val query = args["query"]?.toString() ?: return mapOf("error" to "Missing query")
        val uri = Uri.parse("geo:0,0?q=${Uri.encode(query)}")
        val intent = Intent(Intent.ACTION_VIEW, uri)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
        return mapOf("intent" to uri.toString())
    }

    private fun getLocation(): Map<String, Any?> {
        return mapOf(
            "text" to "Запускаю GPS...",
            "method" to "gps_once"
        )
    }
}
