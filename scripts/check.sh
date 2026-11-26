#!/bin/bash
# Green gate for mongsil-rest — run before every commit. Exit 0 = green.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/kit_lock.py check
echo "== 1/2 unit tests"; python3 -m unittest discover -s tests -q
echo "== 2/2 build is up to date (페이지·SEO 파일을 다시 만들어 비교)"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
rsync -a --exclude='.git' ./ "$tmp/"
python3 "$tmp/scripts/build.py" >/dev/null 2>&1
for f in $(git ls-files -co --exclude-standard '*.html' assets/ipe-lang.js sitemap.xml robots.txt llms.txt); do
  cmp -s "$f" "$tmp/$f" || { echo "$f is stale — run: python3 scripts/build.py"; exit 1; }
done
echo "GREEN"
