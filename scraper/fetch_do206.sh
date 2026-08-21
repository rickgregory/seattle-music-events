#!/bin/bash
# Fetch Do206 music listings for the next 90 days into /tmp/sme/do206_days/
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
OUT=/tmp/sme/do206_days
mkdir -p "$OUT"
for i in $(seq 0 90); do
  d=$(date -v+${i}d "+%Y/%-m/%-d")
  fn=$(date -v+${i}d "+%Y-%m-%d")
  echo "https://do206.com/events/music/$d $OUT/$fn.html"
done > /tmp/sme/do206_urls.txt

cat /tmp/sme/do206_urls.txt | xargs -P 6 -n 2 sh -c 'curl -sS -A "'"$UA"'" --max-time 40 -L -o "$1" "$0" || echo "FAIL $0"'
ls "$OUT" | wc -l
