@echo off
echo SRT Hunter Build Script (Windows)
echo ================================

echo Cleaning previous build...
rmdir /s /q dist 2>nul
rmdir /s /q build 2>nul
del *.spec 2>nul

echo Building executable...
pyinstaller ^
    --name="SRT-Hunter" ^
    --onefile ^
    --windowed ^
    --icon="static/icon/icon.png" ^
    --add-data="static;static" ^
    --hidden-import="PyQt6" ^
    --hidden-import="playwright" ^
    --hidden-import="qdarkstyle" ^
    --clean ^
    --noconfirm ^
    main.py

if exist "dist\SRT-Hunter.exe" (
    echo Build successful!
    echo Output: dist\SRT-Hunter.exe
) else (
    echo Build failed!
    exit /b 1
)

echo ================================
echo Build complete!