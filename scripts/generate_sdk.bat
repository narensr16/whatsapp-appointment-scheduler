@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   Generating Python SDK using OpenAPI Generator CLI
echo ============================================================

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."
cd /d "%ROOT_DIR%"

:: Check if user AppData programs are in PATH, if not add them
if exist "%LOCALAPPDATA%\Programs\Python\Python311" (
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"
)
if exist "%LOCALAPPDATA%\Programs\NodeJS\PFiles64\nodejs" (
    set "PATH=%LOCALAPPDATA%\Programs\NodeJS\PFiles64\nodejs;%PATH%"
)
if exist "%LOCALAPPDATA%\Programs\Java\PFiles64\Eclipse Adoptium\jre-17.0.20.101-hotspot\bin" (
    set "PATH=%LOCALAPPDATA%\Programs\Java\PFiles64\Eclipse Adoptium\jre-17.0.20.101-hotspot\bin;%PATH%"
)

:: Verify Node / npx
where npx >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] npx is not installed or not in PATH. Please install Node.js.
    exit /b 1
)

:: Verify Java
where java >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Java is not installed or not in PATH. OpenAPI Generator requires Java 11+.
    exit /b 1
)

:: Check if openapi.json exists, if not generate it from FastAPI app
if not exist "openapi.json" (
    echo [INFO] Exporting OpenAPI specification from FastAPI application...
    if exist ".venv\Scripts\python.exe" (
        .venv\Scripts\python.exe -c "import json, sys; sys.path.insert(0, 'backend'); from app.main import app; open('openapi.json', 'w').write(json.dumps(app.openapi(), indent=2))"
    ) else (
        python -c "import json, sys; sys.path.insert(0, 'backend'); from app.main import app; open('openapi.json', 'w').write(json.dumps(app.openapi(), indent=2))"
    )
)

echo [INFO] Running OpenAPI Generator CLI for Python...
call npx -y @openapitools/openapi-generator-cli generate -i openapi.json -g python -o wa_sdk --additional-properties=packageName=wa_sdk

if %ERRORLEVEL% neq 0 (
    echo [ERROR] OpenAPI SDK generation failed.
    exit /b 1
)

echo [INFO] Installing generated SDK locally in virtual environment...
if exist ".venv\Scripts\pip.exe" (
    .venv\Scripts\pip.exe install -e wa_sdk
) else (
    pip install -e wa_sdk
)

echo [SUCCESS] Python SDK successfully generated and installed in wa_sdk/
exit /b 0
