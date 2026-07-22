package com.piphone.agents.actions

import android.content.Context
import android.content.Intent
import android.net.Uri
import com.piphone.agents.core.Action
import com.piphone.agents.core.ActionPlugin

class MessagingActions(private val context: Context) : ActionPlugin {
    override val name = "messaging"
    override val version = "1.0.0"
    override val description = "WhatsApp, Telegram, SMS, Phone calls"

    override val actions = mapOf(
        "send_telegram" to Action(
            name = "send_telegram",
            description = "Відкрити Telegram чат з повідомленням",
            params = mapOf("username" to String::class.java, "text" to String::class.java),
            handlerName = "sendTelegram"
        ),
        "send_whatsapp" to Action(
            name = "send_whatsapp",
            description = "Відкрити WhatsApp з текстом повідомлення",
            params = mapOf("phone" to String::class.java, "text" to String::class.java),
            handlerName = "sendWhatsApp"
        ),
        "send_sms" to Action(
            name = "send_sms",
            description = "Відкрити SMS з текстом",
            params = mapOf("phone" to String::class.java, "text" to String::class.java),
            handlerName = "sendSms"
        ),
        "make_call" to Action(
            name = "make_call",
            description = "Зателефонувати на номер",
            params = mapOf("phone" to String::class.java),
            handlerName = "makeCall"
        )
    )

    override suspend fun execute(actionName: String, args: Map<String, Any?>): Map<String, Any?> {
        return when (actionName) {
            "send_telegram" -> sendTelegram(args)
            "send_whatsapp" -> sendWhatsApp(args)
            "send_sms" -> sendSms(args)
            "make_call" -> makeCall(args)
            else -> mapOf("error" to "Unknown action: $actionName")
        }
    }

    private fun sendTelegram(args: Map<String, Any?>): Map<String, Any?> {
        val username = args["username"]?.toString() ?: return mapOf("error" to "Missing username")
        val text = args["text"]?.toString() ?: ""
        val uri = Uri.parse("tg://resolve?domain=$username&text=${Uri.encode(text)}")
        val intent = Intent(Intent.ACTION_VIEW, uri)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
        return mapOf("intent" to uri.toString())
    }

    private fun sendWhatsApp(args: Map<String, Any?>): Map<String, Any?> {
        val phone = args["phone"]?.toString() ?: return mapOf("error" to "Missing phone")
        val text = args["text"]?.toString() ?: ""
        val uri = Uri.parse("https://wa.me/$phone?text=${Uri.encode(text)}")
        val intent = Intent(Intent.ACTION_VIEW, uri)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
        return mapOf("intent" to uri.toString())
    }

    private fun sendSms(args: Map<String, Any?>): Map<String, Any?> {
        val phone = args["phone"]?.toString() ?: return mapOf("error" to "Missing phone")
        val text = args["text"]?.toString() ?: ""
        val uri = Uri.parse("sms:$phone?body=${Uri.encode(text)}")
        val intent = Intent(Intent.ACTION_VIEW, uri)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
        return mapOf("intent" to uri.toString())
    }

    private fun makeCall(args: Map<String, Any?>): Map<String, Any?> {
        val phone = args["phone"]?.toString() ?: return mapOf("error" to "Missing phone")
        val uri = Uri.parse("tel:$phone")
        val intent = Intent(Intent.ACTION_DIAL, uri)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
        return mapOf("intent" to uri.toString())
    }
}
