#!/usr/bin/env python3
"""
Test script for the FastAPI Audio Upload Backend

This script demonstrates how to interact with the audio upload API.
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"


def test_api_info():
    """Test the root endpoint to get API information."""
    print("Testing API info endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure it's running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_upload_file(file_path: str):
    """Test uploading a single file."""
    print(f"\nTesting file upload: {file_path}")

    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return False

    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{BASE_URL}/upload-audio/", files=files)

        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_list_files():
    """Test listing uploaded files."""
    print("\nTesting list files endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/uploaded-files/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_voice_effects():
    """Test the voice effects endpoint."""
    print("\nTesting voice effects endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/voice-effects/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_voice_processing(filename: str, effect: str):
    """Test voice processing with a specific effect."""
    print(f"\nTesting voice processing: {filename} with {effect} effect...")
    try:
        response = requests.post(
            f"{BASE_URL}/process-audio/{filename}?effect={effect}")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print(
                f"✅ Processed file: {data.get('output_filename', 'Unknown')}")
        else:
            print(f"❌ Error Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_all_voice_effects(filename: str):
    """Test all available voice effects."""
    print(f"\n🎛️ Testing all voice effects for {filename}...")
    effects = ["robotic", "male", "female", "baby"]
    results = {}

    for effect in effects:
        print(f"\n--- Testing {effect.upper()} effect ---")
        success = test_voice_processing(filename, effect)
        results[effect] = success
        if success:
            print(f"✅ {effect.capitalize()} effect completed successfully")
        else:
            print(f"❌ {effect.capitalize()} effect failed")

    print(f"\n📊 Voice Processing Results:")
    print(f"{'Effect':<10} {'Status':<10}")
    print("-" * 20)
    for effect, success in results.items():
        status = "✅ Pass" if success else "❌ Fail"
        print(f"{effect.capitalize():<10} {status:<10}")

    return results


def create_sample_audio_file():
    """Create a simple WAV file for testing purposes."""
    print("Creating sample audio file for testing...")
    try:
        # Create a simple WAV file (this is just for testing - it won't be a real audio file)
        sample_content = b'RIFF\x24\x08\x00\x00WAVE' + \
            b'\x00' * 1000  # Minimal WAV-like header

        with open("sample_test.wav", "wb") as f:
            f.write(sample_content)

        print("✅ Created sample_test.wav")
        return "sample_test.wav"
    except Exception as e:
        print(f"❌ Error creating sample file: {e}")
        return None


def main():
    """Run all tests."""
    print("🚀 FastAPI Audio Upload & Voice Processing Backend Test Suite")
    print("=" * 60)

    # Test API info
    if not test_api_info():
        print("\n❌ Server is not running. Please start it first:")
        print("   python run_server.py")
        return

    print("\n✅ Server is running!")

    # Test voice effects endpoint
    test_voice_effects()

    # Create a sample file for testing
    sample_file = create_sample_audio_file()

    if sample_file:
        # Test file upload
        if test_upload_file(sample_file):
            # Test all voice processing effects
            test_all_voice_effects(sample_file)

        # Test listing files
        test_list_files()

        # Clean up
        try:
            Path(sample_file).unlink()
            print(f"\n🧹 Cleaned up {sample_file}")
        except:
            pass

    print("\n" + "=" * 60)
    print("Test completed! 🎉")
    print("\nTo test with real audio files:")
    print("1. Put an MP3 or WAV file in this directory")
    print("2. Run: python test_api.py")
    print("3. Check the uploads/ directory for processed files")
    print("\nNew voice processing endpoints:")
    print("- GET /voice-effects/ - List available voice effects")
    print(
        "- POST /process-audio/{filename}?effect={effect} - Process audio file")


if __name__ == "__main__":
    main()
