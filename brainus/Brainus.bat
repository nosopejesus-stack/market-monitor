@echo off
REM Abre Brainus en el navegador (doble clic).
cd /d "%~dp0"
tasklist /FI "IMAGENAME eq ollama.exe" | find /I "ollama.exe" >nul || start "" /min ollama serve
start "" http://localhost:8765
python brainus.py web
pause
