@echo off
setlocal

REM ===============================================================================
REM  Automated Build & Packaging Script for ANAHKEN's Modular Snake Game
REM ===============================================================================
REM This script automates the entire release process:
REM 1. Cleans previous build artifacts.
REM 2. Generates a version info file for the executable.
REM 3. Runs PyInstaller to create the executable with embedded version info.
REM 4. Runs the VBScript to create the portable shortcut.
REM 5. Packages everything into a clean, versioned, distributable .zip file.

REM --- Configuration ---
set "CurrentVersion=1.2.0"
set "CompanyName=ANAHKEN"
set "FileDescription=ANAHKENs Modular Snake Game"
set "ProductName=ANAHKENs Modular Snake Game"
set "LegalCopyright=Copyright (c) ANAHKEN. All rights reserved."

REM --- Step 0: Get Version Number from User ---
echo.
echo The current version is set to %CurrentVersion%.
set /p "Version=Enter new version number (or press Enter to use %CurrentVersion%): "
if not defined Version set "Version=%CurrentVersion%"
echo [BUILD] Using version: %Version%

REM Convert version string "1.0.0" to "1,0,0,0" for the version file
for /f "tokens=1,2,3 delims=." %%a in ("%Version%") do set "VersionTuple=%%a,%%b,%%c,0"

REM --- Start Build ---
echo [BUILD] Starting the automated build process...

REM --- Step 1: Clean previous build artifacts ---
echo [BUILD] Cleaning previous build artifacts...
if exist "dist" (
    echo      - Removing 'dist' folder...
    rmdir /s /q "dist"
)
if exist "build" (
    echo      - Removing 'build' folder...
    rmdir /s /q "build"
)
if exist "%ProductName%.spec" (
    echo      - Removing '.spec' file...
    del "%ProductName%.spec"
)
if exist "version_info.txt" (
    echo      - Removing 'version_info.txt' file...
    del "version_info.txt"
)
if exist "%ProductName%.lnk" (
    echo      - Removing old shortcut...
    del "%ProductName%.lnk"
)
echo [BUILD] Cleaning complete.
echo.

REM --- Step 2: Generate Version Info File ---
echo [BUILD] Generating version info file (version_info.txt)...
(
    echo # UTF-8
    echo VSVersionInfo(
    echo   ffi=FixedFileInfo(
    echo     filevers=(%VersionTuple%),
    echo     prodvers=(%VersionTuple%),
    echo     mask=0x3f,
    echo     flags=0x0,
    echo     os=0x40004,
    echo     type=0x1,
    echo     subtype=0x0,
    echo     date=(0, 0)
    echo   ),
    echo   kids=[
    echo     StringFileInfo([
    echo       StringTable(
    echo         u'040904B0',
    echo         [StringStruct(u'CompanyName', u'%CompanyName%'),
    echo         StringStruct(u'FileDescription', u'%FileDescription%'),
    echo         StringStruct(u'FileVersion', u'%Version%'),
    echo         StringStruct(u'InternalName', u'ModularSnake'),
    echo         StringStruct(u'LegalCopyright', u'%LegalCopyright%'),
    echo         StringStruct(u'OriginalFilename', u'%ProductName%.exe'),
    echo         StringStruct(u'ProductName', u'%ProductName%'),
    echo         StringStruct(u'ProductVersion', u'%Version%')])
    echo     ]),
    echo     VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
    echo   ]
    echo )
) > version_info.txt
echo [BUILD] Version info file created.
echo.

REM --- Step 3: Run PyInstaller ---
echo [BUILD] Generating PyInstaller spec file...
REM First, generate the .spec file without the version info to avoid race conditions.
py -m PyInstaller --onefile --windowed --name "%ProductName%" --icon="assets/images/icon.ico" --add-data "assets;assets" --splash "assets/images/splash_screen.png" --noconfirm main.py

echo [BUILD] Modifying spec file to include version info...
REM Now, add the version-file argument to the EXE call inside the .spec file.
powershell -Command "(Get-Content '%ProductName%.spec') -replace 'exe = EXE(pyz,', 'exe = EXE(pyz, version=''version_info.txt'',' | Set-Content '%ProductName%.spec'"

echo [BUILD] Building executable from modified spec file...
REM Finally, run PyInstaller using the modified spec file.
py -m PyInstaller "%ProductName%.spec" --noconfirm
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller failed to build the executable. Aborting.
    pause
    exit /b 1
)
echo [BUILD] PyInstaller build successful.
echo.

REM --- Step 4: Create the portable shortcut ---
echo [BUILD] Creating portable Windows shortcut...
cscript //nologo create_shortcut.vbs
if not exist "%ProductName%.lnk" (
    echo [ERROR] Shortcut creation failed. Aborting.
    pause
    exit /b 1
)
echo [BUILD] Shortcut created successfully.
echo.

REM --- Step 5: Package into a .zip file ---
echo [BUILD] Packaging final distributable .zip file...
set "PackageName=ANAHKENs_Snake_Game_Windows_v%Version%"
powershell -Command "Compress-Archive -Path '.\dist', '.\%ProductName%.lnk' -DestinationPath '.\%PackageName%.zip' -Force" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create .zip file. This can happen if PowerShell is restricted.
    echo [ERROR] Please check your system's script execution policy.
    pause
    exit /b 1
)
echo [BUILD] Successfully created '%PackageName%.zip'.
echo.

echo [SUCCESS] Build and packaging process complete!
pause
endlocal