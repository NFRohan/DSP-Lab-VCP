#!/usr/bin/env python3
"""
Test script for voice processing API endpoints
"""

import requests
import json
import os

# API base URL
BASE_URL = "http://localhost:8000"

def test_voice_effects_endpoint():
    """Test the voice effects endpoint"""
    print("Testing /voice-effects/ endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/voice-effects/")
        if response.status_code == 200:
            data = response.json()
            print("✅ Voice effects endpoint working")
            print("Available effects:")
            for effect in data["available_effects"]:
                print(f"  - {effect}: {data['effects_details'][effect]['description']}")
        else:
            print(f"❌ Voice effects endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing voice effects: {e}")

def test_upload_and_process(audio_file_path):
    """Test uploading a file and processing it with voice effects"""
    if not os.path.exists(audio_file_path):
        print(f"❌ Audio file not found: {audio_file_path}")
        return
    
    print(f"\nTesting upload and processing with {audio_file_path}...")
    
    # Upload file
    print("1. Uploading file...")
    try:
        with open(audio_file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{BASE_URL}/upload-audio/", files=files)
        
        if response.status_code == 200:
            upload_data = response.json()
            filename = upload_data["filename"]
            print(f"✅ File uploaded successfully: {filename}")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return
    
    # Test each voice effect
    effects = ["robotic", "male", "female", "baby"]
    for effect in effects:
        print(f"\n2. Processing with {effect} effect...")
        try:
            response = requests.post(
                f"{BASE_URL}/process-audio/{filename}?effect={effect}"
            )
            
            if response.status_code == 200:
                process_data = response.json()
                print(f"✅ {effect.capitalize()} effect applied successfully")
                print(f"   Output file: {process_data['output_filename']}")
            else:
                print(f"❌ {effect.capitalize()} effect failed: {response.status_code}")
                if response.text:
                    print(f"   Error: {response.text}")
        except Exception as e:
            print(f"❌ Processing error for {effect}: {e}")

def test_api_info():
    """Test the root endpoint"""
    print("Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print("✅ Root endpoint working")
            print(f"API: {data['message']}")
            print(f"Voice effects available: {data['available_voice_effects']}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing root endpoint: {e}")

def main():
    print("🎵 Voice Processing API Test Suite")
    print("=" * 40)
    
    # Test basic endpoints
    test_api_info()
    test_voice_effects_endpoint()
    
    # Test file processing (you need to provide an audio file)
    print("\n" + "=" * 40)
    print("File Processing Tests")
    print("=" * 40)
    
    # Check for test audio files in common locations
    test_files = [
        "test_audio.wav",
        "test_audio.mp3",
        "sample.wav", 
        "sample.mp3"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            test_upload_and_process(test_file)
            break
    else:
        print("⚠️  No test audio file found. Please create a test audio file to test processing.")
        print("   Expected files: test_audio.wav, test_audio.mp3, sample.wav, or sample.mp3")

if __name__ == "__main__":
    main()
