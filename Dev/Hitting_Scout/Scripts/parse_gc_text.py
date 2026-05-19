#!/usr/bin/env python3
"""
parse_gc_text.py
Convert raw GameChanger get_page_text output → WCWAA play-by-play format.

Usage:
    python3 parse_gc_text.py <raw_text_file> <output_file>
Import:
    from parse_gc_text import parse_gc_raw
    text = parse_gc_raw(raw_text, game_url, game_date)
"""

import re, sys, os

# All known GC outcome keywords – longer phrases first (order matters for alternation)
OUTCOME_TYPES = [
    "Batter Interference", "Catcher's Interference",
    "Sacrifice Fly", "Sacrifice Bunt",
    "Fielder's Choice", "Double Play", "Hit By Pitch",
    "Infield Fly",
    "Ground Out", "Line Out", "Fly Out", "Pop Out",
    "Home Run", "Strikeout", "Triple", "Double", "Single",
    "Walk", "Error", "Balk",
]

# Outcome keyword followed by a non-lowercase char (digit, uppercase, end)
# This reliably identifies outcome-as-play-start vs. outcome word inside narrative
# ("doubles on" has 's' after Double → no match; "DoubleQCFL" has 'Q' → match)
_ALT = '|'.join(re.escape(o) for o in OUTCOME_TYPES)
OUTCOME_RE = re.compile(r'(' + _ALT + r')(?=[^a-z]|$)')

# Inning header: "Top 3rd - " or "Bottom 2nd - "
HDR_RE = re.compile(r'(Top|Bottom)\s+(\d+)(?:st|nd|rd|th)?\s*-\s*')

# Score line e.g. "QCFL 16 - LGCY 1"
SCORE_RE = re.compile(r'[A-Z]{2,6}\s+\d+\s*[-–]\s*[A-Z]{2,6}\s+\d+')
OUTS_RE  = re.compile(r'^(\d+\s+Outs?)')


def _ordinal(n):
    n = int(n)
    return {1:'1st', 2:'2nd', 3:'3rd'}.get(n, f'{n}th')


def _parse_rest(rest):
    """Given text after an outcome keyword, extract (outs_score, pitch_seq, narrative)."""
    rest = rest.strip()
    parts = []

    # Leading score?
    sm = SCORE_RE.match(rest)
    if sm:
        parts.append(sm.group(0).strip())
        rest = rest[sm.end():].strip()
        # Optional "| N Outs" right after score
        pm = re.match(r'\|\s*(\d+\s+Outs?)\s*', rest)
        if pm:
            parts.append(pm.group(1))
            rest = rest[pm.end():].strip()

    # Leading out count?
    om = OUTS_RE.match(rest)
    if om:
        parts.append(om.group(1).strip())
        rest = rest[om.end():].strip()

    outs_score = ' | '.join(parts)

    # Pitch seq ends at first period; narrative follows
    dot = rest.find('.')
    if dot != -1:
        pitch = rest[:dot+1].strip()
        narr  = rest[dot+1:].strip()
    else:
        pitch, narr = rest.strip(), ''

    return outs_score, pitch, narr


def _parse_body(body):
    """Split one inning's raw body text into list of (outcome, outs_score, pitch, narr)."""
    body = re.sub(r'[A-Z][a-zA-Z]*\s+[A-Z]\s+at\s+bat\s*', '', body).strip()
    if not body:
        return []

    positions = [(m.start(), m.end(), m.group(1)) for m in OUTCOME_RE.finditer(body)]
    plays = []
    for i, (s, e, outcome) in enumerate(positions):
        rest_end = positions[i+1][0] if i+1 < len(positions) else len(body)
        outs_score, pitch, narr = _parse_rest(body[e:rest_end])
        plays.append((outcome, outs_score, pitch, narr))
    return plays


# Known GC name corruptions — applied as text cleanup before parsing.
# Why: GameChanger occasionally renders special characters in player names
# (e.g., "$awyer" instead of "Sawyer"). We fix these at the raw-text level
# so downstream parsers and game files always have clean names.
GC_NAME_FIXES = {
    "$awyer": "Sawyer",
}

