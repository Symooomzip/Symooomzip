"""Scrape the public contribution calendar and render it as an animated SVG.

No API token needed -- github.com/users/<user>/contributions is public HTML.
Cells fade in column by column (left to right), then the brightest ones pulse.
"""

import re
import sys

import requests
from bs4 import BeautifulSoup

from theme import BG, BORDER, LEVELS, MONO, MUTED, PANEL, STEEL_HI, TEXT, esc

USER = "Symooomzip"
OUT = "assets/contrib-heatmap.svg"

W, H = 860, 190
CELL, GAP = 11, 3
PITCH = CELL + GAP  # 14
PAD_X, TOP = 22, 58

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fetch():
    url = f"https://github.com/users/{USER}/contributions"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        date = td.get("data-date")
        if not date:
            continue
        days.append({
            "date": date,
            "level": int(td.get("data-level") or 0),
            "week": int(td.get("data-ix") or 0),
        })

    total = 0
    for s in soup.stripped_strings:
        m = re.search(r"([\d,]+)\s+contributions?\s+in the last year", s)
        if m:
            total = int(m.group(1).replace(",", ""))
            break
    return days, total


def build(days, total):
    # group into columns keyed by ISO week position, rows = weekday
    weeks = {}
    for d in days:
        y, m, dd = (int(x) for x in d["date"].split("-"))
        weeks.setdefault(d["week"], []).append(d)

    order = sorted(weeks)
    ncols = len(order)
    grid_w = ncols * PITCH - GAP
    x0 = (W - grid_w) // 2

    cells = []
    month_marks = []
    seen_month = set()

    for ci, wk in enumerate(order):
        col = sorted(weeks[wk], key=lambda d: d["date"])
        for d in col:
            y, m, dd = (int(x) for x in d["date"].split("-"))
            wd = _weekday(y, m, dd)  # 0 = Sunday, matches GitHub rows
            x = x0 + ci * PITCH
            yy = TOP + wd * PITCH
            lvl = d["level"]
            delay = round(ci * 0.022, 3)

            # month label at the first column of each month
            key = (y, m)
            if dd <= 7 and key not in seen_month:
                seen_month.add(key)
                month_marks.append((x, MONTHS[m - 1]))

            pulse = ""
            if lvl >= 3:
                pulse = (
                    f'<animate attributeName="opacity" values="1;0.55;1" '
                    f'dur="3.2s" begin="{delay + 1.6}s" repeatCount="indefinite"/>'
                )
            cells.append(
                f'<rect x="{x}" y="{yy}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{LEVELS[lvl]}" opacity="0">'
                f'<animate attributeName="opacity" from="0" to="1" dur="0.45s" '
                f'begin="{delay}s" fill="freeze"/>{pulse}'
                f"<title>{d['date']}</title></rect>"
            )

    labels = "".join(
        f'<text x="{x}" y="{TOP - 10}" fill="{MUTED}" font-family="{MONO}" '
        f'font-size="9" opacity="0">{mon}'
        f'<animate attributeName="opacity" from="0" to="1" dur="0.5s" '
        f'begin="0.35s" fill="freeze"/></text>'
        for x, mon in month_marks
    )

    legend_x = W - PAD_X - 5 * PITCH - 68
    legend_y = TOP + 7 * PITCH + 14
    legend = (
        f'<text x="{legend_x - 6}" y="{legend_y + 9}" text-anchor="end" '
        f'fill="{MUTED}" font-family="{MONO}" font-size="9">less</text>'
        + "".join(
            f'<rect x="{legend_x + i * PITCH}" y="{legend_y}" width="{CELL}" '
            f'height="{CELL}" rx="2.5" fill="{c}"/>'
            for i, c in enumerate(LEVELS)
        )
        + f'<text x="{legend_x + 5 * PITCH + 4}" y="{legend_y + 9}" '
        f'fill="{MUTED}" font-family="{MONO}" font-size="9">more</text>'
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub contribution heatmap">
  <defs>
    <linearGradient id="hg" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{STEEL_HI}"/>
      <stop offset="100%" stop-color="#d40cc4"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" rx="14" fill="{PANEL}" stroke="{BORDER}"/>
  <text x="{PAD_X}" y="30" fill="url(#hg)" font-family="{MONO}" font-size="13" font-weight="600">
    contributions
    <animate attributeName="opacity" from="0" to="1" dur="0.6s" fill="freeze"/>
  </text>
  <text x="{W - PAD_X}" y="30" text-anchor="end" fill="{TEXT}" font-family="{MONO}" font-size="11" opacity="0">
    {total} in the last year
    <animate attributeName="opacity" from="0" to="0.75" dur="0.6s" begin="0.2s" fill="freeze"/>
  </text>
  {labels}
  {"".join(cells)}
  {legend}
</svg>
"""


def _weekday(y, m, d):
    """Sunday-indexed weekday (0=Sun) via Zeller, no datetime import needed."""
    import datetime
    return (datetime.date(y, m, d).weekday() + 1) % 7


def main():
    days, total = fetch()
    if not days:
        print("no contribution cells found", file=sys.stderr)
        return 1
    svg = build(days, total)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT} ({len(days)} days, {total} contributions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
