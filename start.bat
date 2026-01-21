@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul 2>&1
pushd "%~dp0"

set "RERUN_FLAG=--stay"
if /i "%~1" neq "%RERUN_FLAG%" (
    cmd /k ""%~f0" %RERUN_FLAG%"
    exit /b 0
)

echo ================================================
echo NBA Analysis System - Quick Start
echo ================================================
echo.

echo Checking project readiness...
echo.

REM Check if we are in the right directory
if not exist "package.json" (
    echo ERROR: Not in project root.
    echo.
    echo Make sure you are in the folder with package.json
    echo.
    pause
    exit /b 1
)

REM Check Windows version (warn if not Windows 10)
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
if not "%VERSION%"=="10.0" (
    echo WARNING: Detected Windows %VERSION%. Script is tested on Windows 10.
    echo.
)

call :check_prereqs
if errorlevel 1 goto :end

REM Check if setup was run
set "VENV_DIR=venv"
if exist "backend\.venv" set "VENV_DIR=.venv"
set "AUTO_SETUP_DONE=0"

call :check_deps
if %errorlevel% equ 0 goto :continue_start

if "%AUTO_SETUP_DONE%"=="1" (
    echo ERROR: Dependencies still missing after setup.
    echo Fix issues above and rerun start.bat.
    echo.
    pause
    exit /b 1
)

echo Missing dependencies. Running setup.bat...
echo.
call setup.bat
if %errorlevel% neq 0 (
    echo ERROR: setup.bat failed. Fix the errors and rerun start.bat.
    echo.
    pause
    exit /b 1
)
set "AUTO_SETUP_DONE=1"
call :check_deps
if errorlevel 1 (
    echo ERROR: Dependencies still missing after setup.
    echo Fix issues above and rerun start.bat.
    echo.
    pause
    exit /b 1
)

:continue_start

REM Check if .env has required keys
findstr /C:"your_supabase_url_here" .env >nul 2>&1
if %errorlevel% equ 0 (
    echo WARNING: .env contains example values.
    echo.
    echo Fill real API keys:
    echo    - VITE_SUPABASE_URL
    echo    - VITE_SUPABASE_ANON_KEY
    echo    - VITE_ODDS_API_KEY
    echo.
    echo See QUICKSTART_WINDOWS.md - section "Wymagane klucze API"
    echo.
    choice /C YN /M "Continue anyway?"
    if errorlevel 2 exit /b 0
    echo.
)

REM Check if backend .env has required keys
if exist "backend\.env" (
    findstr /C:"your_supabase_url_here" backend\.env >nul 2>&1
    if %errorlevel% equ 0 (
        echo WARNING: backend\.env contains example values.
        echo.
        choice /C YN /M "Continue anyway?"
        if errorlevel 2 exit /b 0
        echo.
    )
)

REM Check if backend main.py exists
if not exist "backend\main.py" (
    echo ERROR: Missing backend\main.py
    echo.
    echo Check project structure.
    echo.
    pause
    exit /b 1
)

REM Ensure ports are free (prompt before killing any process)

echo Checking ports 8000 and 5173...

for %%P in (8000 5173) do (

    for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort %%P -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique"`) do (

        echo Port %%P is in use by PID %%I

        choice /C YN /M "Kill this process now?"

        if errorlevel 2 exit /b 1

        taskkill /pid %%I /f >nul 2>&1

    )

)

echo Port check complete.


echo All checks passed. Starting application...
echo.
echo Two terminals will open:
echo    1) Backend (Python/FastAPI) - port 8000
echo    2) Frontend (React/Vite) - port 5173
echo.
echo IMPORTANT: Keep these windows open while using the app.
echo.
echo App URLs:
echo    Frontend: http://localhost:5173
echo    API: http://localhost:8000/docs
echo.
pause

REM Start backend in new window
echo Starting backend...
start "NBA Backend (FastAPI)" cmd /k "echo Starting backend NBA Analytics... && cd backend && %VENV_DIR%\Scripts\activate && echo venv active && python -m uvicorn main:app --host 0.0.0.0 --port 8000"

echo Waiting 4 seconds for backend to start...
timeout /t 4 /nobreak >nul

echo Starting frontend...
start "NBA Frontend (React)" cmd /k "echo Starting frontend NBA Analytics... && npm run dev"

echo.
echo APP STARTED SUCCESSFULLY.
echo.
echo ACCESS:
echo    Frontend:  http://localhost:5173
echo    API:       http://localhost:8000
echo    API Docs:  http://localhost:8000/docs
echo    Health:    http://localhost:8000/health
echo.
echo STOP:
echo    - Close both terminal windows (Backend and Frontend)
echo    - Or run: stop.bat
echo.
echo Opening browser...
timeout /t 2 /nobreak >nul
start http://localhost:5173
echo.
echo Done.
pause >nul
exit /b 0

:check_prereqs
REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed.
    echo.
    echo Install Node.js LTS from: https://nodejs.org/
    echo.
    exit /b 1
)

REM Check if npm is available
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: npm is not available.
    echo.
    echo Reinstall Node.js from: https://nodejs.org/
    echo.
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo.
    echo Install Python 3.11+ from: https://www.python.org/downloads/
    echo.
    exit /b 1
)

REM Check if pip is available
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pip is not available.
    echo.
    echo Reinstall Python with pip option enabled.
    echo.
    exit /b 1
)

exit /b 0

:check_deps
set "MISSING_DEPS=0"

if not exist "backend\%VENV_DIR%" (
    echo Missing Python virtual environment: backend\%VENV_DIR%
    set "MISSING_DEPS=1"
)

if not exist "backend\%VENV_DIR%\Scripts\activate.bat" (
    echo Missing venv activation: backend\%VENV_DIR%\Scripts\activate.bat
    set "MISSING_DEPS=1"
)

if not exist "node_modules" (
    echo Missing frontend dependencies: node_modules
    set "MISSING_DEPS=1"
)

if not exist "backend\requirements.txt" (
    echo Missing backend requirements: backend\requirements.txt
    set "MISSING_DEPS=1"
)

if not exist ".env" (
    echo Missing config: .env
    set "MISSING_DEPS=1"
)

if not exist "backend\.env" (
    echo Missing config: backend\.env
    set "MISSING_DEPS=1"
)

if "%MISSING_DEPS%"=="1" exit /b 1

exit /b 0

:end
pause
exit /b 1
