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
    
    # Remove quarantine attribute for macOS
    if [ -f "dist/SRT-Hunter" ]; then
        xattr -cr dist/SRT-Hunter
        echo "🔓 Removed quarantine attributes"
    fi
    if [ -d "dist/SRT-Hunter.app" ]; then
        xattr -cr dist/SRT-Hunter.app
        echo "🔓 Removed quarantine attributes from app bundle"
    fi
    
    echo "📍 Output: dist/SRT-Hunter"
else
    echo "❌ Build failed!"
    exit 1
fi

echo "================================"
echo "🎉 Build complete!"