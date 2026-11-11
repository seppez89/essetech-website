#!/usr/bin/env python3
"""Keep the business identity in every page's structured data (JSON-LD) identical.

Search engines and AI assistants build one picture of "Essetech" from these
blocks. Before this script each page described the business slightly
differently (different email, missing logo, no founder, no profile links).

Run from the repo root after changing any fact below:

    python3 scripts/schema-identity.py

It is safe to run repeatedly. It only rewrites the business, founder,
author and publisher parts of the JSON-LD and leaves FAQs, breadcrumbs and
page copy alone.
"""
import json
import re
import subprocess
import sys

BASE = "https://www.essetech.com.au"
ORG_ID = BASE + "/#business"
SITE_ID = BASE + "/#website"
PERSON_ID = BASE + "/about.html#jonathon-battifuoco"

# Only profiles that have been checked and really belong to Essetech.
SAME_AS = [
    "https://www.google.com/maps?cid=16344603218736363948",
    "https://www.youtube.com/@Essetech_IT",
    "https://abr.business.gov.au/ABN/View?abn=33697426163",
]

ADDRESS = {
    "@type": "PostalAddress",
    "addressLocality": "Brooklyn Park",
    "addressRegion": "SA",
    "postalCode": "5032",
    "addressCountry": "AU",
}
AREA = [
    {"@type": "City", "name": "Adelaide", "containedInPlace": {"@type": "State", "name": "South Australia"}},
    {"@type": "Country", "name": "Australia"},
]
HOURS = [{
    "@type": "OpeningHoursSpecification",
    "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "opens": "08:00",
    "closes": "18:00",
}]
DESCRIPTION = (
    "Essetech is an IT support, managed IT, cybersecurity and secure AI business in Brooklyn Park, Adelaide, "
    "South Australia. It is run hands-on by founder Jonathon Battifuoco, publishes its prices and works with "
    "small and medium businesses across the Adelaide metro area and remotely across Australia."
)
KNOWS = [
    "IT support", "Managed IT services", "Cybersecurity", "ACSC Essential Eight", "Microsoft 365",
    "Microsoft Copilot", "Claude", "AI automation", "AI use policy", "Cloud migration",
    "Fractional IT management", "Web design",
]


def org_slim():
    """The business as it appears on every page."""
    return {
        "@type": ["LocalBusiness", "ProfessionalService"],
        "@id": ORG_ID,
        "name": "Essetech",
        "legalName": "Essetech Pty Ltd",
        "url": BASE + "/",
        "logo": BASE + "/essetech-logo.png",
        "image": BASE + "/og-image.png",
        "telephone": "+61404311791",
        "email": "support@essetech.com.au",
        "address": ADDRESS,
        "areaServed": AREA,
        "priceRange": "$$",
        "openingHoursSpecification": HOURS,
        "founder": {"@id": PERSON_ID},
        "sameAs": SAME_AS,
    }


def org_full():
    """The complete record, used on the homepage, About and Contact pages."""
    org = org_slim()
    org.update({
        "alternateName": ["Esse Tech", "Essetech IT Consulting"],
        "description": DESCRIPTION,
        "logo": {"@type": "ImageObject", "@id": BASE + "/#logo", "url": BASE + "/essetech-logo.png",
                 "width": 1563, "height": 1563, "caption": "Essetech"},
        "taxID": "33697426163",
        "identifier": [
            {"@type": "PropertyValue", "propertyID": "ABN", "value": "33697426163"},
            {"@type": "PropertyValue", "propertyID": "ACN", "value": "697426163"},
        ],
        "currenciesAccepted": "AUD",
        "knowsAbout": KNOWS,
        "contactPoint": {
            "@type": "ContactPoint", "contactType": "customer support", "telephone": "+61404311791",
            "email": "support@essetech.com.au", "areaServed": "AU", "availableLanguage": "en",
        },
        "founder": person(),
    })
    return org


def person():
    return {
        "@type": "Person",
        "@id": PERSON_ID,
        "name": "Jonathon Battifuoco",
        "jobTitle": "Founder",
        "url": BASE + "/about.html",
        "image": BASE + "/jonathon.webp",
        "worksFor": {"@id": ORG_ID},
        "knowsAbout": ["IT support", "Managed IT services", "Cybersecurity", "Microsoft 365", "AI automation"],
    }


