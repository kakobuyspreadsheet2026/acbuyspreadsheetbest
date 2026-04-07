# acbuyspreadsheetbest.com — acbuy spreadsheet companion (static site)

**Official live site:** **[https://acbuyspreadsheetbest.com](https://acbuyspreadsheetbest.com)**

Independent, static-first companion for people who use an **acbuy spreadsheet** with **ACBuy**: curated hub context (60,000+ products on the linked catalog), workflow notes, QC and shipping explainers—not checkout, not ACBuy corporate.

---

## What you’ll find on the site

| Area | Purpose |
|------|--------|
| **Home** | How the acbuy spreadsheet fits next to ACBuy, category lanes, FAQ, disclosure |
| **Guides** | Wallet, warehouse, rehearsal, customs—plain-language playbook |
| **News** | Changelog-style notes when lanes or reminders shift |
| **Spreadsheet** | Shortcut into the searchable hub (MaisonLooks) with referral tracking |
| **Deep dives** | QC lens, shipping weight / volumetric notes, stale-link hygiene |

Languages: **English** (root), plus **German**, **Spanish**, **Portuguese**, and **Polish** paths under `/de/`, `/es/`, `/pt/`, `/pl/`.

Sitemap (for crawlers): [https://acbuyspreadsheetbest.com/sitemap.xml](https://acbuyspreadsheetbest.com/sitemap.xml)

---

## Tech stack

- Hand-authored **HTML** + **CSS**, no client framework
- **Vercel**-friendly static deploy (`vercel.json` for clean `/` vs `index.html` redirects)
- **Python** helpers to rebuild locale homepages and mirror subpages from English sources

---

## Local preview

```bash
python3 preview.py
# open http://127.0.0.1:8000
```

Rebuild localized `index.html` files after editing English copy or FAQ schema pairs:

```bash
python3 build_index_from_en.py
```

Full locale pass (index + subpages):

```bash
python3 build_all_locales_from_en.py
```

(Optional) `check_seo_h1.py` needs `beautifulsoup4` if you want the H1 sanity check.

---

## Repository vs. product

This repo holds the **source for [acbuyspreadsheetbest.com](https://acbuyspreadsheetbest.com)**.  
Payments, carts, warehouse photos, and tickets stay on **ACBuy** and the **MaisonLooks** catalog hub—we only publish guides, links, and structured notes.

---

## 简介（中文）

本站 **[acbuyspreadsheetbest.com](https://acbuyspreadsheetbest.com)** 是面向 **acbuy spreadsheet** / **ACBuy** 买家的**独立说明站**（静态页面）：提供表格与代购流程相关的笔记、分类入口与常见问题，**不代收付款**，也非 ACBuy 官方网站。多语言页面见站点内语言切换。

---

*If you link to this project, prefer pointing readers to the live site **https://acbuyspreadsheetbest.com** for the full experience.*
