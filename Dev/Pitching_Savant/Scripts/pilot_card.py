"""
pilot_card.py — Pitching Savant PDF Pilot
==========================================
Standalone proof-of-concept for the Baseball-Savant-style pitcher card layout.
Uses made-up (hard-coded) stats to demonstrate the visual design before any
real data parsing is wired up.

Layout decisions demonstrated here:
  - 4 cards per page (2 columns × 2 rows)
  - Each card: header block + gradient slider rows + informational rows
  - Gradient bar: dark-blue (poor) → light-blue → grey (avg) → pink → red (great)
  - Filled circle "bubble" at the percentile position with white text
  - "Low is good" stats (FPSH%, BB/9) have their percentile INVERTED so that a
    lower raw value earns a higher (redder) position on the bar
  - Informational stats (GB%, FB+LD%, 0BB) show a plain grey bar with the raw
    value only — no percentile ranking

Run:
    python3 pilot_card.py
Outputs:
    ../Output/pilot_pitcher_cards.pdf
"""

# ---------------------------------------------------------------------------
# Standard library imports
# ---------------------------------------------------------------------------
import os

# ---------------------------------------------------------------------------
# ReportLab imports — PDF drawing primitives
# ---------------------------------------------------------------------------
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

# ---------------------------------------------------------------------------
# DEBUG CONFIGURATION
# Flip these flags to True to print diagnostic info while developing.
# ---------------------------------------------------------------------------
DEBUG_LAYOUT   = False   # Print card bounding-box coordinates
DEBUG_STAT_ROW = False   # Print each row's computed x/y/width values

# ---------------------------------------------------------------------------
# DESIGN CONSTANTS
# These control the visual look of every card.  Change here; everything else
# follows automatically.
# ---------------------------------------------------------------------------

PAGE_W, PAGE_H = letter          # 612 × 792 points  (8.5" × 11")
MARGIN         = 0.45 * inch     # outer margin on all four sides
GUTTER         = 0.18 * inch     # gap between cards

COLS           = 2               # cards per row
ROWS           = 2               # rows per page
CARDS_PER_PAGE = COLS * ROWS     # 4

# Derived card dimensions (computed once so we never hard-code sizes)
CARD_W = (PAGE_W - 2 * MARGIN - (COLS - 1) * GUTTER) / COLS   # ≈ 261 pts
CARD_H = (PAGE_H - 2 * MARGIN - (ROWS - 1) * GUTTER) / ROWS   # ≈ 351 pts

HEADER_H       = 44              # pts — tall enough for name + sub-line
STAT_ROW_H     = 20              # pts per stat row
LABEL_W        = 58              # pts — left-side stat name column
VALUE_W        = 36              # pts — right-side raw-value column
BAR_H          = 9               # pts — height of the gradient bar
BUBBLE_R       = 7               # pts — radius of the percentile circle

# Typography
FONT_NAME      = "Helvetica"
FONT_BOLD      = "Helvetica-Bold"
FONT_SIZE_HDR  = 9.5
FONT_SIZE_SUBHDR = 7.5
FONT_SIZE_STAT = 7.5
FONT_SIZE_BUBBLE = 6.5
FONT_SIZE_AXIS = 8

# Colour palette (R, G, B in 0-1 range) — mirrors Baseball Savant
COL_DARK_BLUE  = colors.Color(0.09, 0.18, 0.55)   # 0–10th %ile
COL_LIGHT_BLUE = colors.Color(0.42, 0.62, 0.87)   # 11–40th %ile
COL_GREY       = colors.Color(0.78, 0.78, 0.78)   # 41–59th %ile
COL_PINK       = colors.Color(0.90, 0.55, 0.52)   # 60–89th %ile
COL_RED        = colors.Color(0.82, 0.11, 0.11)   # 90–100th %ile
COL_INFO_BAR   = colors.Color(0.70, 0.70, 0.70)   # informational rows
COL_CARD_BG    = colors.Color(0.97, 0.97, 0.97)   # light card background
COL_HEADER_BG  = colors.Color(0.15, 0.22, 0.40)   # dark navy header
COL_WHITE      = colors.white
COL_BLACK      = colors.black
COL_DIVIDER    = colors.Color(0.80, 0.80, 0.80)   # row separator

