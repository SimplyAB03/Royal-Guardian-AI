from pathlib import Path
from datetime import datetime

def generate_html_report(scan):
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    filename = f"royal_guardian_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    path = reports_dir / filename

    d = scan["diagnostics"]
    h = scan["health"]

    issues_html = ""
    if not h["issues"]:
        issues_html = "<p><b>Status:</b> No major issues detected.</p>"
    else:
        for i, issue in enumerate(h["issues"], 1):
            issues_html += f"""
            <div class="issue">
                <h3>Priority {i}: {issue['title']}</h3>
                <p><b>Severity:</b> {issue['severity'].upper()}</p>
                <p><b>Simple Explanation:</b> {issue['explanation']}</p>
                <p><b>Recommended Action:</b> {issue['recommendation']}</p>
            </div>
            """

    drives_html = ""
    for drive in d.get("drives", []):
        drives_html += f"""
        <tr>
            <td>{drive['device']}</td>
            <td>{drive['filesystem']}</td>
            <td>{drive['total_gb']} GB</td>
            <td>{drive['free_gb']} GB</td>
            <td>{drive['used_percent']}%</td>
        </tr>
        """

    html = f"""
    <html>
    <head>
    <title>Royal Guardian Report</title>
    <style>
        body {{ font-family: Segoe UI, Arial; background:#0A0A0F; color:#F0E6C8; padding:30px; }}
        h1 {{ color:#FFD700; }}
        h2 {{ color:#C9A227; border-bottom:1px solid #3A2E10; padding-bottom:6px; }}
        .card {{ background:#12121A; border:1px solid #1E1E2E; border-radius:12px; padding:18px; margin-bottom:16px; }}
        .score {{ font-size:52px; color:#22C55E; font-weight:bold; }}
        .issue {{ border-left:4px solid #EAB308; padding-left:14px; margin-bottom:14px; }}
        table {{ width:100%; border-collapse:collapse; }}
        td, th {{ border-bottom:1px solid #1E1E2E; padding:8px; text-align:left; }}
        th {{ color:#FFD700; }}
    </style>
    </head>
    <body>
        <h1>⚜ Royal Guardian Diagnostic Report</h1>
        <p>Generated: {scan["scan_time"]}</p>

        <div class="card">
            <h2>Overall Health</h2>
            <div class="score">{h["score"]}/100</div>
        </div>

        <div class="card">
            <h2>System Summary</h2>
            <p><b>Computer:</b> {d["computer_name"]}</p>
            <p><b>Windows:</b> {d["windows"]}</p>
            <p><b>Last Boot:</b> {d["last_boot"]}</p>
            <p><b>Uptime:</b> {d["uptime_days"]} days</p>
            <p><b>CPU Usage:</b> {d["cpu_percent"]}%</p>
            <p><b>RAM Usage:</b> {d["ram_percent"]}%</p>
        </div>

        <div class="card">
            <h2>Triage Priorities</h2>
            {issues_html}
        </div>

        <div class="card">
            <h2>Storage Devices</h2>
            <table>
                <tr><th>Drive</th><th>File System</th><th>Total</th><th>Free</th><th>Used</th></tr>
                {drives_html}
            </table>
        </div>
    </body>
    </html>
    """

    path.write_text(html, encoding="utf-8")
    return str(path)