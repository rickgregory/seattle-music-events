#!/bin/bash
# Fetch Do206 music listings for the next 90 days into scraper/fetched/do206_days/
SME="$(cd "$(dirname "$0")" && pwd)/fetched"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
OUT="$SME/do206_days"
mkdir -p "$OUT"

# Plain background jobs (not xargs -n) so paths with spaces (e.g. this repo's
# "Seattle Music" directory) aren't word-split apart.
fetch_one() {
  curl -sS -A "$UA" --max-time 40 -L -o "$1" "$2" || echo "FAIL $2"
}

n=0
for i in $(seq 0 90); do
  d=$(date -v+${i}d "+%Y/%-m/%-d")
  fn=$(date -v+${i}d "+%Y-%m-%d")
  fetch_one "$OUT/$fn.html" "https://do206.com/events/music/$d" &
  n=$((n + 1))
  if [ "$n" -ge 6 ]; then
    wait
    n=0
  fi
done
wait
ls "$OUT" | wc -l
