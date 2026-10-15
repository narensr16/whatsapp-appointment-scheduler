@echo off
setlocal enabledelayedexpansion

echo ===============================================================================
echo   WhatsApp Appointment Scheduler - Environment Setup
echo ===============================================================================

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

:: 0. Check and supplement PATH if user programs are installed in AppData
if exist "%LOCALAPPDATA%\Programs\Python\Python311" (
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"
)
if exist "%LOCALAPPDATA%\Programs\NodeJS\PFiles64\nodejs" (
    set "PATH=%LOCALAPPDATA%\Programs\NodeJS\PFiles64\nodejs;%PATH%"
)
if exist "%LOCALAPPDATA%\Programs\Java\PFiles64\Eclipse Adoptium\jre-17.0.20.101-hotspot\bin" (
    set "PATH=%LOCALAPPDATA%\Programs\Java\PFiles64\Eclipse Adoptium\jre-17.0.20.101-hotspot\bin;%PATH%"
)

:: 1. Check Python installation
echo [1/7] Checking Python installation...
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python was not found in PATH.
    echo Please install Python 3.10 or higher and ensure Add to PATH is enabled.
    exit /b 1
)
python --version

:: 2. Check Node.js and npm installation
echo [2/7] Checking Node.js and npm installation...
where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js was not found in PATH.
    echo Please install Node.js LTS from https://nodejs.org.
    exit /b 1
)
where npm >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] npm was not found in PATH.
    exit /b 1
)
node --version
call npm --version

:: 3. Configure environment variables (.env)
echo [3/7] Setting up environment configuration (.env)...
if not exist ".env" (
    if exist ".env.example" (
        copy /Y ".env.example" ".env" >nul
        echo [INFO] Created .env from .env.example
    ) else (
        echo [WARNING] .env.example not found, skipping .env creation.
    )
) else (
    echo [INFO] Existing .env file found; preserving your configuration.
)

:: 4. Create Python Virtual Environment
echo [4/7] Setting up Python virtual environment (.venv)...
if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Creating new virtual environment in .venv...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
) else (
    echo [INFO] Existing .venv detected.
)

:: 5. Install backend dependencies
echo [5/7] Installing backend Python dependencies...
call ".venv\Scripts\pip.exe" install --upgrade pip >nul 2>nul
call ".venv\Scripts\pip.exe" install -r backend\requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install backend dependencies from backend\requirements.txt.
    exit /b 1
)
if exist "wa_sdk\setup.py" (
    echo [INFO] Installing local wa_sdk package in development mode...
    call ".venv\Scripts\pip.exe" install -e wa_sdk >nul 2>nul
)

:: 6. Apply Alembic database migrations and seed data
echo [6/7] Applying Alembic database migrations...
cd /d "%ROOT_DIR%backend"
call "..\.venv\Scripts\alembic.exe" upgrade head
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Alembic migration failed.
    cd /d "%ROOT_DIR%"
    exit /b 1
)

echo [INFO] Checking and loading seed data...
call "..\.venv\Scripts\python.exe" -c "import sqlite3, os; conn = sqlite3.connect('appointments.db'); conn.executescript(open('seed_data.sql').read()); conn.commit(); print('Sample doctors loaded successfully.')"
cd /d "%ROOT_DIR%"

:: 7. Install frontend dependencies
echo [7/7] Installing frontend npm packages...
cd /d "%ROOT_DIR%frontend"
call npm install
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install frontend npm packages.
    cd /d "%ROOT_DIR%"
    exit /b 1
)
cd /d "%ROOT_DIR%"

echo ===============================================================================
echo   [SUCCESS] Development environment setup is complete!
echo   To launch backend and frontend, run: runapplication.bat
echo ===============================================================================
exit /b 0