# ---------------------------------------------------------------------------
# STAT DIRECTION REFERENCE
# For most stats, higher raw value = better = red bar (low_is_good = False).
# Two stats are FLIPPED — a lower raw value is actually better for a pitcher,
# so we invert the percentile rank before drawing (rank 1st lowest → 100th %ile):
#
#   FPSH%  — first-pitch-strike-to-hit rate: lower = you're finishing batters
#   BB/9   — walk rate: lower = more command and control
#
# GB% and FB+LD% are both treated as "high is good" for this league —
# they are informational context, not a quality judgment, so both scale normally.
# ---------------------------------------------------------------------------

# Gradient band boundaries [percentile thresholds] and their colours
# Each tuple is (start_pct, end_pct, colour)
GRADIENT_BANDS = [
    (  0,  10, COL_DARK_BLUE),
    ( 10,  40, COL_LIGHT_BLUE),
    ( 40,  60, COL_GREY),
    ( 60,  90, COL_PINK),
    ( 90, 100, COL_RED),
]

# ---------------------------------------------------------------------------
# SAMPLE DATA — made-up pitcher cards to demonstrate the layout
# ---------------------------------------------------------------------------
# Each stat entry is a dict:
#   label      : display name shown on card
#   value      : formatted raw stat string  (e.g. ".642", "9.7", "5")
#   pct        : 0–100 integer percentile rank (None = informational only)
#   low_is_good: True = invert so lower raw value → higher percentile bar
# ---------------------------------------------------------------------------

