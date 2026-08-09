$ErrorActionPreference = "Stop"
python -m pip install -r requirements.txt
python -m pip install pyinstaller pywin32
pyinstaller --noconfirm --clean --name RoyalGuardianEndpoint --onefile --hidden-import win32timezone endpoint/service.py
pyinstaller --noconfirm --clean --name RoyalGuardian --onefile endpoint_cli.py
Write-Host "Unsigned binaries created under dist/. Sign them before commercial distribution."
