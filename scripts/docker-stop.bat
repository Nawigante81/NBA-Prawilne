@echo off
setlocal
echo ================================================
echo NBA Analytics - Docker Stop
echo ================================================
echo.

echo Checking Docker Compose...

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo Docker Compose is not available.
        echo Install Docker Desktop and try again.
        pause
        exit /b 1
    ) else (
        set "COMPOSE_CMD=docker compose"
    )
) else (
    set "COMPOSE_CMD=docker-compose"
)

echo.
echo Stopping Docker containers...
echo.

%COMPOSE_CMD% down

if %errorlevel% equ 0 (
    echo All containers stopped.
) else (
    echo Error while stopping containers.
)

echo.
echo Container status:
%COMPOSE_CMD% ps
echo.
echo Data in Redis and logs is preserved.
echo.
echo Start again with: docker-start.bat
echo Or manually: %COMPOSE_CMD% up -d
echo.
pause
