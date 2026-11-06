@echo off
REM Abre Brainus en el navegador (doble clic).
cd /d "%~dp0"
start "" http://localhost:8765
python brainus.py web
pause
