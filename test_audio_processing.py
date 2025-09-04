#!/usr/bin/env python3
"""
Simple test to identify the exact issue with voice processing
"""

import librosa
import numpy as np
import soundfile as sf
from pathlib import Path


def test_audio_file(filename):
    """Test if we can load and process an audio file."""
    print(f"🧪 Testing audio file: {filename}")

    file_path = Path("uploads") / filename
    print(f"   File path: {file_path}")
    print(f"   File exists: {file_path.exists()}")

    if not file_path.exists():
        print("   ❌ File does not exist!")
        return False

    try:
        print("   Loading with librosa...")
        audio_data, sample_rate = librosa.load(str(file_path), sr=None)
        print(f"   ✅ Loaded successfully!")
        print(f"   Audio shape: {audio_data.shape}")
        print(f"   Sample rate: {sample_rate}")
        print(f"   Duration: {len(audio_data) / sample_rate:.2f} seconds")

        # Test a simple voice effect
        print("   Testing pitch shift...")
        processed = librosa.effects.pitch_shift(
            y=audio_data, sr=sample_rate, n_steps=2)
        print(f"   ✅ Pitch shift successful!")
        print(f"   Processed shape: {processed.shape}")

        # Test saving
        output_path = Path("uploads") / f"test_output_{filename}"
        sf.write(str(output_path), processed, sample_rate)
        print(f"   ✅ Saved test output to: {output_path}")

        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    print("🎵 Audio File Processing Test")
    print("=" * 40)

    # Test the existing file
    test_audio_file("Untitled notebook.wav")

    print("\n" + "=" * 40)
    print("Test completed!")


if __name__ == "__main__":
    main()
