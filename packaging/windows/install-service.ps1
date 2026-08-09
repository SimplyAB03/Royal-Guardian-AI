param([string]$InstallDir="$env:ProgramFiles\Royal Guardian")
$ErrorActionPreference="Stop"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item ".\dist\RoyalGuardianEndpoint.exe" "$InstallDir\RoyalGuardianEndpoint.exe" -Force
& "$InstallDir\RoyalGuardianEndpoint.exe" --startup auto install
Start-Service RoyalGuardianEndpoint
