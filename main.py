import traceback
import logging
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
import librosa
import numpy as np
import soundfile as sf

# Import your audio transformation functions
from functions import robotic_voice, male_voice, female_voice, baby_voice, detect_gender

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI
app = FastAPI(title="Audio File Upload & Processing API", version="1.0.0")

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Restrict to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory for uploaded and processed files
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed formats
ALLOWED_EXTENSIONS = {".mp3", ".wav"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


# ----------------- Helpers -----------------
def validate_audio_file(file: UploadFile) -> bool:
    """Check if file extension is allowed."""
    return Path(file.filename).suffix.lower() in ALLOWED_EXTENSIONS


def get_safe_filename(filename: str) -> str:
    """Prevent path traversal."""
    return Path(filename).name


def validate_file_exists_and_type(filename: str) -> Path:
    """Ensure file exists and is valid audio."""
    safe_filename = get_safe_filename(filename)
    file_path = UPLOAD_DIR / safe_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Invalid file")
    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not allowed")
    return file_path


# ----------------- Routes -----------------
@app.get("/")
async def root():
    return {
        "message": "Audio File Upload & Processing API",
        "version": "1.0.0",
        "supported_formats": list(ALLOWED_EXTENSIONS),
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
    }


@app.post("/upload-audio")
async def upload_audio_file(file: UploadFile = File(...)):
    """Upload and save audio file."""
    try:
        if not validate_audio_file(file):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        # Check size
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)
        if size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large (max 50MB)")

        # Safe name (avoid overwrite)
        safe_name = get_safe_filename(file.filename)
        file_path = UPLOAD_DIR / safe_name
        counter = 1
        while file_path.exists():
            file_path = UPLOAD_DIR / f"{Path(safe_name).stem}_{counter}{Path(safe_name).suffix}"
            counter += 1

        # Save file
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(await file.read())

        return {
            "message": "File uploaded successfully",
            "filename": file_path.name,
            "file_size_bytes": size,
            "file_path": str(file_path),
            "content_type": file.content_type,
        }

    except HTTPException as he:
        # Re-raise intended client/server HTTP errors without masking them
        raise he
    except Exception as e:
        logging.error(f"Upload error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Upload error")


@app.get("/uploaded-files")
async def list_uploaded_files():
    """List uploaded files."""
    try:
        files = []
        for p in UPLOAD_DIR.iterdir():
            if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS:
                stat = p.stat()
                files.append(
                    {
                        "filename": p.name,
                        "size_bytes": stat.st_size,
                        "created_at": stat.st_ctime,
                        "file_path": str(p),
                    }
                )
        return {"files": files, "total_count": len(files)}
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"List error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="List error")


@app.get("/download-file/{filename}")
async def download_file(filename: str):
    """Download a file."""
    try:
        file_path = validate_file_exists_and_type(filename)
        media_type = "audio/mpeg" if file_path.suffix.lower() == ".mp3" else "audio/wav"
        return FileResponse(str(file_path), filename=file_path.name, media_type=media_type)
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Download error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Download error")


@app.delete("/delete-file/{filename}")
async def delete_file(filename: str):
    """Delete a file."""
    try:
        file_path = validate_file_exists_and_type(filename)
        file_path.unlink()
        return {"message": "File deleted", "filename": file_path.name}
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Delete error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Delete error")


