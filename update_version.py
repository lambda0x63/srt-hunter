import sys
import re
import os

def update_version(new_version):
    with open('version.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = re.sub(r'VERSION = "[^"]+"', f'VERSION = "{new_version}"', content)
    
    with open('version.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"version.py 업데이트 완료: {new_version}")

    if os.path.exists('pyproject.toml'):
        with open('pyproject.toml', 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = re.sub(r'version = "[^"]+"', f'version = "{new_version}"', content)
        
        with open('pyproject.toml', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"pyproject.toml 업데이트 완료: {new_version}")
    
    if os.path.exists('README.md'):
        with open('README.md', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if lines and "SRT" in lines[0]:
            lines[0] = re.sub(r'\(v[^)]+\)', f'(v{new_version})', lines[0])
            
            if len(lines) > 1 and "CLI version" in lines[1]:
                lines[1] = re.sub(r'to GUI version\(v[^)]+\)', f'to GUI version(v{new_version})', lines[1])
            
            with open('README.md', 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            print(f"README.md 업데이트 완료: {new_version}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용법: python update_version.py [새 버전 번호]")
        print("예: python update_version.py 1.2.2")
        sys.exit(1)
    
    new_version = sys.argv[1]
    update_version(new_version)
    print(f"모든 파일의 버전 정보가 {new_version}으로 업데이트되었습니다.") 