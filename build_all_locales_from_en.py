#!/usr/bin/env python3
"""
Rebuild all locale pages (de, es, pt, pl) from English HTML in the repo root.
- index: uses build_index_from_en (German copy + FAQ; ES/PT/PL mirror EN + localized FAQ JSON-LD).
- Other pages: same DOM as English; URLs/canonicals/hreflang/breadcrumbs/Article JSON-LD localized;
  visible copy stays English with <html lang="en"> for non-DE subpages and for ES/PT/PL.
- German subpages: English body + lang="en"; shared German labels in header/footer where listed.

Run: python3 build_all_locales_from_en.py
"""

from __future__ import annotations

import re
from pathlib import Path

import build_index_from_en as idx

ROOT = Path(__file__).resolve().parent

PAGES = [
    "guides.html",
    "news.html",
    "contact.html",
    "spreadsheet.html",
    "acbuy-spreadsheet-qc.html",
    "acbuy-spreadsheet-shipping-weight.html",
    "acbuy-spreadsheet-dead-links.html",
]

# Longest first — full acbuyai URLs that appear in EN sources (avoid breaking already-localized links)
FULL_ACBUY_URLS: tuple[str, ...] = (
    "https://acbuyai.com/acbuy-spreadsheet-shipping-weight.html",
    "https://acbuyai.com/acbuy-spreadsheet-dead-links.html",
    "https://acbuyai.com/acbuy-spreadsheet-qc.html",
    "https://acbuyai.com/spreadsheet.html",
    "https://acbuyai.com/contact.html",
    "https://acbuyai.com/news.html",
    "https://acbuyai.com/guides.html",
)

# Shared DE chrome (body copy stays English; nav/chrome only)
DE_CHROME: tuple[tuple[str, str], ...] = (
    ("Skip to content", "Zum Inhalt springen"),
    ('aria-label="Primary"', 'aria-label="Hauptnavigation"'),
    ("Categories", "Kategorien"),
    ("Open hub", "Hub öffnen"),
    ('aria-label="Language selector"', 'aria-label="Sprache"'),
    ('aria-label="Choose language"', 'aria-label="Sprache wählen"'),
    ('<a href="/">Home</a>', '<a href="/de/">Startseite</a>'),
    (">Guides</a>", ">Anleitungen</a>"),
    (">Contact</a>", ">Kontakt</a>"),
)


def hreflang_block(basename: str) -> str:
    base = "https://acbuyai.com"
    if basename == "index.html":
        paths = {
            "en": "/",
            "pl": "/pl/",
            "pt": "/pt/",
            "es": "/es/",
            "de": "/de/",
            "x": "/",
        }
    else:
        paths = {
            "en": f"/{basename}",
            "pl": f"/pl/{basename}",
            "pt": f"/pt/{basename}",
            "es": f"/es/{basename}",
            "de": f"/de/{basename}",
            "x": f"/{basename}",
        }
    lines = [
        f'    <link rel="alternate" hreflang="en" href="{base}{paths["en"]}" />',
        f'    <link rel="alternate" hreflang="pl" href="{base}{paths["pl"]}" />',
        f'    <link rel="alternate" hreflang="pt-PT" href="{base}{paths["pt"]}" />',
        f'    <link rel="alternate" hreflang="es" href="{base}{paths["es"]}" />',
        f'    <link rel="alternate" hreflang="de" href="{base}{paths["de"]}" />',
        f'    <link rel="alternate" hreflang="x-default" href="{base}{paths["x"]}" />',
    ]
    return "\n".join(lines)


HREFLANG_RE = re.compile(
    r"\s*<link rel=\"alternate\" hreflang=\"en\"[^>]+>\s*\n"
    r"\s*<link rel=\"alternate\" hreflang=\"pl\"[^>]+>\s*\n"
    r"\s*<link rel=\"alternate\" hreflang=\"pt-PT\"[^>]+>\s*\n"
    r"\s*<link rel=\"alternate\" hreflang=\"es\"[^>]+>\s*\n"
    r"\s*<link rel=\"alternate\" hreflang=\"de\"[^>]+>\s*\n"
    r"\s*<link rel=\"alternate\" hreflang=\"x-default\"[^>]+>",
)


