"""Windows Service wrapper for the Royal Guardian endpoint.

This module requires pywin32 and is exercised during Windows packaging, not on
non-Windows development hosts.
"""
from __future__ import annotations
import time
from endpoint.client import load_config, once

try:
    import win32event, win32service, win32serviceutil, servicemanager  # type: ignore
except ImportError:  # pragma: no cover
    win32event=win32service=win32serviceutil=servicemanager=None

if win32serviceutil:
    class RoyalGuardianService(win32serviceutil.ServiceFramework):
        _svc_name_="RoyalGuardianEndpoint"
        _svc_display_name_="Royal Guardian Endpoint"
        _svc_description_="Secure Royal Guardian device diagnostics and approved remediation service."
        def __init__(self,args):
            super().__init__(args); self.stop_event=win32event.CreateEvent(None,0,0,None)
        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING); win32event.SetEvent(self.stop_event)
        def SvcDoRun(self):
            servicemanager.LogInfoMsg("Royal Guardian Endpoint started")
            cfg=load_config()
            while win32event.WaitForSingleObject(self.stop_event,20000)==win32event.WAIT_TIMEOUT:
                try: once(cfg)
                except Exception as exc: servicemanager.LogErrorMsg(f"Royal Guardian endpoint error: {exc}")

if __name__=="__main__":
    if not win32serviceutil: raise SystemExit("pywin32 is required to install/run the Windows service")
    win32serviceutil.HandleCommandLine(RoyalGuardianService)