SAMPLE_PITCHERS = [
    {
        "name":    "Oliver P.",
        "jersey":  "#8",
        "team":    "Braves-Rue",
        "gs":      4,
        "ip":      "8.1",
        "stats": [
            {"label": "S%",      "value": "64%",  "pct": 82,  "low_is_good": False},
            {"label": "FPS%",    "value": "57%",  "pct": 71,  "low_is_good": False},
            {"label": "Whiff%",  "value": "33%",  "pct": 55,  "low_is_good": False},
            {"label": "FPSO%",   "value": "50%",  "pct": 63,  "low_is_good": False},
            {"label": "K/9",     "value": "9.7",  "pct": 91,  "low_is_good": False},
            {"label": "K:BB",    "value": "3.2",  "pct": 74,  "low_is_good": False},
            {"label": "K%",      "value": "32%",  "pct": 85,  "low_is_good": False},
            {"label": "0BB",     "value": "5",    "pct": 78,  "low_is_good": False},
            {"label": "GB%",     "value": "41%",  "pct": 52,  "low_is_good": False},
            {"label": "FB+LD%",  "value": "44%",  "pct": 48,  "low_is_good": False},  # high is good — informational
            {"label": "IP",      "value": "8.1",  "pct": 80,  "low_is_good": False},
            {"label": "FPSH%",   "value": "13%",  "pct": 88,  "low_is_good": True},   # FLIP: low = better
            {"label": "BB/9",    "value": "2.7",  "pct": 72,  "low_is_good": True},
        ],
    },
    {
        "name":    "Marcus R.",
        "jersey":  "#22",
        "team":    "Braves-Rue",
        "gs":      3,
        "ip":      "5.2",
        "stats": [
            {"label": "S%",      "value": "54%",  "pct": 38,  "low_is_good": False},
            {"label": "FPS%",    "value": "46%",  "pct": 28,  "low_is_good": False},
            {"label": "Whiff%",  "value": "20%",  "pct": 22,  "low_is_good": False},
            {"label": "FPSO%",   "value": "33%",  "pct": 31,  "low_is_good": False},
            {"label": "K/9",     "value": "5.1",  "pct": 34,  "low_is_good": False},
            {"label": "K:BB",    "value": "1.3",  "pct": 18,  "low_is_good": False},
            {"label": "K%",      "value": "17%",  "pct": 29,  "low_is_good": False},
            {"label": "0BB",     "value": "2",    "pct": 22,  "low_is_good": False},
            {"label": "GB%",     "value": "55%",  "pct": 68,  "low_is_good": False},
            {"label": "FB+LD%",  "value": "32%",  "pct": 30,  "low_is_good": False},  # high is good — informational
            {"label": "IP",      "value": "5.2",  "pct": 40,  "low_is_good": False},
            {"label": "FPSH%",   "value": "33%",  "pct": 22,  "low_is_good": True},   # FLIP: low = better
            {"label": "BB/9",    "value": "6.4",  "pct": 24,  "low_is_good": True},
        ],
    },
    {
        "name":    "Cole S.",
        "jersey":  "#11",
        "team":    "Padres-Schick",
        "gs":      5,
        "ip":      "11.0",
        "stats": [
            {"label": "S%",      "value": "70%",  "pct": 95,  "low_is_good": False},
            {"label": "FPS%",    "value": "65%",  "pct": 93,  "low_is_good": False},
            {"label": "Whiff%",  "value": "42%",  "pct": 90,  "low_is_good": False},
            {"label": "FPSO%",   "value": "60%",  "pct": 87,  "low_is_good": False},
            {"label": "K/9",     "value": "11.5", "pct": 97,  "low_is_good": False},
            {"label": "K:BB",    "value": "5.8",  "pct": 94,  "low_is_good": False},
            {"label": "K%",      "value": "40%",  "pct": 91,  "low_is_good": False},
            {"label": "0BB",     "value": "8",    "pct": 95,  "low_is_good": False},
            {"label": "GB%",     "value": "38%",  "pct": 44,  "low_is_good": False},
            {"label": "FB+LD%",  "value": "48%",  "pct": 56,  "low_is_good": False},  # high is good — informational
            {"label": "IP",      "value": "11.0", "pct": 96,  "low_is_good": False},
            {"label": "FPSH%",   "value": "7%",   "pct": 96,  "low_is_good": True},   # FLIP: low = better
            {"label": "BB/9",    "value": "1.6",  "pct": 92,  "low_is_good": True},
        ],
    },
    {
        "name":    "Jaylen T.",
        "jersey":  "#3",
        "team":    "Padres-Schick",
        "gs":      2,
        "ip":      "3.1",
        "stats": [
            {"label": "S%",      "value": "50%",  "pct": 5,   "low_is_good": False},
            {"label": "FPS%",    "value": "40%",  "pct": 8,   "low_is_good": False},
            {"label": "Whiff%",  "value": "10%",  "pct": 7,   "low_is_good": False},
            {"label": "FPSO%",   "value": "25%",  "pct": 12,  "low_is_good": False},
            {"label": "K/9",     "value": "3.2",  "pct": 9,   "low_is_good": False},
            {"label": "K:BB",    "value": "0.5",  "pct": 4,   "low_is_good": False},
            {"label": "K%",      "value": "11%",  "pct": 6,   "low_is_good": False},
            {"label": "0BB",     "value": "1",    "pct": 8,   "low_is_good": False},
            {"label": "GB%",     "value": "48%",  "pct": 55,  "low_is_good": False},
            {"label": "FB+LD%",  "value": "40%",  "pct": 45,  "low_is_good": False},  # high is good — informational
            {"label": "IP",      "value": "3.1",  "pct": 12,  "low_is_good": False},
            {"label": "FPSH%",   "value": "50%",  "pct": 6,   "low_is_good": True},   # FLIP: low = better
            {"label": "BB/9",    "value": "10.8", "pct": 5,   "low_is_good": True},
        ],
    },
]


# ---------------------------------------------------------------------------
# HELPER: percentile → fill colour
# ---------------------------------------------------------------------------