def parse_gc_raw(raw_text, game_url='', game_date=''):
    """Return WCWAA-formatted string from raw GC page text."""
    # Apply known GC name corruptions before any parsing
    for bad, good in GC_NAME_FIXES.items():
        raw_text = raw_text.replace(bad, good)

    lines = [f'GAME: {game_date} | {game_url}', '']

    # Isolate plays section
    m = re.search(r'Plays\s*All Plays', raw_text)
    body_start = m.end() if m else 0
    plays_text = raw_text[body_start:]
    # Strip filter UI text
    plays_text = re.sub(r'^Scoring PlaysOutsPlayer(?:Reverse Chronological|Chronological)?\s*', '', plays_text)

    # Find all inning header positions
    headers = list(HDR_RE.finditer(plays_text))

    for i, hdr in enumerate(headers):
        half, num = hdr.group(1), hdr.group(2)
        name_start = hdr.end()
        next_hdr   = headers[i+1].start() if i+1 < len(headers) else len(plays_text)
        chunk      = plays_text[name_start:next_hdr]  # "TeamName<plays>"

        # Team name ends at first outcome keyword OR at GC noise patterns that can
        # appear directly after the team name before any real play outcome:
        #   • "Runner Out"  — caught stealing / pickoff (not an OUTCOME_TYPE)
        #   • "Batter Out"  — batter interference
        #   • "N Out(s)"    — explicit out-count (e.g. "3 Outs", "1 Out")
        #   • "X Y at bat"  — current-batter indicator shown on partial innings
        #   • score line    — "CRSH 12 - SBCN 0"
        # Without this, these strings get swallowed into the team name and the
        # resulting malformed header can't be matched by INNING_RE, causing the
        # entire half-inning to be silently skipped.
        TEAM_NOISE_RE = re.compile(
            r'(?:'
            r'Runner\s+Out'                                  # caught stealing / pickoff
            r'|Batter\s+Out'                                 # batter interference
            r'|Inning\s+Ended'                               # half-inning ended by scorekeeper
            r'|\d+\s+Outs?(?=[^a-z]|$)'                     # "3 Outs" / "1 Out"
            r'|[A-Z][a-zA-Z]*\s+[A-Z]\s+at\s+bat'          # "Jack D at bat" or "J S at bat" current-batter
            r'|[A-Z]{2,6}\s+\d+\s*[-\u2013]\s*[A-Z]{2,6}\s+\d+'  # score abbreviation
            r')'
        )
        fo = OUTCOME_RE.search(chunk)
        fn = TEAM_NOISE_RE.search(chunk)
        # Use whichever boundary comes first
        if fo and fn:
            split_at = min(fo.start(), fn.start())
        elif fo:
            split_at = fo.start()
        elif fn:
            split_at = fn.start()
        else:
            split_at = None

        if split_at is not None:
            team_name = chunk[:split_at].strip()
            body      = chunk[split_at:]
        else:
            # No plays (walk-off end of game or truly empty)
            team_name = re.sub(r'\s*[A-Z][a-zA-Z]*\s+[A-Z]\s+at\s+bat.*$', '', chunk).strip()
            body = ''

        lines.append(f'==={half} {_ordinal(num)} - {team_name}===')

        for outcome, outs_score, pitch, narr in _parse_body(body):
            lines.append(f'{outcome} | {outs_score} | {pitch}')
            if narr:
                lines.append(narr)

    return '\n'.join(lines)


def verify_parse(raw_text, parsed_text):
    """
    Compare raw GC text vs parsed output and warn about:
      1. Inning headers present in raw but missing from parsed output
         (indicates a team-name noise pattern that TEAM_NOISE_RE didn't catch)

    Prints warnings to console; returns number of warnings found.
    """
    # Count (half, inning_num, team_name) in raw
    raw_headers = set()
    for m in HDR_RE.finditer(raw_text):
        half, num = m.group(1), m.group(2)
        # The team name in raw ends at the next HDR_RE match or at the first
        # outcome keyword — we just need the rough count per (half, num) pair
        raw_headers.add((half, int(num)))

    # Count headers in parsed output
    parsed_headers = set()
    for m in re.finditer(r'^===(Top|Bottom) (\d+)(?:st|nd|rd|th) -', parsed_text, re.MULTILINE):
        parsed_headers.add((m.group(1), int(m.group(2))))

    missing = raw_headers - parsed_headers
    warnings = 0
    for half, num in sorted(missing, key=lambda x: (x[1], x[0])):
        ordinals = {1:'1st',2:'2nd',3:'3rd'}
        ord_str  = ordinals.get(num, f'{num}th')
        print(f"  ⚠ PARSE: raw has '{half} {ord_str}' but it's missing from parsed output")
        warnings += 1

    return warnings


def _auto_filename(parsed_text, fallback='game'):
    """
    Derive standard filename from parsed output:
      {Mon}{DD}-{Away_Team}_vs_{Home_Team}-Reviewed.txt
    Falls back to <fallback>-Reviewed.txt if headers can't be found.
    """
    date_m = re.search(r'^GAME:\s*(.*?)\s*\|', parsed_text, re.MULTILINE)
    date_str = date_m.group(1).strip() if date_m else ''
    dm = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d+)', date_str)
    date_slug = f"{dm.group(1)}{dm.group(2).zfill(2)}" if dm else None

    away_m = re.search(r'^===Top 1st - (.+?)(?:\s*===|$)', parsed_text, re.MULTILINE)
    home_m = re.search(r'^===Bottom 1st - (.+?)(?:\s*===|$)', parsed_text, re.MULTILINE)

    away = re.sub(r'\s+', '_', (away_m.group(1).strip() if away_m else 'Unknown'))
    home = re.sub(r'\s+', '_', (home_m.group(1).strip() if home_m else 'Unknown'))

    if date_slug and away != 'Unknown':
        return f"{date_slug}-{away}_vs_{home}-Reviewed.txt"
    return f"{fallback}-Reviewed.txt"


def main():
    if len(sys.argv) < 2:
        print('Usage: parse_gc_text.py <raw_file> [output_file]')
        print('  If output_file is omitted, filename is auto-derived from game date and teams.')
        sys.exit(1)

    raw_file = sys.argv[1]
    with open(raw_file) as f:
        raw = f.read()

    url_m  = re.search(r'URL:\s*(https?://\S+)', raw)
    date_m = re.search(r'((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+)', raw)

    result = parse_gc_raw(
        raw,
        game_url  = url_m.group(1)  if url_m  else '',
        game_date = date_m.group(1) if date_m else '',
    )

    if len(sys.argv) >= 3:
        out_file = sys.argv[2]
    else:
        # Auto-derive filename from parsed content; place alongside the raw file
        raw_dir  = os.path.dirname(raw_file) or '.'
        out_file = os.path.join(raw_dir, _auto_filename(result, fallback=os.path.splitext(os.path.basename(raw_file))[0]))

    nw = verify_parse(raw, result)
    if nw == 0:
        print('  ✓ All inning headers accounted for')
    else:
        print(f'  ⚠ {nw} inning header(s) in raw not found in parsed output — review above')

    os.makedirs(os.path.dirname(out_file) or '.', exist_ok=True)
    with open(out_file, 'w') as f:
        f.write(result)
    print(f'Saved {len(result)} chars → {out_file}')


if __name__ == '__main__':
    main()
