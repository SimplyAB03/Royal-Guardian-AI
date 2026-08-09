$ErrorActionPreference="SilentlyContinue"
Stop-Service RoyalGuardianEndpoint -Force
& "$env:ProgramFiles\Royal Guardian\RoyalGuardianEndpoint.exe" remove
Remove-Item "$env:ProgramFiles\Royal Guardian" -Recurse -Force
