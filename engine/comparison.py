from engine.timeline import load_scan_history

def compare_to_previous(current_result):
    history = load_scan_history(limit=2)

    if len(history) < 2:
        return {
            "has_previous": False,
            "summary": "No previous scan available for comparison.",
            "changes": []
        }

    previous = history[1]

    current_score = current_result.get("health", {}).get("score")
    previous_score = previous.get("score")

    changes = []

    if current_score is not None and previous_score is not None:
        diff = current_score - previous_score

        if diff > 0:
            changes.append(f"Health score improved by {diff} point(s).")
        elif diff < 0:
            changes.append(f"Health score decreased by {abs(diff)} point(s).")
        else:
            changes.append("Health score is unchanged.")

    current_issues = len(current_result.get("health", {}).get("issues", []))
    previous_issues = previous.get("issues")

    if previous_issues is not None:
        if current_issues < previous_issues:
            changes.append("Fewer issues were found than the previous scan.")
        elif current_issues > previous_issues:
            changes.append("More issues were found than the previous scan.")
        else:
            changes.append("Issue count is unchanged.")

    return {
        "has_previous": True,
        "previous_scan_time": previous.get("scan_time"),
        "summary": "Royal Guardian compared this scan with the previous one.",
        "changes": changes
    }