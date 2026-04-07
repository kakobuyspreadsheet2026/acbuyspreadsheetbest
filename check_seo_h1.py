#!/usr/bin/env python3
"""
SEO guardrail: every public HTML page must have exactly one <h1>, and that heading must
contain the literal phrase "acbuy spreadsheet" exactly once (case-insensitive match).

Run after edits or locale builds:

  .venv/bin/python check_seo_h1.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
KEYWORD_LOWER = "acbuy spreadsheet"
SKIP_DIR_PARTS = frozenset({".venv", "node_modules"})


def check() -> list[str]:
    errors: list[str] = []
    for path in sorted(ROOT.rglob("*.html")):
        if any(p in SKIP_DIR_PARTS for p in path.parts):
            continue
        rel = path.relative_to(ROOT)
        html = path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "lxml")
        h1s = soup.find_all("h1")
        if len(h1s) != 1:
            errors.append(f"{rel}: expected exactly 1 <h1>, found {len(h1s)}")
            continue
        text = h1s[0].get_text(" ", strip=True)
        low = text.lower()
        n = low.count(KEYWORD_LOWER)
        if n != 1:
            errors.append(
                f"{rel}: expected exactly 1× {KEYWORD_LOWER!r} inside <h1>, found {n}. "
                f"H1 text (truncated): {text[:120]!r}"
            )
    return errors


def main() -> None:
    errors = check()
    if errors:
        print("check_seo_h1.py failed:\n", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        raise SystemExit(1)
    nfiles = sum(
        1
        for p in ROOT.rglob("*.html")
        if not any(x in SKIP_DIR_PARTS for x in p.parts)
    )
    print(
        f"OK: {nfiles} HTML file(s) — each has one <h1> with {KEYWORD_LOWER!r} exactly once."
    )


if __name__ == "__main__":
    main()
