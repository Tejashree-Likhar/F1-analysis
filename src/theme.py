"""F1-inspired visual theme: team colors + shared CSS for the Streamlit app."""

TEAM_COLORS = {
    "Mercedes": "#00D7B6",
    "Ferrari": "#E8002D",
    "McLaren": "#FF8000",
    "Red Bull": "#1E41FF",
    "Alpine": "#00A1E8",
    "Racing Bulls": "#6C98FF",
    "Haas": "#B6BABD",
    "Williams": "#00A0DE",
    "Audi": "#D40000",
    "Aston Martin": "#00594F",
    "Cadillac": "#8A8D8F",
}

BG_DARK = "#0B0E14"
BG_PANEL = "#141922"
ACCENT_RED = "#E10600"
TEXT_LIGHT = "#F4F4F4"
TEXT_MUTED = "#9AA3AF"

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Titillium+Web:wght@400;600;700;900&family=Orbitron:wght@500;700;900&display=swap');

html, body, [class*="css"] {{
    font-family: 'Titillium Web', sans-serif;
}}

.stApp {{
    background: radial-gradient(circle at 15% 0%, #1a1024 0%, {BG_DARK} 45%, #05070a 100%);
    color: {TEXT_LIGHT};
}}

section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0d0f14 0%, #05070a 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}}

h1, h2, h3 {{
    font-family: 'Orbitron', sans-serif;
    letter-spacing: 0.5px;
}}

.f1-hero {{
    background: linear-gradient(120deg, rgba(225,6,0,0.18), rgba(0,0,0,0) 60%),
                linear-gradient(135deg, #14181f 0%, #0a0c10 100%);
    border: 1px solid rgba(225,6,0,0.35);
    border-radius: 18px;
    padding: 28px 34px;
    margin-bottom: 18px;
    position: relative;
    overflow: hidden;
}}
.f1-hero::before {{
    content: "";
    position: absolute;
    top: -40%; right: -10%;
    width: 260px; height: 260px;
    background: radial-gradient(circle, rgba(225,6,0,0.35), transparent 70%);
    filter: blur(10px);
}}
.f1-hero h1 {{
    font-size: 2.1rem;
    margin: 0 0 6px 0;
    color: {TEXT_LIGHT};
}}
.f1-hero p {{
    color: {TEXT_MUTED};
    font-size: 1.02rem;
    margin: 0;
}}
.f1-stripe {{
    height: 4px;
    width: 64px;
    background: {ACCENT_RED};
    border-radius: 2px;
    margin-bottom: 14px;
}}

.metric-card {{
    background: {BG_PANEL};
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 16px 18px;
    text-align: left;
}}
.metric-card .label {{
    color: {TEXT_MUTED};
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
.metric-card .value {{
    font-family: 'Orbitron', sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: {TEXT_LIGHT};
}}

.driver-chip {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 600;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
}}

div[data-testid="stMetric"] {{
    background: {BG_PANEL};
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 12px 16px;
}}

.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
}}
.stTabs [data-baseweb="tab"] {{
    background: {BG_PANEL};
    border-radius: 10px 10px 0 0;
    padding: 10px 18px;
    color: {TEXT_MUTED};
}}
.stTabs [aria-selected="true"] {{
    color: {TEXT_LIGHT} !important;
    background: linear-gradient(180deg, rgba(225,6,0,0.25), {BG_PANEL}) !important;
    border-bottom: 2px solid {ACCENT_RED};
}}

.footer-note {{
    color: {TEXT_MUTED};
    font-size: 0.78rem;
    margin-top: 30px;
    border-top: 1px solid rgba(255,255,255,0.07);
    padding-top: 14px;
}}

.checkered {{
    background-image:
        linear-gradient(45deg, #000 25%, transparent 25%),
        linear-gradient(-45deg, #000 25%, transparent 25%),
        linear-gradient(45deg, transparent 75%, #000 75%),
        linear-gradient(-45deg, transparent 75%, #000 75%);
    background-size: 14px 14px;
    background-position: 0 0, 0 7px, 7px -7px, -7px 0px;
    height: 6px;
    opacity: 0.5;
    border-radius: 4px;
    margin: 6px 0 22px 0;
}}
</style>
"""


def team_color(team: str) -> str:
    return TEAM_COLORS.get(team, "#888888")
