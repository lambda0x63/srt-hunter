@echo off
chcp 65001 > nul
echo SRT-Hunter Windows Build Starting...

REM Check version info
for /f "tokens=2 delims==" %%a in ('findstr "VERSION" version.py') do set VERSION=%%a
set VERSION=%VERSION:"=%
set VERSION=%VERSION: =%
echo Current Version: %VERSION%

REM Prepare environment
echo Initializing Poetry environment...
call poetry install

REM Create resources directory
if not exist resources mkdir resources

REM Generate executable with PyInstaller
echo Running PyInstaller...
call poetry run pyinstaller --noconfirm --clean ^
    --name="SRT-Hunter" ^
    --add-data="LICENSE;." ^
    --add-data="README.md;." ^
    --add-data="resources;resources" ^
    --noconsole ^
    --onefile ^
    main.py

REM Check if build was successful
if not exist "dist\SRT-Hunter.exe" (
    echo Build failed! Executable not found.
    exit /b 1
)

REM Create ZIP file
echo Creating ZIP file...
cd dist
if exist "SRT-Hunter-v%VERSION%-Windows.zip" del "SRT-Hunter-v%VERSION%-Windows.zip"
powershell -Command "Compress-Archive -Path 'SRT-Hunter.exe' -DestinationPath 'SRT-Hunter-v%VERSION%-Windows.zip' -Force"

REM Verify ZIP file was created (with more flexible check)
dir "SRT-Hunter-v*-Windows.zip" > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Windows build completed successfully!
    echo ZIP file created: SRT-Hunter-v%VERSION%-Windows.zip
    cd ..
    exit /b 0
) else (
    echo ZIP file creation failed!
    cd ..
    exit /b 1
) 