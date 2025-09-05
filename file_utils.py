from pathlib import Path
from fastapi import HTTPException, UploadFile
import time
import gc
from config import UPLOAD_DIR, ALLOWED_EXTENSIONS


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


def get_unique_filename(base_path: Path) -> Path:
    """
    Generate a unique filename by adding a counter if the file already exists.

    Args:
        base_path: The desired file path

    Returns:
        Path: A unique file path
    """
    if not base_path.exists():
        return base_path

    counter = 1
    original_path = base_path
    while base_path.exists():
        name_part = original_path.stem
        extension = original_path.suffix
        base_path = original_path.parent / f"{name_part}_{counter}{extension}"
        counter += 1

    return base_path
