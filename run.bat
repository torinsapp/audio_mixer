@echo off
:: Check if a path argument is provided
if "%~1"=="" (
    echo Usage: %~nx0 ^<path_to_project^>
    exit /b 1
)

cd /d "%~1"

:: Check if the script is already running
tasklist /FI "IMAGENAME eq pythonw.exe" | findstr /I "audio.py" >nul
if not errorlevel 1 exit

:: Activate virtual environment and run the script
call .venv\Scripts\activate
start /B .venv\Scripts\pythonw.exe audio.py