def pct_to_color(pct: int) -> colors.Color:
    """
    Map a 0–100 integer percentile rank to one of the five gradient colours.

    Why five bands?  Mirrors the Baseball Savant visual language that users
    already understand: blue = struggling, grey = average, red = elite.

    Args:
        pct: Integer 0–100 representing the percentile rank.

    Returns:
        A ReportLab Color object for that band.
    """
    if pct >= 90:
        return COL_RED
    elif pct >= 60:
        return COL_PINK
    elif pct >= 40:
        return COL_GREY
    elif pct >= 10:
        return COL_LIGHT_BLUE
    else:
        return COL_DARK_BLUE


# ---------------------------------------------------------------------------
# DRAW: gradient background bar
# ---------------------------------------------------------------------------

def draw_gradient_bar(c: canvas.Canvas, x: float, y: float, bar_w: float,
                      pct: int):
    """
    Draw a single solid-colour bar whose colour matches the percentile band.
    This is simpler and more readable than a 5-segment gradient — the colour
    immediately tells you which tier the pitcher is in without needing to read
    where the bubble lands on a rainbow track.

    Args:
        c:     ReportLab canvas.
        x:     Left edge of the bar in points.
        y:     Vertical centre of the bar in points (we draw ± BAR_H/2).
        bar_w: Total pixel width available for the bar.
        pct:   Percentile rank (0–100) — determines the fill colour.
    """
    bar_y   = y - BAR_H / 2
    bar_col = pct_to_color(pct)

    # The bar only extends as far as the percentile position — no trailing
    # grey track beyond the bubble.  A short bar (e.g. 10th %ile) is visually
    # short; a long bar (e.g. 95th %ile) nearly fills the column.
    fill_w = bar_w * (pct / 100)
    c.setFillColor(bar_col)
    c.rect(x, bar_y, fill_w, BAR_H, stroke=0, fill=1)

    if DEBUG_STAT_ROW:
        print(f"  solid bar  pct={pct}  x={x:.1f}  y={y:.1f}  fill_w={fill_w:.1f}")


# ---------------------------------------------------------------------------
# DRAW: percentile bubble on bar
# ---------------------------------------------------------------------------

def draw_bubble(c: canvas.Canvas, x: float, y: float, bar_w: float, pct: int):
    """
    Draw the filled circle at the correct position along the bar, with the
    percentile number in white text inside.

    The bubble colour matches the bar colour (same percentile band), so the
    circle stands out as a darker/same-hue dot on top of the filled bar.

    Args:
        c:     ReportLab canvas.
        x:     Left edge of the bar.
        y:     Vertical centre of the bar.
        bar_w: Total bar width in points.
        pct:   0–100 percentile rank to display and position.
    """
    bubble_x   = x + bar_w * (pct / 100)
    bubble_col = pct_to_color(pct)

    # Filled circle
    c.setFillColor(bubble_col)
    c.setStrokeColor(COL_WHITE)
    c.setLineWidth(0.8)
    c.circle(bubble_x, y, BUBBLE_R, stroke=1, fill=1)

    # Percentile number inside the bubble
    c.setFillColor(COL_WHITE)
    c.setFont(FONT_BOLD, FONT_SIZE_BUBBLE)
    c.drawCentredString(bubble_x, y - FONT_SIZE_BUBBLE / 2 + 1, str(pct))

    if DEBUG_STAT_ROW:
        print(f"  bubble  pct={pct}  x={bubble_x:.1f}")


# ---------------------------------------------------------------------------
# DRAW: one stat row (slider or informational)
# ---------------------------------------------------------------------------

