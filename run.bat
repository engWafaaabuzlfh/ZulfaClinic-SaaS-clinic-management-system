@echo off
cd /d "%~dp0"

set "PYTHON_EXE=..\Scripts\python.exe"

if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" run.py
) else (
    py -3 run.py
)

if errorlevel 1 (
    echo.
    echo Failed to start Zulfa Clinic. Make sure dependencies are installed and PostgreSQL is running.
    pause
)
