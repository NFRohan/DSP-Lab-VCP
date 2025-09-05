@echo off
echo Installing DSP Lab Voice Processing Backend
echo ========================================

echo.
echo Setting up Python virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Error: Failed to create virtual environment
    echo Please make sure Python is installed and in your PATH
    pause
    exit /b 1
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate

echo.
echo Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install Python dependencies
    pause
    exit /b 1
)

echo.
echo Setting up frontend...
cd frontend
npm install
if %errorlevel% neq 0 (
    echo Error: Failed to install Node.js dependencies
    echo Please make sure Node.js and npm are installed
    pause
    exit /b 1
)

cd ..

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo To start the application:
echo   1. Run: start.bat
echo   2. Open: http://localhost:5173
echo.
echo API Documentation will be available at:
echo   - Swagger UI: http://localhost:8000/docs
echo   - ReDoc: http://localhost:8000/redoc
echo.
pause
