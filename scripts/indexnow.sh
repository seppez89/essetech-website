#!/bin/bash
# Tell Bing (and the other IndexNow search engines) which pages changed.
# Bing's index feeds Microsoft Copilot and DuckDuckGo, and ChatGPT draws on it for some searches,
# so run this after every deploy that changes a page.
#   scripts/indexnow.sh                 -> submits every URL in sitemap.xml
#   scripts/indexnow.sh URL [URL ...]   -> submits just those URLs
# The key file 27cfc73280cc6bc279c6f4b0bbd2540f.txt in the site root proves we own the domain. No account is needed.
set -euo pipefail
cd "$(dirname "$0")/.."
KEY="27cfc73280cc6bc279c6f4b0bbd2540f"
HOST="www.essetech.com.au"
if [ "$#" -gt 0 ]; then
  URLS=$(printf '%s\n' "$@")
else
  URLS=$(grep -o '<loc>[^<]*</loc>' sitemap.xml | sed -e 's/<loc>//' -e 's#</loc>##')
fi
BODY=$(printf '%s\n' "$URLS" | python3 -c '
import json, sys
urls = [u.strip() for u in sys.stdin if u.strip()]
print(json.dumps({"host": sys.argv[1], "key": sys.argv[2], "keyLocation": "https://%s/%s.txt" % (sys.argv[1], sys.argv[2]), "urlList": urls}))
' "$HOST" "$KEY")
COUNT=$(printf '%s\n' "$URLS" | grep -c . || true)
CODE=$(curl -s -o /dev/null -w '%{http_code}' -m 30 -X POST 'https://api.indexnow.org/indexnow' -H 'Content-Type: application/json; charset=utf-8' -d "$BODY")
echo "IndexNow: submitted $COUNT URLs, HTTP $CODE (200 or 202 = accepted)"
