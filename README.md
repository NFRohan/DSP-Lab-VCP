# FastAPI Audio Upload & Voice Processing Backend

A modern FastAPI backend with a React frontend for uploading, managing, downloading, and processing audio files with voice effects.

## Features

- **File Operations**: Upload, download, list, and delete audio files (MP3/WAV).
- **Voice Processing**: Apply effects like robotic, male, female, and baby voices.
- **Modern Frontend**: A responsive React UI with a built-in audio player, progress bar, and dark mode.
- **Advanced Functionality**: Includes file validation, safe filename handling, and hot-reloading for development.

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop)
- [Git](https://git-scm.com/downloads) (optional)

### Installation with Docker (Recommended)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/NFRohan/DSP-Lab-VCP.git
    cd DSP-Lab-VCP
    ```

2.  **Build and run the application:**
    ```bash
    docker-compose up --build
    ```

Once the services are running, you can access:

-   **Frontend**: `http://localhost:5173`
-   **Backend**: `http://localhost:8000`
-   **API Docs**: `http://localhost:8000/docs`

## Manual Installation

If you prefer to run the application without Docker, follow these steps:

### Prerequisites

- [Python 3.8+](https://www.python.org/downloads/)
- [Node.js 16+](https://nodejs.org/)

### Backend Setup

1.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the backend server:**
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```

### Frontend Setup

1.  **Install Node.js dependencies:**
    ```bash
    cd frontend
    npm install
    ```

2.  **Run the frontend development server:**
    ```bash
    npm run dev:frontend
    ```

## API Endpoints

-   `GET /`: API information and available voice effects.
-   `POST /upload-audio/`: Upload an audio file.
-   `POST /process-audio/{filename}`: Apply a voice effect to an audio file.
-   `GET /files/{filename}`: Serve an audio file for playback.
-   `GET /download-file/{filename}`: Download an audio file.
-   `GET /uploaded-files/`: List all uploaded files.
-   `DELETE /delete-file/{filename}`: Delete an audio file.

For more details, see the [API documentation](http://localhost:8000/docs) after starting the application.
