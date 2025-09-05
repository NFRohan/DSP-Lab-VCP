from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
import librosa
import numpy as np
import soundfile as sf
import scipy.signal as signal
from scipy.ndimage import gaussian_filter1d
from scipy.fft import fft, ifft
import os
import time
import gc

app = FastAPI(title="Audio File Upload API", version="1.0.0")

# Add CORS middleware to allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed audio file extensions
ALLOWED_EXTENSIONS = {".mp3", ".wav"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit

# Available voice effects
AVAILABLE_EFFECTS = ["robotic", "male", "female",
                     "baby", "cartoon", "echo", "distorted", "anonymized"]


def validate_audio_file(file: UploadFile) -> bool:
    """Validate if the uploaded file is an audio file with allowed extension."""
    if not file.filename:
        return False
    file_extension = Path(file.filename).suffix.lower()
    return file_extension in ALLOWED_EXTENSIONS


def get_safe_filename(filename: str) -> str:
    """Generate a safe filename to prevent path traversal attacks."""
    # Remove any path components and keep only the filename
    safe_name = Path(filename).name
    return safe_name


def validate_file_exists_and_type(filename: str) -> Path:
    """
    Validate that a file exists and is a valid audio file.

    Args:
        filename: The name of the file to validate

    Returns:
        Path: The validated file path

    Raises:
        HTTPException: If file doesn't exist, is invalid, or wrong type
    """
    # Validate filename to prevent path traversal
    safe_filename = get_safe_filename(filename)
    file_path = UPLOAD_DIR / safe_filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Invalid file")

    # Check if it's an allowed audio file
    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not allowed")

    return file_path


def safe_delete_file(file_path: Path, max_attempts: int = 5, delay: float = 0.5) -> bool:
    """
    Safely delete a file with retry mechanism to handle Windows file locks.

    Args:
        file_path: Path to the file to delete
        max_attempts: Maximum number of deletion attempts
        delay: Delay between attempts in seconds

    Returns:
        bool: True if file was deleted successfully

    Raises:
        Exception: If file cannot be deleted after all attempts
    """
    for attempt in range(max_attempts):
        try:
            # Force garbage collection to release any file handles
            gc.collect()

            # Try to delete the file
            if file_path.exists():
                file_path.unlink()
                return True
            else:
                return True  # File already deleted

        except PermissionError as e:
            if attempt == max_attempts - 1:
                # Last attempt failed
                raise Exception(
                    f"Cannot delete file '{file_path.name}' - it may be in use by another process. Please stop any audio playback and try again.")

            # Wait before retrying
            time.sleep(delay)
            delay *= 1.5  # Exponential backoff

        except Exception as e:
            # Other errors, don't retry
            raise Exception(
                f"Error deleting file '{file_path.name}': {str(e)}")

    return False

# ==============================
# Voice Processing Functions
# ==============================


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


def validate_file_exists_and_type(filename: str) -> Path:
    """
    Validate that a file exists and is a valid audio file.

    Args:
        filename: The name of the file to validate

    Returns:
        Path: The validated file path

    Raises:
        HTTPException: If file doesn't exist, is invalid, or wrong type
    """
    # Validate filename to prevent path traversal
    safe_filename = get_safe_filename(filename)
    file_path = UPLOAD_DIR / safe_filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Invalid file")

    # Check if it's an allowed audio file
    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not allowed")

    return file_path


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Audio File Upload & Voice Processing API",
        "version": "1.0.0",
        "supported_formats": list(ALLOWED_EXTENSIONS),
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "available_voice_effects": AVAILABLE_EFFECTS,
        "endpoints": {
            "upload": "/upload-audio/",
            "process": "/process-audio/{filename}?effect={effect_type}",
            "download": "/download-file/{filename}",
            "list": "/uploaded-files/",
            "delete": "/delete-file/{filename}",
            "effects": "/voice-effects/"
        }
    }


