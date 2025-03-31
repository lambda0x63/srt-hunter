<h1 align="center">SRT-Hunter</h1>

<div align="center">
  <img src="https://github.com/user-attachments/assets/ee92a87a-700e-4c9b-ba02-5e4ad9ee64a9" alt="SRT-Hunter UI" width="400"/>
</div>

<h2 align="left">Features</h2>

- GUI-based interface
- SRT automatic login and booking automation
- KakaoPay automatic payment integration
- Multi-passenger reservation support (1-4 people)
- Pause and reset functionality
- Display of payment completion details

<h2 align="left">UI</h2>

<div align="center">
  <img src="https://github.com/user-attachments/assets/30db9ec0-493e-4cc2-852b-4ec1fe2ff06a" alt="SRT-Hunter UI" width="400"/>
</div>
<h2 align="left">Download</h2>

- Download: [Latest Release](https://github.com/root39293/srt-hunter/releases/latest)
- Run on your own PC
```bash
git clone https://github.com/root39293/srt-hunter.git
cd srt-hunter
poetry install
poetry run python main.py
```

<h2 align="left">Notice</h2>

- For personal use only
- Recommended refresh interval of 0.05 seconds or higher
- Chrome browser required

<h2 align="left">Change Log</h2>

### v1.3.6
- Added logic to check for no seats left message and improved handling of failed checkout button clicks

### v1.3.5
- Fixed alert handling for double SRT trains
- Improved payment button click stability
- Added wait time before payment button click
- Enhanced error handling for train reservation process

### v1.3.4
- Fixed build script bugs

### v1.3.3
- Added multi-passenger reservation feature (1-4 people)
- Improved login information management method (text file saving excluding password)
- Changed seat type selection to radio buttons
- Added pause and reset buttons
- Improved user interface

### v1.2.1
- Added login information saving feature

### v1.1.1
- Improved payment completion detection logic
- Added payment details (amount, approval date/time) display feature
- Enhanced payment completion page stability

<h2 align="left">License</h2>

MIT License
