#!/bin/sh
#: asked-by: Henri, 2026-08-19 — "it's a clock in the wrist that shows the time.  that might be helpful to review before you report any time."
# clock.sh — the wrist clock.  Read it before reporting any time.
#
#   tools/clock.sh              now, and how long since the last commit
#   tools/clock.sh HEAD~5       ...and how long since that commit
#   tools/clock.sh fixme.md     ...and how long since that file changed
#   tools/clock.sh 2026-08-14   ...and how long since that date
#
# Henri, 2026-08-19: *"it's a clock in the wrist that shows the time.
# that might be helpful to review before you report any time."*
#
# **Built because a session has no clock and does not know it.**  There
# is no felt duration between messages and no gradient across a
# conversation — the whole of it is present at once, undecayed — so an
# elapsed time is never *recalled*, it is inferred from how much
# happened.  That inference runs one way: a dense day reads as a long
# one.  On the day this was written `doc/consent.md` said a friend had
# been named *for a week* before he was asked.  It was one day.  The
# repository had known all along, in one command.
#
# So the rule this exists to make cheap: **an elapsed time is computed,
# never remembered.**  Nothing here is clever — that is the point.  The
# instrument that gets used is the one that costs less than the guess.
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"

# **Never a bare unit, and never rounded down to one.**  F169: this
# printed `1h` for one hour and fifty-eight minutes, and Henri read it
# and retracted a true statement — he had said "2 hours or so" and was
# right to within two minutes.  Integer division on the larger unit
# discards up to fifty-nine minutes and it discards them *one way*, so
# the instrument built to stop a session guessing was itself
# understating, silently, by up to an hour.  A clock that is read
# instead of guessed at has to be right at the boundary, because the
# boundary is where somebody checks it against what they remember.
elapsed () {
    d=$1
    if   [ "$d" -lt 3600 ];   then printf '%dm' "$((d / 60))"
    elif [ "$d" -lt 172800 ]; then printf '%dh%02dm' "$((d / 3600))" "$(((d % 3600) / 60))"
    else                           printf '%dd%dh' "$((d / 86400))" "$(((d % 86400) / 3600))"
    fi
}

now=$(date +%s)
printf 'now        %s\n' "$(date '+%Y-%m-%d %H:%M %A')"

# `%ct` is the commit's own timestamp, not the checkout's — the number
# somebody would be estimating if this script were not here.
last=$(git log -1 --format=%ct 2>/dev/null || echo '')
[ -n "$last" ] && printf 'last commit %s   (%s ago)\n' \
    "$(git log -1 --format='%h %ad' --date=format:'%Y-%m-%d %H:%M')" \
    "$(elapsed $((now - last)))"

# Today's own span, if the workbench has been open.  `presence.tsv` is
# the only record of a day that is not a commit, and a day with no
# commits is not a day with no work.
state=${XDG_STATE_HOME:-$HOME/.local/state}/gestate/presence.tsv
if [ -f "$state" ]; then
    today=$(date +%Y-%m-%d)
    line=$(grep "^$today" "$state" 2>/dev/null || true)
    [ -n "$line" ] && printf 'workbench  %s\n' \
        "$(echo "$line" | awk -F'\t' '{printf "%s to %s, %dm worked, %d touches", $2, $3, $4/60, $5}')"
fi

[ $# -eq 0 ] && exit 0

# One argument, three kinds, tried in the order that cannot be wrong:
# a path is a path even when it looks like a revision, and a date is
# only a date once git has declined it.
what=$1
if [ -e "$what" ]; then
    then_ts=$(date -r "$what" +%s); label="modified"
elif git rev-parse --verify --quiet "$what^{commit}" >/dev/null 2>&1; then
    then_ts=$(git log -1 --format=%ct "$what"); label="committed"
elif then_ts=$(date -d "$what" +%s 2>/dev/null); then
    label="that date"
else
    echo "clock: \`$what\` is not a path, a commit or a date" >&2; exit 2
fi

d=$((now - then_ts))
[ $d -lt 0 ] && { printf '\n%-10s %s — in the future\n' "$what" "$label"; exit 0; }
printf '\n%-10s %s %s\n' "$what" "$label" "$(date -d "@$then_ts" '+%Y-%m-%d %H:%M')"
printf '           %d days, %d hours, %d minutes ago\n' \
    "$((d / 86400))" "$(((d % 86400) / 3600))" "$(((d % 3600) / 60))"