def draw_stat_row(c: canvas.Canvas, card_x: float, row_y: float,
                  card_inner_w: float, stat: dict, row_idx: int):
    """
    Draw one complete stat row inside a card.

    Layout per row (left→right):
      [LABEL_W] stat name  |  [bar area]  |  [VALUE_W] raw value

    For informational rows (pct is None), we draw a plain grey dashed line
    with the raw value — no gradient, no bubble.

    Args:
        c:            ReportLab canvas.
        card_x:       Left edge of the card's inner content area.
        row_y:        Y coordinate of the vertical centre of this row.
        card_inner_w: Usable card width (card width minus left/right padding).
        stat:         Dict with keys: label, value, pct, low_is_good.
        row_idx:      0-based row index (used to draw alternating row lines).
    """
    label      = stat["label"]
    value      = stat["value"]
    pct        = stat["pct"]
    low_is_good = stat["low_is_good"]

    # --- Row divider (subtle horizontal line between rows) ---
    if row_idx > 0:
        c.setStrokeColor(COL_DIVIDER)
        c.setLineWidth(0.3)
        c.line(card_x, row_y + STAT_ROW_H / 2,
               card_x + card_inner_w, row_y + STAT_ROW_H / 2)

    bar_x     = card_x + LABEL_W
    bar_w     = card_inner_w - LABEL_W - VALUE_W
    bar_y_ctr = row_y

    # --- Stat label (left column) ---
    c.setFillColor(COL_BLACK)
    c.setFont(FONT_NAME, FONT_SIZE_STAT)
    # Low-is-good stats are grouped together in the card layout (no arrow needed)
    c.drawString(card_x, bar_y_ctr - FONT_SIZE_STAT / 2 + 1, label)

    # All stats get a solid colour bar + bubble — pct=None stats use grey (50th)
    effective_pct = pct if pct is not None else 50
    draw_gradient_bar(c, bar_x, bar_y_ctr, bar_w, effective_pct)
    draw_bubble(c, bar_x, bar_y_ctr, bar_w, effective_pct)

    # --- Raw value (right column) ---
    c.setFillColor(COL_BLACK)
    c.setFont(FONT_BOLD, FONT_SIZE_STAT)
    val_x = card_x + card_inner_w - VALUE_W + 3
    c.drawString(val_x, bar_y_ctr - FONT_SIZE_STAT / 2 + 1, value)


# ---------------------------------------------------------------------------
# DRAW: axis labels (POOR / AVERAGE / GREAT) — drawn once above the first row
# ---------------------------------------------------------------------------

def draw_axis_labels(c: canvas.Canvas, card_x: float, axis_y: float,
                     card_inner_w: float):
    """
    Draw the POOR / AVERAGE / GREAT labels above the stat rows, mimicking
    the Baseball Savant axis header.

    Args:
        c:            ReportLab canvas.
        card_x:       Left edge of the inner content area.
        axis_y:       Y coordinate for the axis label text baseline.
        card_inner_w: Usable card width.
    """
    bar_x = card_x + LABEL_W
    bar_w = card_inner_w - LABEL_W - VALUE_W

    c.setFont(FONT_NAME, FONT_SIZE_AXIS)
    c.setFillColor(COL_DARK_BLUE)
    c.drawString(bar_x, axis_y, "POOR")

    c.setFillColor(COL_GREY)
    c.drawCentredString(bar_x + bar_w / 2, axis_y, "AVG")

    c.setFillColor(COL_RED)
    c.drawRightString(bar_x + bar_w, axis_y, "GREAT")


# ---------------------------------------------------------------------------
# DRAW: one full pitcher card
# ---------------------------------------------------------------------------

