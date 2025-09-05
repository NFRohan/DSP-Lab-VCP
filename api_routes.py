from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
import aiofiles
import librosa
import numpy as np
import soundfile as sf
from config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE, AVAILABLE_EFFECTS, API_INFO, EFFECTS_INFO
from file_utils import validate_audio_file, get_safe_filename, validate_file_exists_and_type, safe_delete_file, get_unique_filename
from voice_processing import apply_voice_effect

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint with API information."""
    return API_INFO


@router.post("/upload-audio/")
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
        file_path = get_unique_filename(file_path)

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


@router.get("/uploaded-files/")
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


@router.get("/files/{filename}")
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


@router.get("/voice-effects/")
async def get_voice_effects():
    """Get available voice effects and their descriptions."""
    return JSONResponse(
        status_code=200,
        content={
            "available_effects": AVAILABLE_EFFECTS,
            "effects_details": EFFECTS_INFO,
            "total_effects": len(AVAILABLE_EFFECTS)
        }
    )


@router.get("/download-file/{filename}")
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


@router.delete("/delete-file/{filename}")
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


@router.post("/process-audio/{filename}")
async def process_audio(filename: str, effect: str = Query(..., description="Voice effect to apply")):
    """
    Process an audio file with voice transformation.

    Args:
        filename: The name of the file to process
        effect: Type of voice transformation (male, female, robotic, baby, etc.)

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
        output_file_path = get_unique_filename(output_file_path)

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
            processed_audio = processed_audio / \
                np.max(np.abs(processed_audio)) * 0.95

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
