
#!/bin/bash
# Build APK for APKPure deployment

echo "🔨 Building Dadaal App APK for APKPure..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
if [ -d "app/build" ]; then
    rm -rf app/build
fi

# Create Android project structure
echo "📁 Creating Android project structure..."
mkdir -p app/src/main/java/com/dadaal/app
mkdir -p app/src/main/res/layout
mkdir -p app/src/main/res/values
mkdir -p app/src/main/res/mipmap-hdpi
mkdir -p app/src/main/res/mipmap-mdpi
mkdir -p app/src/main/res/mipmap-xhdpi
mkdir -p app/src/main/res/mipmap-xxhdpi
mkdir -p app/src/main/res/mipmap-xxxhdpi

# Move files to correct locations
echo "📋 Moving files to Android structure..."
mv MainActivity.java app/src/main/java/com/dadaal/app/
mv AndroidManifest.xml app/src/main/
mv activity_main.xml app/src/main/res/layout/
mv strings.xml app/src/main/res/values/
mv colors.xml app/src/main/res/values/

# Generate keystore for signing
echo "🔐 Generating release keystore..."
if [ ! -f "dadaal-release-key.keystore" ]; then
    keytool -genkey -v -keystore dadaal-release-key.keystore \
        -alias dadaal-key -keyalg RSA -keysize 2048 -validity 10000 \
        -storepass dadaal2025 -keypass dadaal2025 \
        -dname "CN=Dadaal Technologies, OU=Mobile, O=Dadaal, L=Mogadishu, S=Somalia, C=SO"
fi

# Build APK
echo "🔨 Building release APK..."
if command -v ./gradlew &> /dev/null; then
    ./gradlew clean assembleRelease
else
    echo "⚠️ Gradle wrapper not found. Installing..."
    gradle wrapper
    ./gradlew clean assembleRelease
fi

# Check if APK was built successfully
APK_PATH="app/build/outputs/apk/release/app-release.apk"
if [ -f "$APK_PATH" ]; then
    echo "✅ APK built successfully!"
    echo "📱 APK location: $APK_PATH"
    echo "📏 APK size: $(du -h "$APK_PATH" | cut -f1)"
    
    # Upload to APKPure
    echo "📤 Uploading to APKPure..."
    python3 apkpure-upload.py
    
else
    echo "❌ APK build failed!"
    exit 1
fi

echo "🎉 Dadaal App APK ready for APKPure!"
