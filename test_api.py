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

def create_sample_audio_file():
    """Create a simple WAV file for testing purposes."""
    print("Creating sample audio file for testing...")
    try:
        # Create a simple WAV file (this is just for testing - it won't be a real audio file)
        sample_content = b'RIFF\x24\x08\x00\x00WAVE' + b'\x00' * 1000  # Minimal WAV-like header
        
        with open("sample_test.wav", "wb") as f:
            f.write(sample_content)
        
        print("✅ Created sample_test.wav")
        return "sample_test.wav"
    except Exception as e:
        print(f"❌ Error creating sample file: {e}")
        return None

def main():
    """Run all tests."""
    print("🚀 FastAPI Audio Upload Backend Test Suite")
    print("=" * 50)
    
    # Test API info
    if not test_api_info():
        print("\n❌ Server is not running. Please start it first:")
        print("   python run_server.py")
        return
    
    print("\n✅ Server is running!")
    
    # Create a sample file for testing
    sample_file = create_sample_audio_file()
    
    if sample_file:
        # Test file upload
        test_upload_file(sample_file)
        
        # Test listing files
        test_list_files()
        
        # Clean up
        try:
            Path(sample_file).unlink()
            print(f"\n🧹 Cleaned up {sample_file}")
        except:
            pass
    
    print("\n" + "=" * 50)
    print("Test completed! 🎉")
    print("\nTo test with real audio files:")
    print("1. Put an MP3 or WAV file in this directory")
    print("2. Run: python test_api.py")
    print("3. Check the uploads/ directory for saved files")

if __name__ == "__main__":
    main()
