# FastAPI Audio Upload & Voice Processing Backend

A modern FastAPI backend with React frontend for uploading, managing, downloading, and processing audio files with voice effects (MP3 or WAV).

## Features

- ✅ Upload single audio files (MP3/WAV)
- ✅ Download uploaded files  
- ✅ File validation (type and size)
- ✅ Safe filename handling
- ✅ List uploaded files
- ✅ Delete uploaded files with Windows lock handling
- ✅ **Voice Processing Effects**:
  - 🤖 **Robotic Voice** - Ring modulation with metallic distortion
  - 👨 **Male Voice** - Pitch shifting for masculine sound
  - 👩 **Female Voice** - Pitch shifting for feminine sound  
  - 👶 **Baby Voice** - High-pitched with time stretching
- ✅ **Modern React Frontend**:
  - 🎵 **Built-in Audio Player** - Play audio directly in browser
  - 📊 **Progress Bar & Controls** - Seek, volume, play/pause
  - 📁 **File Grouping** - Original files grouped with their voice effects
  - 🌙 **Dark Mode UI** - Professional dark theme
  - 📱 **Responsive Design** - Works on desktop and mobile
- ✅ **Advanced Features**:
  - 🔄 **Hot Reload** - Automatic updates during development
  - 🛡️ **Error Handling** - Graceful error management
  - 🔐 **Safe File Operations** - Prevents path traversal attacks
  - ⚡ **Fast Processing** - Optimized audio processing pipeline
- ✅ Automatic API documentation (Swagger/OpenAPI)
- ✅ File size limits (50MB max per file)
- ✅ Duplicate filename handling

## Prerequisites

Before running this project, ensure you have the following installed:

