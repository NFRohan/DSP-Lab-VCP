from pathlib import Path

# Directory configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# File handling configuration
ALLOWED_EXTENSIONS = {".mp3", ".wav"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit

# Available voice effects
AVAILABLE_EFFECTS = ["robotic", "male", "female",
                     "baby", "cartoon", "echo", "distorted", "anonymized"]

# API information
API_INFO = {
    "title": "Audio File Upload & Voice Processing API",
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

# Effects information
EFFECTS_INFO = {
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
