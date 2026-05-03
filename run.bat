@echo off
title JARVIS - Startup Sequence
echo.
echo  ============================
echo   J . A . R . V . I . S
echo   Starting systems...
echo  ============================
echo.

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [JARVIS] Starting Ollama...
    start "" ollama serve
    timeout /t 4 /nobreak >nul
)

REM Pull model if not present
echo [JARVIS] Verifying model...
ollama pull qwen2.5:7b

REM Install Python dependencies
echo [JARVIS] Checking dependencies...
pip install -r "%~dp0requirements.txt" -q

REM Start FastAPI backend
echo [JARVIS] Bringing neural core online...
start "JARVIS Backend" cmd /k "cd /d %~dp0 && uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 2 /nobreak >nul

REM Open frontend in default browser
echo [JARVIS] Launching interface...
start "" "%~dp0frontend\index.html"

echo.
echo  [ONLINE] Backend : http://localhost:8000
echo  [ONLINE] API Docs: http://localhost:8000/docs
echo  [ONLINE] Frontend: frontend\index.html
echo.
echo  JARVIS is ready, Sir.
pause
