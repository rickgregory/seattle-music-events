#!/bin/bash
cd /Users/rickgregory/Desktop/seattle-music-events
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
echo "=== spot-check 8 event URLs (EverOut/Bandsintown bot-block curl per skill) ==="
grep -oE 'href="https://(do206|www\.edmondscenterforthearts|artsevents\.washington|everout)[^"]+"' index.html \
  | sed 's/href="//;s/"$//' | sort -u | awk 'NR%37==1' | head -8 | while read u; do
  printf "%s  %s\n" "$(curl -sS -o /dev/null -w '%{http_code}' -A "$UA" --max-time 30 -L "$u")" "$u"
done
