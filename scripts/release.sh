#!/bin/bash
# One command to build, check and (optionally) ship essetech.com.au.
#
#   scripts/release.sh            build + check only (safe; changes generated files, pushes nothing)
#   scripts/release.sh --push     build + check, then pull --rebase, push to main and ping IndexNow
#
# The order is the documented one (project_essetech_deploy memory): page builder ->
# key facts -> footer links -> schema identity -> Tailwind -> checks. It refuses to
# push if the checks fail or if anything is left uncommitted after the build, so
# generated changes always ship together with the commit that caused them.
# Added 22 Nov 2026 (AI ecosystem audit, Week 2).
set -euo pipefail
cd "$(dirname "$0")/.."
PUSH=0; [ "${1:-}" = "--push" ] && PUSH=1

step() { printf '\n== %s\n' "$*"; }

step "1/6 build-pages.py";     python3 scripts/build-pages.py
step "2/6 key-facts.py";       python3 scripts/key-facts.py
step "3/6 footer-links.py";    python3 scripts/footer-links.py
step "4/6 schema-identity.py"; python3 scripts/schema-identity.py
step "5/6 Tailwind";           npx --yes tailwindcss@3.4.17 -c tailwind.config.js -i tailwind-input.css -o tailwind.css --minify 2>&1 | tail -1
step "6/6 checks";             python3 scripts/check-site.py

[ "$PUSH" = 1 ] || { printf '\nBuild + checks passed. Nothing pushed. Commit, then run: scripts/release.sh --push\n'; exit 0; }

# Only tracked, deployable changes matter; untracked drafts are reported by the check.
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo; echo "STOP: the build left uncommitted changes to tracked files:"; git status -s --untracked-files=no
  echo "Review and commit them, then run --push again."; exit 1
fi

step "pull --rebase (Grok may have pushed)"; git pull --rebase -q origin main
python3 scripts/check-site.py >/dev/null || { echo "Checks fail after pulling. Not pushing."; exit 1; }
step "push";      git push -q origin main
step "IndexNow";  scripts/indexnow.sh
printf '\nShipped %s. Vercel deploys main automatically; check the live site in about a minute.\n' "$(git rev-parse --short HEAD)"
