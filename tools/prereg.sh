#!/bin/bash
#: asked-by: Henri, 2026-08-24 — "It's the second issue" — nothing on either side stopped a run whose own pre-registration said it could not decide
# tools/prereg.sh — refuse to start a trial whose sheet cannot decide anything.
#
#     tools/prereg.sh PREREGISTRATION.md      exit 0 if the sheet can decide, 1 with the blank lines named
#
# Three lines, each non-empty, each somewhere in the sheet:
#
#     decision:   what changes if the result comes out either way
#     control:    what isolates the variable — and "told not to look" is not a control
#     n:          samples per arm, a number
#
# Not a judgement of the sheet.  A sheet with all three filled can still
# be wrong; a sheet with one of them blank has said in its own words that
# the run cannot decide, and on 2026-08-23 three such sheets were written
# and run anyway.  The check is the part that did not exist that day.
set -u
[ $# -eq 1 ] && [ -f "$1" ] || { echo "usage: tools/prereg.sh PREREGISTRATION.md" >&2; exit 2; }
blank=0
for k in decision control n; do
  v=$(grep -m1 -iE "^[[:space:]]*\**${k}\**:" "$1" | sed -E "s/^[[:space:]]*\**${k}\**:[[:space:]]*(\*\*)?[[:space:]]*//I")
  if [ -z "$v" ]; then echo "  BLANK   $k:"; blank=$((blank+1)); else printf '  ok      %-9s %s\n' "$k:" "$v"; fi
done
case "$(grep -m1 -iE '^[[:space:]]*\**n\**:' "$1" | sed -E 's/^[^:]*:[[:space:]]*(\*\*)?[[:space:]]*//')" in
  ''|*[!0-9]*) [ $blank -eq 0 ] && { echo "  BLANK   n: is not a number"; blank=1; } ;;
esac
[ $blank -eq 0 ] || { echo "prereg: $blank line(s) blank — the sheet says it cannot decide; do not start the arms"; exit 1; }
