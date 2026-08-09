# Windows Endpoint Agent

## Current flow
1. Business/admin creates an enrollment token in the web app.
2. On Windows, run `python endpoint_cli.py enroll --server https://YOUR-SERVER --token TOKEN` during development.
3. The endpoint stores a device credential in `%PROGRAMDATA%/RoyalGuardian/device.json` (or user home on non-Windows dev hosts).
4. `endpoint_cli.py run` sends diagnostics, polls one queued command at a time, executes only registered allowlisted actions and returns results.

## Before commercial distribution
- Run as a least-privilege Windows Service where possible.
- Store device secret using Windows DPAPI/Credential Manager rather than a plaintext JSON file.
- Build a signed installer/MSI.
- Implement signed auto-update with rollback.
- Add service recovery policy and local tamper protection.
- Add secure uninstall/device-revocation behavior.
- Verify each action on supported Windows versions.
