import librosa
import numpy as np
import scipy.signal as signal
from scipy.ndimage import gaussian_filter1d


def detect_gender(y, sr):
    """Detect gender based on fundamental frequency analysis."""
    try:
        # Estimate pitch contour
        f0 = librosa.yin(y, fmin=50, fmax=300, sr=sr)
        mean_f0 = np.nanmean(f0)

        if mean_f0 < 165:
            return "male", mean_f0
        else:
            return "female", mean_f0
    except Exception:
        # If pitch detection fails, assume male voice
        return "male", 150.0


def robotic_voice(y, sr):
    """Apply robotic voice effect using ring modulation and pitch flattening."""
    # Ring modulation (classic robot effect)
    t = np.linspace(0, len(y)/sr, len(y))
    modulator = np.sin(2*np.pi*30*t)  # 30Hz modulation
    robotic = y * modulator

    # Flatten pitch with STFT
    D = librosa.stft(robotic)
    mag, phase = np.abs(D), np.angle(D)
    robotic = librosa.istft(mag * np.exp(1j * np.sign(phase)), length=len(y))

    # Slight distortion for metallic effect
    robotic = np.tanh(robotic * 3)
    return robotic


def male_voice(y, sr):
    """Transform voice to sound more masculine."""
    gender, f0 = detect_gender(y, sr)
    if gender == "male":
        # already male → shift slightly lower
        return librosa.effects.pitch_shift(y=y, sr=sr, n_steps=-2)
    else:
        # female to male → bigger shift down
        return librosa.effects.pitch_shift(y=y, sr=sr, n_steps=-5)


def female_voice(y, sr):
    """
    Enhanced female voice transformation with improved formant shifting and reduced noise
    """
    # Step 1: Pitch shift
    pitch_shift_semitones = 5  # Increased for better female F0 range
    y_pitched = librosa.effects.pitch_shift(
        y, sr=sr, n_steps=pitch_shift_semitones)

    # Step 2: Formant shifting
    hop_length = 512
    n_fft = 2048
    D = librosa.stft(y_pitched, hop_length=hop_length, n_fft=n_fft)
    magnitude = np.abs(D)
    phase = np.angle(D)
    formant_shift_factor = 1.2  # Increased to better simulate female vocal tract
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    shifted_magnitude = np.zeros_like(magnitude)
    for i, frame_mag in enumerate(magnitude.T):
        new_freqs = freqs / formant_shift_factor
        valid_idx = new_freqs <= freqs[-1]
        shifted_frame = np.interp(
            freqs, new_freqs[valid_idx], frame_mag[valid_idx])
        shifted_magnitude[:, i] = shifted_frame
    D_shifted = shifted_magnitude * np.exp(1j * phase)
    y_formant_shifted = librosa.istft(D_shifted, hop_length=hop_length)

    # Step 3: Subtle breathiness (reduced to minimize static)
    noise = np.random.normal(0, 0.002, len(
        y_formant_shifted))  # Lowered amplitude
    y_breathy = y_formant_shifted + noise

    # Step 4: EQ adjustments for female formants
    nyquist = sr // 2
    low_freq = 2000 / nyquist
    high_freq = 4000 / nyquist
    sos = signal.butter(4, [low_freq, high_freq], btype='band', output='sos')
    boost_signal = signal.sosfilt(sos, y_breathy)
    y_eq = y_breathy + 0.3 * boost_signal  # Increased boost for clarity

    # Step 5: High-frequency emphasis
    pre_emphasis = 0.9
    y_preemph = np.append(y_eq[0], y_eq[1:] - pre_emphasis * y_eq[:-1])
    y_eq = 0.8 * y_eq + 0.2 * y_preemph  # Subtle mix for brightness

    # Step 6: Gentle compression
    threshold = 0.4  # Raised threshold for more natural dynamics
    ratio = 2.5  # Softer compression
    y_compressed = np.where(np.abs(y_eq) > threshold,
                            np.sign(y_eq) * (threshold +
                                             (np.abs(y_eq) - threshold) / ratio),
                            y_eq)

    # Step 7: Normalize
    if np.max(np.abs(y_compressed)) > 0:
        y_compressed = y_compressed / np.max(np.abs(y_compressed)) * 0.95

    return y_compressed


def baby_voice(y, sr):
    """Transform voice to sound like a baby."""
    gender, f0 = detect_gender(y, sr)
    if gender == "female":
        shift = 5  # less shift (otherwise becomes chipmunk)
    else:
        shift = 7  # more shift for male voice
    y = librosa.effects.pitch_shift(y=y, sr=sr, n_steps=shift)
    y = librosa.effects.time_stretch(y=y, rate=1.2)
    return y


def cartoon_voice(y, sr):
    """Cartoon-like voice effect"""
    y = librosa.effects.pitch_shift(y=y, sr=sr, n_steps=8)
    D = librosa.stft(y, n_fft=2048, hop_length=512)
    mag, phase = np.abs(D), np.angle(D)
    freq_bins = np.fft.fftfreq(2048, 1/sr)[:1025]
    for i, factor in enumerate([1.2, 0.9, 1.1]):
        start_freq = 200 + i * 800
        end_freq = start_freq + 800
        mask = (freq_bins >= start_freq) & (freq_bins <= end_freq)
        mag[mask] = mag[mask] * factor
    y = librosa.istft(mag * np.exp(1j * phase), hop_length=512)
    y = librosa.effects.time_stretch(y=y, rate=1.3)
    t = np.linspace(0, len(y)/sr, len(y))
    modulator = 1 + 0.3 * np.sin(2*np.pi*50*t)
    y = y * modulator
    return y


