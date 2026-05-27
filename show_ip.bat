@echo off
chcp 65001 >nul
echo ========================================
echo   Your LAN IP Address
echo ========================================
echo.
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set "ip=%%a"
    setlocal enabledelayedexpansion
    echo   http://!ip: =!:8501
    endlocal
)
echo.
echo Share this URL with colleagues on the same network.
echo ========================================
pause
