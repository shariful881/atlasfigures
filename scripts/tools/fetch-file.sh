#!/usr/bin/env bash
# fetch-file (task 149): download ONE file, trying its main address and then backup addresses of the SAME file,
# for the fetch workflows of new sources (tasks 150–157). Fails unless the result is at least --min-bytes and,
# when given, starts with --expect (e.g. a CSV header), so an error page is never saved as data.
#   scripts/tools/fetch-file.sh -o data/raw/x/file.csv --min-bytes 100000 --expect 'Area Code' URL1 [URL2 …]
# Prints the address that worked (for SOURCE.md). Backups must be checked by hand before they are listed.
set -euo pipefail
OUT=''; MIN=1; EXPECT=''
URLS=()
while [ $# -gt 0 ]; do
  case "$1" in
    -o) OUT="$2"; shift 2 ;;
    --min-bytes) MIN="$2"; shift 2 ;;
    --expect) EXPECT="$2"; shift 2 ;;
    *) URLS+=("$1"); shift ;;
  esac
done
[ -n "$OUT" ] && [ ${#URLS[@]} -gt 0 ] || { echo "usage: fetch-file.sh -o OUT [--min-bytes N] [--expect TEXT] URL [URL…]" >&2; exit 2; }
UA='AtlasFigures data fetch (github.com/shariful881/atlasfigures)'
mkdir -p "$(dirname "$OUT")"
for U in "${URLS[@]}"; do
  if curl -fsSL --retry 3 --retry-delay 5 -A "$UA" -o "$OUT.part" "$U"; then
    SIZE=$(stat -c %s "$OUT.part")
    if [ "$SIZE" -lt "$MIN" ]; then echo "::warning::$U gave only $SIZE bytes" >&2; continue; fi
    if [ -n "$EXPECT" ] && ! head -c 4096 "$OUT.part" | grep -qF -- "$EXPECT"; then echo "::warning::$U does not start with the expected content" >&2; continue; fi
    mv "$OUT.part" "$OUT"; echo "$U"; exit 0
  fi
  echo "::warning::$U failed" >&2
done
rm -f "$OUT.part"
echo "::error::every address failed for $OUT" >&2
exit 1
