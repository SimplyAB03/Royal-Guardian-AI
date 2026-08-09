def calculate_health_score(data):
    score = 100
    issues = []

    if data["ram_percent"] >= 85:
        score -= 15
        issues.append({
            "severity": "medium",
            "title": "High memory usage",
            "explanation": "Your computer is using a lot of RAM, which can make apps feel slow.",
            "recommendation": "Close unused apps or restart the computer."
        })

    if data["disk_used_percent"] >= 90:
        score -= 20
        issues.append({
            "severity": "high",
            "title": "Low disk space",
            "explanation": "Your storage drive is almost full. Windows needs free space to run smoothly.",
            "recommendation": "Delete temporary files or move large files to another drive."
        })

    if data["uptime_days"] >= 7:
        score -= 8
        issues.append({
            "severity": "medium",
            "title": "Computer has not restarted recently",
            "explanation": "Long uptime can cause memory buildup and pending updates to stay stuck.",
            "recommendation": "Restart the computer when convenient."
        })

    return {
        "score": max(score, 0),
        "issues": issues
    }