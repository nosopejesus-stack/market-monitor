@echo off
REM Abre Mi IA en el navegador (doble clic).
cd /d "%~dp0"
start "" http://localhost:8765
python mi_ia.py web
pause
