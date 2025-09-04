@echo off
title FastAPI & React Development Server
echo.
echo =======================================================
echo    Starting FastAPI Backend and React Frontend
echo =======================================================
echo.
echo Starting both servers with concurrently...
echo Backend will be available at: http://localhost:8000
echo Frontend will be available at: http://localhost:5173
echo.

call venv\Scripts\activate
start cmd /k "uvicorn main:app --reload"

cd frontend
start cmd /k "npm run dev"
