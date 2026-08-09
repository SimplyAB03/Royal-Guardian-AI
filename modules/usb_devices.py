import psutil

def run():
    devices = []
    issues = []

    for part in psutil.disk_partitions(all=False):
        opts = (part.opts or "").lower()
        is_removable = "removable" in opts or "cdrom" in opts

        if is_removable:
            devices.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "filesystem": part.fstype,
                "type": "removable"
            })

    return {
        "module": "usb_devices",
        "title": "USB / Removable Devices",
        "status": "healthy",
        "priority": 0,
        "summary": "Checks for removable USB storage devices.",
        "data": {
            "usb_devices": devices,
            "count": len(devices)
        },
        "issues": []
    }