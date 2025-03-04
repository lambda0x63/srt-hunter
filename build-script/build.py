#!/usr/bin/env python3
"""
SRT-Hunter 빌드 스크립트
Windows 또는 macOS를 자동 감지하여 적절한 빌드 스크립트를 실행합니다.
"""
import os
import sys
import platform
import subprocess
import re
import glob

def get_version():
    """version.py 파일에서 버전 정보 추출"""
    with open('version.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'VERSION = "([^"]+)"', content)
    if match:
        return match.group(1).strip()
    return "unknown"

def main():
    # 현재 운영체제 확인
    system = platform.system()
    version = get_version()
    
    print(f"SRT-Hunter v{version} 빌드 시작...")
    print(f"운영체제: {system}")
    
    # build-script 디렉토리 확인
    script_dir = 'build-script'
    if not os.path.exists(script_dir):
        os.makedirs(script_dir)
    
    # 운영체제별 빌드 스크립트 선택
    if system == 'Windows':
        script_path = os.path.join(script_dir, 'build_windows.bat')
        cmd = [script_path]
        output_pattern = f"dist/SRT-Hunter-v*-Windows.zip"
    elif system == 'Darwin':  # macOS
        script_path = os.path.join(script_dir, 'build_macos.sh')
        os.chmod(script_path, 0o755)  # 실행 권한 부여
        cmd = ['/bin/bash', script_path]
        output_pattern = f"dist/SRT-Hunter-v*-macOS.zip"
    else:
        print(f"지원되지 않는 운영체제: {system}")
        print("현재는 Windows와 macOS만 지원합니다.")
        sys.exit(1)
    
    # 빌드 스크립트 실행
    try:
        result = subprocess.run(cmd, check=False)
        
        # 결과 파일 확인 (패턴 매칭 사용)
        output_files = glob.glob(output_pattern)
        if output_files:
            print(f"빌드 성공! 결과 파일: {output_files[0]}")
            return 0
        else:
            print(f"빌드는 완료되었으나 결과 파일을 찾을 수 없습니다: {output_pattern}")
            return 1
    except Exception as e:
        print(f"빌드 중 오류 발생: {e}")
        return 1
    
if __name__ == "__main__":
    sys.exit(main()) 