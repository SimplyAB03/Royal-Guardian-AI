COLORS = {
    "bg": "#0A0A0F",
    "panel": "#14141D",
    "panel_2": "#1A1A24",
    "gold": "#C9A227",
    "gold_bright": "#FFD700",
    "text": "#F3F4F6",
    "muted": "#8A8A9A",
    "green": "#22C55E",
    "warning": "#FBBF24",
    "critical": "#EF4444",
    "border": "#2A2413"
}

APP_STYLE = f"""
QWidget {{
    background: {COLORS["bg"]};
    color: {COLORS["text"]};
    font-family: Segoe UI;
}}

QFrame {{
    background: {COLORS["panel"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 16px;
}}

QPushButton {{
    background: {COLORS["gold"]};
    color: #0A0A0F;
    border: none;
    padding: 10px 16px;
    border-radius: 10px;
    font-weight: 700;
}}

QPushButton:hover {{
    background: {COLORS["gold_bright"]};
}}

QLabel#Title {{
    color: {COLORS["gold_bright"]};
    font-size: 26px;
    font-weight: 800;
}}

QLabel#Muted {{
    color: {COLORS["muted"]};
}}

QLabel#Score {{
    color: {COLORS["green"]};
    font-size: 76px;
    font-weight: 900;
}}
"""