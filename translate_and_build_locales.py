#!/usr/bin/env python3
"""
Machine-translate all locale HTML from English sources, then apply URL/hreflang/chrome.

Requires: python3 -m venv .venv && .venv/bin/pip install deep-translator beautifulsoup4 lxml

Run: .venv/bin/python translate_and_build_locales.py
     (or: python3 translate_and_build_locales.py  if venv activated)

Uses Google Translate via deep-translator (unofficial). Brands/URLs are protected.

Primary SEO phrase (literal in every locale): SEO_PRIMARY_KEYWORD — protected from MT and
normalized after translate so titles/meta/JSON-LD keep the same query-shaped string.

German index: optional — by default keeps FAQ JSON-LD from build_index_from_en.FAQ;
  body is still machine-translated from EN for consistency with other DE pages.
"""

from __future__ import annotations

import html
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from bs4 import BeautifulSoup, Comment, Doctype
from deep_translator import GoogleTranslator

import build_all_locales_from_en as ball
import build_index_from_en as idx

ROOT = Path(__file__).resolve().parent

ALL_PAGES = [
    "index.html",
    "guides.html",
    "news.html",
    "contact.html",
    "spreadsheet.html",
    "acbuy-spreadsheet-qc.html",
    "acbuy-spreadsheet-shipping-weight.html",
    "acbuy-spreadsheet-dead-links.html",
]

LANG_MAP = {"de": "de", "es": "es", "pt": "pt", "pl": "pl"}

# Exact query-shaped phrase for SEO (unchanged in localized pages; MT must not translate it).
SEO_PRIMARY_KEYWORD = "acbuy spreadsheet"

# Longest first — protect before MT
PROTECT_TERMS: tuple[tuple[str, str], ...] = (
    (SEO_PRIMARY_KEYWORD, "\uE000ACBUYSS\uE001"),
    ("acbuyspreadsheetbest.com", "\uE000ACBUYAI\uE001"),
    ("MaisonLooks", "\uE000ML\uE001"),
    ("ACBuy official", "\uE000ACBO\uE001"),
    ("ACBuy", "\uE000ACBUY\uE001"),
    ("acbuy", "\uE000ACBUYL\uE001"),
    ("Taobao", "\uE000TB\uE001"),
    ("Weidian", "\uE000WD\uE001"),
    ("1688", "\uE00016\uE001"),
    ("Discord", "\uE000DC\uE001"),
    ("QC", "\uE000QC\uE001"),
    ("SKU", "\uE000SKU\uE001"),
    ("PCI", "\uE000PCI\uE001"),
    ("VAT", "\uE000VAT\uE001"),
    ("SSL", "\uE000SSL\uE001"),
    ("USD", "\uE000USD\uE001"),
    ("EUR", "\uE000EUR\uE001"),
)

SKIP_TAGS = frozenset({"script", "style", "noscript", "code", "pre"})
META_TRANSLATE = (
    ("meta", {"name": "description"}, "content"),
    ("meta", {"property": "og:title"}, "content"),
    ("meta", {"property": "og:description"}, "content"),
    ("meta", {"name": "twitter:title"}, "content"),
    ("meta", {"name": "twitter:description"}, "content"),
)


def protect(s: str) -> str:
    for a, b in PROTECT_TERMS:
        s = s.replace(a, b)
    return s


def unprotect(s: str) -> str:
    for a, b in PROTECT_TERMS:
        s = s.replace(b, a)
    return s


# Google Translate may alter letters inside U+E000…U+E001, so unprotect misses. Map by observed inner text.
_PUA = "\uE000"
_PUB = "\uE001"
_PUA_PAIR = re.compile("\uE000([^\uE001]+)\uE001")

# Exact inner forms (post-protect tokens)
_INNER_EXACT: dict[str, str] = {
    "ACBUY": "ACBuy",
    "ACBO": "ACBuy official",
    "ACBUYSS": SEO_PRIMARY_KEYWORD,
    "ACBUYAI": "acbuyspreadsheetbest.com",
    "ACBUYL": "acbuy",
    "ML": "MaisonLooks",
    "TB": "Taobao",
    "WD": "Weidian",
    "16": "1688",
    "DC": "Discord",
    "QC": "QC",
    "SKU": "SKU",
    "PCI": "PCI",
    "VAT": "VAT",
    "SSL": "SSL",
    "USD": "USD",
    "EUR": "EUR",
}

