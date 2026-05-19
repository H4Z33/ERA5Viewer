@echo off
echo Starting ERA5 Data Viewer Setup...

REM Check if uv is installed
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: 'uv' is not installed or not in PATH.
    echo Please install uv from https://github.com/astral-sh/uv
    pause
    exit /b 1
)

echo Syncing dependencies...
uv sync

if %errorlevel% neq 0 (
    echo Error: Failed to sync dependencies.
    pause
    exit /b 1
)

echo Starting web server on http://127.0.0.1:8008 ...
uv run uvicorn main:app --host 127.0.0.1 --port 8008

if %errorlevel% neq 0 (
    echo Server stopped with error.
    pause
    exit /b 1
)
