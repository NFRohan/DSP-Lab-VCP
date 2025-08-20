# FastAPI Audio Upload Backend

A modern FastAPI backend with React frontend for uploading, managing, and downloading audio files (MP3 or WAV).

## Features

- ✅ Upload single audio files (MP3/WAV)
- ✅ Download uploaded files
- ✅ File validation (type and size)
- ✅ Safe filename handling
- ✅ List uploaded files
- ✅ Delete uploaded files
- ✅ Modern React frontend
- ✅ Dark mode UI
- ✅ Automatic API documentation
- ✅ File size limits (50MB max per file)
- ✅ Duplicate filename handling

## Quick Start

### **Start the Application**
Run the batch file to start both backend and frontend:
```bash
start.bat
```

This will automatically:
- Start the FastAPI backend server on http://localhost:8000
- Start the React development server on http://localhost:5173
- Both servers run concurrently

## 🌐 **Access Points:**
- **React Frontend**: http://localhost:5173 (Main interface)
- **API Backend**: http://localhost:8000
- **Swagger Documentation**: http://localhost:8000/docs  
- **ReDoc Documentation**: http://localhost:8000/redoc

## API Endpoints

### 1. Root Endpoint
- **GET** `/`
- Returns API information and supported formats

### 2. Upload Audio File
- **POST** `/upload-audio/`
- Accepts: `multipart/form-data` with file field
- Supported formats: MP3, WAV
- Max file size: 50MB

### 3. Download File
- **GET** `/download-file/{filename}`
- Downloads a specific uploaded audio file

### 4. List Uploaded Files
- **GET** `/uploaded-files/`
- Returns list of all uploaded audio files

### 5. Delete File
- **DELETE** `/delete-file/{filename}`
- Deletes a specific uploaded file

## Usage Examples

### Using curl

Upload a file:
```bash
curl -X POST "http://localhost:8000/upload-audio/" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_audio.mp3"
```

Download a file:
```bash
curl -X GET "http://localhost:8000/download-file/your_audio.mp3" \
     --output "downloaded_audio.mp3"
```

List uploaded files:
```bash
curl -X GET "http://localhost:8000/uploaded-files/"
```

Delete a file:
```bash
curl -X DELETE "http://localhost:8000/delete-file/your_audio.mp3"
```

### Using Python requests

```python
import requests

# Upload a file
with open('audio.mp3', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/upload-audio/', files=files)
    print(response.json())

# List files
response = requests.get('http://localhost:8000/uploaded-files/')
print(response.json())
```

## API Documentation

Once the server is running, you can access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## File Storage

- Files are stored in the `uploads/` directory
- Duplicate filenames are automatically handled by adding a counter
- File paths are sanitized to prevent path traversal attacks

## Security Features

- File type validation (only MP3/WAV allowed)
- File size limits (50MB max)
- Safe filename handling
- Path traversal protection
- Input validation

## Configuration

You can modify the following settings in `main.py`:
- `MAX_FILE_SIZE`: Maximum file size (default: 50MB)
- `ALLOWED_EXTENSIONS`: Allowed file extensions
- `UPLOAD_DIR`: Upload directory path

## Development

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Backend Development
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Run Both (Recommended)
```bash
start.bat
```

The servers will automatically:
- Enable auto-reload on code changes
- Run concurrently for full-stack development
- Create necessary directories