@echo off
REM =================================================================
REM NBA Analytics - Upload to Self-Hosted Server
REM =================================================================
REM Skrypt do przesłania projektu na własny serwer przez SCP
REM =================================================================

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║     🚀 NBA Analytics - Upload to Self-Hosted Server      ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Sprawdź czy jesteśmy w katalogu projektu
if not exist "docker-compose.prod.yml" (
    echo ❌ Błąd: Nie znaleziono pliku docker-compose.prod.yml
    echo    Upewnij się, że jesteś w katalogu projektu!
    pause
    exit /b 1
)

echo Skrypt pomaga przesłać projekt na Twój serwer.
echo.
echo UWAGA: Potrzebujesz:
echo   1. Zainstalowany OpenSSH Client w Windows
echo   2. IP serwera
echo   3. Użytkownik i hasło SSH
echo.

REM Zapytaj o dane serwera
set /p SERVER_IP="Podaj IP serwera (np. 192.168.1.100): "
set /p SERVER_USER="Podaj użytkownika SSH (np. ubuntu): "

echo.
echo Przesyłanie plików na %SERVER_USER%@%SERVER_IP%...
echo To może potrwać kilka minut...
echo.

REM Użyj SCP do przesłania plików
REM Wyklucz zbędne katalogi
scp -r ^
    -o "StrictHostKeyChecking=no" ^
    --exclude="node_modules" ^
    --exclude=".git" ^
    --exclude="dist" ^
    --exclude="build" ^
    --exclude="__pycache__" ^
    --exclude=".venv" ^
    --exclude="venv" ^
    * %SERVER_USER%@%SERVER_IP%:~/nba-analytics/

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Upload zakończony!
    echo.
    echo ════════════════════════════════════════════════════════════
    echo NASTĘPNE KROKI NA SERWERZE:
    echo ════════════════════════════════════════════════════════════
    echo 1. Zaloguj się do serwera:
    echo    ssh %SERVER_USER%@%SERVER_IP%
    echo.
    echo 2. Przejdź do katalogu:
    echo    cd ~/nba-analytics
    echo.
    echo 3. Uruchom aplikację:
    echo    docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
    echo.
    echo 4. Sprawdź status:
    echo    docker compose -f docker-compose.prod.yml ps
    echo.
    echo 📚 Zobacz: SELF_HOSTING_GUIDE.md
    echo ════════════════════════════════════════════════════════════
) else (
    echo.
    echo ❌ Błąd podczas uploadu!
    echo.
    echo Możliwe przyczyny:
    echo   - OpenSSH Client nie jest zainstalowany
    echo   - Nieprawidłowy IP lub użytkownik
    echo   - Serwer nie jest dostępny
    echo   - Firewall blokuje port 22
    echo.
    echo ALTERNATYWA: Użyj WinSCP lub FileZilla
    echo   1. Pobierz WinSCP: https://winscp.net/
    echo   2. Host: %SERVER_IP%
    echo   3. Port: 22
    echo   4. Upload wszystkie pliki
)

echo.
pause
