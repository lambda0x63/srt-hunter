#!/bin/bash

echo "🚀 SRT Hunter Build Script (macOS)"
echo "================================"

# Clean previous build
echo "📦 Cleaning previous build..."
rm -rf dist build *.spec

# Get version from version.py
VERSION=$(python -c "from version import VERSION; print(VERSION)")
echo "📌 Building version: $VERSION"

# Run PyInstaller
echo "🔨 Building executable..."
pyinstaller \
    --name="SRT-Hunter" \
    --onefile \
    --windowed \
    --icon="static/icon/icon.png" \
    --add-data="static:static" \
    --hidden-import="PyQt6" \
    --hidden-import="playwright" \
    --hidden-import="qdarkstyle" \
    --clean \
    --noconfirm \
    main.py

# Check if build was successful
if [ -f "dist/SRT-Hunter.app" ] || [ -f "dist/SRT-Hunter" ]; then
    echo "✅ Build successful!"
    echo "📍 Output: dist/SRT-Hunter.app"
else
    echo "❌ Build failed!"
    exit 1
fi

echo "================================"
echo "🎉 Build complete!"