#!/usr/bin/env python3
"""
아이콘 변환 도구: PNG -> ICO/ICNS 변환
사용법: python icon_converter.py input.png
"""
import os
import sys
import subprocess
from PIL import Image

def png_to_ico(png_path, output_path=None):
    """PNG 파일을 Windows ICO 형식으로 변환"""
    if output_path is None:
        output_path = os.path.splitext(png_path)[0] + '.ico'
    
    sizes = [16, 32, 48, 64, 128, 256]
    img = Image.open(png_path)
    icons = []
    
    for size in sizes:
        resized_img = img.resize((size, size), Image.LANCZOS)
        icons.append(resized_img)
    
    icons[0].save(output_path, format='ICO', sizes=[(s, s) for s in sizes], 
                  append_images=icons[1:])
    print(f"ICO 파일 생성 완료: {output_path}")

def png_to_icns(png_path, output_path=None):
    """PNG 파일을 macOS ICNS 형식으로 변환 (Mac에서만 작동)"""
    if output_path is None:
        output_path = os.path.splitext(png_path)[0] + '.icns'
    
    # 임시 디렉토리 생성
    temp_dir = 'temp_iconset'
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    # 여러 크기의 아이콘 생성
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    img = Image.open(png_path)
    
    for size in sizes:
        resized_img = img.resize((size, size), Image.LANCZOS)
        icon_path = f"{temp_dir}/icon_{size}x{size}.png"
        icon_path2x = f"{temp_dir}/icon_{size//2}x{size//2}@2x.png"
        
        resized_img.save(icon_path)
        if size > 16:  # 16x16은 @2x가 필요없음
            resized_img.save(icon_path2x)
    
    # iconutil로 ICNS 생성 (macOS 전용)
    try:
        cmd = ['iconutil', '-c', 'icns', temp_dir, '-o', output_path]
        subprocess.run(cmd, check=True)
        print(f"ICNS 파일 생성 완료: {output_path}")
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print(f"ICNS 변환 실패: {e}")
        print("참고: iconutil은 macOS에서만 사용 가능합니다.")
    
    # 임시 디렉토리 정리
    for file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file))
    os.rmdir(temp_dir)

def main():
    if len(sys.argv) < 2:
        print("사용법: python icon_converter.py input.png")
        sys.exit(1)
    
    png_path = sys.argv[1]
    if not os.path.exists(png_path):
        print(f"파일을 찾을 수 없음: {png_path}")
        sys.exit(1)
    
    # resources 디렉토리에 출력
    resources_dir = 'resources'
    if not os.path.exists(resources_dir):
        os.makedirs(resources_dir)
    
    base_name = os.path.splitext(os.path.basename(png_path))[0]
    ico_path = os.path.join(resources_dir, f"{base_name}.ico")
    icns_path = os.path.join(resources_dir, f"{base_name}.icns")
    
    # 변환 실행
    png_to_ico(png_path, ico_path)
    
    # macOS에서는 ICNS도 생성
    if sys.platform == 'darwin':
        png_to_icns(png_path, icns_path)
    else:
        print("ICNS 변환은 macOS 환경에서만 지원됩니다.")

if __name__ == "__main__":
    main() 