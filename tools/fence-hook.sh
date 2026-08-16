#!/usr/bin/env bash
#
# tools/fence-hook.sh — put builds and tests inside the fence by default.
#
# A `PreToolUse` hook on `Bash`.  It reads the tool call on stdin and, when
# the command is one that **executes dependency code**, rewrites it to run
# under `tools/sandbox.sh`.  Everything else passes through untouched.
#
# **Why only builds and tests.**  `spec/sandbox.md` keeps two threats
# apart, and the fence answers exactly one of them: dependency code
# executing.  `cargo` runs build scripts and proc-macros as arbitrary code
# at compile time and `pytest` imports whatever is importable — those two
# are the whole exposure, so those two are what is wrapped.  Wrapping more
# would be theatre, and wrapping the window would be a bug (see below).
#
# **What must NOT be wrapped, and why**
#
#   * anything that opens a window — `gestate.workbench`, the editor, the
#     panel.  The fence binds no X11 socket, so a wrapped window does not
#     fail safely, it just fails.
#   * `cargo fetch` — the fence has no network, which is the point.  Use
#     `tools/sandbox.sh --net cargo fetch` deliberately, on the rare
#     occasion the lock genuinely moves.
#   * anything already inside the fence — no double wrapping.
#
# **The escape hatch.**  Prefix a command with `NOFENCE=1` and it runs
# unwrapped.  That is deliberate and visible: an unfenced build should
# take a word to ask for.
#
# Install: see doc/hardening.md §"Making the fence automatic".

set -euo pipefail

PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

payload="$(cat)"
cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // ""')"

# Nothing to do: no command, already fenced, or explicitly opted out.
case "$cmd" in
  ""|*tools/sandbox.sh*|NOFENCE=1*) exit 0 ;;
esac

# `cargo fetch` and `cargo update` want the network the fence removes.
if printf '%s' "$cmd" | grep -qE '(^|[;&|]|\n)[[:space:]]*cargo[[:space:]]+(fetch|update|login|publish)\b'; then
  exit 0
fi

# Anything that draws needs an X11 socket the fence does not bind.
if printf '%s' "$cmd" | grep -qE 'gestate\.(workbench|panel|editor)|--window|audioperform'; then
  exit 0
fi

# The two that execute dependency code, anchored to a command position.
#
# **This biases towards NOT wrapping, on purpose.**  A missed wrap is a
# build running unfenced — bad, but visible, and `tools/sandbox.sh` can
# always be typed by hand.  A false wrap *breaks a working command*, which
# is worse and harder to diagnose.  The first version of this line used
# `[;&|]` as the separator class and wrapped
#
#     ps -eo args= | awk '/suite\.py|pytest/ {print}'
#
# because the `|` **inside the awk pattern** read as a command position.
# So: a separator must be followed by whitespace, and `|` is not a
# separator at all — nothing is ever piped *into* `pytest` or `cargo`.
FENCED='(^|&&[[:space:]]|;[[:space:]]|\|\|[[:space:]])[[:space:]]*((python3?[[:space:]]+-m[[:space:]]+)?pytest|cargo[[:space:]]+(build|test|check|clippy|bench))\b'

if ! printf '%s' "$cmd" | grep -qE "$FENCED"; then
  exit 0
fi

# `jq -Rsr` — raw in, raw out.  Without `-r` the shell quoting comes back
# JSON-encoded and the escapes reach bash doubled, which is the second bug
# the awk command above exposed.
quoted="$(printf '%s' "$cmd" | jq -Rsr 'rtrimstr("\n") | @sh')"
wrapped="$PROJECT/tools/sandbox.sh bash -c $quoted"

jq -n --arg w "$wrapped" --argjson orig "$(printf '%s' "$payload" | jq '.tool_input')" '
  {
    systemMessage: "fenced: running under tools/sandbox.sh",
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      updatedInput: ($orig + {command: $w}),
      permissionDecisionReason: "builds and tests run inside the fence (tools/fence-hook.sh); prefix NOFENCE=1 to opt out"
    }
  }'
