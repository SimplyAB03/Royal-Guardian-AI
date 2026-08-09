WEIGHTS = {
    "system_basic": 10,
    "storage": 15,
    "usb_devices": 0,
    "windows_updates": 20,
    "defender": 25,
    "startup_apps": 10,
    "network": 10,
    "battery": 5,
    "services": 5
}

STATUS_MULTIPLIER = {
    "healthy": 0,
    "warning": 0.5,
    "critical": 1
}


def calculate_score(modules):
    score = 100

    for module in modules:

        weight = WEIGHTS.get(module["module"], 5)

        multiplier = STATUS_MULTIPLIER.get(module["status"], 0)

        score -= weight * multiplier

    return max(round(score), 0)