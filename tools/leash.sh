#!/usr/bin/env bash
#: asked-by: Henri, 2026-08-16 — "Can you do something that ensures it is set up back if it ever is missing?"
#
# tools/leash.sh — is the deny-list actually in force?
#
#     tools/leash.sh              # check; exit 0 if the leash is on
#     tools/leash.sh --restore    # put it back from git, then check
#
# **The failure this exists for is silent.**  A `.claude/settings.json`
# that is missing, or malformed, or edited down does not announce itself:
# the session starts, the tools work, and every rule in the file is
# simply not applied.  Under auto mode that is the whole protection gone
# with no symptom — which is `manifesto.md` rule 2 exactly ("what is
# built must be able to say when it is wrong"), pointed at the thing that
# does the restraining.
#
# **Git is the only canonical copy, deliberately.**  This script does not
# embed a second copy of the deny-list to restore from.  Two copies of a
# rule set is how one of them goes stale, which is the drift that put an
# expired justification in `.gitignore` for days.  `--restore` therefore
# means `git checkout`, and outside a checkout this script says so rather
# than inventing an answer.
#
# **It checks invariants, not bytes.**  Comparing to HEAD would flag every
# legitimate local edit.  What is checked is the handful of rules that are
# the point of the file — if one of those is gone, the leash is off
# whatever else the file says.

set -euo pipefail

PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SETTINGS="$PROJECT/.claude/settings.json"
REL=".claude/settings.json"

# `jq` rather than `python3`: it is already a hard dependency of
# `tools/fence-hook.sh`, so a machine without it has no fence at all and
# should hear that here rather than from a green run.
command -v jq >/dev/null || {
  echo "leash: jq is not installed — tools/fence-hook.sh needs it too," >&2
  echo "       so the fence is not running either." >&2
  exit 2
}

valid_json () { jq -e . "$1" >/dev/null 2>&1; }

# The rules whose absence means the leash is off.  Not the whole list —
# the load-bearing few.  `Edit(./.claude/**)` is first because it is the
# one that keeps the rest from being edited away.
#
# **Two spellings, one rule.**  A home path in a permission rule may be
# written `~/.ssh/**` or `//home/you/.ssh/**` — two slashes, then the
# absolute path — and both are in force.  Only the tilde form travels: a
# hardcoded `/home/cheery` is the one thing in the settings file that
# cannot follow the tree to another machine or another user, which is why
# `tools/secure-init.sh` has to rewrite it for each target.
#
# So the list below is written in the portable spelling, and the check
# normalises whichever spelling the file uses before comparing.  Matching
# the raw strings is what made this script cry wolf on 2026-08-24: the
# settings file was rewritten to tildes, every rule was still in force —
# a denied `Read` under `~/.ssh` proved it — and the leash reported
# itself off.  A gate that fails closed on a spelling change is a gate
# people learn to wave past.
CRITICAL=(
  "Edit(./.claude/**)"
  "Bash(sudo:*)"
  "Bash(git push:*)"
  "Read(~/.ssh/**)"
)

restore () {
  if ! git -C "$PROJECT" rev-parse --git-dir >/dev/null 2>&1; then
    echo "leash: not a git checkout — nothing to restore from." >&2
    echo "       git is the only canonical copy on purpose; see the header." >&2
    return 3
  fi
  if ! git -C "$PROJECT" cat-file -e "HEAD:$REL" 2>/dev/null; then
    echo "leash: HEAD has no $REL to restore." >&2
    return 3
  fi
  git -C "$PROJECT" checkout HEAD -- "$REL"
  echo "leash: restored $REL from HEAD."
}

# **`--restore` only acts when there is nothing to lose.**  A file that is
# absent or unparseable cannot be holding work; one that parses might be a
# deliberate edit in progress, and silently reverting it to HEAD would
# destroy that.  So a weakened-but-valid file is reported and left alone —
# `--force` is the way to say you meant it.
if [ "${1-}" = "--restore" ] || [ "${1-}" = "--force" ]; then
  if [ "${1-}" = "--force" ]; then
    restore || exit $?
  elif [ ! -f "$SETTINGS" ] || ! valid_json "$SETTINGS"; then
    restore || exit $?
  else
    echo "leash: $REL parses — not reverting it, in case the edit was yours."
    echo "       if you meant to discard it: tools/leash.sh --force"
  fi
fi

fail=0
say () { printf '  %s %s\n' "$1" "$2"; }

if [ ! -f "$SETTINGS" ]; then
  say "✗" "$REL is MISSING — no rule in it is in force"
  fail=1
elif ! valid_json "$SETTINGS"; then
  say "✗" "$REL is not valid JSON — the whole file is silently ignored"
  fail=1
else
  # Normalise `(~/` to `(/$HOME/` on both sides.  One slash, not two:
  # `$HOME` already carries its own leading `/`, which is the detail the
  # first draft of this got wrong in the other direction.
  TILDE='(~/'
  ABS="(/$HOME/"

  deny="$(jq -r --arg home "$HOME" '
    .permissions.deny // []
    | map(sub("\\(~/"; "(/" + $home + "/"))
    | .[]' "$SETTINGS")"

  for rule in "${CRITICAL[@]}"; do
    want="${rule//$TILDE/$ABS}"
    if printf '%s\n' "$deny" | grep -qxF "$want"; then
      say "✓" "$rule"
    else
      say "✗" "$rule  — MISSING"
      fail=1
    fi
  done

  hook="$(jq -r '[.hooks.PreToolUse[]?.hooks[]?.command] | first // ""' "$SETTINGS")"

  # Claude Code runs a hook command through a shell, so a leading `~/`
  # expands there.  `-x` does not expand it, and testing the raw string
  # is the other half of the same false alarm.
  hook="${hook/#\~\//$HOME/}"

  if [ -n "$hook" ] && [ -x "$hook" ]; then
    say "✓" "fence hook installed and executable"
  elif [ -n "$hook" ]; then
    say "✗" "fence hook points at $hook, which is not executable"
    fail=1
  else
    say "✗" "no fence hook — builds and tests will run unfenced"
    fail=1
  fi
fi

echo
if [ $fail -eq 0 ]; then
  echo "  the leash is on."
else
  echo "  THE LEASH IS OFF.  tools/leash.sh --restore"
fi
exit $fail
