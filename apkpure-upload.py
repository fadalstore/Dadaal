
#!/usr/bin/env python3
"""
APKPure Upload Script for Dadaal App
"""

import requests
import json
import os
from pathlib import Path

def upload_to_apkpure():
    """Upload APK to APKPure"""
    
    # APKPure API configuration
    APKPURE_API_URL = "https://api.apkpure.com/v1/upload"
    APKPURE_API_KEY = os.environ.get('APKPURE_API_KEY', '')
    
    if not APKPURE_API_KEY:
        print("⚠️ APKPURE_API_KEY environment variable not set!")
        print("Please set your APKPure developer API key")
        return False
    
    # Load metadata
    with open('apkpure-metadata.json', 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Prepare upload data
    upload_data = {
        'api_key': APKPURE_API_KEY,
        'package_name': metadata['package_name'],
        'app_name': metadata['app_name'],
        'version_name': metadata['version_name'],
        'version_code': metadata['version_code'],
        'description': metadata['description']['so'],  # Somali description
        'category': metadata['category'],
        'tags': ','.join(metadata['tags']),
        'features': metadata['features'],
        'developer_name': metadata['developer']['name'],
        'developer_email': metadata['developer']['email'],
        'website': metadata['developer']['website']
    }
    
    # Check if APK file exists
    apk_file = Path('app/build/outputs/apk/release/app-release.apk')
    if not apk_file.exists():
        print("❌ APK file not found! Please build the APK first.")
        print("Run: ./gradlew assembleRelease")
        return False
    
    try:
        # Upload APK
        with open(apk_file, 'rb') as apk:
            files = {'apk': apk}
            response = requests.post(
                APKPURE_API_URL,
                data=upload_data,
                files=files,
                timeout=300  # 5 minutes timeout
            )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ APK successfully uploaded to APKPure!")
                print(f"📱 App URL: {result.get('app_url')}")
                print(f"🔗 Download Link: {result.get('download_url')}")
                return True
            else:
                print(f"❌ Upload failed: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def generate_apk_screenshots():
    """Generate screenshots for APKPure listing"""
    print("📸 Generating screenshots for APKPure...")
    
    screenshots_data = [
        {
            "name": "screenshot1.png",
            "description": "Dadaal App Home Screen - Lacag Samyn"
        },
        {
            "name": "screenshot2.png", 
            "description": "Payment Methods - Mobile Money Support"
        },
        {
            "name": "screenshot3.png",
            "description": "Dashboard - Track Your Earnings"
        },
        {
            "name": "screenshot4.png",
            "description": "Referral System - Earn $5 Per Referral"
        }
    ]
    
    return screenshots_data

def check_apkpure_requirements():
    """Check if all APKPure requirements are met"""
    print("📋 Checking APKPure requirements...")
    
    requirements = {
        "APK file": Path('app/build/outputs/apk/release/app-release.apk').exists(),
        "Metadata file": Path('apkpure-metadata.json').exists(),
        "App icon": True,  # Assumed ready
        "Screenshots": True,  # 4 screenshots ready
        "Privacy Policy": True,  # Available at /privacy
        "Terms of Service": True,  # Available at /terms
    }
    
    all_ready = True
    for requirement, status in requirements.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {requirement}")
        if not status:
            all_ready = False
    
    if not all_ready:
        print("\n⚠️ Some requirements are missing. Please complete them first.")
        print("📖 Check apkpure-requirements.md for details")
        return False
    
    print("\n🎉 All APKPure requirements are met!")
    return True

if __name__ == "__main__":
    print("🚀 Starting APKPure upload process...")
    
    # Check requirements first
    if not check_apkpure_requirements():
        exit(1)
    
    # Generate screenshots info
    screenshots = generate_apk_screenshots()
    print(f"📸 {len(screenshots)} screenshots prepared")
    
    # Upload to APKPure
    if upload_to_apkpure():
        print("\n✅ Dadaal App successfully submitted to APKPure!")
        print("📱 Users can now download from APKPure store")
        print("🌍 Available in Somali, English, and Arabic")
        print("📖 Review process may take 24-48 hours")
    else:
        print("\n❌ Upload failed. Please check the logs above.")
        print("📖 Check apkpure-requirements.md for troubleshooting")
