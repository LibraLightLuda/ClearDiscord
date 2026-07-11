@echo off
title Undiscord Python GUI EXE Builder
echo ==================================================
echo         Undiscord Python GUI EXE Builder
echo ==================================================
echo.

REM 0. Check Python Command
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH.
    echo Please install Python and ensure 'Add Python to PATH' is checked.
    if not "%CI%"=="true" pause
    exit /b 1
)

REM 1. Check Python Dependencies
echo [1/4] Checking Python dependencies...
python -c "import requests" 2>nul
if %errorlevel% neq 0 (
    echo 'requests' library is missing. Installing...
    pip install requests
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install 'requests'.
        if not "%CI%"=="true" pause
        exit /b 1
    )
) else (
    echo 'requests' library is already installed.
)

python -c "import cryptography" 2>nul
if %errorlevel% neq 0 (
    echo 'cryptography' library is missing. Installing...
    pip install cryptography
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install 'cryptography'.
        if not "%CI%"=="true" pause
        exit /b 1
    )
) else (
    echo 'cryptography' library is already installed.
)

python -c "import webview" 2>nul
if %errorlevel% neq 0 (
    echo 'pywebview' library is missing. Installing...
    pip install pywebview
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install 'pywebview'.
        if not "%CI%"=="true" pause
        exit /b 1
    )
) else (
    echo 'pywebview' library is already installed.
)

python -c "import curl_cffi" 2>nul
if %errorlevel% neq 0 (
    echo 'curl_cffi' library is missing. Installing...
    pip install curl_cffi
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install 'curl_cffi'.
        if not "%CI%"=="true" pause
        exit /b 1
    )
) else (
    echo 'curl_cffi' library is already installed.
)

REM 2. Check PyInstaller
echo [2/4] Checking PyInstaller installation...
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo PyInstaller is not installed. Installing...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install PyInstaller.
        if not "%CI%"=="true" pause
        exit /b 1
    )
    echo PyInstaller installed successfully.
) else (
    echo PyInstaller is already installed.
)
echo.

REM 3. Start packaging into EXE
echo [3/4] Building executable file (.exe)...
echo (This may take up to 2 minutes. Please wait...)
echo.

python -m PyInstaller --onefile --noconsole --icon="cold.ico" --add-data "cold.png;." --add-data "cold.ico;." --hidden-import=webview --hidden-import=curl_cffi --name "UndiscordGUI" undiscord_gui.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed. Please check the logs above.
    if not "%CI%"=="true" pause
    exit /b 1
)
echo.

REM 4. Cleanup temp files
echo [4/4] Copying output and cleaning up build cache...
if exist "dist\UndiscordGUI.exe" (
    copy "dist\UndiscordGUI.exe" ".\UndiscordGUI.exe" > nul
    echo.
    echo --------------------------------------------------
    echo [SUCCESS] Build finished successfully!
    echo 'UndiscordGUI.exe' has been created in this folder.
    echo --------------------------------------------------
) else (
    echo [ERROR] Build output 'UndiscordGUI.exe' not found in dist folder.
)

if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "UndiscordGUI.spec" del /f /q "UndiscordGUI.spec"

echo.
echo Done. You can close this window.
if not "%CI%"=="true" pause
