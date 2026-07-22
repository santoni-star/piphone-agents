#!/data/data/com.termux/files/usr/bin/bash
# Build PiPhone APK (Gradle + Kotlin)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
KEYSTORE="$SCRIPT_DIR/piphone.keystore"

export ANDROID_HOME="$HOME/android-sdk"

echo "=== Building PiPhone APK (Gradle) ==="
echo "Project: $PROJECT_DIR/android"

# 1. Build with Gradle
echo "=== 1. Gradle Build ==="
cd "$PROJECT_DIR/android"
./gradlew assembleDebug

# 2. Copy APK
echo "=== 2. Copy APK ==="
cp "$PROJECT_DIR/android/app/build/outputs/apk/debug/app-debug.apk" "$SCRIPT_DIR/piphone.apk"
cp "$SCRIPT_DIR/piphone.apk" "$HOME/PiPhone.apk"
cp "$SCRIPT_DIR/piphone.apk" "$HOME/storage/downloads/PiPhone.apk" 2>/dev/null || true

echo ""
echo "✅ APK ready: $SCRIPT_DIR/piphone.apk"
ls -la "$SCRIPT_DIR/piphone.apk"
echo ""
echo "📍 Also copied to:"
echo "   ~/PiPhone.apk"
echo "   ~/storage/downloads/PiPhone.apk"
