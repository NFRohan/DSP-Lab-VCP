#!/usr/bin/env python3
"""
Generate a simple test audio file for voice processing demo
"""

import numpy as np
import soundfile as sf


def generate_test_audio():
    """Generate a simple test audio with multiple tones."""
    duration = 3.0  # seconds
    sample_rate = 22050  # Hz

    # Generate time array
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # Create a simple melody with multiple frequencies (simulates speech-like frequencies)
    frequencies = [220, 261, 294, 330, 370]  # A3, C4, D4, E4, F#4

    signal = np.zeros_like(t)
    for i, freq in enumerate(frequencies):
        # Add each frequency with decreasing amplitude and at different times
        start_time = i * duration / len(frequencies)
        end_time = (i + 1) * duration / len(frequencies)

        mask = (t >= start_time) & (t < end_time)
        amplitude = 0.3 * (1 - i * 0.1)  # Decreasing amplitude

        signal[mask] += amplitude * np.sin(2 * np.pi * freq * t[mask])

    # Add some harmonics to make it more voice-like
    for harmonic in [2, 3]:
        for freq in frequencies:
            signal += 0.1 * np.sin(2 * np.pi * freq * harmonic * t)

    # Apply envelope to avoid clicks
    envelope = np.ones_like(signal)
    fade_samples = int(0.01 * sample_rate)  # 10ms fade
    envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
    envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)

    signal *= envelope

    # Normalize
    signal = signal / np.max(np.abs(signal)) * 0.8

    return signal, sample_rate


def main():
    print("🎵 Generating test audio file...")

    # Generate test audio
    audio_data, sample_rate = generate_test_audio()

    # Save as WAV file
    filename = "test_voice_sample.wav"
    sf.write(filename, audio_data, sample_rate)

    print(f"✅ Generated {filename}")
    print(f"   Duration: 3.0 seconds")
    print(f"   Sample Rate: {sample_rate} Hz")
    print(f"   File Size: {len(audio_data) * 4 / 1024:.1f} KB")
    print(f"\n🧪 You can now test voice processing with this file!")
    print(
        f"   1. Upload {filename} to the web interface at http://localhost:5173")
    print(f"   2. Try different voice effects: robotic, male, female, baby")
    print(f"   3. Download the processed files")


if __name__ == "__main__":
    main()
