from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import aiofiles

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

def validate_audio_file(file: UploadFile) -> bool:
    """Validate if the uploaded file is an audio file with allowed extension."""
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

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Audio File Upload API",
        "version": "1.0.0",
        "supported_formats": list(ALLOWED_EXTENSIONS),
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024)
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
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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
        raise HTTPException(status_code=500, detail=f"Error retrieving files: {str(e)}")

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
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@app.delete("/delete-file/{filename}")
async def delete_file(filename: str):
    """Delete an uploaded audio file."""
    try:
        # Validate file exists and is correct type
        file_path = validate_file_exists_and_type(filename)
        
        # Delete the file
        file_path.unlink()
        
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
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

@app.post("/process-audio/{filename}")
async def process_audio(filename: str, voice_type: str):
    """
    Process an audio file with voice transformation.
    
    Args:
        filename: The name of the file to process
        voice_type: Type of voice transformation (male, female, robot, alien, helium)
        
    Returns:
        JSON response with processing status and processed file information
    """
    try:
        # Validate voice type
        allowed_voice_types = ["male", "female", "robot", "alien", "helium"]
        if voice_type.lower() not in allowed_voice_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid voice type. Allowed types: {', '.join(allowed_voice_types)}"
            )
        
        # Validate file exists and is correct type
        input_file_path = validate_file_exists_and_type(filename)
        
        # Generate output filename
        name_part = input_file_path.stem
        extension = input_file_path.suffix
        output_filename = f"{name_part}_{voice_type.lower()}{extension}"
        output_file_path = UPLOAD_DIR / output_filename
        
        # Handle duplicate output filenames
        counter = 1
        original_output_path = output_file_path
        while output_file_path.exists():
            output_filename = f"{name_part}_{voice_type.lower()}_{counter}{extension}"
            output_file_path = UPLOAD_DIR / output_filename
            counter += 1
        
        # TODO: Implement actual voice processing logic here
        # For now, this is a placeholder that will be implemented later
        # The actual processing will involve audio manipulation libraries
        
        # Placeholder response - in real implementation, this would contain
        # the processed audio file information
        return JSONResponse(
            status_code=200,
            content={
                "message": f"Audio processing initiated for {voice_type} voice transformation",
                "input_filename": input_file_path.name,
                "output_filename": output_filename,
                "voice_type": voice_type.lower(),
                "status": "processing",
                "note": "Voice processing implementation pending"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")
