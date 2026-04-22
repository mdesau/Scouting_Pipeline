"""
diag_schedule.py — Diagnostic: dump raw schedule JS output from GC

PURPOSE:
    The gc_scraper.py filenames are coming out wrong:
      - Missing date prefix (files start with '-' instead of 'Apr21-')
      - Some files named like '-Sat_vs_18.txt' instead of proper team names

    This script loads the Minors schedule page and prints exactly what
    the browser returns so we can see what the DOM looks like NOW and
    fix the SCHEDULE_JS and date/team parsing logic in gc_scraper.py.

USAGE:
    cd Scripts/
    python3 diag_schedule.py
"""

import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

SESSION_FILE = Path(__file__).parent / "gc_session.json"
GC_BASE_URL  = "https://web.gc.com"
MINORS_ORG   = "GdcFopba2PbE"

# ── Step 1: Broad sweep — dump ALL leaf-node text elements on the schedule page
# This shows us every text string the browser sees, so we can find the date format.
DUMP_ALL_TEXT_JS = """
() => {
    const results = [];
    document.body.querySelectorAll('*').forEach(el => {
        if (el.children.length === 0) {
            const t = el.innerText ? el.innerText.trim() : '';
            if (t.length > 0 && t.length < 200) {
                results.push({tag: el.tagName, cls: el.className.toString().slice(0,60), text: t});
            }
        }
    });
    return results;
}
"""

# ── Step 2: Focused sweep — just the <a> tags that link to game pages
DUMP_GAME_LINKS_JS = """
() => {
    const uuidRe = /\\/schedule\\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/;
    const results = [];
    document.body.querySelectorAll('a').forEach(el => {
        const m = el.href.match(uuidRe);
        if (m) {
            results.push({
                href: el.href,
                uuid: m[1],
                innerText: el.innerText.trim(),
                lines: el.innerText.trim().split('\\n').map(x=>x.trim()).filter(x=>x)
            });
        }
    });
    return results;
}
"""

def main():
    sched_url = f"{GC_BASE_URL}/organizations/{MINORS_ORG}/schedule"

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx     = browser.new_context(storage_state=str(SESSION_FILE))
        page    = ctx.new_page()

        print(f"\nLoading: {sched_url}")
        page.goto(sched_url, wait_until="networkidle", timeout=30_000)
        time.sleep(2)

        # ── Dump 1: All leaf-node text (look for date-like strings)
        print("\n" + "="*70)
        print("STEP 1 — Scanning for date-like text elements")
        print("="*70)
        all_text = page.evaluate(DUMP_ALL_TEXT_JS)
        date_keywords = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday",
                         "jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]
        for item in all_text:
            tl = item["text"].lower()
            if any(k in tl for k in date_keywords) and any(c.isdigit() for c in tl):
                print(f"  TAG={item['tag']:8s}  CLS={item['cls'][:40]:40s}  TEXT={item['text']!r}")

        # ── Dump 2: Game link cards — what text does each game card contain?
        print("\n" + "="*70)
        print("STEP 2 — Game link cards (first 10)")
        print("="*70)
        links = page.evaluate(DUMP_GAME_LINKS_JS)
        print(f"  Total game links found: {len(links)}")
        for lnk in links[:10]:
            print(f"\n  UUID:  {lnk['uuid']}")
            print(f"  Lines: {lnk['lines']}")
            print(f"  Raw:   {lnk['innerText']!r}")

        # ── Dump 3: Full raw output from the CURRENT SCHEDULE_JS (what gc_scraper actually uses)
        print("\n" + "="*70)
        print("STEP 3 — Output from current SCHEDULE_JS (first 5 games)")
        print("="*70)
        CURRENT_SCHEDULE_JS = """
() => {
    const uuidRe = /\\/schedule\\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/;
    const results = [];
    const seen = new Set();
    let currentDate = '';

    document.body.querySelectorAll('*').forEach(el => {
        if (el.children.length === 0 && el.innerText) {
            const t = el.innerText.trim();
            if (/^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday) \\w+ \\d+, \\d{4}$/.test(t)) {
                currentDate = t;
            }
        }
        if (el.tagName === 'A') {
            const m = el.href.match(uuidRe);
            if (m && !seen.has(m[1])) {
                seen.add(m[1]);
                const lines = el.innerText.trim().split('\\n').map(x => x.trim()).filter(x => x);
                results.push({
                    date: currentDate,
                    id: m[1],
                    text: lines.join(' | '),
                    final: lines.includes('FINAL')
                });
            }
        }
    });
    return results;
}
"""
        games = page.evaluate(CURRENT_SCHEDULE_JS) or []
        print(f"  Total games returned: {len(games)}")
        for g in games[:5]:
            print(f"\n  date={g['date']!r}  final={g['final']}")
            print(f"  text={g['text']!r}")

        browser.close()
    print("\nDone.")

if __name__ == "__main__":
    main()
