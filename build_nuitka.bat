@echo off
echo ==========================================
echo Starting Naina AI Backend Build with Nuitka
echo ==========================================

cd python\engine

:: First activate the virtual environment
if exist "..\synapse_env\Scripts\activate.bat" (
    echo Activating virtual environment...
    call "..\synapse_env\Scripts\activate.bat"
) else (
    echo Warning: Virtual environment not found at python\synapse_env
)

echo Installing Nuitka...
python -m pip install nuitka zstandard

echo Running Nuitka Build...
:: We use --standalone to create a self-contained folder
:: We use --include-data-dir for known_faces and other resources
python -m nuitka --standalone ^
    --include-module=uvicorn.logging ^
    --include-module=uvicorn.loops ^
    --include-module=uvicorn.loops.auto ^
    --include-module=uvicorn.protocols.http.auto ^
    --include-module=uvicorn.protocols.websockets.auto ^
    --include-module=uvicorn.lifespan.on ^
    --include-package=openwakeword ^
    --include-package=cv2 ^
    --include-package=pygame ^
    --include-package=pyaudio ^
    --include-package=colorama ^
    --include-package=ollama ^
    --include-package=thefuzz ^
    --include-package=ultralytics ^
    --include-package=insightface ^
    --assume-yes-for-downloads ^
    --output-dir=build_naina ^
    main.py

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Nuitka build failed!
    exit /b %ERRORLEVEL%
)

:: Deactivate virtual environment if it was activated
if exist "..\synapse_env\Scripts\activate.bat" (
    call deactivate
)

echo.
echo ==========================================
echo BACKEND BUILD COMPLETE!
echo The backend is located at:
echo E:\MyProjects\CPP\Trinetra_Vision\python\engine\build_naina\main.dist\
echo ==========================================
pause