def swap_hreflang(html: str, basename: str) -> str:
    return HREFLANG_RE.sub("\n" + hreflang_block(basename), html, count=1)


def lang_menu_inner(basename: str, active: str) -> str:
    """EN / PL / PT / ES / DE links for the globe menu."""
    if basename == "index.html":
        hrefs = {
            "en": "/",
            "pl": "/pl/",
            "pt": "/pt/",
            "es": "/es/",
            "de": "/de/",
        }
    else:
        hrefs = {
            "en": f"/{basename}",
            "pl": f"/pl/{basename}",
            "pt": f"/pt/{basename}",
            "es": f"/es/{basename}",
            "de": f"/de/{basename}",
        }
    codes = ("en", "pl", "pt", "es", "de")
    lang_attr = {"en": "", "pl": ' lang="pl"', "pt": ' lang="pt-PT"', "es": ' lang="es"', "de": ' lang="de"'}
    lines = []
    for code in codes:
        cur = ' aria-current="page"' if code == active else ""
        lines.append(f'              <a href="{hrefs[code]}"{lang_attr[code]}{cur}>{code.upper()}</a>')
    return "\n".join(lines)


LANG_MENU_RE = re.compile(
    r'<div class="lang-menu" role="menu">\s*.*?</div>\s*(?=\s*</nav>)',
    re.DOTALL,
)


def swap_lang_menu_page(html: str, basename: str, active: str) -> str:
    m = LANG_MENU_RE.search(html)
    if not m:
        raise RuntimeError(f"lang-menu not found in {basename}")
    inner = lang_menu_inner(basename, active)
    return html[: m.start()] + f'<div class="lang-menu" role="menu">\n{inner}\n            </div>\n          ' + html[m.end() :]


def mechanical_subpage(html: str, lang: str, basename: str) -> str:
    html = html.replace('href="styles.css"', 'href="../styles.css"')
    html = html.replace('href="images/', 'href="../images/')
    html = html.replace('src="images/', 'src="../images/')
    html = html.replace('<a class="brand" href="/"', f'<a class="brand" href="/{lang}/"')
    html = html.replace('<html lang="en">', f'<html lang="{lang}">', 1)
    return html


def localize_acbuy_urls(html: str, lang: str) -> str:
    """After hreflang swap: replace EN acbuyai URLs with /{lang}/… versions."""
    if lang == "en":
        return html
    for url in FULL_ACBUY_URLS:
        if url not in html:
            continue
        tail = url.replace("https://acbuyai.com/", "")
        loc = f"https://acbuyai.com/{lang}/{tail}"
        html = html.replace(url, loc)
    html = html.replace('"https://acbuyai.com/"', f'"https://acbuyai.com/{lang}/"')
    html = html.replace("'https://acbuyai.com/'", f"'https://acbuyai.com/{lang}/'")
    return html


def apply_de_chrome(html: str) -> str:
    for old, new in sorted(DE_CHROME, key=lambda x: len(x[0]), reverse=True):
        html = html.replace(old, new)
    return html


def build_subpage(basename: str, lang: str) -> None:
    html = (ROOT / basename).read_text(encoding="utf-8")
    html = mechanical_subpage(html, lang, basename)
    html = localize_acbuy_urls(html, lang)
    html = swap_hreflang(html, basename)
    html = swap_lang_menu_page(html, basename, lang)
    if lang == "de":
        html = apply_de_chrome(html)
        html = html.replace('<html lang="de">', '<html lang="en">', 1)
    elif lang in ("es", "pt", "pl"):
        html = html.replace(f'<html lang="{lang}">', '<html lang="en">', 1)
    out = ROOT / lang / basename
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print("wrote", out)


def main() -> None:
    idx.build_locale("de")
    for loc in ("es", "pt", "pl"):
        idx.build_locale_fallback_en_body(loc)

    for page in PAGES:
        for lang in ("de", "es", "pt", "pl"):
            build_subpage(page, lang)

    print("done.")

    import check_seo_h1

    check_seo_h1.main()


if __name__ == "__main__":
    main()
