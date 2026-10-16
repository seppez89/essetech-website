#!/usr/bin/env python3
"""Set each <lastmod> in sitemap.xml to the date of the last git commit that touched the page.

Run from the repo root after committing page changes:  python3 scripts/update-sitemap-lastmod.py
Then commit sitemap.xml. Also warns about indexable HTML pages missing from the sitemap.
"""
import re, subprocess, sys, os
HOST = "https://www.essetech.com.au"   # keep in sync with the canonical host
xml = open("sitemap.xml").read()

def path_for(url):
    p = url[len(HOST):] or "/"
    if p.endswith("/"):
        return p.lstrip("/") + "index.html"
    return p.lstrip("/")

def sub(m):
    url = m.group(1)
    f = path_for(url)
    d = subprocess.check_output(["git", "log", "-1", "--format=%cs", "--", f], text=True).strip()
    if not d:
        print("no git history for", f, file=sys.stderr); return m.group(0)
    return m.group(0).replace(m.group(2), d)

new = re.sub(r"<loc>(" + re.escape(HOST) + r"[^<]*)</loc>\s*<lastmod>([^<]*)</lastmod>", sub, xml)
open("sitemap.xml", "w").write(new)

listed = {path_for(u) for u in re.findall(r"<loc>([^<]*)</loc>", new)}
ignore = {"404.html", "ai-services-new.html", "email-signature.html"}
for root, _, files in os.walk("."):
    if root.startswith("./.git") or root.startswith("./scripts"): continue
    for n in files:
        if n.endswith(".html"):
            p = os.path.relpath(os.path.join(root, n), ".")
            if p in listed or p in ignore: continue
            head = open(p, errors="ignore").read(6000)
            if "noindex" in head or p.startswith(("Essetech-email", "linkedin-")): continue
            print("NOT IN SITEMAP:", p)