# MT-corrupted inners (Polish and other locales) → canonical
_INNER_MANGLED: dict[str, str] = {
    "AKUP": SEO_PRIMARY_KEYWORD,
    "AKBUYAI": "acbuyspreadsheetbest.com",
    "AKUPACH": SEO_PRIMARY_KEYWORD,
    "AKUPOWANIA": SEO_PRIMARY_KEYWORD,
    "AKUPAMI": SEO_PRIMARY_KEYWORD,
    "KUPUJ": SEO_PRIMARY_KEYWORD,
    "KUP": "ACBuy",
}


def repair_protected_tokens(s: str) -> str:
    """Restore brand terms when MT corrupts PUA-wrapped placeholders or breaks pairs."""

    def repl(m: re.Match) -> str:
        inner = m.group(1).strip()
        if inner in _INNER_EXACT:
            return _INNER_EXACT[inner]
        if inner.lower() == SEO_PRIMARY_KEYWORD:
            return SEO_PRIMARY_KEYWORD
        up = inner.upper()
        if up in _INNER_MANGLED:
            return _INNER_MANGLED[up]
        if up in _INNER_EXACT:
            return _INNER_EXACT[up]
        return m.group(0)

    s = _PUA_PAIR.sub(repl, s)
    # Closing U+E001 lost before tag end (seen pl/news h1)
    s = re.sub(r"\uE000acbuy spreadsheet(?!\uE001)", SEO_PRIMARY_KEYWORD, s)
    # Broken pair: space before translated tail (closing U+E001 lost; seen in pl meta)
    s = re.sub(r"\uE000ACBUYSS(\s+)", SEO_PRIMARY_KEYWORD + r"\1", s)
    # Bare leaked token from partial MT
    s = re.sub(r"(?<![A-Za-z])ACBUYSS(?![A-Za-z])", SEO_PRIMARY_KEYWORD, s)
    # Logo alt: MT turns "acbuy" into local verb (e.g. pl "kupić")
    s = re.sub(r'(?i)\balt="kupić"', 'alt="acbuy"', s)
    s = re.sub(r">Acbuyai<", ">acbuyspreadsheetbest<", s)
    s = s.replace('"Acbuyai"', '"acbuyspreadsheetbest"')
    # MT turned "acbuy spreadsheet rhythm" into bogus Polish noun in quotes
    s = s.replace("\u201eAKUPOWANIA\u201d", "\u201e" + SEO_PRIMARY_KEYWORD + "\u201d")
    # Glued word after MT (pl news title)
    s = s.replace("spreadsheetaktualności", "spreadsheet aktualności")
    s = re.sub(r"\bAcbuyai\b", "acbuyspreadsheetbest", s)
    # Normalize any casing drift of the two-word SEO phrase (e.g. Acbuy spreadsheet → acbuy spreadsheet)
    s = re.sub(r"(?i)\bacbuy spreadsheet\b", SEO_PRIMARY_KEYWORD, s)
    return s


def should_skip_text(stripped: str) -> bool:
    if len(stripped) < 2:
        return True
    if re.fullmatch(r"[\d\s\.\,\:\;\-\+\/\(\)%&]+", stripped):
        return True
    if stripped.startswith("http") or stripped.startswith("/") or stripped.startswith("#"):
        return True
    if re.fullmatch(r"EN|PL|PT|ES|DE", stripped):
        return True
    return False


def translate_json_strings(obj, translator: GoogleTranslator, cache: dict[str, str]) -> None:
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if k in ("@id", "@type", "@context", "position", "datePublished", "dateModified"):
                continue
            if isinstance(v, (dict, list)):
                translate_json_strings(v, translator, cache)
            elif isinstance(v, str) and len(v) > 2:
                if v.startswith("http") or v.startswith("/"):
                    continue
                obj[k] = tr_cached(v, translator, cache)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, (dict, list)):
                translate_json_strings(item, translator, cache)
            elif isinstance(item, str) and len(item) > 2 and not item.startswith("http"):
                obj[i] = tr_cached(item, translator, cache)


def tr_cached(s: str, translator: GoogleTranslator, cache: dict[str, str]) -> str:
    s = html.unescape(s.strip())
    if should_skip_text(s):
        return s
    if s not in cache:
        p = protect(s)
        time.sleep(0.12)
        try:
            cache[s] = repair_protected_tokens(unprotect(translator.translate(p)))
        except Exception as e:
            print("translate error:", e, s[:60], flush=True)
            cache[s] = s
    return cache[s]


