
#!/bin/bash
echo "🔧 Setting up Android development environment..."

# Set Android environment variables
export ANDROID_HOME=/opt/android-sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools

# Create directories
mkdir -p /opt/android-sdk/{tools,platform-tools,platforms,build-tools}

echo "✅ Android environment configured!"
echo "Run: source setup-android.sh"
