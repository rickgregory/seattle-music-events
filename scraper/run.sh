#!/usr/bin/env bash
# Refresh the Seattle music-events calendar end to end.
# Usage: ./scraper/run.sh            (live fetch + build + commit + push)
#        ./scraper/run.sh --no-fetch (rebuild from already-fetched HTML in scraper/fetched/)
set -u
PROJ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJ"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
SME="$PROJ/scraper"
NO_FETCH=0
[ "${1:-}" = "--no-fetch" ] && NO_FETCH=1

echo "=== [1/4] Fetch sources ==="
if [ "$NO_FETCH" -eq 0 ]; then
  mkdir -p "$SME/fetched"
  curl -sS -A "$UA" --max-time 90 -L -o "$SME/fetched/everout.html" "https://everout.com/seattle/music/" \
    && echo "everout: $(wc -c < "$SME/fetched/everout.html") bytes" || echo "everout FETCH FAILED"
  curl -sS -A "$UA" --max-time 60 -L -o "$SME/fetched/eca.html" "https://www.edmondscenterforthearts.org/events/" \
    && echo "eca: $(wc -c < "$SME/fetched/eca.html") bytes" || echo "eca FETCH FAILED"
  for p in 0 1; do
    curl -sS -A "$UA" --max-time 45 -L -o "$SME/fetched/uw$p.html" \
      "https://artsevents.washington.edu/artsuw-events?event_genre%5B30%5D=30&view_id=event_listing&display_id=embed_1&page=$p" \
      && echo "uw$p: $(wc -c < "$SME/fetched/uw$p.html") bytes" || echo "uw$p FETCH FAILED"
  done
  bash "$SME/fetch_do206.sh" || echo "do206 FETCH FAILED (non-fatal)"
else
  echo "skipped (--no-fetch)"
fi

echo "=== [2/4] Parse + dedupe + genre ==="
( cd "$SME" && python3 pipeline.py ) 2>&1 | grep -vE "DeprecationWarning|re\.split" | tail -8

echo "=== [3/4] Generate HTML ==="
( cd "$SME" && python3 gen_html.py )

echo "=== [4/4] Commit + push ==="
DATESTAMP="$(date "+%b %d, %Y")"
git add -A
git commit -q -m "Weekly refresh $DATESTAMP" && echo "committed" || echo "nothing to commit"
git push origin main 2>&1 | tail -3
echo "DONE"