def echo_voice(y, sr):
    """Add echo effect using FIR filter"""
    delay_samples = int(0.3 * sr)
    b = np.zeros(delay_samples + 1)
    b[0] = 1.0
    b[-1] = 0.5
    y_echo = signal.lfilter(b, [1], y)
    return y_echo


def distorted_voice(y, sr):
    """Apply distortion using nonlinear processing"""
    drive = 3.0
    y_dist = np.tanh(drive * y) / drive
    y_dist = y_dist + 0.1 * np.sin(2 * np.pi * y_dist * sr / 1000)
    b, a = signal.butter(4, 100, btype='highpass', fs=sr)
    y_dist = signal.filtfilt(b, a, y_dist)
    return y_dist


def anonymized_voice(y, sr):
    """
    Anonymous Organization-style voice anonymization
    Maintains intelligibility while providing anonymity
    """
    # Step 1: Pitch shift to lower register
    pitch_shift_semitones = -6
    y_pitched = librosa.effects.pitch_shift(
        y=y, sr=sr, n_steps=pitch_shift_semitones)

    # Step 2: Formant shifting
    D = librosa.stft(y_pitched, n_fft=2048, hop_length=512)
    magnitude = np.abs(D)
    phase = np.angle(D)
    freq_bins = np.fft.fftfreq(2048, 1/sr)[:1025]
    formant_regions = [(200, 800), (800, 1800), (1800, 3200)]
    for i, (low_freq, high_freq) in enumerate(formant_regions):
        mask = (freq_bins >= low_freq) & (freq_bins <= high_freq)
        if i == 0:
            magnitude[mask] *= 0.85
        elif i == 1:
            magnitude[mask] *= 1.1
        else:
            magnitude[mask] *= 0.9
    for i in range(len(freq_bins)):
        if freq_bins[i] > 4000:
            magnitude[i] *= 0.7 * np.exp(-(freq_bins[i] - 4000) / 2000)
        elif 1000 <= freq_bins[i] <= 3000:
            magnitude[i] *= 1.05
    y_formant = librosa.istft(magnitude * np.exp(1j * phase), hop_length=512)

    # Step 3: Bandpass filter (300–3400 Hz)
    b, a = signal.butter(4, [300, 3400], btype='band', fs=sr)
    y_filtered = signal.filtfilt(b, a, y_formant)

    # Step 4: Subtle distortion
    drive = 1.5
    y_driven = np.tanh(drive * y_filtered) / drive

    # Step 5: Dynamic range compression
    threshold = 0.3
    ratio = 4.0
    attack = 0.003
    release = 0.1
    envelope = np.zeros_like(y_driven)
    attack_coeff = np.exp(-1.0 / (attack * sr))
    release_coeff = np.exp(-1.0 / (release * sr))
    for i in range(1, len(y_driven)):
        input_level = abs(y_driven[i])
        if input_level > envelope[i-1]:
            envelope[i] = attack_coeff * envelope[i-1] + \
                (1 - attack_coeff) * input_level
        else:
            envelope[i] = release_coeff * envelope[i-1] + \
                (1 - release_coeff) * input_level
    compressed = np.zeros_like(y_driven)
    for i in range(len(y_driven)):
        if envelope[i] > threshold:
            over_threshold = envelope[i] - threshold
            compressed_over = over_threshold / ratio
            gain_reduction = (threshold + compressed_over) / \
                envelope[i] if envelope[i] > 0 else 1
            compressed[i] = y_driven[i] * gain_reduction
        else:
            compressed[i] = y_driven[i]
    y_compressed = compressed

    # Step 6: Subtle vocoder-like effect
    D = librosa.stft(y_compressed, n_fft=2048, hop_length=512)
    magnitude = np.abs(D)
    phase = np.angle(D)
    magnitude_smooth = gaussian_filter1d(magnitude, sigma=0.5, axis=0)
    magnitude_blend = 0.85 * magnitude + 0.15 * magnitude_smooth
    y_vocoded = librosa.istft(
        magnitude_blend * np.exp(1j * phase), hop_length=512)

    # Step 7: Final normalization
    if np.max(np.abs(y_vocoded)) > 0:
        y_vocoded = y_vocoded / np.max(np.abs(y_vocoded)) * 0.95

    return y_vocoded


def apply_voice_effect(audio_data, sample_rate, effect_type):
    """
    Apply the specified voice effect to audio data.

    Args:
        audio_data: numpy array of audio samples
        sample_rate: sample rate of the audio
        effect_type: type of effect to apply

    Returns:
        processed audio data as numpy array
    """
    effect_type = effect_type.lower()

    if effect_type == "robotic":
        return robotic_voice(audio_data, sample_rate)
    elif effect_type == "male":
        return male_voice(audio_data, sample_rate)
    elif effect_type == "female":
        return female_voice(audio_data, sample_rate)
    elif effect_type == "baby":
        return baby_voice(audio_data, sample_rate)
    elif effect_type == "cartoon":
        return cartoon_voice(audio_data, sample_rate)
    elif effect_type == "echo":
        return echo_voice(audio_data, sample_rate)
    elif effect_type == "distorted":
        return distorted_voice(audio_data, sample_rate)
    elif effect_type == "anonymized":
        return anonymized_voice(audio_data, sample_rate)
    else:
        raise ValueError(f"Unknown effect type: {effect_type}")
