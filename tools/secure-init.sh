#!/usr/bin/env bash
#: asked-by: Henri, 2026-08-16 — "There is no protection in place, in case there's injection attack or bad luck with dependencies." — the same fence, portable to a new machine
#
# tools/secure-init.sh — give another project the same fence.
#
#     tools/secure-init.sh ~/newproject
#     tools/secure-init.sh ~/newproject --dry-run
#
# Installs, into the target project: `sandbox.sh` (the bwrap fence and its
# thirteen-probe self-check), `fence-hook.sh` (builds and tests wrapped by
# default), `leash.sh` (does the deny-list actually apply?), the AppArmor
# profile, and a `.claude/settings.json` carrying the deny-list.
#
# **Why this lives in gestate rather than in a template repo.**  Because
# `spec/sandbox.md` is the argument for every one of those files, and a
# template that travels without its reasoning is a set of magic scripts.
# Copying reasoning is what goes stale; here the scripts and the argument
# for them stay in one tree, and this command is how another project
# borrows both.
#
# **There is no second copy of the rules.**  The deny-list is read from
# *this* project's `.claude/settings.json` and rewritten for the target.
# Two copies of a rule set is how one goes stale — the same reason
# `leash.sh` restores from git rather than from an embedded copy, and the
# same drift that left an expired justification in `.gitignore` for days.
# gestate's own settings file is the source; improve it there and every
# later project gets the improvement.
#
# What it does NOT do: anything needing root.  The AppArmor profile is
# copied in and the two `sudo` lines are printed for you to run.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DRY=0
TARGET=""

for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    -*) echo "secure-init: unknown option $a" >&2; exit 2 ;;
    *)  TARGET="$a" ;;
  esac
done

[ -n "$TARGET" ] || { echo "usage: tools/secure-init.sh <project-dir> [--dry-run]" >&2; exit 2; }
TARGET="$(cd "$TARGET" 2>/dev/null && pwd)" || { echo "secure-init: no such directory: $TARGET" >&2; exit 2; }
[ "$TARGET" != "$SRC" ] || { echo "secure-init: that is this project." >&2; exit 2; }

say () { printf '  %s\n' "$1"; }
do_ () { if [ $DRY -eq 1 ]; then say "would: $*"; else "$@"; fi; }

echo "secure-init: $SRC  ->  $TARGET"
[ $DRY -eq 1 ] && echo "  (dry run — nothing is written)"

do_ mkdir -p "$TARGET/tools" "$TARGET/.claude"

for f in sandbox.sh fence-hook.sh leash.sh apparmor-bwrap.profile; do
  if [ -e "$TARGET/tools/$f" ] && [ $DRY -eq 0 ]; then
    say "kept:    tools/$f (already there — not overwritten)"
  else
    do_ cp "$SRC/tools/$f" "$TARGET/tools/$f"
    say "copied:  tools/$f"
  fi
done
[ $DRY -eq 0 ] && chmod +x "$TARGET"/tools/*.sh

# The deny-list, rewritten for the target: absolute home paths normalised
# to whoever is running this, and the fence hook repointed at the target's
# own copy.  Everything else carries over untouched.
if [ -e "$TARGET/.claude/settings.json" ] && [ $DRY -eq 0 ]; then
  say "kept:    .claude/settings.json (already there — not overwritten)"
else
  do_ python3 - "$SRC/.claude/settings.json" "$TARGET/.claude/settings.json" "$HOME" "$TARGET" <<'PY'
import json, re, sys
src, dst, home, target = sys.argv[1:5]
d = json.load(open(src))
d["permissions"]["deny"] = [
    re.sub(r"//[^/]+/[^/]+/", "/" + home + "/", r) if "//" in r else r
    for r in d["permissions"]["deny"]
]
d["hooks"] = {"PreToolUse": [{"matcher": "Bash", "hooks": [
    {"type": "command", "command": f"{target}/tools/fence-hook.sh"}]}]}
json.dump(d, open(dst, "w"), indent=2)
open(dst, "a").write("\n")
PY
  say "wrote:   .claude/settings.json (deny-list, hook repointed)"
fi

echo
if [ $DRY -eq 1 ]; then
  echo "  dry run complete."
  exit 0
fi

# **Verify rather than announce.**  The whole point of the thing being
# installed is that it says when it is wrong, so installation ends by
# asking it.
echo "  --- the fence ---"
if "$TARGET/tools/sandbox.sh" --check >/dev/null 2>&1; then
  say "fence is up (tools/sandbox.sh --check passes)"
else
  say "FENCE NOT UP.  Almost always the AppArmor profile; run:"
  say "    sudo install -m 644 $TARGET/tools/apparmor-bwrap.profile /etc/apparmor.d/bwrap"
  say "    sudo apparmor_parser -r /etc/apparmor.d/bwrap"
  say "  then: $TARGET/tools/sandbox.sh --check"
fi

echo "  --- the leash ---"
"$TARGET/tools/leash.sh" || true

echo
echo "  Remaining, and they need you:"
echo "    * branch protection on the new repo (blocks force-push; the backstop)"
echo "    * open /hooks once so the fence hook is picked up"
echo "    * doc/hardening.md in $SRC is the full runbook"
