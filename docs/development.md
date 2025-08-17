# Development Setup

## Requirements
- Python 3.11+
- Chrome browser

## Setup

### 1. Clone repository
```bash
git clone https://github.com/lambda0x63/srt-hunter.git
cd srt-hunter
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

## Run
```bash
python main.py
```

## Build

### macOS
```bash
chmod +x build.sh
./build.sh
```

### Windows
```bash
build.bat
```

## Release
Push a tag to trigger automatic release:
```bash
git tag v2.0.1
git push origin v2.0.1
```