@echo off
echo ==========================================
echo Starting Naina AI Full Bundling Process...
echo ==========================================

echo.
echo [1/3] Building Python Backend with Nuitka...
call build_nuitka.bat

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Backend build failed!
    exit /b %ERRORLEVEL%
)

echo.
echo [2/3] Installing Frontend Dependencies (electron-builder)...

:: Ye line terminal ko wapas main project folder me le aayegi
cd /d "%~dp0"
cd frontend\visualizer-app

call npm install electron-builder --save-dev
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install npm dependencies!
    exit /b %ERRORLEVEL%
)

echo.
echo [3/3] Building and Packaging Frontend with Electron...
call npm run pack-app
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Frontend packaging failed!
    exit /b %ERRORLEVEL%
)



echo.
echo ==========================================
echo BUNDLING COMPLETE!
echo Your final executable is located at:
echo E:\MyProjects\CPP\Trinetra_Vision\frontend\visualizer-app\dist\
echo ==========================================
pause