@echo off
title Undiscord Release Packager
echo ==================================================
echo         Undiscord Release Packager
echo ==================================================
echo.

REM 1. Run build.bat to compile the executable
echo [1/3] Compiling GUI application via build.bat...
call build.bat

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Compilation failed. Packaging aborted.
    if not "%CI%"=="true" pause
    exit /b 1
)

REM 2. Check if build output exists
echo.
echo [2/3] Verifying executable output...
if not exist "UndiscordGUI.exe" (
    echo.
    echo [ERROR] UndiscordGUI.exe not found. Build might have failed silently.
    if not "%CI%"=="true" pause
    exit /b 1
)
echo Executable verified.

REM 3. Package to ZIP archive
echo.
echo [3/3] Creating zip archive...
powershell -Command "Compress-Archive -Path 'UndiscordGUI.exe', 'README.md', 'PATCH_NOTES.md' -DestinationPath 'UndiscordGUI_Release.zip' -Force"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to create ZIP archive.
    if not "%CI%"=="true" pause
    exit /b 1
)

echo.
echo --------------------------------------------------
echo [SUCCESS] Release package created successfully!
echo File: UndiscordGUI_Release.zip
echo Contents: UndiscordGUI.exe, README.md, PATCH_NOTES.md
echo --------------------------------------------------
echo.
if not "%CI%"=="true" pause
