package com.piphone.agents.speech

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.RecognitionListener
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.util.Log
import java.util.Locale

class VoiceManager(private val context: Context) {
    companion object {
        private const val TAG = "VoiceManager"
    }

    private var tts: TextToSpeech? = null
    private var recognizer: SpeechRecognizer? = null
    private var ttsReady = false
    private var sttCallback: ((String) -> Unit)? = null
    private var sttErrorCallback: ((String) -> Unit)? = null
    private var isListening = false

    init {
        tts = TextToSpeech(context) { status ->
            ttsReady = (status == TextToSpeech.SUCCESS)
            tts?.language = Locale("uk", "UA")
            tts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                override fun onStart(uttId: String?) {}
                override fun onDone(uttId: String?) {}
                override fun onError(uttId: String?) {}
            })
        }
    }

    // ─── TTS ──────────────────────────────────────────────

    fun speak(text: String, callback: (() -> Unit)? = null) {
        if (ttsReady) {
            val utteranceId = "piphone_${System.currentTimeMillis()}"
            tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, utteranceId)
            if (callback != null) {
                tts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                    override fun onStart(uttId: String?) {}
                    override fun onDone(uttId: String?) {
                        if (uttId == utteranceId) callback()
                    }
                    override fun onError(uttId: String?) {}
                })
            }
        }
    }

    fun stopSpeaking() {
        tts?.stop()
    }

    fun isSpeaking(): Boolean = tts?.isSpeaking ?: false

    // ─── STT ──────────────────────────────────────────────

    fun startListening(
        language: String = "uk-UA",
        onResult: (String) -> Unit,
        onError: ((String) -> Unit)? = null
    ) {
        if (isListening) return
        isListening = true
        sttCallback = onResult
        sttErrorCallback = onError

        if (recognizer == null) {
            recognizer = SpeechRecognizer.createSpeechRecognizer(context)
        }

        recognizer?.setRecognitionListener(object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) {
                Log.d(TAG, "STT ready")
            }

            override fun onBeginningOfSpeech() {
                Log.d(TAG, "STT beginning")
            }

            override fun onRmsChanged(rmsdB: Float) {}

            override fun onBufferReceived(buffer: ByteArray?) {}

            override fun onEndOfSpeech() {
                Log.d(TAG, "STT end")
            }

            override fun onError(error: Int) {
                isListening = false
                val msg = when (error) {
                    SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Network timeout"
                    SpeechRecognizer.ERROR_NETWORK -> "Network error"
                    SpeechRecognizer.ERROR_AUDIO -> "Audio error"
                    SpeechRecognizer.ERROR_SERVER -> "Server error"
                    SpeechRecognizer.ERROR_CLIENT -> "Client error"
                    SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "No speech detected"
                    SpeechRecognizer.ERROR_NO_MATCH -> "No match"
                    SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Recognizer busy"
                    SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Missing RECORD_AUDIO permission"
                    SpeechRecognizer.ERROR_LANGUAGE_NOT_SUPPORTED -> "Language not supported"
                    else -> "Unknown error ($error)"
                }
                Log.w(TAG, "STT error: $msg")
                sttErrorCallback?.invoke(msg)
            }

            override fun onResults(results: Bundle?) {
                isListening = false
                val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if (!matches.isNullOrEmpty()) {
                    sttCallback?.invoke(matches[0])
                } else {
                    sttErrorCallback?.invoke("No recognition results")
                }
            }

            override fun onPartialResults(partialResults: Bundle?) {}

            override fun onEvent(eventType: Int, params: Bundle?) {}
        })

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, language)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, language)
            putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, context.packageName)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
        }

        recognizer?.startListening(intent)
    }

    fun stopListening() {
        isListening = false
        recognizer?.stopListening()
    }

    fun cancelListening() {
        isListening = false
        recognizer?.cancel()
    }

    fun isListening(): Boolean = isListening

    // ─── Cleanup ───────────────────────────────────────────

    fun shutdown() {
        stopListening()
        stopSpeaking()
        tts?.shutdown()
        recognizer?.destroy()
        recognizer = null
    }
}
