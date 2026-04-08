#!/usr/bin/env python3
"""
Rebuild locale index.html from English (single source of truth).

For the full site (all pages × de/es/pt/pl), run from repo root:

  python3 build_all_locales_from_en.py

Run this file alone only if you are iterating on index translations:

  python3 build_index_from_en.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# FAQ JSON-LD — questions and answers must match the visible FAQ on index.html (same order, 9 items).
# es/pt/pl pages still show English body copy, so their FAQ schema uses English too.
_EN_FAQ: list[tuple[str, str]] = [
    (
        "How many products are in the hub?",
        "The ACBuy Spreadsheet hub on MaisonLooks currently surfaces 60,000+ products in curated rows—numbers move as listings are added, merged, or retired.",
    ),
    (
        'Is this the "official" ACBuy Spreadsheet?',
        "It is official to our merchant crew, not to ACBuy HQ branding. Policies, coupons, and account safety always come from ACBuy channels.",
    ),
    (
        "Do you store payment info?",
        "No. acbuyspreadsheetbest.com is static pages plus outbound links. Wallets and cards stay inside ACBuy's PCI environment.",
    ),
    (
        "How often do rows refresh?",
        "High-churn categories (sneakers, tech) can update weekly; long-tail items may sit longer. Watch News for sweep announcements that affect the ACBuy Spreadsheet.",
    ),
    (
        "What if two rows list the same URL?",
        "Usually it is intentional—different notes or QC batches. If it is a mistake, tell us on Discord so we can merge duplicates.",
    ),
    (
        "Dead or hijacked links—now what?",
        "See the stale links playbook (acbuy-spreadsheet-dead-links.html on this site) for how we tag suspect rows and how to self-check a listing before you pay.",
    ),
    (
        "Shipping math feels off—who do I trust?",
        "Trust rehearsal measurements inside ACBuy. For theory, read the weight and volumetric primer (acbuy-spreadsheet-shipping-weight.html on this site).",
    ),
    (
        "How do I read QC consistently?",
        "Follow the warehouse QC walkthrough (acbuy-spreadsheet-qc.html on this site) so you know what to verify before you approve freight.",
    ),
    (
        "Where is the live catalog?",
        "Jump from the ACBuy Spreadsheet shortcut (spreadsheet.html on this site) straight into the hub with tracking parameters intact.",
    ),
]

_DE_FAQ: list[tuple[str, str]] = [
    (
        "Wie viele Produkte hat der Hub?",
        "Der acbuy-spreadsheet-Hub auf MaisonLooks zeigt aktuell 60.000+ Produkte in kuratierten Zeilen—Zahlen ändern sich mit Angeboten.",
    ),
    (
        "Ist das das „offizielle“ ACBuy Spreadsheet?",
        "Offiziell für unser Händlerteam, nicht für ACBuy-HQ-Marketing. Richtlinien, Coupons und Kontosicherheit kommen immer von ACBuy.",
    ),
    (
        "Speichern Sie Zahlungsdaten?",
        "Nein. acbuyspreadsheetbest.com sind statische Seiten plus Links. Wallet und Karten bleiben in ACBuys PCI-Umfeld.",
    ),
    (
        "Wie oft werden Zeilen aktualisiert?",
        "Schnelle Kategorien (Sneaker, Tech) wöchentlich; Long-Tail länger. News für Ankündigungen lesen, die das ACBuy Spreadsheet betreffen.",
    ),
    (
        "Zwei Zeilen mit derselben URL?",
        "Meist Absicht—unterschiedliche Notizen oder QC-Batches. Irrtum? Auf Discord melden, wir mergen Duplikate.",
    ),
    (
        "Tote oder entführte Links—und jetzt?",
        "Siehe den Leitfaden zu veralteten Links (acbuy-spreadsheet-dead-links.html auf dieser Site) für Markierungen und Selbstprüfung vor der Zahlung.",
    ),
    (
        "Versandrechnung wirkt falsch—wem vertrauen?",
        "Messwerte aus Rehearsal in ACBuy vertrauen. Theorie: Gewicht & Volumen (acbuy-spreadsheet-shipping-weight.html auf dieser Site).",
    ),
    (
        "Wie lese ich QC konsistent?",
        "Siehe den Lager-QC-Walkthrough (acbuy-spreadsheet-qc.html auf dieser Site)—was Sie vor Freigabe prüfen sollten.",
    ),
    (
        "Wo ist der Live-Katalog?",
        "Vom ACBuy Spreadsheet shortcut (spreadsheet.html auf dieser Site) direkt in den Hub mit Tracking-Parametern.",
    ),
]

FAQ = {
    "en": _EN_FAQ,
    "de": _DE_FAQ,
    "es": _EN_FAQ,
    "pt": _EN_FAQ,
    "pl": _EN_FAQ,
}


def faq_json_ld(lang: str) -> str:
    items = []
    for q, a in FAQ[lang]:
        items.append(
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
        )
    data = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": items}
    return json.dumps(data, ensure_ascii=False, indent=6)


def mechanical(html: str, lang: str) -> str:
    base = f"https://acbuyspreadsheetbest.com/{lang}/"
    html = html.replace('<html lang="en">', f'<html lang="{lang}">')
    html = html.replace('href="styles.css"', 'href="../styles.css"')
    html = html.replace('href="images/', 'href="../images/')
    html = html.replace('src="images/', 'src="../images/')
    # BS4 may reorder attributes; match canonical / og:url regardless of order
    html = re.sub(
        r'<link\b[^>]*(?:\bhref="https://acbuyspreadsheetbest\.com/"[^>]*\brel="canonical"|\brel="canonical"[^>]*\bhref="https://acbuyspreadsheetbest\.com/")[^>]*\/?>',
        f'<link rel="canonical" href="{base}" />',
        html,
        count=1,
    )
    html = re.sub(
        r'<meta\b[^>]*(?:\bcontent="https://acbuyspreadsheetbest\.com/"[^>]*\bproperty="og:url"|\bproperty="og:url"[^>]*\bcontent="https://acbuyspreadsheetbest\.com/")[^>]*\/?>',
        f'<meta property="og:url" content="{base}" />',
        html,
        count=1,
    )
    html = html.replace('"@id": "https://acbuyspreadsheetbest.com/#website"', f'"@id": "{base}#website"')
    html = html.replace('"@id": "https://acbuyspreadsheetbest.com/#org"', f'"@id": "{base}#org"')
    html = html.replace('"publisher": { "@id": "https://acbuyspreadsheetbest.com/#org" }', f'"publisher": {{ "@id": "{base}#org" }}')
    html = html.replace('"url": "https://acbuyspreadsheetbest.com/"', f'"url": "{base}"')
    html = html.replace('<a class="brand" href="/"', f'<a class="brand" href="/{lang}/"')
    return html


def replace_faq_block(html: str, lang: str) -> str:
    import re

    scripts = list(re.finditer(r'<script type="application/ld\+json">\s*.*?\s*</script>', html, re.DOTALL))
    if len(scripts) < 2:
        raise RuntimeError("expected 2 application/ld+json blocks")
    m = scripts[1]
    new_block = f'<script type="application/ld+json">\n      {faq_json_ld(lang)}\n    </script>'
    return html[: m.start()] + new_block + html[m.end() :]


def refresh_root_index_faq() -> None:
    """Keep English index.html FAQ JSON-LD in sync with visible FAQ (source of truth: FAQ['en'])."""
    path = ROOT / "index.html"
    html = path.read_text(encoding="utf-8")
    path.write_text(replace_faq_block(html, "en"), encoding="utf-8")
    print("refreshed", path, "FAQ JSON-LD")


LANG_MENUS = {
    "de": """              <a href="/">EN</a>
              <a href="/pl/" lang="pl">PL</a>
              <a href="/pt/" lang="pt-PT">PT</a>
              <a href="/es/" lang="es">ES</a>
              <a href="/de/" lang="de" aria-current="page">DE</a>""",
    "es": """              <a href="/">EN</a>
              <a href="/pl/" lang="pl">PL</a>
              <a href="/pt/" lang="pt-PT">PT</a>
              <a href="/es/" lang="es" aria-current="page">ES</a>
              <a href="/de/" lang="de">DE</a>""",
    "pt": """              <a href="/">EN</a>
              <a href="/pl/" lang="pl">PL</a>
              <a href="/pt/" lang="pt-PT" aria-current="page">PT</a>
              <a href="/es/" lang="es">ES</a>
              <a href="/de/" lang="de">DE</a>""",
    "pl": """              <a href="/">EN</a>
              <a href="/pl/" lang="pl" aria-current="page">PL</a>
              <a href="/pt/" lang="pt-PT">PT</a>
              <a href="/es/" lang="es">ES</a>
              <a href="/de/" lang="de">DE</a>""",
}


def swap_lang_menu(html: str, lang: str) -> str:
    import re

    pat = re.compile(
        r'<div class="lang-menu" role="menu">\s*.*?</div>\s*(?=\s*</nav>)',
        re.DOTALL,
    )
    m = pat.search(html)
    if not m:
        raise RuntimeError("lang-menu not found")
    inner = LANG_MENUS[lang]
    return html[: m.start()] + f'<div class="lang-menu" role="menu">\n{inner}\n            </div>\n          ' + html[m.end() :]


def nav_home(html: str, lang: str, label: str) -> str:
    return html.replace(
        '<li><a href="/" aria-current="page">Home</a></li>',
        f'<li><a href="/{lang}/" aria-current="page">{label}</a></li>',
    )


# Longest-first string replacements for visible copy (EN -> locale)
PAIRS: dict[str, list[tuple[str, str]]] = {
    "de": [
        ("Skip to content", "Zum Inhalt springen"),
        ('<h2 id="steps-start" class="visually-hidden">Workflow</h2>', '<h2 id="steps-start" class="visually-hidden">Ablauf</h2>'),
        ("Runners, trainers, boots", "Sneaker, Trainer, Boots"),
        ("Shells, puffers, coats", "Shells, Daunen, Mäntel"),
        ("Layers &amp; knits", "Layer &amp; Strick"),
        ("Graphics &amp; basics", "Prints &amp; Basics"),
        ("Denim &amp; casual", "Denim &amp; Casual"),
        ("Totes, crossbody, travel", "Totes, Crossbody, Reise"),
        ("Caps &amp; beanies", "Caps &amp; Beanies"),
        ("Belts, jewelry, small goods", "Gürtel, Schmuck, Kleinigkeiten"),
        ("Gadgets &amp; audio", "Gadgets &amp; Audio"),
        ("Scents &amp; bottles", "Düfte &amp; Flakons"),
        ("Shirts &amp; kits", "Shirts &amp; Kits"),
        ("Mixed / seasonal", "Gemischt / saisonal"),
        (
            "ACBuy Spreadsheet 2026 | 60,000+ products — curated finds for ACBuy | acbuyspreadsheetbest.com",
            "ACBuy Spreadsheet 2026 | 60.000+ Produkte — kuratierte Funde für ACBuy | acbuyspreadsheetbest.com",
        ),
        (
            "ACBuy Spreadsheet with 60,000+ products: merchant-curated Taobao, Weidian &amp; 1688 links and QC context—browse the hub on MaisonLooks, then pay and ship in your ACBuy account. Independent site, not ACBuy corporate.",
            "ACBuy Spreadsheet mit 60.000+ Produkten: von Händlern kuratierte Taobao-, Weidian- und 1688-Links plus QC-Kontext—Hub auf MaisonLooks öffnen, dann in Ihrem ACBuy-Konto bezahlen und versenden. Unabhängige Seite, nicht ACBuy Konzern.",
        ),
        (
            "ACBuy Spreadsheet 2026 | 60,000+ products for ACBuy buyers",
            "ACBuy Spreadsheet 2026 | 60.000+ Produkte für ACBuy-Käufer",
        ),
        (
            "60,000+ curated products: side-by-side batch comparison, stale-link flags, and category lanes—then paste into ACBuy when you are ready to order.",
            "60.000+ kuratierte Produkte: Batch-Vergleich, veraltete Links markiert, Kategorie-Spuren—dann in ACBuy einfügen, wenn Sie bestellen.",
        ),
        (
            "60,000+ curated products—marketplace links and QC cues for ACBuy Spreadsheet shoppers using ACBuy.",
            "60.000+ kuratierte Produkte—Marktplatz-Links und QC-Hinweise für acbuy-spreadsheet-Nutzer mit ACBuy.",
        ),
        (
            "Independent companion site for buyers who use an ACBuy Spreadsheet: 60,000+ curated products, QC context, and workflow notes—checkout occurs on ACBuy.",
            "Begleitseite für Käufer mit ACBuy Spreadsheet: 60.000+ kuratierte Produkte, QC-Kontext und Workflow-Hinweise—Checkout in ACBuy.",
        ),
        ("aria-label=\"Primary\"", 'aria-label="Hauptnavigation"'),
        ("Categories", "Kategorien"),
        ("Guides", "Anleitungen"),
        ("Contact", "Kontakt"),
        ("aria-label=\"Language selector\"", 'aria-label="Sprache"'),
        ('aria-label="Choose language"', 'aria-label="Sprache wählen"'),
        (
            '<meta name="twitter:title" content="ACBuy Spreadsheet 2026 | 60,000+ products" />',
            '<meta name="twitter:title" content="ACBuy Spreadsheet 2026 | 60.000+ Produkte" />',
        ),
        ('aria-label="Homepage sections"', 'aria-label="Bereiche auf der Startseite"'),
        ("Shop smarter with side-by-side links", "Cleverer shoppen mit Links zum Vergleichen"),
        (
            "2026 · ACBuy Spreadsheet · 60,000+ products · curated rows · QC cues · paste-to-ACBuy workflow",
            "2026 · ACBuy Spreadsheet · 60.000+ Produkte · kuratierte Zeilen · QC-Hinweise · ACBuy-Workflow",
        ),
        ("ACBuy official", "ACBuy offiziell"),
        (
            "Taobao · Weidian · 1688",
            "Taobao · Weidian · 1688",
        ),
        ("Batch &amp; note fields", "Batch- &amp; Notizfelder"),
        ("Warehouse QC still on ACBuy", "Lager-QC bleibt bei ACBuy"),
        (
            "Think of the <strong>ACBuy Spreadsheet</strong> as a filter on noisy marketplace search: the hub lists\n            <strong>60,000+ products</strong> in rotating rows—tightened, tagged, and occasionally refreshed when sellers\n            swap batches. We surface context so you can shortlist faster—then you paste the winning URL into\n            <strong>ACBuy</strong> for payment, inspection, and shipping. Nothing on acbuyspreadsheetbest.com replaces your ACBuy\n            wallet or tickets.",
            "Das <strong>ACBuy Spreadsheet</strong> filtert lauten Marktplatz-Suchlärm: Der Hub listet <strong>60.000+ Produkte</strong> in rotierenden Zeilen—gestrafft, getaggt, gelegentlich aktualisiert, wenn Verkäufer Batches wechseln. Wir liefern Kontext für eine schnellere Vorauswahl—dann fügen Sie die gewählte URL in <strong>ACBuy</strong> für Zahlung, Inspektion und Versand ein. Nichts auf acbuyspreadsheetbest.com ersetzt Ihr ACBuy-Wallet oder Tickets.",
        ),
        (
            "Disclosure: acbuyspreadsheetbest.com is an independent marketing front for our ACBuy Spreadsheet—not ACBuy corporate.",
            "Hinweis: acbuyspreadsheetbest.com ist ein unabhängiges Marketing-Frontend für unser ACBuy Spreadsheet—nicht ACBuy Konzern.",
        ),
        ("Snapshot", "Kurzüberblick"),
        ("Lanes", "Spuren"),
        ("What is the ACBuy Spreadsheet here?", "Was ist das ACBuy Spreadsheet hier?"),
        (
            "It is a <strong>merchant-maintained link table</strong> with <strong>60,000+ products</strong> for people\n              who already use or want to try <strong>ACBuy</strong>: each row usually combines a marketplace URL, price\n              context, and optional QC snapshots so you can compare sellers without opening fifteen Taobao tabs.",
            "Es ist eine <strong>von Händlern gepflegte Link-Tabelle</strong> mit <strong>60.000+ Produkten</strong> für alle, die <strong>ACBuy</strong> schon nutzen oder testen wollen: Jede Zeile verbindet meist Marktplatz-URL, Preiskontext und optionale QC-Schnappschüsse—so vergleichen Sie Verkäufer ohne fünfzehn Taobao-Tabs.",
        ),
        (
            "acbuyspreadsheetbest.com explains how to read those rows responsibly. When you are ready to commit, every yuan still\n              flows through <strong>ACBuy’s checkout</strong>—we never touch your card or balance.",
            "acbuyspreadsheetbest.com erklärt, wie man diese Zeilen verantwortlich liest. Wenn Sie kaufen: Jedes Yuan läuft über <strong>ACBuys Checkout</strong>—wir berühren weder Karte noch Guthaben.",
        ),
        ("At a glance", "Auf einen Blick"),
        ("<strong>Official ACBuy site?</strong> No—this is a companion.", "<strong>Offizielle ACBuy-Seite?</strong> Nein—dies ist eine Begleitseite."),
        ("<strong>Who updates rows?</strong> Our merchant team on ACBuy.", "<strong>Wer aktualisiert?</strong> Unser Händlerteam bei ACBuy."),
        ("<strong>Where is money handled?</strong> Inside ACBuy only.", "<strong>Wo läuft das Geld?</strong> Nur in ACBuy."),
        ("<strong>Why bookmark?</strong> Faster discovery + fewer dead links.", "<strong>Warum merken?</strong> Schneller finden + weniger tote Links."),
        ("Jump in by category—not by random search tabs", "Einstieg über Kategorien—nicht über zufällige Such-Tabs"),
        (
            "Pick a lane that matches what you are hunting, skim comparable listings, then carry only the strongest URL\n            into ACBuy. That is the ACBuy Spreadsheet rhythm: <strong>narrow first, paste second</strong>.",
            "Wählen Sie eine Spur passend zur Suche, vergleichen Sie Listings, nehmen Sie nur die stärkste URL mit nach ACBuy. So klingt ACBuy Spreadsheet: <strong>zuerst eingrenzen, dann einfügen</strong>.",
        ),
        ("Why lanes beat keyword roulette", "Warum Spuren besser sind als Keyword-Roulette"),
        (
            "Categories cluster similar silhouettes and price bands. Instead of unrelated results, you stay inside one\n              product family long enough to notice batch differences.",
            "Kategorien bündeln ähnliche Silhouetten und Preisbänder. Statt zusammenhangloser Treffer bleiben Sie in einer Produktfamilie, bis Batch-Unterschiede sichtbar werden.",
        ),
        ("After you open a lane", "Nach dem Öffnen einer Spur"),
        (
            "Flag two or three finalists, compare notes, then open ACBuy in another tab. If a row looks stale, cross-check\n              the link before you pay domestic shipping.",
            "Markieren Sie zwei oder drei Favoriten, vergleichen Sie Notizen, öffnen Sie ACBuy im zweiten Tab. Wirkt eine Zeile alt, prüfen Sie den Link vor Inlandsversand.",
        ),
        (
            "Lanes rotate as inventory shifts—if something disappears, check News or Guides for dead-link notes on the\n          <strong>ACBuy Spreadsheet</strong> before you assume a batch is gone forever.",
            "Spuren rotieren mit dem Bestand—verschwindet etwas, lesen Sie in News oder Anleitungen Hinweise zu toten Links im <strong>ACBuy Spreadsheet</strong>, bevor Sie glauben, ein Batch sei weg.",
        ),
        ("Where most people start", "Wo die meisten starten"),
        (
            "Footwear and outerwear get the heaviest traffic, then bags and accessories. Perfume and electronics need\n            extra caution on battery or liquid rules—confirm ACBuy’s prohibited list before you lock a forwarder line.",
            "Schuhe und Oberbekleidung haben den meisten Traffic, dann Taschen und Accessoires. Parfüm und Elektronik: Batterie- und Flüssigkeitsregeln prüfen—ACBuys Verbotsliste vor Forwarder-Wahl lesen.",
        ),
        ("Inside the hub—not inside your wallet", "Im Hub—nicht in Ihrer Wallet"),
        ("ACBuy Spreadsheet hub →", "ACBuy Spreadsheet-Hub →"),
        (
            "At <strong>60,000+ products</strong> and counting, <strong>ACBuy Spreadsheet</strong> rows blend\n            <strong>Taobao, Weidian, and 1688</strong> listings with human notes: think of it as a live notebook that\n            tracks price drift, seller quirks, and QC references when buyers share them.",
            "Bei <strong>60.000+ Produkten</strong> und steigend verbinden <strong>ACBuy Spreadsheet</strong>-Zeilen <strong>Taobao, Weidian und 1688</strong> mit menschlichen Notizen: ein lebendes Notizbuch zu Preisdrift, Verkäufer-Eigenheiten und QC-Hinweisen aus der Community.",
        ),
        (
            "<strong>ACBuy</strong> still owns the purchase path—domestic freight, warehouse photos, rehearsal, and\n            international labels all live in your account. On acbuyspreadsheetbest.com we layer <strong>ACBuy Spreadsheet</strong>\n            context; on ACBuy you pay, rehearse, and ship.",
            "<strong>ACBuy</strong> führt den Kaufweg—Inlandsfracht, Lagerfotos, Rehearsal und internationale Labels liegen in Ihrem Konto. Auf acbuyspreadsheetbest.com liefern wir <strong>ACBuy Spreadsheet</strong>-Kontext; in ACBuy zahlen Sie, proben und versenden.",
        ),
        ("Fields you will commonly see", "Felder, die Sie oft sehen"),
        ("Plain-language title + link integrity check", "Klartitel + Link-Integrität"),
        ("Currency context (often USD/EUR hints for planning)", "Währungskontext (oft USD/EUR zur Planung)"),
        ("Optional QC thumbnails—always re-verify in warehouse", "Optionale QC-Vorschau—im Lager immer neu prüfen"),
        ("Seller reputation cues when we track them", "Verkäufer-Reputation, wenn wir sie tracken"),
        ("Occasional “stale” or “verify” tags when listings move", "Gelegentlich „stale“ oder „verify“, wenn Angebote wechseln"),
        (
            "Communities evolve fast; we would rather mark uncertainty than silently ship you to a 404. When in doubt,\n            paste only after the mobile listing loads in full.",
            "Community ändert sich schnell; wir markieren Unsicherheit lieber, als Sie still auf 404 zu schicken. Im Zweifel erst einfügen, wenn die mobile Seite vollständig lädt.",
        ),
        ("Why buyers keep the tab pinned", "Warum Käufer den Tab offen lassen"),
        ("Comparison-first layout", "Layout mit Vergleich im Fokus"),
        (
            "Rows line up similar SKUs so you can contrast stitching, price steps, and seller history without juggling\n              browser windows.",
            "Zeilen ordnen ähnliche SKUs, damit Sie Nähte, Preisstufen und Verkäuferhistorie ohne Fensterjonglage vergleichen.",
        ),
        ("Structured columns instead of chaotic screenshots", "Strukturierte Spalten statt chaotischer Screenshots"),
        ("Notes that call out known batch differences", "Notizen zu bekannten Batch-Unterschieden"),
        ("Quick copy/paste into ACBuy’s submit box", "Schnell in ACBuys Einfügefeld"),
        ("Lane filters to avoid category bleed", "Spur-Filter gegen Kategorie-Vermischung"),
        ("Periodic sweeps for broken storefronts", "Regelmäßige Säuberung kaputter Shops"),
        ("Discovery without algorithm noise", "Entdeckung ohne Algorithmus-Lärm"),
        (
            "Marketplace search feeds change hourly; the ACBuy Spreadsheet is edited by people who actually pack boxes.",
            "Marktplatz-Feeds ändern sich stündlich; das ACBuy Spreadsheet pflegen Menschen, die wirklich Pakete packen.",
        ),
        ("Human-written blurbs, not auto-translate spam", "Menschliche Texte, kein Auto-Translate-Spam"),
        ("Signals when a colorway is trending again", "Signale, wenn eine Colorway wieder trendet"),
        ("Cross-links to guides for insurance, rehearsal, duties", "Querverweise zu Leitfäden: Versicherung, Rehearsal, Zoll"),
        ("Discord pings for bigger catalog shifts", "Discord-Hinweise bei größeren Katalog-Umbauten"),
        ("Room to ask “which batch?” before you spend", "Spielraum für „welcher Batch?“ vor dem Kauf"),
        ("Honest about limits", "Ehrlich bei Grenzen"),
        (
            "We are not a factory—we cannot guarantee a seller will ship. We can promise transparent tagging and quick\n              communication when rows break.",
            "Wir sind keine Fabrik—Versand durch Verkäufer nicht garantiert. Wir versprechen transparente Tags und schnelle Infos, wenn Zeilen brechen.",
        ),
        ("No fake “official” badges", "Keine falschen „offiziell“-Siegel"),
        ("No checkout on acbuyspreadsheetbest.com", "Kein Checkout auf acbuyspreadsheetbest.com"),
        ("Clear separation from ACBuy HQ policies", "Klare Trennung von ACBuy-HQ-Richtlinien"),
        ("Encouragement to read warehouse photos cold", "Bitte Lagerfotos nüchtern lesen"),
        ("Reminders that duties are yours to research", "Erinnerung: Zoll recherchieren Sie selbst"),
        ("No secret handshake—just a disciplined loop from bookmark to mailbox:", "Kein Geheimhandshake—nur eine disziplinierte Schleife vom Lesezeichen bis zum Postfach:"),
        ("① Shortlist in the ACBuy Spreadsheet hub", "① Vorauswahl im ACBuy Spreadsheet-Hub"),
        (
            "Filter a lane, open rows that match your size/colorway, and save two backups in case links die overnight.",
            "Spur filtern, passende Zeilen öffnen, zwei Backups merken für den Fall, dass Links über Nacht sterben.",
        ),
        ("② Compare QC context—not hype", "② QC-Kontext vergleichen—nicht dem Hype folgen"),
        (
            "Read seller photos skeptically. If something looks too clean, scroll Discord or News for buyer shots\n                before you move on.",
            "Verkäuferfotos skeptisch lesen. Wirkt etwas zu perfekt, in Discord oder News nach Käuferfotos suchen.",
        ),
        ("③ Paste into ACBuy", "③ In ACBuy einfügen"),
        (
            "Submit the URL, choose options, and pay through ACBuy’s checkout. Domestic shipping and seller chat are\n                on-platform from here.",
            "URL einreichen, Optionen wählen, über ACBuy bezahlen. Inlandsversand und Verkäuferchat laufen ab hier in der Plattform.",
        ),
        ("④ Warehouse photos are the verdict", "④ Lagerfotos sind das Urteil"),
        (
            "When items hit the warehouse, zoom in on labels, soles, and packaging. This is your last easy exit before\n                international postage.",
            "Kommen Artikel ins Lager: Labels, Sohlen, Verpackung vergrößern. Letzte einfache Ausstiegsmöglichkeit vor internationalem Porto.",
        ),
        ("⑤ Ship or rehearse, then track", "⑤ Versenden oder rehearsen, dann tracken"),
        (
            "Pick a line that balances speed and seizure risk for your country. After dispatch, tracking stays inside\n                ACBuy until delivery—typically one to three weeks depending on the service.",
            "Linie wählen, die Tempo und Beschlagnahme-Risiko für Ihr Land balanciert. Nach Versand bleibt Tracking in ACBuy—oft ein bis drei Wochen je nach Dienst.",
        ),
        ("Agent stack reminder", "Erinnerung: Agenten-Stack"),
        (
            "<strong>Note:</strong> ACBuy (and peers like it) exist because most global cards cannot check out on Chinese\n            marketplaces directly. Budget for agent service fees, photography packs, and possible returns—the acbuy\n            spreadsheet only gets you to the starting line.",
            "<strong>Hinweis:</strong> ACBuy (und ähnliche) existieren, weil die meisten globalen Karten nicht direkt auf chinesischen Marktplätzen zahlen können. Planen Sie Agenten-Gebühren, Foto-Pakete und mögliche Retouren—das ACBuy Spreadsheet bringt Sie nur an die Startlinie.",
        ),
        ("Still stuck? Start with Guides or ping us on Discord.", "Noch hängen? Anleitungen lesen oder auf Discord melden."),
        ("How many products are in the hub?", "Wie viele Produkte hat der Hub?"),
        (
            "The ACBuy Spreadsheet hub on MaisonLooks currently surfaces <strong>60,000+ products</strong> in curated\n              rows—numbers move as listings are added, merged, or retired.",
            "Der acbuy-spreadsheet-Hub auf MaisonLooks zeigt aktuell <strong>60.000+ Produkte</strong> in kuratierten Zeilen—Zahlen ändern sich mit Angeboten.",
        ),
        ("Is this the “official” ACBuy Spreadsheet?", "Ist das das „offizielle“ ACBuy Spreadsheet?"),
        (
            "It is official to <em>our</em> merchant crew, not to ACBuy HQ branding. Policies, coupons, and account\n              safety always come from ACBuy channels.",
            "Offiziell für <em>unser</em> Händlerteam, nicht für ACBuy-HQ-Marketing. Richtlinien, Coupons und Kontosicherheit kommen immer von ACBuy.",
        ),
        ("Do you store payment info?", "Speichern Sie Zahlungsdaten?"),
        (
            "No. acbuyspreadsheetbest.com is static pages plus outbound links. Wallets and cards stay inside ACBuy’s PCI environment.",
            "Nein. acbuyspreadsheetbest.com sind statische Seiten plus Links. Wallet und Karten bleiben in ACBuys PCI-Umfeld.",
        ),
        ("How often do rows refresh?", "Wie oft werden Zeilen aktualisiert?"),
        (
            "High-churn categories (sneakers, tech) can update weekly; long-tail items may sit longer. Watch News for\n              sweep announcements that affect the <strong>ACBuy Spreadsheet</strong>.",
            "Schnelle Kategorien (Sneaker, Tech) wöchentlich; Long-Tail länger. News für Ankündigungen lesen, die das <strong>ACBuy Spreadsheet</strong> betreffen.",
        ),
        ("What if two rows list the same URL?", "Zwei Zeilen mit derselben URL?"),
        (
            "Usually it is intentional—different notes or QC batches. If it is a mistake, tell us on Discord so we can\n              merge duplicates.",
            "Meist Absicht—unterschiedliche Notizen oder QC-Batches. Irrtum? Auf Discord melden, wir mergen Duplikate.",
        ),
        ("Dead or hijacked links—now what?", "Tote oder entführte Links—und jetzt?"),
        (
            "See\n              <a href=\"acbuy-spreadsheet-dead-links.html\">stale links playbook</a>\n              for how we tag suspect rows and how to self-check a listing before you pay.",
            "Siehe\n              <a href=\"acbuy-spreadsheet-dead-links.html\">Leitfaden zu veralteten Links</a>\n              wie wir Zeilen markieren und wie Sie Listings selbst prüfen.",
        ),
        ("Shipping math feels off—who do I trust?", "Versandrechnung wirkt falsch—wem vertrauen?"),
        (
            "Trust rehearsal measurements inside ACBuy. For theory, read\n              <a href=\"acbuy-spreadsheet-shipping-weight.html\">weight &amp; volumetric primer</a>.",
            "Messwerte aus Rehearsal in ACBuy vertrauen. Theorie:\n              <a href=\"acbuy-spreadsheet-shipping-weight.html\">Gewicht &amp; Volumen</a>.",
        ),
        ("How do I read QC consistently?", "Wie lese ich QC konsistent?"),
        (
            "Follow the\n              <a href=\"acbuy-spreadsheet-qc.html\">warehouse QC walkthrough</a>\n              so you know what to verify before you approve freight.",
            "Siehe\n              <a href=\"acbuy-spreadsheet-qc.html\">Lager-QC-Walkthrough</a>\n              was Sie vor Freigabe prüfen sollten.",
        ),
        ("Where is the live catalog?", "Wo ist der Live-Katalog?"),
        (
            "Jump from the\n              <a href=\"spreadsheet.html\">ACBuy Spreadsheet shortcut</a>\n              straight into the hub with tracking parameters intact.",
            "Von\n              <a href=\"spreadsheet.html\">ACBuy Spreadsheet shortcut</a>\n              direkt in den Hub mit Tracking-Parametern.",
        ),
        ("Ready when you are", "Bereit, wenn Sie es sind"),
        (
            "Grab your ACBuy login, open the MaisonLooks hub behind the <strong>ACBuy Spreadsheet</strong>, and bring back\n            a link you actually trust—then let warehouse QC do the final say-so.",
            "ACBuy-Login, MaisonLooks-Hub hinter dem <strong>ACBuy Spreadsheet</strong> öffnen, einen Link mitbringen, dem Sie vertrauen—dann entscheidet das Lager-QC.",
        ),
        (
            "acbuyspreadsheetbest.com publishes field notes, lane links, and QC explainers for shoppers who rely on an\n            <strong>ACBuy Spreadsheet</strong> (hub: <strong>60,000+ products</strong>). We do not sell inventory, store\n            balances, or speak for ACBuy corporate policies.",
            "acbuyspreadsheetbest.com veröffentlicht Feldnotizen, Spur-Links und QC-Erklärungen für Nutzer eines <strong>ACBuy Spreadsheet</strong> (Hub: <strong>60.000+ Produkte</strong>). Wir verkaufen kein Inventar, halten keine Guthaben und sprechen nicht für ACBuy-Konzernrichtlinien.",
        ),
        (
            "<strong>You are responsible for import rules, duties, and final purchase decisions.</strong> When in doubt,\n            screenshot warehouse photos and open a ticket inside ACBuy.",
            "<strong>Sie sind für Importregeln, Zölle und Kaufentscheidungen verantwortlich.</strong> Im Zweifel: Lagerfotos sichern und Ticket in ACBuy.",
        ),
        ("· ACBuy Spreadsheet merchants · all rights reserved", "· ACBuy Spreadsheet Händler · alle Rechte vorbehalten"),
        ("ACBuy Spreadsheet hub", "ACBuy Spreadsheet-Hub"),
    ],
}


def build_locale(lang: str) -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    html = mechanical(html, lang)
    if lang not in PAIRS:
        raise KeyError(f"add PAIRS['{lang}'] or implement partial build")
    for old, new in sorted(PAIRS[lang], key=lambda x: len(x[0]), reverse=True):
        c = html.count(old)
        if c == 0:
            print("WARN", lang, "missing substring:", repr(old[:70]))
        elif c > 1 and old not in ("Categories", "Guides", "News", "Contact"):
            print("INFO", lang, "multiple hits:", c, repr(old[:50]))
        html = html.replace(old, new)
    html = replace_faq_block(html, lang)
    html = swap_lang_menu(html, lang)
    labels = {"de": "Startseite", "es": "Inicio", "pt": "Início", "pl": "Start"}
    html = nav_home(html, lang, labels[lang])
    out = ROOT / lang / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print("wrote", out)


def build_locale_fallback_en_body(lang: str) -> None:
    """Same layout/sections as English; visible copy stays EN until PAIRS[lang] exists. FAQ JSON-LD is localized."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    html = mechanical(html, lang)
    # Visible copy is still English; keep document language consistent until PAIRS[lang] ships.
    html = html.replace(f'<html lang="{lang}">', '<html lang="en">', 1)
    html = replace_faq_block(html, lang)
    html = swap_lang_menu(html, lang)
    labels = {"de": "Startseite", "es": "Inicio", "pt": "Início", "pl": "Start"}
    html = nav_home(html, lang, labels[lang])
    out = ROOT / lang / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print("wrote (EN body, localized FAQ/schema)", out)


if __name__ == "__main__":
    refresh_root_index_faq()
    build_locale("de")
    for loc in ("es", "pt", "pl"):
        build_locale_fallback_en_body(loc)
