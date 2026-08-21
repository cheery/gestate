#!/usr/bin/env bash
#
# tools/limit.sh — a sitting has a length, and the length is not a session's to judge.
#
#     tools/limit.sh              how long this sitting has run, and what is left
#     tools/limit.sh reset        start a new sitting (refused inside a session)
#     tools/limit.sh stop "why"   close this sitting now — the one call a session may make
#     tools/limit.sh --hook       as a UserPromptSubmit hook: block past the limit
#
# **Declaring a longer sitting.**  Type `sitting 90` as a whole prompt.  The
# hook reads it, sets the length, and never passes it on — it is a control
# word, not a question.  `sitting` alone is the default 15.
#
# **Why this is a script and not a promise.**  Henri, 2026-08-21: *"Me
# logging in to ask or check one small thing, then it explodes into two
# hours.  Can you set me a limit?"*  A session agreeing to stop at fifteen
# minutes is the same thing that wants to keep going, holding its own leash
# — see doc/memory/weights-context-suite.md: enforcement stays outside the
# model, in checks the model cannot write to.  So the stop lives here, and
# the install line lives in `.claude/settings.json`, which the fence denies
# a session.  That denial is the feature.
#
# **The length is declared at the door, not at the buzzer.**  Henri,
# 2026-08-21: *"What do we do when it\'s time to work?"*  The answer is not
# a longer default — the unstated sitting is the dangerous one, and 15 is
# right for it.  It is that a work sitting is one you **name a number for
# before you start**, while you are cold.  At minute 15, deep in it, you are
# the worst available judge of whether to continue; at the door you are the
# best.  Typing a number is a decision.  Hitting the same key again is a
# reflex, and a limit dismissed by reflex has stopped being a limit.
#
# **A session may end a sitting and may never extend one.**  Henri,
# 2026-08-21: *"Could you make it such that you set the timer to kick me
# out?"*  Yes, in one direction only.  Ending can cost nothing but time he
# wanted, and he can sit down again with a word a session cannot type;
# extending is the direction where a session\'s pull and his in-flow impulse
# point the same way with nothing on the other side.  So `stop` is open to a
# session and `reset` is shut.
#
# **And the grant is out of a session\'s reach on purpose.**  It arrives only
# as a typed prompt, which the hook reads on stdin and a session cannot
# produce.  `reset` from the command line is refused while CLAUDECODE is
# set, so the escape hatch is a real terminal, not this one.  A session may
# *read* the clock freely — reading grants nothing.
#
# **A sitting ends by silence.**  No stamp, or a gap longer than
# GESTATE_LIMIT_GAP minutes since the last prompt, starts a new one — which
# is the shape of the actual problem: logging in for one small thing.
#
# Env: GESTATE_LIMIT_MIN (default 15), GESTATE_LIMIT_GAP (default 30).
#
# Install: add to .claude/settings.json —
#
#     "UserPromptSubmit": [ { "hooks": [ { "type": "command",
#       "command": "/home/cheery/gestate/tools/limit.sh --hook" } ] } ]

set -euo pipefail

LIMIT_MIN="${GESTATE_LIMIT_MIN:-15}"
GAP_MIN="${GESTATE_LIMIT_GAP:-30}"
STATE="${XDG_RUNTIME_DIR:-/tmp}/gestate-sitting-$(id -u)"

now=$(date +%s)
started=0
last=0
limit="$LIMIT_MIN"
closed=""
[ -f "$STATE" ] && read -r started last limit closed < "$STATE" || true
[ -n "$limit" ] || limit="$LIMIT_MIN"

case "${1:-}" in
  stop)
    [ "$started" -eq 0 ] && started=$now
    printf '%s %s %s %s\n' "$started" "$now" 0 "${2:-the thing you came for is done}" > "$STATE"
    echo "sitting closed at $(date +%H:%M)."
    exit 0 ;;
  reset)
    if [ -n "${CLAUDECODE:-}" ]; then
      echo "limit: refused — a sitting is not granted from inside a session." >&2
      echo "       type \`sitting 90\` as a prompt, or run this from a real terminal." >&2
      exit 3
    fi
    printf '%s %s %s\n' "$now" "$now" "$LIMIT_MIN" > "$STATE"
    echo "new sitting, $(date +%H:%M).  $LIMIT_MIN minutes."
    exit 0 ;;
esac

# A fresh sitting: nothing stamped, or the desk was empty long enough.
if [ "$started" -eq 0 ] || [ $(( (now - last) / 60 )) -ge "$GAP_MIN" ]; then
  started=$now
  limit="$LIMIT_MIN"
fi

if [ "${1:-}" = "--hook" ]; then
  prompt="$(cat | jq -r '.prompt // ""')"
  # The one grant a session cannot forge: a word Henri typed himself.
  if [[ "$prompt" =~ ^[[:space:]]*sitting([[:space:]]+([0-9]+))?[[:space:]]*$ ]]; then
    limit="${BASH_REMATCH[2]:-$LIMIT_MIN}"
    printf '%s %s %s\n' "$now" "$now" "$limit" > "$STATE"
    echo "Sitting of $limit minutes, from $(date +%H:%M).  Ends $(date -d "@$((now + limit*60))" +%H:%M)." >&2
    exit 2
  fi
fi

elapsed=$(( (now - started) / 60 ))
left=$(( limit - elapsed ))

if [ "${1:-}" = "--hook" ]; then
  printf '%s %s %s %s\n' "$started" "$now" "$limit" "$closed" > "$STATE"
  if [ "$elapsed" -ge "$limit" ]; then
    # exit 2 on UserPromptSubmit: the prompt is blocked, this text goes to Henri.
    if [ "$limit" -eq 0 ]; then
      echo "Sitting closed — $closed." >&2
      echo "It started $(date -d "@$started" +%H:%M) and it is now $(date +%H:%M).  Nothing is lost; the tree holds it." >&2
    else
      echo "The $limit minutes are up — this sitting started at $(date -d "@$started" +%H:%M), it is now $(date +%H:%M)." >&2
      echo "You asked for this stop on 2026-08-21.  Write down what you were about to ask, and come back to it." >&2
    fi
    echo "To sit down again on purpose, type: sitting 45   (or any number of minutes)" >&2
    exit 2
  fi
  exit 0
fi

if [ "$limit" -eq 0 ]; then
  echo "sitting  closed at $(date -d "@$last" +%H:%M) — $closed"
else
  echo "sitting  started $(date -d "@$started" +%H:%M), ${elapsed}m in, ${left}m left of $limit"
fi