def _inside_language_switcher(node) -> bool:
    p = getattr(node, "parent", None)
    while p is not None:
        if getattr(p, "name", None) and p.get("class"):
            cls = " ".join(p["class"]) if isinstance(p["class"], list) else p["class"]
            if "language-switcher" in cls or "lang-menu" in cls:
                return True
        p = getattr(p, "parent", None)
    return False


def translate_html_document(html: str, lang_code: str) -> str:
    translator = GoogleTranslator(source="en", target=lang_code)
    cache: dict[str, str] = {}

    soup = BeautifulSoup(html, "lxml")

    if soup.title and soup.title.string:
        t = str(soup.title.string).strip()
        if t:
            soup.title.string = tr_cached(t, translator, cache)

    for tag_name, attrs, attr in META_TRANSLATE:
        for tag in soup.find_all(tag_name, attrs=attrs):
            if tag.get(attr):
                tag[attr] = tr_cached(tag[attr], translator, cache)

    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string or not script.string.strip():
            continue
        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            continue
        translate_json_strings(data, translator, cache)
        script.string = json.dumps(data, ensure_ascii=False, indent=2)

    for text in soup.find_all(string=True):
        if isinstance(text, (Comment, Doctype)):
            continue
        parent = getattr(text, "parent", None)
        if not parent or parent.name in SKIP_TAGS:
            continue
        if _inside_language_switcher(text):
            continue
        raw = str(text)
        stripped = raw.strip()
        if not stripped:
            continue
        if should_skip_text(stripped):
            continue
        new_s = tr_cached(stripped, translator, cache)
        text.replace_with(new_s)

    for tag in soup.find_all(True):
        for attr in ("aria-label", "alt", "title", "placeholder"):
            if tag.get(attr) and len(tag[attr]) > 1:
                tag[attr] = tr_cached(tag[attr], translator, cache)

    return repair_protected_tokens(str(soup))


def fix_index_home_nav(html: str, lang: str, label: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    a = soup.select_one('header nav > ul > li > a[href="/"][aria-current="page"]')
    if a:
        a["href"] = f"/{lang}/"
        a.clear()
        a.append(label)
    return str(soup)


PAGES_SUB = [p for p in ALL_PAGES if p != "index.html"]


def patch_index_faq_from_module(html: str, lang: str) -> str:
    """Use curated FAQ JSON-LD from build_index_from_en."""
    return idx.replace_faq_block(html, lang)


def build_one_locale_index(lang: str) -> None:
    en = (ROOT / "index.html").read_text(encoding="utf-8")
    print(f"  translating index -> {lang} …", flush=True)
    translated = translate_html_document(en, LANG_MAP[lang])
    translated = idx.mechanical(translated, lang)
    translated = patch_index_faq_from_module(translated, lang)
    translated = idx.swap_lang_menu(translated, lang)
    labels = {"de": "Startseite", "es": "Inicio", "pt": "Início", "pl": "Start"}
    translated = fix_index_home_nav(translated, lang, labels[lang])
    translated = translated.replace('<html lang="en">', f'<html lang="{lang}">', 1)
    out = ROOT / lang / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(translated, encoding="utf-8")
    print("  wrote", out, flush=True)


def build_one_subpage(basename: str, lang: str) -> None:
    en = (ROOT / basename).read_text(encoding="utf-8")
    print(f"  translating {basename} -> {lang} …", flush=True)
    translated = translate_html_document(en, LANG_MAP[lang])
    translated = ball.mechanical_subpage(translated, lang, basename)
    translated = ball.localize_acbuy_urls(translated, lang)
    translated = ball.swap_hreflang(translated, basename)
    translated = ball.swap_lang_menu_page(translated, basename, lang)
    translated = translated.replace('<html lang="en">', f'<html lang="{lang}">', 1)
    if lang == "de":
        translated = ball.apply_de_chrome(translated)
    out = ROOT / lang / basename
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(translated, encoding="utf-8")
    print("  wrote", out, flush=True)


def worker_lang(lang: str) -> None:
    print(f"== language {lang} ==", flush=True)
    build_one_locale_index(lang)
    for base in PAGES_SUB:
        build_one_subpage(base, lang)
    print(f"== done {lang} ==", flush=True)


def main() -> None:
    langs = ("de", "es", "pt", "pl")
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(worker_lang, lg): lg for lg in langs}
        for fut in as_completed(futures):
            fut.result()
    print("All locales built.", flush=True)

    import check_seo_h1

    check_seo_h1.main()


if __name__ == "__main__":
    main()
