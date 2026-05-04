@echo off
echo ============================================
echo   UMAMI Premium Sushi - Ishga Tushirish
echo ============================================
echo.

cd /d "%~dp0"

echo [1/5] Django server ishga tushmoqda...
cd resturant
start "UMAMI Server" cmd /k python manage.py runserver 0.0.0.0:8000
timeout /t 3 /nobreak >nul

echo [2/5] ngrok tunnel ishga tushmoqda...
cd ..
start "UMAMI ngrok" cmd /k ngrok.exe http 8000
timeout /t 5 /nobreak >nul

echo [3/5] Foydalanuvchi bot (@amina_suhsi_order_bot) ishga tushmoqda...
cd resturant
start "UMAMI User Bot" cmd /k python bot.py
timeout /t 2 /nobreak >nul

echo [4/5] Kassir Chat Bot ishga tushmoqda...
start "UMAMI Kassir Chat" cmd /k python bot_cashier.py
timeout /t 2 /nobreak >nul

echo [5/5] Staff bot (@umami_staff_bot) ishga tushmoqqda...
start "UMAMI Staff Bot" cmd /k python bot_staff.py

echo.
echo ============================================
echo   HAMMASI ISHGA TUSHDI!
echo ============================================
echo.
echo   Sayt: http://localhost:8000
echo   ngrok: https://nicotine-unsealed-debit.ngrok-free.dev
echo   Admin: http://localhost:8000/admin (admin/admin123)
echo   User Bot: @amina_suhsi_order_bot
echo   Kassir Chat: @chat_amina_bot
echo   Staff Bot: @umami_staff_bot
echo.
echo   Oynalarni yopmang!
echo ============================================
pause
