#!/bin/bash
echo "SRT-Hunter macOS 빌드 시작..."

# 스크립트 실행 권한 설정
chmod +x build-script/build_macos.sh

# 버전 정보 확인
VERSION=$(grep -o 'VERSION = "[^"]*"' version.py | cut -d'"' -f2)
echo "현재 버전: $VERSION"

# 환경 준비
echo "Poetry 환경 초기화 중..."
poetry install --no-dev

# resources 디렉토리 생성 (아이콘 및 리소스 파일용)
mkdir -p resources

# PyInstaller로 앱 번들 생성
echo "PyInstaller 실행 중..."
poetry run pyinstaller --noconfirm --clean \
    --name="SRT-Hunter" \
    --icon=resources/icon.icns \
    --add-data="LICENSE:." \
    --add-data="README.md:." \
    --add-data="resources:resources" \
    --windowed \
    --onefile \
    main.py

# 출력 파일명 변경 및 압축
cd dist
echo "생성된 파일 압축 중..."
zip -r "SRT-Hunter-v${VERSION}-macOS.zip" "SRT-Hunter"
cd ..

echo "macOS 빌드 완료! (dist/SRT-Hunter-v${VERSION}-macOS.zip)" 