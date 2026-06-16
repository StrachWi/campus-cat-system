@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Backend virtual environment is missing.
  echo Run: C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m venv .venv
  echo Then: .venv\Scripts\python.exe -m pip install -r requirements.txt
  pause
  exit /b 1
)
echo Starting Campus Cat backend on http://0.0.0.0:5000
echo Health check: http://10.133.134.168:5000/api/health
".venv\Scripts\python.exe" app.py
pause
