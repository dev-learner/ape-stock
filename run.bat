@echo off
cd /d "%~dp0"

echo Clearing Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create venv. Make sure Python is in PATH.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat
python -m pip install -r requirements.txt -q

start "ape-stock" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate.bat && python app.py"

echo Waiting for Flask to start on port 5050...
:waitloop
timeout /t 1 /nobreak >nul
netstat -an | find "127.0.0.1:5050" | find "LISTENING" >nul
if errorlevel 1 goto waitloop

echo Flask is ready.
start "" http://127.0.0.1:5050