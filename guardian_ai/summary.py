def build_summary(scan):
    score = scan.get("score", 0)
    modules = scan.get("modules", [])
    issues = scan.get("issues", [])

    healthy_modules = [m for m in modules if m.get("status") == "healthy"]
    warning_modules = [m for m in modules if m.get("status") == "warning"]
    critical_modules = [m for m in modules if m.get("status") == "critical"]

    if score >= 95 and not issues:
        headline = "Your computer looks excellent."
        tone = "positive"
        simple = "Royal Guardian did not find anything that needs attention right now."
    elif critical_modules:
        headline = "Your computer needs attention."
        tone = "critical"
        simple = "Royal Guardian found at least one issue that should be reviewed soon."
    elif warning_modules:
        headline = "Your computer is mostly healthy."
        tone = "warning"
        simple = "Royal Guardian found a few items worth checking, but nothing appears urgent."
    else:
        headline = "Your computer looks healthy."
        tone = "positive"
        simple = "Everything checked by Royal Guardian appears normal."

    highlights = []

    for module in modules:
        if module.get("status") == "healthy":
            highlights.append(f"{module.get('title')} looks healthy.")
        elif module.get("status") == "warning":
            highlights.append(f"{module.get('title')} needs review.")
        elif module.get("status") == "critical":
            highlights.append(f"{module.get('title')} needs immediate attention.")

    recommended_actions = []

    if issues:
        for issue in issues[:3]:
            recommended_actions.append(issue.get("recommendation", "Review this issue."))
    else:
        recommended_actions.append("No action is required right now.")

    return {
        "headline": headline,
        "tone": tone,
        "simple_summary": simple,
        "score": score,
        "healthy_count": len(healthy_modules),
        "warning_count": len(warning_modules),
        "critical_count": len(critical_modules),
        "highlights": highlights,
        "recommended_actions": recommended_actions
    }