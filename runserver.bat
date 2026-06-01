@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "CONDA_ENV=shapez2_factory"
set "NEW_ENV=0"

where conda >nul 2>&1
if errorlevel 1 (
    echo [ERROR] conda not found on PATH.
    echo Install Miniconda/Anaconda, or open Anaconda Prompt and retry.
    exit /b 1
)

for /f "delims=" %%B in ('conda info --base 2^>nul') do set "CONDA_BASE=%%B"
if not defined CONDA_BASE (
    echo [ERROR] could not locate conda base. Run: conda init cmd.exe
    exit /b 1
)

call "%CONDA_BASE%\Scripts\activate.bat" "%CONDA_BASE%"
if errorlevel 1 exit /b 1

conda env list | findstr /B /C:"%CONDA_ENV% " >nul 2>&1
if errorlevel 1 (
    echo Creating conda env "%CONDA_ENV%" with Python 3.12...
    call conda create -n %CONDA_ENV% python=3.12 -y
    if errorlevel 1 exit /b 1
    set "NEW_ENV=1"
)

call conda activate %CONDA_ENV%
if errorlevel 1 (
    echo [ERROR] failed to activate "%CONDA_ENV%".
    exit /b 1
)

if "%NEW_ENV%"=="1" (
    echo Installing dev dependencies...
    python -m pip install -U pip
    python -m pip install -e ".[dev]"
    if errorlevel 1 exit /b 1
)

if not exist ".env" (
    if exist ".env.example" (
        echo Copying .env.example to .env ...
        copy /Y ".env.example" ".env" >nul
    )
)
echo Making migrations...
python manage.py makemigrations
if errorlevel 1 exit /b 1

echo Applying migrations...
python manage.py migrate --noinput
if errorlevel 1 exit /b 1

echo Starting Django dev server at http://127.0.0.1:8000/
python manage.py runserver 0.0.0.0:8000
endlocal
