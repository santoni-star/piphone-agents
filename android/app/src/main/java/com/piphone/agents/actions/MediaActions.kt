package com.piphone.agents.actions

import android.content.Context
import android.content.Intent
import android.net.Uri
import com.piphone.agents.core.Action
import com.piphone.agents.core.ActionPlugin

class MediaActions(private val context: Context) : ActionPlugin {
    override val name = "media"
    override val version = "1.0.0"
    override val description = "YouTube video playback"

    override val actions = mapOf(
        "play_video" to Action(
            name = "play_video",
            description = "Увімкнути YouTube відео",
            params = mapOf("query" to String::class.java),
            handlerName = "playVideo"
        ),
        "search_video" to Action(
            name = "search_video",
            description = "Пошук відео на YouTube",
            params = mapOf("query" to String::class.java),
            handlerName = "searchVideo"
        )
    )

    override suspend fun execute(actionName: String, args: Map<String, Any?>): Map<String, Any?> {
        return when (actionName) {
            "play_video" -> playVideo(args)
            "search_video" -> searchVideo(args)
            else -> mapOf("error" to "Unknown action: $actionName")
        }
    }

    private fun playVideo(args: Map<String, Any?>): Map<String, Any?> {
        val query = args["query"]?.toString() ?: return mapOf("error" to "Missing query")
        val uri = if (query.matches(Regex("^[a-zA-Z0-9_-]{11}$"))) {
            Uri.parse("vnd.youtube:$query")
        } else {
            Uri.parse("https://www.youtube.com/results?search_query=${Uri.encode(query)}")
        }
        val intent = Intent(Intent.ACTION_VIEW, uri)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
        return mapOf("intent" to uri.toString())
    }

    private fun searchVideo(args: Map<String, Any?>): Map<String, Any?> {
        val query = args["query"]?.toString() ?: return mapOf("error" to "Missing query")
        val uri = Uri.parse("https://www.youtube.com/results?search_query=${Uri.encode(query)}")
        val intent = Intent(Intent.ACTION_VIEW, uri)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
        return mapOf("intent" to uri.toString())
    }
}
