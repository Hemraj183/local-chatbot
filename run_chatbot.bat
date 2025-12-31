@echo off
TITLE Local Chatbot Launcher

:: 1. Get Local IP Address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr "IPv4 Address"') do set IP=%%a
set IP=%IP:~1%

ECHO =====================================================
ECHO   🚀 STARTING LOCAL AI SYSTEM
ECHO =====================================================
ECHO.
ECHO   [INFO] To access from your phone, connect to same WiFi and open:
ECHO   http://%IP%:8501
ECHO.
ECHO =====================================================

:: 2. Start LM Studio Server
ECHO [1/3] Starting LM Studio Server...
start /MIN cmd /c "lms server start --bind 0.0.0.0 --cors true"

:: Wait for server to initialize
timeout /t 5 /nobreak >nul

:: 3. Auto-Load Default Model (Qwen 4B)
:: This ensures the AI is ready immediately.
ECHO [2/3] Auto-Loading AI Model...
call lms load qwen/qwen3-4b-thinking-2507

:: 4. Start the Chatbot App
ECHO [3/3] Starting Chatbot Interface...
cd /d "%~dp0"
streamlit run app.py --server.address 0.0.0.0

pause
