@echo off
REM Compatibility wrapper — runs the root setup menu
cd /d "%~dp0.."
call "%~dp0..\setup.bat" %*
