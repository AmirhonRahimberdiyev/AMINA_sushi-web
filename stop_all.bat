@echo off
echo ============================================
echo   UMAMI - Barcha terminalarni to'xtatish
echo ============================================
echo.

echo [1/5] Django server to'xtatilmoqda...
taskkill /F /FI "WINDOWTITLE eq UMAMI Server*" 2>nul

echo [2/5] ngrok to'xtatilmoqda...
taskkill /F /FI "WINDOWTITLE eq UMAMI ngrok*" 2>nul

echo [3/5] User Bot to'xtatilmoqda...
taskkill /F /FI "WINDOWTITLE eq UMAMI User Bot*" 2>nul

echo [4/5] Kassir Bot to'xtatilmoqda...
taskkill /F /FI "WINDOWTITLE eq UMAMI Kassir*" 2>nul

echo [5/5] Staff Bot to'xtatilmoqda...
taskkill /F /FI "WINDOWTITLE eq UMAMI Staff*" 2>nul

echo.
echo ✅ Barcha terminalar to'xtatildi!
echo ============================================
timeout /t 2 /nobreak >nul