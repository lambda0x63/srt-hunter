@echo off
echo SRT-Hunter Windows 빌드 시작...

REM 버전 정보 확인
for /f "tokens=2 delims==" %%a in ('findstr "VERSION" version.py') do set VERSION=%%a
set VERSION=%VERSION:"=%
echo 현재 버전: %VERSION%

REM 환경 준비
echo Poetry 환경 초기화 중...
call poetry install --no-dev

REM resources 디렉토리 생성 (아이콘 및 리소스 파일용)
if not exist resources mkdir resources

REM PyInstaller로 실행 파일 생성
echo PyInstaller 실행 중...
call poetry run pyinstaller --noconfirm --clean ^
    --name="SRT-Hunter" ^
    --icon=resources/icon.ico ^
    --add-data="LICENSE;." ^
    --add-data="README.md;." ^
    --add-data="resources;resources" ^
    --noconsole ^
    --onefile ^
    main.py

REM 출력 파일명 변경 및 압축
cd dist
echo 생성된 파일 압축 중...
rename "SRT-Hunter.exe" "SRT-Hunter.exe"
powershell Compress-Archive -Force -Path "SRT-Hunter.exe" -DestinationPath "SRT-Hunter-v%VERSION%-Windows.zip"
cd ..

echo Windows 빌드 완료! (dist/SRT-Hunter-v%VERSION%-Windows.zip) 