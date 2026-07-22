#!/data/data/com.termux/files/usr/bin/bash
# Build PiPhone APK
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"
KEYSTORE="$SCRIPT_DIR/piphone.keystore"

# Android SDK
ANDROID_JAR=$(find /data/data/com.termux/files/home/android-sdk/platforms -name "android.jar" | tail -1)
if [ -z "$ANDROID_JAR" ]; then
    echo "❌ android.jar not found. Install Android SDK."
    exit 1
fi

echo "=== Building PiPhone APK ==="
echo "Android JAR: $ANDROID_JAR"

# Clean
rm -rf "$SCRIPT_DIR/build" "$SCRIPT_DIR/"*.apk "$SCRIPT_DIR/build"
mkdir -p "$SCRIPT_DIR/build/classes"

# 1. Compile Java
echo "=== 1. Compile Java ==="
javac -cp "$ANDROID_JAR" \
    -d "$SCRIPT_DIR/build/classes" \
    "$SCRIPT_DIR/src/com/piphone/agents/MainActivity.java"

# 2. Convert to DEX
echo "=== 2. DEX ==="
d8 --lib "$ANDROID_JAR" \
    --output "$SCRIPT_DIR/build" \
    "$SCRIPT_DIR/build/classes/com/piphone/agents/MainActivity.class"

# 3. Package resources
echo "=== 3. Package APK ==="
aapt package -f \
    -M "$SCRIPT_DIR/AndroidManifest.xml" \
    -S "$SCRIPT_DIR/res" \
    -I "$ANDROID_JAR" \
    -F "$SCRIPT_DIR/build/piphone-unsigned.apk" 2>/dev/null

# 4. Add DEX
echo "=== 4. Add DEX ==="
aapt add "$SCRIPT_DIR/build/piphone-unsigned.apk" \
    "$SCRIPT_DIR/build/classes.dex" >/dev/null

# 5. Create keystore if needed
if [ ! -f "$KEYSTORE" ]; then
    echo "=== Creating keystore ==="
    keytool -genkey -v \
        -keystore "$KEYSTORE" \
        -alias piphone \
        -keyalg RSA -keysize 2048 \
        -validity 10000 \
        -storepass 111111 -keypass 111111 \
        -dname "CN=PiPhone, O=PiPhone Agents, C=UA"
fi

# 6. Sign
echo "=== 5. Sign APK ==="
apksigner sign \
    --ks "$KEYSTORE" \
    --ks-pass pass:111111 \
    --key-pass pass:111111 \
    --out "$SCRIPT_DIR/piphone.apk" \
    "$SCRIPT_DIR/build/piphone-unsigned.apk"

# Clean up
rm -rf "$SCRIPT_DIR/build"

echo ""
echo "✅ APK ready: $SCRIPT_DIR/piphone.apk"
ls -la "$SCRIPT_DIR/piphone.apk"
