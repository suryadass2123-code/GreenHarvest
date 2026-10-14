@echo off
setlocal
cd /d "%~dp0"

echo =============================================
echo GreenHarvest - Windows Quick Run
 echo =============================================

if not exist venv\Scripts\python.exe (
    echo Creating virtual environment...
    py -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

if not exist .env (
    echo Creating .env from .env.example...
    copy /Y .env.example .env >nul
    echo.
    echo IMPORTANT: Open .env and enter your MySQL password.
    echo Then run this file again.
    pause
    exit /b 0
)

echo Installing project packages...
venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo Package installation failed.
    pause
    exit /b 1
)

echo.
echo Checking Django...
venv\Scripts\python.exe manage.py check
if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo Running migrations...
venv\Scripts\python.exe manage.py makemigrations accounts products orders payments reviews
venv\Scripts\python.exe manage.py migrate
if errorlevel 1 (
    echo Migration failed. Check MySQL is running and .env has the correct root password.
    pause
    exit /b 1
)

echo.
echo Starting GreenHarvest...
echo Open http://127.0.0.1:8000/ in your browser.
echo Press CTRL+C to stop the server.
echo.
venv\Scripts\python.exe manage.py runserver

endlocal