@app.post("/upload-audio/")
async def upload_audio_file(file: UploadFile = File(...)):
    """
    Upload an audio file (MP3 or WAV) and save it to local storage.

    Args:
        file: The audio file to upload

    Returns:
        JSON response with upload status and file information
    """
    try:
        # Validate file extension
        if not validate_audio_file(file):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed."
            )

        # Check file size
        file.file.seek(0, 2)  # Move to end of file
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB."
            )

        # Generate safe filename
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file must have a filename."
            )
        safe_filename = get_safe_filename(file.filename)
        file_path = UPLOAD_DIR / safe_filename

        # Handle duplicate filenames by adding a counter
        counter = 1
        original_path = file_path
        while file_path.exists():
            name_part = original_path.stem
            extension = original_path.suffix
            file_path = UPLOAD_DIR / f"{name_part}_{counter}{extension}"
            counter += 1

        # Save the file asynchronously
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        return JSONResponse(
            status_code=200,
            content={
                "message": "File uploaded successfully",
                "filename": file_path.name,
                "original_filename": file.filename,
                "file_size_bytes": file_size,
                "file_path": str(file_path),
                "content_type": file.content_type
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/uploaded-files/")
async def list_uploaded_files():
    """List all uploaded audio files."""
    try:
        files = []
        for file_path in UPLOAD_DIR.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ALLOWED_EXTENSIONS:
                file_stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "size_bytes": file_stat.st_size,
                    "created_at": file_stat.st_ctime,
                    "file_path": str(file_path)
                })

        return JSONResponse(
            status_code=200,
            content={
                "message": "Files retrieved successfully",
                "files": files,
                "total_count": len(files)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving files: {str(e)}")


@app.get("/files/{filename}")
async def get_file(filename: str):
    """Serve audio files for playback."""
    try:
        # Validate and get safe filename
        safe_filename = get_safe_filename(filename)
        file_path = validate_file_exists_and_type(safe_filename)

        # Return the file for streaming/download
        return FileResponse(
            path=file_path,
            media_type="audio/wav",
            filename=safe_filename
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"File '{filename}' not found")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error serving file: {str(e)}")


@app.get("/voice-effects/")
async def get_voice_effects():
    """Get available voice effects and their descriptions."""
    effects_info = {
        "robotic": {
            "name": "Robotic Voice",
            "description": "Applies ring modulation and pitch flattening for a metallic robot sound"
        },
        "male": {
            "name": "Male Voice",
            "description": "Transforms voice to sound more masculine by lowering pitch"
        },
        "female": {
            "name": "Female Voice",
            "description": "Enhanced female voice with formant shifting, breathiness, and EQ adjustments"
        },
        "baby": {
            "name": "Baby Voice",
            "description": "Creates a high-pitched baby-like voice with time stretching"
        },
        "cartoon": {
            "name": "Cartoon Voice",
            "description": "Cartoon-like effect with high pitch, frequency manipulation, and modulation"
        },
        "echo": {
            "name": "Echo Voice",
            "description": "Adds echo effect using FIR filter for spatial depth"
        },
        "distorted": {
            "name": "Distorted Voice",
            "description": "Applies distortion using nonlinear processing and high-pass filtering"
        },
        "anonymized": {
            "name": "Anonymized Voice",
            "description": "Anonymous organization-style voice anonymization with pitch lowering, formant shifting, bandpass filtering, and dynamic compression while maintaining intelligibility"
        }
    }

    return JSONResponse(
        status_code=200,
        content={
            "available_effects": AVAILABLE_EFFECTS,
            "effects_details": effects_info,
            "total_effects": len(AVAILABLE_EFFECTS)
        }
    )


@app.get("/download-file/{filename}")
async def download_file(filename: str):
    """Download an uploaded audio file."""
    try:
        # Validate file exists and is correct type
        file_path = validate_file_exists_and_type(filename)

        # Return the file as a download response
        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type='application/octet-stream'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error downloading file: {str(e)}")


@app.delete("/delete-file/{filename}")
async def delete_file(filename: str):
    """Delete an uploaded audio file."""
    try:
        # Validate file exists and is correct type
        file_path = validate_file_exists_and_type(filename)

        # Delete the file safely with retry mechanism
        safe_delete_file(file_path)

        return JSONResponse(
            status_code=200,
            content={
                "message": "File deleted successfully",
                "filename": file_path.name
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting file: {str(e)}")


@app.post("/process-audio/{filename}")
async def process_audio(filename: str, effect: str = Query(..., description="Voice effect to apply")):
    """
    Process an audio file with voice transformation.

    Args:
        filename: The name of the file to process
        effect: Type of voice transformation (male, female, robotic, baby)

    Returns:
        JSON response with processing status and processed file information
    """
    try:
        # Validate effect type
        if effect.lower() not in AVAILABLE_EFFECTS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid effect type. Allowed types: {', '.join(AVAILABLE_EFFECTS)}"
            )

        # Validate file exists and is correct type
        input_file_path = validate_file_exists_and_type(filename)

        # Generate output filename
        name_part = input_file_path.stem
        extension = input_file_path.suffix
        output_filename = f"{name_part}_{effect.lower()}{extension}"
        output_file_path = UPLOAD_DIR / output_filename

        # Handle duplicate output filenames
        counter = 1
        original_output_path = output_file_path
        while output_file_path.exists():
            output_filename = f"{name_part}_{effect.lower()}_{counter}{extension}"
            output_file_path = UPLOAD_DIR / output_filename
            counter += 1

        # Load audio file
        try:
            audio_data, sample_rate = librosa.load(
                str(input_file_path), sr=None)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error loading audio file: {str(e)}"
            )

        # Apply voice effect
        try:
            processed_audio = apply_voice_effect(
                audio_data, sample_rate, effect.lower())
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error applying voice effect: {str(e)}"
            )

        # Apply volume boost to make output louder
        if np.max(np.abs(processed_audio)) > 0:
            processed_audio = processed_audio / np.max(np.abs(processed_audio)) * 0.95

        # Save processed audio
        try:
            sf.write(str(output_file_path), processed_audio, sample_rate)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error saving processed audio: {str(e)}"
            )

        # Get file size for response
        processed_file_size = output_file_path.stat().st_size

        return JSONResponse(
            status_code=200,
            content={
                "message": f"Audio processing completed successfully",
                "input_filename": input_file_path.name,
                "output_filename": output_file_path.name,
                "effect_applied": effect.lower(),
                "output_size_bytes": processed_file_size,
                "status": "completed"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing audio: {str(e)}")
