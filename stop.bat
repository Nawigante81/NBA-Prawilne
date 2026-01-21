@echo off
echo ================================================
echo NBA Analysis System - Stop
echo ================================================
echo.
echo Stopping application...
echo.

echo Closing backend...
taskkill /FI "WINDOWTITLE eq NBA Backend (FastAPI)" /T /F >nul 2>&1
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique"`) do (
    taskkill /pid %%I /f >nul 2>&1
)

echo Closing frontend...
taskkill /FI "WINDOWTITLE eq NBA Frontend (React)" /T /F >nul 2>&1
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique"`) do (
    taskkill /pid %%I /f >nul 2>&1
)

echo.
echo Application stopped.
echo.
pause