async def transform_audio_handler(effect: str, file: UploadFile):
    """Apply transformation effect: robotic, male, female, baby."""
    logging.info(f"Transform request for effect: {effect}")
    
    if not validate_audio_file(file):
        raise HTTPException(status_code=400, detail="Invalid file type.")

    # Validate effect
    valid_effects = ["robotic", "male", "female", "baby"]
    if effect not in valid_effects:
        raise HTTPException(status_code=400, detail=f"Invalid effect. Must be one of: {valid_effects}")

    try:
        # Save temp file using a safe filename
        safe_name = get_safe_filename(file.filename)
        tmp = UPLOAD_DIR / f"temp_{safe_name}"
        async with aiofiles.open(tmp, "wb") as f:
            await f.write(await file.read())

        # Load audio as mono to simplify processing and avoid shape issues
        try:
            y, sr = librosa.load(str(tmp), sr=None, mono=True)
            logging.info(f"Loaded audio: shape={y.shape}, sr={sr}")
        except Exception as load_err:
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass
            logging.error(f"Decode error with librosa: {load_err}\n{traceback.format_exc()}")
            raise HTTPException(
                status_code=415,
                detail="Unsupported or corrupt audio file. For MP3 support, install FFmpeg and ensure it's on PATH."
            )
        finally:
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                # Ignore Windows file-lock races
                pass

        # Replace NaN/Inf values if any and ensure 1-D float32 array
        y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32, copy=False)
        if y.ndim != 1:
            y = np.ascontiguousarray(y.reshape(-1))
        
        # Handle empty or extremely short audio by returning as-is
        if y.size < 16:
            logging.warning("Input audio too short for processing; returning original.")
            processed = y
            effect = "original"
            headers = {"X-Processing-Note": "Input too short; returned original"}
        else:
            # Apply effect
            headers = {}
            try:
                logging.info(f"Applying effect: {effect}")
                if effect == "robotic":
                    processed = robotic_voice(y, sr)
                elif effect == "male":
                    processed = male_voice(y, sr)
                elif effect == "female":
                    processed = female_voice(y, sr)
                elif effect == "baby":
                    processed = baby_voice(y, sr)
                
                logging.info(f"Effect applied successfully. Output shape: {processed.shape}")
                
            except Exception as fx_err:
                logging.error(f"Effect '{effect}' failed, falling back to original: {fx_err}\n{traceback.format_exc()}")
                processed = y
                headers["X-Processing-Note"] = f"Effect '{effect}' failed: {fx_err}"

        # Ensure processed signal is finite and within [-1, 1]
        processed = np.nan_to_num(processed, nan=0.0, posinf=0.0, neginf=0.0)
        max_abs = np.max(np.abs(processed)) if processed.size > 0 else 0.0
        if max_abs > 1.0:
            processed = processed / max_abs

        # Save processed file as WAV regardless of input type to ensure compatibility
        original_stem = Path(get_safe_filename(file.filename)).stem
        out = UPLOAD_DIR / f"processed_{effect}_{original_stem}.wav"
        
        try:
            sf.write(str(out), processed, sr)
            logging.info(f"Written processed audio to: {out}")
        except Exception as write_err:
            logging.error(f"Write error: {write_err}\n{traceback.format_exc()}")
            # Fall back to sending original data if writing processed fails
            out = UPLOAD_DIR / f"processed_original_{original_stem}.wav"
            try:
                sf.write(str(out), y, sr)
            except Exception as write_err2:
                logging.error(f"Fallback write error: {write_err2}\n{traceback.format_exc()}")
                raise HTTPException(status_code=500, detail=f"Write error: {write_err2}")
            headers = headers or {}
            headers["X-Processing-Note"] = headers.get("X-Processing-Note", "") + "; write failed, returned original"

        return FileResponse(str(out), media_type="audio/wav", filename=out.name, headers=headers)

    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Processing error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


# Register both routes with and without trailing slash
@app.post("/transform/{effect}")
async def transform_audio(effect: str, file: UploadFile = File(...)):
    """Apply transformation effect without trailing slash."""
    return await transform_audio_handler(effect, file)


@app.post("/transform/{effect}/")
async def transform_audio_with_slash(effect: str, file: UploadFile = File(...)):
    """Apply transformation effect with trailing slash."""
    return await transform_audio_handler(effect, file)


@app.get("/uploaded-files/{filename}")
@app.get("/uploaded-files/{filename}/")
async def get_uploaded_file(filename: str):
    """Serve uploaded (original or processed) file."""
    try:
        file_path = UPLOAD_DIR / get_safe_filename(filename)
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found.")
        media_type = "audio/mpeg" if file_path.suffix.lower() == ".mp3" else "audio/wav"
        return FileResponse(str(file_path), media_type=media_type, filename=file_path.name)
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Get file error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Get file error")