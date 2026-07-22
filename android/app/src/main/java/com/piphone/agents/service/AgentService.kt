package com.piphone.agents.service

import android.app.*
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import com.piphone.agents.MainActivity
import com.piphone.agents.core.*
import com.piphone.agents.actions.*
import kotlinx.coroutines.*

class AgentService : Service() {
    companion object {
        const val CHANNEL_ID = "piphone_agent"
        const val NOTIFICATION_ID = 1
        var isRunning = false
    }

    private val serviceScope = CoroutineScope(Dispatchers.Default + SupervisorJob())
    private lateinit var agentLoop: AgentLoop

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()

        val actionManager = ActionManager()
        actionManager.register(MessagingActions(this))
        actionManager.register(MediaActions(this))
        actionManager.register(NavigationActions(this))
        actionManager.register(SystemActions(this))

        val cactus = CactusAdapter()
        val llm = null // LLMClient(LLMConfig())

        agentLoop = AgentLoop(
            cactus = cactus,
            llm = llm,
            actions = actionManager
        )
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        isRunning = true
        val notification = createNotification()
        startForeground(NOTIFICATION_ID, notification)
        Log.i("AgentService", "PiPhone Agent started")
        return START_STICKY
    }

    fun processQuery(query: String, callback: (String) -> Unit) {
        serviceScope.launch {
            try {
                val result = agentLoop.run(query)
                callback(result)
            } catch (e: Exception) {
                callback("❌ Помилка: ${e.message}")
            }
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        isRunning = false
        serviceScope.cancel()
        super.onDestroy()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "PiPhone Agent",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "PiPhone background service"
            }
            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager.createNotificationChannel(channel)
        }
    }

    private fun createNotification(): Notification {
        val pendingIntent = PendingIntent.getActivity(
            this, 0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE
        )
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("🧠 PiPhone")
            .setContentText("Слухаю...")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()
    }
}
