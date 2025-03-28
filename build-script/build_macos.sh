#!/bin/bash
echo "SRT-Hunter macOS Build Starting..."

echo "현재 작업 디렉토리: $(pwd)"
ls -la

# Check version info
VERSION=$(grep -o 'VERSION = "[^"]*"' version.py | cut -d'"' -f2)
echo "Current Version: $VERSION"

# Prepare environment
echo "Initializing Poetry environment..."
poetry install

# Create resources directory
mkdir -p resources

# Generate app bundle with PyInstaller
echo "Running PyInstaller..."
poetry run pyinstaller --noconfirm --clean \
    --name="SRT-Hunter" \
    --add-data="LICENSE:." \
    --add-data="README.md:." \
    --add-data="resources:resources" \
    --windowed \
    --onefile \
    main.py

# Check if build was successful
if [ ! -f "dist/SRT-Hunter" ]; then
    echo "Build failed! Executable not found."
    exit 1
fi

# Create ZIP file
cd dist
echo "Creating ZIP file..."
zip -r "SRT-Hunter-v${VERSION}-macOS.zip" "SRT-Hunter"
cd ..

# Verify ZIP file was created
if [ -f "dist/SRT-Hunter-v${VERSION}-macOS.zip" ]; then
    echo "macOS build completed successfully! (dist/SRT-Hunter-v${VERSION}-macOS.zip)"
else
    echo "ZIP file creation failed!"
    exit 1
fi 