def draw_pitcher_card(c: canvas.Canvas, card_x: float, card_y: float,
                      pitcher: dict):
    """
    Draw a complete pitcher card (header + all stat rows) at the given
    bottom-left position.

    Args:
        c:       ReportLab canvas.
        card_x:  Left edge of this card in page coordinates.
        card_y:  Bottom edge of this card in page coordinates.
        pitcher: Dict with keys: name, jersey, team, gs, ip, stats.
    """
    PADDING = 8   # inner horizontal padding on each side

    if DEBUG_LAYOUT:
        print(f"Card '{pitcher['name']}'  x={card_x:.1f}  y={card_y:.1f}  "
              f"w={CARD_W:.1f}  h={CARD_H:.1f}")

    # --- Card background ---
    c.setFillColor(COL_CARD_BG)
    c.setStrokeColor(COL_DIVIDER)
    c.setLineWidth(0.5)
    c.roundRect(card_x, card_y, CARD_W, CARD_H, 4, stroke=1, fill=1)

    # --- Header block (dark navy background) ---
    c.setFillColor(COL_HEADER_BG)
    c.roundRect(card_x, card_y + CARD_H - HEADER_H,
                CARD_W, HEADER_H, 4, stroke=0, fill=1)
    # Cover bottom corners of the header so it looks flush
    c.rect(card_x, card_y + CARD_H - HEADER_H,
           CARD_W, HEADER_H / 2, stroke=0, fill=1)

    # Player name (large, bold, white)
    c.setFillColor(COL_WHITE)
    c.setFont(FONT_BOLD, FONT_SIZE_HDR)
    name_str = f"{pitcher['name']}  {pitcher['jersey']}"
    c.drawString(card_x + PADDING,
                 card_y + CARD_H - HEADER_H + HEADER_H * 0.55,
                 name_str)

    # Sub-header: team | GS | IP
    c.setFont(FONT_NAME, FONT_SIZE_SUBHDR)
    sub_str = f"{pitcher['team']}   GS: {pitcher['gs']}   IP: {pitcher['ip']}"
    c.drawString(card_x + PADDING,
                 card_y + CARD_H - HEADER_H + HEADER_H * 0.15,
                 sub_str)

    # --- Axis label row (POOR / AVG / GREAT) ---
    inner_x = card_x + PADDING
    inner_w = CARD_W - 2 * PADDING
    axis_y  = card_y + CARD_H - HEADER_H - 10
    draw_axis_labels(c, inner_x, axis_y, inner_w)

    # --- Stat rows ---
    # Start just below the axis labels; rows stack downward
    first_row_y = axis_y - STAT_ROW_H * 0.8

    for idx, stat in enumerate(pitcher["stats"]):
        row_y = first_row_y - idx * STAT_ROW_H
        draw_stat_row(c, inner_x, row_y, inner_w, stat, idx)


# ---------------------------------------------------------------------------
# MAIN: layout all cards across pages and save
# ---------------------------------------------------------------------------

def generate_pilot_pdf(output_path: str):
    """
    Generate the pilot PDF with all SAMPLE_PITCHERS.

    Cards are laid out in a 2-column × 2-row grid.  A new page is started
    whenever all 4 slots on the current page are filled.

    Args:
        output_path: Absolute path where the PDF will be written.
    """
    c = canvas.Canvas(output_path, pagesize=letter)
    c.setTitle("WCWAA Pitching Savant — Pilot 2026")

    # Pre-compute card origin positions for each of the 4 slots on a page.
    # ReportLab's origin is bottom-left, so row 0 = top of page.
    #
    # Slot layout (col, row) → (0,0)=top-left, (1,0)=top-right,
    #                           (0,1)=bot-left, (1,1)=bot-right
    def card_origin(slot_idx: int):
        """Return (x, y) bottom-left corner of the given slot index (0–3)."""
        col = slot_idx % COLS
        row = slot_idx // COLS
        x = MARGIN + col * (CARD_W + GUTTER)
        # Row 0 is near the top: bottom edge = PAGE_H - MARGIN - CARD_H
        y = PAGE_H - MARGIN - (row + 1) * CARD_H - row * GUTTER
        return x, y

    for i, pitcher in enumerate(SAMPLE_PITCHERS):
        slot = i % CARDS_PER_PAGE
        if slot == 0 and i > 0:
            c.showPage()   # start a new page every CARDS_PER_PAGE pitchers

        cx, cy = card_origin(slot)
        draw_pitcher_card(c, cx, cy, pitcher)

    c.save()
    print(f"✅  Pilot PDF written → {output_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Output directory is one level up from Scripts/
    script_dir  = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    out_path    = os.path.join(project_dir, "Output", "pilot_pitcher_cards.pdf")

    generate_pilot_pdf(out_path)
