package com.piphone.agents.speech

import android.content.Context
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import android.content.Intent
import android.os.Bundle
import android.util.Log
import java.util.Locale
import kotlin.coroutines.resume
import kotlin.coroutines.suspendCoroutine

class VoiceManager(private val context: Context) {
    private var tts: TextToSpeech? = null
    private var isTtsReady = false
    private var speechRecognizer: SpeechRecognizer? = null

    init {
        tts = TextToSpeech(context) { status ->
            isTtsReady = (status == TextToSpeech.SUCCESS)
            tts?.language = Locale("uk", "UA")
        }
    }

    fun speak(text: String) {
        if (isTtsReady) {
            tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, null)
        }
    }

    fun shutdown() {
        tts?.stop()
        tts?.shutdown()
        speechRecognizer?.destroy()
    }
}
