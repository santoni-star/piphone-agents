package com.piphone.agents

import android.Manifest
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.IBinder
import android.speech.SpeechRecognizer
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.piphone.agents.service.AgentService
import com.piphone.agents.speech.VoiceManager
import com.piphone.agents.ui.chat.ChatScreen
import com.piphone.agents.ui.settings.SettingsScreen
import com.piphone.agents.ui.theme.PiPhoneTheme

class MainActivity : ComponentActivity() {
    companion object {
        private const val TAG = "MainActivity"
        private const val PERMISSION_REQUEST_CODE = 100

        private val REQUIRED_PERMISSIONS = buildList {
            add(Manifest.permission.RECORD_AUDIO)
            add(Manifest.permission.CAMERA)
            add(Manifest.permission.ACCESS_FINE_LOCATION)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                add(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
    }

    private var agentService: AgentService? = null
    private var voiceManager: VoiceManager? = null
    private var bound = false

    private val connection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, service: IBinder?) {
            val binder = service as AgentService.AgentBinder
            agentService = binder.getService()
            bound = true
            Log.i(TAG, "Bound to AgentService")
        }

        override fun onServiceDisconnected(name: ComponentName?) {
            agentService = null
            bound = false
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        voiceManager = VoiceManager(this)

        // Start foreground service
        val serviceIntent = Intent(this, AgentService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent)
        } else {
            startService(serviceIntent)
        }

        // Request permissions
        requestNeededPermissions()

        setContent {
            var showSettings by remember { mutableStateOf(false) }

            PiPhoneTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    if (showSettings) {
                        SettingsScreen(onNavigateBack = { showSettings = false })
                    } else {
                        ChatScreen(
                            agentService = agentService,
                            voiceManager = voiceManager,
                            onNavigateSettings = { showSettings = true }
                        )
                    }
                }
            }
        }
    }

    override fun onStart() {
        super.onStart()
        // Bind to service for IPC
        val intent = Intent(this, AgentService::class.java)
        bindService(intent, connection, Context.BIND_AUTO_CREATE)
    }

    override fun onStop() {
        super.onStop()
        if (bound) {
            unbindService(connection)
            bound = false
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        voiceManager?.shutdown()
    }

    private fun requestNeededPermissions() {
        val missing = REQUIRED_PERMISSIONS.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (missing.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, missing.toTypedArray(), PERMISSION_REQUEST_CODE)
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSION_REQUEST_CODE) {
            permissions.forEachIndexed { i, perm ->
                val granted = grantResults[i] == PackageManager.PERMISSION_GRANTED
                Log.i(TAG, "Permission $perm: ${if (granted) "GRANTED" else "DENIED"}")
            }
        }
    }
}