def author():
    return {
        "@type": "Person", "@id": PERSON_ID, "name": "Jonathon Battifuoco", "jobTitle": "Founder",
        "url": BASE + "/about.html",
        "worksFor": {"@type": "Organization", "@id": ORG_ID, "name": "Essetech"},
    }


def publisher():
    return {
        "@type": "Organization", "@id": ORG_ID, "name": "Essetech", "url": BASE + "/",
        "logo": {"@type": "ImageObject", "url": BASE + "/essetech-logo.png"},
    }


def provider():
    return {"@type": "LocalBusiness", "@id": ORG_ID, "name": "Essetech", "url": BASE + "/"}


def is_business(node):
    t = node.get("@type")
    types = t if isinstance(t, list) else [t]
    return "LocalBusiness" in types or "ProfessionalService" in types


def fix_service(node):
    if isinstance(node, dict):
        if node.get("@type") == "Service" and "provider" in node:
            node["provider"] = provider()
        for value in node.values():
            fix_service(value)
    elif isinstance(node, list):
        for value in node:
            fix_service(value)


def rewrite(path, data, full):
    """Return the new JSON-LD object for one block, or None to leave it alone."""
    if not isinstance(data, dict):
        return None
    context = data.get("@context", "https://schema.org")
    kind = data.get("@type")

    if "@graph" in data:
        graph = []
        for node in data["@graph"]:
            if is_business(node):
                node = org_full() if full else org_slim()
            elif node.get("@type") == "WebSite":
                node = website()
            elif node.get("@type") == "Person" and node.get("@id") == PERSON_ID:
                node = person()
            graph.append(node)
        return {"@context": context, "@graph": graph}

    if is_business(data):
        if path == "index.html":
            return {"@context": context, "@graph": [org_full(), website()]}
        new = org_full() if full else org_slim()
        return {"@context": context, **new}

    if kind == "WebSite":
        return "DROP" if path == "index.html" else {"@context": context, **website()}

    if kind in ("AboutPage", "ContactPage"):
        data["mainEntity"] = org_full()
        data["isPartOf"] = {"@id": SITE_ID}
        return data

    if kind in ("Article", "BlogPosting"):
        was_person = isinstance(data.get("author"), dict) and data["author"].get("@type") == "Person"
        data["author"] = author() if was_person else {"@type": "Organization", "@id": ORG_ID, "name": "Essetech", "url": BASE + "/"}
        data["publisher"] = publisher()
        if not data.get("datePublished") and data.get("dateModified"):
            data["datePublished"] = data["dateModified"]
        return data

    if kind in ("Service", "ItemList"):
        before = json.dumps(data, sort_keys=True)
        fix_service(data)
        return data if json.dumps(data, sort_keys=True) != before else None

    return None


def website():
    return {
        "@type": "WebSite", "@id": SITE_ID, "name": "Essetech", "url": BASE + "/",
        "inLanguage": "en-AU", "publisher": {"@id": ORG_ID},
    }


def dump(obj, pretty, indent):
    if not pretty:
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    text = json.dumps(obj, ensure_ascii=False, indent=4)
    return "\n" + "\n".join(indent + line for line in text.split("\n")) + "\n" + indent


def main():
    tracked = subprocess.run(["git", "ls-files", "*.html"], capture_output=True, text=True).stdout.split()
    skip = re.compile(r"Essetech-email|linkedin-|email-signature|ai-services")
    changed = 0
    for path in tracked:
        if skip.search(path):
            continue
        html = open(path, encoding="utf-8").read()
        full = path in ("index.html", "about.html", "contact.html")
        pattern = re.compile(r'([ \t]*)(<script type="application/ld\+json">)(.*?)(</script>)(\n?)', re.S)

        def repl(match):
            lead, open_tag, body, close_tag, newline = match.groups()
            try:
                data = json.loads(body)
            except ValueError as error:
                print("  !! invalid JSON-LD left alone in %s: %s" % (path, error))
                return match.group(0)
            new = rewrite(path, data, full)
            if new is None:
                return match.group(0)
            if new == "DROP":
                return ""
            pretty = "\n" in body.strip()
            return lead + open_tag + dump(new, pretty, lead) + close_tag + newline

        updated = pattern.sub(repl, html)
        if updated != html:
            open(path, "w", encoding="utf-8").write(updated)
            changed += 1
            print("  updated", path)
    print("%d pages updated" % changed)


if __name__ == "__main__":
    sys.exit(main())
