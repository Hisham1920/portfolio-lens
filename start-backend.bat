@echo off
title PortfolioLens Backend
cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
  echo Creating the Python environment...
  python -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo.
  echo Add your OpenAI API key to the file that opens, save it, then close Notepad.
  notepad ".env"
)

python app.py
pause
