@echo off
color 0A
title SYNAPSE Core Inference Engine (Windows)
echo 
echo       [SYNAPSE] Powering Naina AI - Desktop Edition
echo       Hardware: NVIDIA CUDA Core Initialization...
echo 
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment 'venv' not found!
    echo Please run 'python -m venv venv' and install requirements.
    pause
    exit /b
)

echo [SYSTEM] Activating Virtual Environment...
call venv\Scripts\activate.bat

echo [SYSTEM] Launching Synapse Backend Engine...
echo.

python main.py

pause