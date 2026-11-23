#!/usr/bin/env python3
"""Pre-deploy checks for essetech.com.au. Read-only: it never edits a file.

Run from the repo root before pushing (scripts/release.sh runs it for you):
    python3 scripts/check-site.py

Exit 0 = safe to push, 1 = at least one ERROR. WARNs don't block.

What it checks, and why (each one is a mistake that has shipped or nearly shipped):
  1. Every public page loads /site.js (analytics + tel/mailto click counting).
  2. Every JSON-LD block parses (a broken block silently drops the rich result).
  3. Internal links point at a page, file or redirect that exists.
  4. Every price in scripts/key-facts.py appears on pricing-adelaide.html
     (prices are hand-copied in both places).
  5. sitemap.xml lists only pages that exist, and every indexable page is in it.
  6. Untracked .html drafts in the repo (one `git add .` would publish them).
  7. The local checkout isn't behind origin/main (Grok pushes from its sandbox).
Added 22 Nov 2026 (AI ecosystem audit, Week 2).
"""
import ast
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
errors, warns = [], []


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout


def vercelignore():
    f = ROOT / ".vercelignore"
    return [l.strip() for l in f.read_text().splitlines()
            if l.strip() and not l.startswith("#")] if f.exists() else []


IGNORED = vercelignore()


def deployed(path):
    """Tracked by git (deploys come from `git push`) and not in .vercelignore."""
    return not any(fnmatch.fnmatch(path, pat.rstrip("/")) or path.startswith(pat.rstrip("/") + "/")
                   for pat in IGNORED)


TRACKED = [p for p in git("ls-files").splitlines() if deployed(p)]
TRACKED_SET = set(TRACKED)
PAGES = [p for p in TRACKED if p.endswith(".html")]


def text(p):
    return (ROOT / p).read_text(errors="ignore")


def is_noindex(html):
    return bool(re.search(r'<meta[^>]+name=["\']robots["\'][^>]+noindex', html, re.I))


def is_public_page(html, page=""):
    """Skip email signatures, banners and other non-page HTML."""
    if "signature" in page:
        return False
    return "<html" in html.lower() and "<title" in html.lower()


# ---- redirects (vercel.json) so links to old URLs aren't flagged
cfg = json.loads(text("vercel.json")) if (ROOT / "vercel.json").exists() else {}
# Rules with a `has` condition (e.g. only for the old vercel.app host) don't
# apply to links on the live site, so they must not excuse a broken link.
REDIRECT_SOURCES = [r["source"] for r in cfg.get("redirects", []) if not r.get("has")]


def source_regex(src):
    """Vercel path-to-regexp subset: :name(alt|alt) -> (alt|alt), :name* -> .*, :name -> [^/]+"""
    out, i = "", 0
    for m in re.finditer(r":[A-Za-z_]+(\([^)]*\))?(\*)?", src):
        out += re.escape(src[i:m.start()])
        out += m.group(1) if m.group(1) else (".*" if m.group(2) else "[^/]+")
        i = m.end()
    return "^" + out + re.escape(src[i:]) + "$"


def redirect_matches(path):
    for src in REDIRECT_SOURCES:
        rx = source_regex(src)
        if re.match(rx, path):
            return True
    return False


def resolves(path):
    """Does a site-root path like /about or /blog/x.html exist in the deploy?"""
    p = path.split("#")[0].split("?")[0]
    if p in ("", "/"):
        return True
    rel = p.lstrip("/")
    candidates = [rel, rel + ".html", rel.rstrip("/") + "/index.html"]
    return any(c in TRACKED_SET for c in candidates) or redirect_matches(p)


# 1-3: per-page checks
for page in PAGES:
    html = text(page)
    if not is_public_page(html, page):
        continue
    noindex = is_noindex(html)

    if "/site.js" not in html:
        (warns if noindex else errors).append(f"{page}: missing /site.js")

    for i, block in enumerate(re.findall(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.S | re.I)):
        try:
            json.loads(block)
        except json.JSONDecodeError as exc:
            errors.append(f"{page}: JSON-LD block {i + 1} doesn't parse ({exc.msg}, line {exc.lineno})")

    base = "/" + page
    live_markup = re.sub(r"<!--.*?-->", "", html, flags=re.S)  # commented-out code isn't served
    for href in re.findall(r'(?:href|src)=["\']([^"\']+)["\']', live_markup):
        if href.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:", "javascript:", "sms:")):
            u = urlparse(href)
            if u.netloc.endswith("essetech.com.au") and u.netloc != "it.essetech.com.au":
                href = u.path or "/"
            else:
                continue
        if "{" in href or "$" in href:
            continue  # template strings inside inline JS
        path = href if href.startswith("/") else str(Path(base).parent / href)
        path = re.sub(r"/\./", "/", path)
        if not resolves(path):
            errors.append(f"{page}: broken internal link {href}")

# 4: prices in key-facts.py vs pricing page
kf = ROOT / "scripts" / "key-facts.py"
pricing = ROOT / "pricing-adelaide.html"
if kf.exists() and pricing.exists():
    tree = ast.parse(kf.read_text())
    facts = next((ast.literal_eval(n.value) for n in ast.walk(tree)
                  if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "FACTS" for t in n.targets)), {})
    price_text = re.sub(r"<[^>]+>", " ", pricing.read_text())
    price_text = re.sub(r"\s+", " ", price_text)
    on_pricing = set(re.findall(r"\$\d[\d,]*", price_text))
    for page, block in facts.items():
        for fact in block.get("facts", []):
            for amount in re.findall(r"\$\d[\d,]*", " ".join(fact)):
                if amount not in on_pricing:
                    errors.append(f"key-facts.py ({page}, '{fact[0]}'): {amount} not found on pricing-adelaide.html")

# 5: sitemap
sm = ROOT / "sitemap.xml"
if sm.exists():
    locs = re.findall(r"<loc>([^<]+)</loc>", sm.read_text())
    paths = {urlparse(l).path or "/" for l in locs}
    for p in sorted(paths):
        if not resolves(p):
            errors.append(f"sitemap.xml lists {p}, which isn't a page")
    for page in PAGES:
        html = text(page)
        if not is_public_page(html, page) or is_noindex(html) or page == "404.html":
            continue
        clean = "/" + re.sub(r"(index)?\.html$", "", page)
        if clean not in paths and "/" + page not in paths and clean.rstrip("/") not in paths:
            warns.append(f"{page} is indexable but not in sitemap.xml")

# 6: untracked drafts
untracked = [p for p in git("ls-files", "--others", "--exclude-standard").splitlines() if p.endswith(".html")]
if untracked:
    warns.append(f"{len(untracked)} untracked .html file(s) not deployed (don't `git add .`): "
                 + ", ".join(untracked[:6]) + (" …" if len(untracked) > 6 else ""))

# 7: behind origin?
subprocess.run(["git", "fetch", "-q", "origin"], cwd=ROOT, capture_output=True, timeout=30)
behind = git("rev-list", "--count", "HEAD..origin/main").strip()
if behind and behind != "0":
    errors.append(f"local main is {behind} commit(s) behind origin/main (Grok may have pushed): "
                  "run `git pull --rebase` first")

print(f"Checked {len(PAGES)} deployed pages.")
for w in warns:
    print(f"  WARN  {w}")
for e in errors:
    print(f"  ERROR {e}")
print("PASS: safe to push." if not errors else f"FAIL: {len(errors)} error(s). Fix before pushing.")
sys.exit(1 if errors else 0)
