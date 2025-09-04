#!/usr/bin/env python3
"""
Debug voice processing issues
"""

import requests
import json
import urllib.parse

BASE_URL = "http://localhost:8000"


def test_process_with_existing_file():
    """Test processing with the existing file in uploads."""
    print("🔍 Debugging voice processing issue...")

    # First, check what files exist
    print("\n1. Checking uploaded files...")
    try:
        r = requests.get(f"{BASE_URL}/uploaded-files/")
        if r.status_code == 200:
            files = r.json()["files"]
            print(f"   Found {len(files)} files:")
            for f in files:
                print(f"   - {f['filename']}")
        else:
            print(f"   Error: {r.status_code}")
            return
    except Exception as e:
        print(f"   Connection error: {e}")
        return

    if not files:
        print("   No files found!")
        return

    # Test with the first file
    test_filename = files[0]['filename']
    print(f"\n2. Testing voice processing with: {test_filename}")

    # Test each effect
    effects = ["robotic", "male", "female", "baby"]
    for effect in effects:
        print(f"\n   Testing {effect} effect...")

        try:
            # URL encode the filename properly
            encoded_filename = urllib.parse.quote(test_filename, safe='')
            url = f"{BASE_URL}/process-audio/{encoded_filename}?effect={effect}"
            print(f"   Request URL: {url}")

            r = requests.post(url)
            print(f"   Status: {r.status_code}")

            if r.status_code != 200:
                print(f"   Error Response: {r.text}")
            else:
                result = r.json()
                print(f"   ✅ Success: {result.get('message', 'No message')}")
                print(
                    f"   Output file: {result.get('output_filename', 'Unknown')}")

        except Exception as e:
            print(f"   ❌ Exception: {e}")


if __name__ == "__main__":
    test_process_with_existing_file()
