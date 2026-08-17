#!/bin/sh
# andon.sh — pull the cord.  A session needs Henri.
#
#   tools/andon.sh              ring once
#   tools/andon.sh 3            ring three times, eight seconds apart
#
# The sound is `tools/andon.ges`, and why it sounds the way it does is
# written there.  This script exists so a session rings it the same way
# every time instead of re-deriving the flags — and so the *interval*
# between rings is decided once, here, rather than in a loop somebody
# writes at two in the morning.
#
# It is deliberately hard to make this loud or frequent.  Rings are
# capped at three: if three calls eight seconds apart did not reach him,
# he is not in the room, and ringing thirty times will not change that —
# it will only be waiting, at volume, when he walks back in.
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
times=${1:-1}
# A count that is not a count is a typo, not a request for silence: say
# so rather than ringing zero times and exiting clean, which is the one
# failure a cord may not have.
case $times in
    ''|*[!0-9]*) echo "andon: \`$times\` is not a number of rings" >&2; exit 2 ;;
esac
[ "$times" -lt 1 ] && times=1
[ "$times" -gt 3 ] && times=3

i=0
while [ "$i" -lt "$times" ]; do
    [ "$i" -gt 0 ] && sleep 8
    (cd "$root" && python -m gestate.audioperform tools/andon.ges --seconds 5) >/dev/null 2>&1 \
        || { echo "andon: could not reach the sound card" >&2; exit 1; }
    i=$((i + 1))
done
