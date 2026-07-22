"""Neofetch-style info card, hand-authored SVG with a staggered line reveal.

Each row slides in from the left and fades up, one after another, then the
prompt caret blinks forever.
"""

from theme import (BG, BORDER, LEVELS, MAGENTA, MONO, MUTED, PANEL, PURPLE,
                   STEEL_HI, TEXT, esc)

OUT = "assets/info-card.svg"
W, H = 490, 490

PAD = 26
LINE = 21.5
FS = 11.5

USER = "mohammed@github"

# (label, [value lines]) -- label "" means a continuation line
ROWS = [
    ("Location", ["Casablanca, Morocco"]),
    ("Role", ["Data Scientist / Data Engineer / AI Dev"]),
    ("Education", ["MSc Data Science & AI - Mundiapolis '26",
                   "BSc Full Stack Development '24"]),
    ("Core", ["Python . SQL . Java . JavaScript . C#"]),
    ("ML/DL", ["scikit-learn . XGBoost . PyTorch . TensorFlow"]),
    ("GenAI", ["LLM . RAG . LoRA/PEFT . LangChain . ChromaDB"]),
    ("Data Eng", ["ETL . Data Warehouse . SQL Server . Power BI"]),
    ("Web", ["React . Node.js . .NET . Flutter . REST"]),
    ("Shipped", ["churn XGBoost AUC 0.81 . CLV . RFM+K-Means",
                 "oil-spill segmentation IoU 0.88",
                 "YOLOv8 student behavior mAP50 0.80"]),
    ("Languages", ["Arabic native . English . French"]),
    ("Status", ["open to work"]),
]

LABEL_W = 92  # px reserved for the label column


def build():
    parts = []
    y = PAD + 20
    i = 0

    def delay(idx):
        return round(0.25 + idx * 0.11, 3)

    def reveal(idx, extra=""):
        d = delay(idx)
        return (
            f'<animate attributeName="opacity" from="0" to="1" dur="0.42s" '
            f'begin="{d}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="-10 0" to="0 0" dur="0.42s" begin="{d}s" fill="freeze"/>{extra}'
        )

    # header: user@github
    parts.append(
        f'<text x="{PAD}" y="{y}" font-family="{MONO}" font-size="{FS + 1.5}" '
        f'font-weight="600" fill="{STEEL_HI}" opacity="0" transform="translate(-10 0)">'
        f'{esc(USER)}{reveal(0)}</text>'
    )
    y += LINE * 0.85
    parts.append(
        f'<line x1="{PAD}" y1="{y}" x2="{PAD}" y2="{y}" stroke="{BORDER}" stroke-width="1">'
        f'<animate attributeName="x2" from="{PAD}" to="{W - PAD}" dur="0.5s" '
        f'begin="{delay(1)}s" fill="freeze"/></line>'
    )
    y += LINE * 0.95
    i = 2

    for label, values in ROWS:
        for j, val in enumerate(values):
            g = [f'<g opacity="0" transform="translate(-10 0)">{reveal(i)}']
            if j == 0:
                g.append(
                    f'<text x="{PAD}" y="{y}" font-family="{MONO}" font-size="{FS}" '
                    f'fill="{MAGENTA}" font-weight="600">{esc(label)}</text>'
                )
            accent = STEEL_HI if label == "Status" else TEXT
            g.append(
                f'<text x="{PAD + LABEL_W}" y="{y}" font-family="{MONO}" '
                f'font-size="{FS}" fill="{accent}">{esc(val)}</text>'
            )
            if label == "Status" and j == 0:
                # pulsing dot before "open to work"
                g.append(
                    f'<circle cx="{PAD + LABEL_W - 11}" cy="{y - 4}" r="3.2" fill="#3fd07a">'
                    f'<animate attributeName="opacity" values="1;0.25;1" dur="1.8s" '
                    f'begin="{delay(i)}s" repeatCount="indefinite"/></circle>'
                )
            g.append("</g>")
            parts.append("".join(g))
            y += LINE
            i += 1
        y += 2.5

    # neofetch-style palette strip
    y += 6
    sw, sh = 26, 9
    swatches = [LEVELS[1], LEVELS[2], LEVELS[3], LEVELS[4], PURPLE,
                MAGENTA, MUTED, STEEL_HI]
    for k, c in enumerate(swatches):
        parts.append(
            f'<rect x="{PAD + k * (sw + 4)}" y="{y}" width="{sw}" height="{sh}" '
            f'rx="2" fill="{c}" opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" dur="0.35s" '
            f'begin="{round(delay(i) + k * 0.05, 3)}s" fill="freeze"/></rect>'
        )

    # blinking prompt caret
    cy = y + 30
    parts.append(
        f'<text x="{PAD}" y="{cy}" font-family="{MONO}" font-size="{FS}" '
        f'fill="{MUTED}" opacity="0">$ <animate attributeName="opacity" from="0" '
        f'to="1" dur="0.3s" begin="{round(delay(i) + 0.5, 3)}s" fill="freeze"/></text>'
        f'<rect x="{PAD + 16}" y="{cy - 9}" width="7" height="11" fill="{MAGENTA}" opacity="0">'
        f'<animate attributeName="opacity" values="0;1;1;0;0" dur="1.1s" '
        f'begin="{round(delay(i) + 0.5, 3)}s" repeatCount="indefinite"/></rect>'
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Profile info card">
  <defs>
    <linearGradient id="cardEdge" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{MAGENTA}" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="{PURPLE}" stop-opacity="0.12"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" rx="14" fill="{PANEL}" stroke="url(#cardEdge)" stroke-width="1"/>
  {"".join(parts)}
</svg>
"""


def main():
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(build())
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
