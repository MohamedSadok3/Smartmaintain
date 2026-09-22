@echo off
cls
echo ============================================
echo   SmartMaintain - Quick Start
echo ============================================
echo.

cd /d "%~dp0"

echo [1] Checking Docker...
docker ps >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop is not running!
    echo.
    echo Please start Docker Desktop manually and run this script again.
    echo.
    pause
    exit /b 1
)
echo [OK] Docker is running
echo.

echo [2] Starting SmartMaintain services...
echo This may take a few minutes on first run...
echo.
docker-compose up -d

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start services
    echo Check logs with: docker-compose logs
    pause
    exit /b 1
)

echo.
echo ============================================
echo   SmartMaintain Started Successfully!
echo ============================================
echo.
echo Frontend:    http://localhost:3000
echo API Gateway: http://localhost:5000
echo.
echo Default Login:
echo   Email:    superadmin@smartmaintain.local
echo   Password: superadmin123
echo.
echo Model Version: Latest (Simplified Inputs)
echo.
echo View logs: docker-compose logs -f
echo Stop:      docker-compose stop
echo.

timeout /t 3 >nul
start http://localhost:3000

echo Opening browser...
echo.
pause
