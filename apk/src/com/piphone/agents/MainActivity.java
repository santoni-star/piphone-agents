package com.piphone.agents;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        try {
            // Запускаємо PiPhone через Termux RUN_COMMAND
            Intent intent = new Intent("com.termux.RUN_COMMAND");
            intent.setClassName("com.termux",
                "com.termux.app.RunCommandService");
            intent.putExtra("com.termux.RUN_COMMAND_PATH",
                "/data/data/com.termux/files/usr/bin/piphone");
            intent.putExtra("com.termux.RUN_COMMAND_BACKGROUND", false);
            startService(intent);
        } catch (Exception e) {
            // Fallback: просто відкрити Termux
            Intent fallback = new Intent();
            fallback.setClassName("com.termux",
                "com.termux.app.TermuxActivity");
            fallback.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(fallback);
        }

        finish();
    }
}
