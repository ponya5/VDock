@echo off
REM Start VDock Backend

echo Starting VDock Backend...
cd backend
call ..\.venv\Scripts\activate.bat
python app.py
pause

