@echo off
cd /d "%~dp0"
if errorlevel 1 exit /b 1

set "PYTHON=py"
py --version >nul 2>&1
if errorlevel 1 set "PYTHON=python"

%PYTHON% -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dashboard dependencies.
    pause
    exit /b 1
)

%PYTHON% -m streamlit run app.py
if errorlevel 1 (
    echo The dashboard exited with an error.
    pause
    exit /b 1
)

pause
