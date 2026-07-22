package com.piphone.agents

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.core.content.ContextCompat
import com.piphone.agents.service.AgentService
import com.piphone.agents.ui.chat.ChatScreen
import com.piphone.agents.ui.theme.PiPhoneTheme

class MainActivity : ComponentActivity() {
    private var agentService: AgentService? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Start foreground service
        val serviceIntent = Intent(this, AgentService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent)
        } else {
            startService(serviceIntent)
        }

        setContent {
            PiPhoneTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    ChatScreen(agentService)
                }
            }
        }
    }

    private fun bindService() {
        // TODO: bind to AgentService for IPC
    }
}
