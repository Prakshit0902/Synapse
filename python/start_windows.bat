@echo off
:: color de diya
color 0A
:: Title for windows terminal
title SYNAPSE Core Inference Engine (Windows)

echo.
echo       [SYNAPSE] Powering Naina AI - Desktop Edition
echo       Hardware: NVIDIA CUDA Core Initialization...
echo.

REM Check if virtual environment exists
if not exist "synapse_env\Scripts\activate.bat" (
    REM file nahi mili to pehle show karo
    echo [ERROR] Virtual environment 'synapse_env' not found!
    REM print statement
    echo Please check if your environment folder is named correctly.
    pause
    REM exit karo
    exit /b
)

echo [SYSTEM] Activating Virtual Environment...
REM venv wali file activate karo and wapas terminal me aa jaao
call synapse_env\Scripts\activate.bat

echo [SYSTEM] Setting up PyCharm equivalent Environment...
REM Path na mile to ek folder piche jaa kar dekh bhaiye
set PYTHONPATH=..

echo [SYSTEM] Launching Synapse Backend Engine...
echo.
REM python command to run main file
python engine\main.py

REM screen rok do and print kar do "Press any key to continue"
pause