- **Python 3.8+** - [Download from python.org](https://www.python.org/downloads/)
- **Node.js 16+** and **npm** - [Download from nodejs.org](https://nodejs.org/)
- **Git** (optional) - For cloning the repository
- **Docker** - [Download from docker.com](https://www.docker.com/products/docker-desktop)

## Docker Setup (Recommended)

To build and run the application using Docker, run the following command in the root directory:

```bash
docker-compose up --build
```

This will build the Docker images for the frontend and backend and start the services.

## Manual Installation & Setup

### Quick Setup (Windows)
For a one-click setup on Windows, simply run:
```bash
install.bat
```
This will automatically create a virtual environment, install all dependencies, and set up the frontend.

### Manual Setup

### 1. Clone the Repository
```bash
git clone https://github.com/NFRohan/DSP-Lab-VCP.git
cd DSP-Lab-VCP
```

Or download and extract the ZIP file from GitHub.

### 2. Backend Setup (Python)

#### Install Python Dependencies
```bash
# Create a virtual environment (Recommended)
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

#### Alternative: Direct Installation
If you prefer not to use a virtual environment:
```bash
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 python-multipart==0.0.6 aiofiles==23.2.1 requests==2.31.0 librosa==0.10.1 "numpy>=1.24.3,<2.0" soundfile==0.12.1 "scipy>=1.11.1"
```

#### **Important Notes:**
- **Python Version**: Use Python 3.12 or compatible version (avoid 3.13+ due to librosa compatibility)
- **Audio Libraries**: The voice processing features require audio processing libraries (librosa, numpy, soundfile, scipy)
- **Installation Time**: Initial installation may take 5-10 minutes due to audio processing dependencies
- **Windows Users**: Ensure Visual Studio Build Tools are installed if you encounter compilation errors

### 3. Frontend Setup (React)

Navigate to the frontend directory and install dependencies:
```bash
cd frontend
npm install
```

#### **Frontend Dependencies Include:**
- **React 19+** - Modern React framework
- **Vite** - Fast build tool and development server
- **Concurrently** - Runs backend and frontend simultaneously
- **ESLint** - Code linting and formatting

#### **Development Features:**
- Hot Module Replacement (HMR) for instant updates
- Integrated backend/frontend development workflow
- Modern ES6+ JavaScript support
- Responsive design with CSS Grid/Flexbox

### 4. Verify Installation

Test the backend:
```bash
# From the root directory
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Test the frontend:
```bash
# From the frontend directory
npm run dev:frontend
```

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
- Returns API information, supported formats, and available voice effects

### 2. Upload Audio File
- **POST** `/upload-audio/`
- Accepts: `multipart/form-data` with file field
- Supported formats: MP3, WAV
- Max file size: 50MB

### 3. Process Audio File (NEW!)
- **POST** `/process-audio/{filename}?effect={effect_type}`
- Applies voice effects to uploaded audio files
- Available effects: `robotic`, `male`, `female`, `baby`
- Returns processed file information

### 4. Get Voice Effects (NEW!)
- **GET** `/voice-effects/`
- Returns list of available voice effects with descriptions

### 5. Serve Audio File (NEW!)
- **GET** `/files/{filename}`
- Serves audio files for in-browser playback
- Supports streaming for audio player controls
- Returns audio file with appropriate media type headers

### 6. Download File
- **GET** `/download-file/{filename}`
- Downloads a specific uploaded audio file

### 7. List Uploaded Files
- **GET** `/uploaded-files/`
- Returns list of all uploaded audio files

### 8. Delete File
- **DELETE** `/delete-file/{filename}`
- Deletes a specific uploaded file
- Includes retry mechanism for Windows file lock handling

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

**Voice Processing Examples:**

Get available voice effects:
```bash
curl -X GET "http://localhost:8000/voice-effects/"
```

Process audio with robotic voice effect:
```bash
curl -X POST "http://localhost:8000/process-audio/your_audio.mp3?effect=robotic"
```

Process audio with female voice effect:
```bash
curl -X POST "http://localhost:8000/process-audio/your_audio.mp3?effect=female"
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

# Process audio with voice effects
response = requests.post('http://localhost:8000/process-audio/audio.mp3?effect=robotic')
print(response.json())

# Get available voice effects
response = requests.get('http://localhost:8000/voice-effects/')
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

### Prerequisites for Development
Ensure you have completed the [Installation & Setup](#installation--setup) steps above.

### Backend Development
To run only the backend server with auto-reload:
```bash
# Make sure you're in the root directory and virtual environment is activated
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Development
To run only the frontend development server:
```bash
cd frontend
npm run dev:frontend
```

### Run Both Servers (Recommended for Full Development)
Use the provided batch file to run both servers concurrently:
```bash
# From the root directory
start.bat
```

Or manually using npm from the frontend directory:
```bash
cd frontend
npm run dev
```

### Project Structure
```
DSP-Lab-VCP/
├── main.py                 # FastAPI backend server
├── requirements.txt        # Python dependencies
├── start.bat              # Batch file to start both servers
├── test_api.py            # API test scripts
├── uploads/               # Directory for uploaded files (auto-created)
└── frontend/
    ├── package.json       # Node.js dependencies
    ├── src/
    │   ├── App.jsx       # Main React component
    │   └── ...
    └── public/
```

### Making Changes
- **Backend changes**: The server will auto-reload when you modify `main.py`
- **Frontend changes**: The development server will hot-reload when you modify files in `frontend/src/`

### Adding Dependencies
- **Python packages**: Add to `requirements.txt` and run `pip install -r requirements.txt`
- **Node.js packages**: Use `npm install <package-name>` in the `frontend/` directory

The servers will automatically:
- Enable auto-reload on code changes
- Run concurrently for full-stack development
- Create necessary directories

## Troubleshooting

### Common Issues

#### Python/pip not found
- Ensure Python is installed and added to your system PATH
- On Windows, use `py` instead of `python` if needed: `py -m pip install -r requirements.txt`

#### Node.js/npm not found
- Download and install Node.js from [nodejs.org](https://nodejs.org/)
- Restart your terminal after installation

#### Port already in use
- Backend (port 8000): Kill the process using the port or change the port in the command
- Frontend (port 5173): Vite will automatically use the next available port

#### Permission errors on Windows
- Run your terminal as Administrator
- Or use `python -m pip install --user -r requirements.txt` to install packages for the current user only

#### Virtual environment activation issues
- On Windows PowerShell, you might need to run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Then activate with: `venv\Scripts\Activate.ps1`

#### Backend server won't start
- Check if all dependencies are installed: `pip list`
- Ensure you're in the correct directory (where `main.py` is located)
- Check the console for error messages

#### Frontend won't start
- Delete `node_modules` and `package-lock.json`, then run `npm install` again

#### Audio playback issues
- Ensure the backend server is running on port 8000
- Check browser console (F12) for JavaScript errors
- Try refreshing the file list to reload audio elements
- Some audio formats may not be supported by your browser

#### File deletion problems ("file in use" errors)
- Audio files are automatically stopped before deletion
- If deletion fails, wait a few seconds and try again
- Close any other applications that might be using the audio file
- On Windows, the system may briefly lock files after playback

#### Voice processing takes too long
- Large audio files (>10MB) may take 30+ seconds to process
- Check the console output for progress messages
- Ensure sufficient RAM is available (processing uses memory)
- Try with smaller audio files first to test the system
- Check Node.js version: `node --version` (should be 16+)

### Getting Help
If you encounter issues not covered here:
1. Check the console/terminal output for specific error messages
2. Ensure all prerequisites are properly installed
3. Try running the backend and frontend separately to isolate issues