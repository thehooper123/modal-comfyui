@echo off
REM FitSweetTreat Video Automation - Startup Script (Windows)
REM Starts all required services for the video automation pipeline

setlocal enabledelayedexpansion

set PROJECT_DIR=%~dp0
echo 📦 Starting FitSweetTreat Video Automation Pipeline
echo 🏗️  Project Directory: %PROJECT_DIR%

REM Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Install Python 3.9+
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python %PYTHON_VERSION% found

REM Setup venv
echo [2/5] Setting up virtual environment...
if not exist "%PROJECT_DIR%.venv" (
    python -m venv .venv
)
call "%PROJECT_DIR%.venv\Scripts\activate.bat"
python -m pip install --upgrade pip -q
echo ✓ Virtual environment ready

REM Install dependencies
echo [3/5] Installing dependencies...
pip install -q -r "%PROJECT_DIR%requirements.txt"
if errorlevel 1 (
    echo ⚠️  Some packages may require manual installation
)
echo ✓ Dependencies installed

REM Check .env file
if not exist "%PROJECT_DIR%.env" (
    echo ⚠️  .env file not found!
    echo Creating from .env.example...
    copy "%PROJECT_DIR%.env.example" "%PROJECT_DIR%.env"
    echo 📝 Please edit .env with your credentials
    echo.
)

echo [4/5] Checking required services...
echo.
echo Required Services:
echo   • n8n: http://localhost:5678 (not auto-started)
echo   • KokoroTTS: http://localhost:8000 (not auto-started)
echo   • Gemini API: Requires .env credentials
echo.

echo [5/5] Starting services...
echo.

REM Start callback server in new window
echo ➤ Starting Callback Server (port 5000)
start "Callback Server" python "%PROJECT_DIR%callback_server.py"
timeout /t 2 /nobreak

REM Start main app
echo ➤ Starting FitSweetTreat App
start "FitSweetTreat App" python "%PROJECT_DIR%app.py"

echo.
echo ═══════════════════════════════════════════════════════════════
echo ✅ FitSweetTreat Video Automation Pipeline Ready!
echo ═══════════════════════════════════════════════════════════════
echo.
echo 📋 Services Running:
echo   • Callback Server: http://localhost:5000 (in separate window)
echo   • Main App UI: (in separate window)
echo.
echo ⚠️  Make sure these services are also running:
echo   1. n8n: http://localhost:5678
echo   2. KokoroTTS: http://localhost:8000
echo.
echo 📁 Key Files:
echo   • app.py - Main application
echo   • callback_server.py - Video delivery server
echo   • n8n_workflow_with_callback.json - n8n workflow
echo   • SETUP_GUIDE.md - Complete documentation
echo   • .env - Your API credentials (EDIT THIS!)
echo.
echo 🎬 Next Steps:
echo   1. Edit .env with your API keys
echo   2. Ensure n8n is running: http://localhost:5678
echo   3. Ensure KokoroTTS is running: http://localhost:8000
echo   4. Import n8n_workflow_with_callback.json into n8n
echo   5. Test with a recipe prompt in the App!
echo.
echo Close this window to continue...
pause
