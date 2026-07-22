package com.piphone.agents.service

import android.app.*
import android.content.Intent
import android.os.Binder
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
        var instance: AgentService? = null
        private const val TAG = "AgentService"
    }

    inner class AgentBinder : Binder() {
        fun getService(): AgentService = this@AgentService
    }

    private val binder = AgentBinder()
    private val serviceScope = CoroutineScope(Dispatchers.Default + SupervisorJob())
    lateinit var agentLoop: AgentLoop
        private set

    override fun onCreate() {
        super.onCreate()
        instance = this
        createNotificationChannel()

        val actionManager = ActionManager()
        actionManager.register(MessagingActions(this))
        actionManager.register(MediaActions(this))
        actionManager.register(NavigationActions(this))
        actionManager.register(SystemActions(this))

        val cactus = CactusAdapter()
        val llm = LLMClient(LLMConfig())

        agentLoop = AgentLoop(
            cactus = cactus,
            llm = llm,
            actions = actionManager
        )

        Log.i(TAG, "AgentService created with ${actionManager.actionCount} actions")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        isRunning = true
        val notification = createNotification()
        startForeground(NOTIFICATION_ID, notification)
        Log.i(TAG, "PiPhone Agent started (foreground)")
        return START_STICKY
    }

    fun processQuery(query: String, callback: (String) -> Unit) {
        serviceScope.launch {
            try {
                val result = agentLoop.run(query)
                withContext(Dispatchers.Main) {
                    callback(result)
                }
            } catch (e: Exception) {
                Log.e(TAG, "processQuery error", e)
                withContext(Dispatchers.Main) {
                    callback("❌ Помилка: ${e.message}")
                }
            }
        }
    }

    override fun onBind(intent: Intent?): IBinder = binder

    override fun onDestroy() {
        isRunning = false
        instance = null
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
                description = "Служба голосового асистента PiPhone"
                setShowBadge(false)
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
            .setContentText("Готовий до команд")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()
    }
}
