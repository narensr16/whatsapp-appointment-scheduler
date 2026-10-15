@echo off
setlocal enabledelayedexpansion

echo ===============================================================================
echo   WhatsApp Appointment Scheduling System - Application Launcher
echo ===============================================================================

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

:: Check and supplement PATH if user programs are installed in AppData
if exist "%LOCALAPPDATA%\Programs\Python\Python311" (
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"
)
if exist "%LOCALAPPDATA%\Programs\NodeJS\PFiles64\nodejs" (
    set "PATH=%LOCALAPPDATA%\Programs\NodeJS\PFiles64\nodejs;%PATH%"
)

:: 1. Verify environment setup
if not exist ".venv\Scripts\uvicorn.exe" (
    echo [ERROR] Backend virtual environment not found or uvicorn is missing.
    echo Please run setupdev.bat first to configure dependencies.
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo [ERROR] Frontend node_modules not found.
    echo Please run setupdev.bat first to install frontend dependencies.
    pause
    exit /b 1
)

:: 2. Check for port conflicts (8000 and 5173)
netstat -ano | findstr ":8000 " >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [WARNING] Port 8000 appears to be already in use.
    echo If a previous backend instance is running, please close it or terminate its process.
)

netstat -ano | findstr ":5173 " >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [WARNING] Port 5173 appears to be already in use.
    echo Vite will automatically attempt the next available port if 5173 is busy.
)

echo.
echo [1/2] Starting FastAPI Backend on http://localhost:8000 ...
start "WhatsApp Scheduler - Backend (FastAPI)" cmd /k "cd /d "%ROOT_DIR%backend" && call "..\.venv\Scripts\activate.bat" && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Starting React Frontend on http://localhost:5173 ...
start "WhatsApp Scheduler - Frontend (React/Vite)" cmd /k "cd /d "%ROOT_DIR%frontend" && npm run dev"

echo.
echo ===============================================================================
echo   Applications are now launching in dedicated terminal windows!
echo.
echo   - React Frontend:        http://localhost:5173
echo   - FastAPI Backend:       http://localhost:8000
echo   - Swagger API Docs:      http://localhost:8000/docs
echo   - OpenAPI Specification: http://localhost:8000/openapi.json
echo   - Health Check Endpoint: http://localhost:8000/health
echo.
echo   Close the respective terminal windows to terminate the servers.
echo ===============================================================================

exit /b 0
