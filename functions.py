import librosa
import numpy as np
import soundfile as sf
import logging

def detect_gender(y, sr):
    """Estimate gender from pitch contour. Falls back safely if estimation fails."""
    try:
        if y is None or len(y) == 0:
            return "female", 200.0
        
        # Use piptrack instead of yin for better stability
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr, fmin=50, fmax=400)
        
        # Extract pitch values where magnitude is high
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        if len(pitch_values) == 0:
            return "female", 200.0
            
        mean_f0 = np.mean(pitch_values)
        
        if np.isnan(mean_f0) or np.isinf(mean_f0):
            return "female", 200.0
            
        if mean_f0 < 165:
            return "male", mean_f0
        else:
            return "female", mean_f0
    except Exception as e:
        logging.warning(f"Gender detection failed: {e}")
        return "female", 200.0

def robotic_voice(y, sr):
    """Apply robotic (ring modulation) effect."""
    try:
        y = np.asarray(y, dtype=np.float32)
        if y.size == 0 or sr <= 0:
            return y
        
        t = np.linspace(0, len(y) / sr, len(y), dtype=np.float32)
        modulator = np.sin(2 * np.pi * 30 * t)  # 30Hz modulation
        robotic = y * modulator
        
        try:
            D = librosa.stft(robotic)
            mag, phase = np.abs(D), np.angle(D)
            robotic = librosa.istft(mag * np.exp(1j * np.sign(phase)))
        except Exception:
            pass
        
        # Apply soft clipping
        robotic = np.tanh(robotic * 3)
        return robotic.astype(np.float32, copy=False)
    except Exception as e:
        logging.error(f"Robotic voice effect failed: {e}")
        return y

def male_voice(y, sr):
    """Transform voice to male."""
    try:
        y = np.asarray(y, dtype=np.float32)
        if y.size == 0:
            return y
        
        gender, _ = detect_gender(y, sr)
        n_steps = -2 if gender == "male" else -5
        
        return librosa.effects.pitch_shift(y=y, sr=sr, n_steps=n_steps)
    except Exception as e:
        logging.error(f"Male voice transformation failed: {e}")
        return y

def female_voice(y, sr):
    """Transform voice to female."""
    try:
        y = np.asarray(y, dtype=np.float32)
        if y.size == 0:
            return y
        
        gender, _ = detect_gender(y, sr)
        n_steps = 2 if gender == "female" else 5
        
        return librosa.effects.pitch_shift(y=y, sr=sr, n_steps=n_steps)
    except Exception as e:
        logging.error(f"Female voice transformation failed: {e}")
        return y

def baby_voice(y, sr):
    """Transform voice to baby."""
    try:
        y = np.asarray(y, dtype=np.float32)
        if y.size == 0:
            return y
        
        gender, _ = detect_gender(y, sr)
        shift = 5 if gender == "female" else 7
        
        # Apply pitch shift
        try:
            y_shifted = librosa.effects.pitch_shift(y=y, sr=sr, n_steps=shift)
        except Exception as e:
            logging.warning(f"Pitch shift failed: {e}")
            y_shifted = y
        
        # Instead of time_stretch, use a simpler approach with resampling
        try:
            # Simulate faster speech by resampling and then padding/truncating
            target_length = int(len(y_shifted) * 0.85)  # Make it 15% faster
            if target_length > 0:
                # Simple linear interpolation for speed change
                indices = np.linspace(0, len(y_shifted) - 1, target_length)
                y_stretched = np.interp(indices, np.arange(len(y_shifted)), y_shifted)
            else:
                y_stretched = y_shifted
        except Exception as e:
            logging.warning(f"Time stretching failed: {e}")
            y_stretched = y_shifted
        
        # Add a slight tremolo effect for baby-like quality
        try:
            t = np.linspace(0, len(y_stretched) / sr, len(y_stretched))
            tremolo = 1 + 0.1 * np.sin(2 * np.pi * 5 * t)  # 5Hz tremolo
            y_stretched = y_stretched * tremolo
        except Exception as e:
            logging.warning(f"Tremolo effect failed: {e}")
        
        return y_stretched.astype(np.float32, copy=False)
        
    except Exception as e:
        logging.error(f"Baby voice transformation failed: {e}")
        return y