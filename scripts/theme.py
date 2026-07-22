"""Shared palette + SVG helpers.

Colors mirror the portfolio site (symo-portfolio.pages.dev) so the profile
and the site read as one brand.
"""

BG = "#121414"
PANEL = "#171a1b"
BORDER = "#242829"
TEXT = "#d7e2ea"
MUTED = "#646973"
STEEL_HI = "#bbccd7"
MAGENTA = "#b600a8"
PURPLE = "#7621b0"

# contribution levels 0..4, magenta -> purple ramp instead of GitHub green
LEVELS = ["#1b1f20", "#3d1148", "#5c1a7d", "#8f18a0", "#d40cc4"]

MONO = "ui-monospace,'SF Mono',SFMono-Regular,'Cascadia Mono',Menlo,Consolas,monospace"


def esc(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
