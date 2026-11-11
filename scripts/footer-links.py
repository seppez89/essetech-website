#!/usr/bin/env python3
"""Add the "Specialist help" column to every standard page footer.

The footer is how search engines and AI crawlers find the deeper pages, and
before this the industry pages were linked from only two places. This adds
one column listing the specialist and industry pages, and widens the footer
grid from four columns to five so it still sits on one row on a desktop.

Edit LINKS below, then run from the repo root:

    python3 scripts/footer-links.py

Safe to run repeatedly. Blog posts, the 404 page and the thank-you page use a
different one-row footer and are left alone.
"""
import re
import subprocess
import sys

LINKS = [
    ("/ai-growth-system-adelaide.html", "AI Growth System"),
    ("/ai-consultant-adelaide.html", "AI Consultant"),
    ("/microsoft-copilot-consultant-adelaide.html", "Microsoft Copilot Setup"),
    ("/microsoft-365-support-adelaide.html", "Microsoft 365 Support"),
    ("/essential-eight-adelaide.html", "Essential Eight"),
    ("/it-consulting-adelaide.html", "IT Consulting"),
    ("/it-for-trades-adelaide.html", "IT for Trades"),
    ("/it-for-medical-clinics-adelaide.html", "IT for Medical Clinics"),
    ("/it-for-not-for-profits-adelaide.html", "IT for Not-for-Profits"),
]

START = "<!-- SPECIALIST LINKS START (scripts/footer-links.py) -->"
END = "<!-- SPECIALIST LINKS END -->"
OLD_GRID = "grid md:grid-cols-4 gap-10 md:gap-8"
NEW_GRID = "grid md:grid-cols-2 lg:grid-cols-5 gap-10 md:gap-8"
CONTACT = re.compile(r'<div>\s*<h3 class="text-sm font-bold text-white uppercase(?: tracking-wider)? mb-4">Contact</h3>')


def column():
    items = "".join(
        '<li><a href="%s" class="text-sm text-white/60 hover:text-fire-400 transition-colors">%s</a></li>' % link
        for link in LINKS)
    return (START + '<div><h3 class="text-sm font-bold text-white uppercase tracking-wider mb-4">Specialist help</h3>'
            '<ul class="space-y-3">' + items + "</ul></div>" + END)


def main():
    pages = subprocess.run(["git", "ls-files", "*.html"], capture_output=True, text=True).stdout.split()
    skip = re.compile(r"Essetech-email|linkedin-|email-signature|ai-services")
    done = 0
    for page in pages:
        if skip.search(page):
            continue
        html = open(page, encoding="utf-8").read()
        footer_at = html.rfind("<footer")
        if footer_at < 0:
            continue
        head, footer = html[:footer_at], html[footer_at:]
        if OLD_GRID not in footer and NEW_GRID not in footer:
            continue
        footer = footer.replace(OLD_GRID, NEW_GRID, 1)
        footer = footer.replace('<div class="md:col-span-2">', '<div class="lg:col-span-2">', 1)
        if START in footer:
            footer = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: column(), footer, flags=re.S)
        else:
            match = CONTACT.search(footer)
            if not match:
                print("  !! no Contact column found in", page)
                continue
            footer = footer[:match.start()] + column() + "\n                " + footer[match.start():]
        if head + footer != html:
            open(page, "w", encoding="utf-8").write(head + footer)
            done += 1
    print("%d footers updated" % done)


if __name__ == "__main__":
    sys.exit(main())
