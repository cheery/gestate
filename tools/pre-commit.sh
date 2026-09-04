#!/bin/sh
#: asked-by: Henri, 2026-08-19 — "lets start and implement the cheap-gates.  It could be a git hook."
#
# tools/pre-commit.sh — the gates, at the commit that breaks them.
#
#     tools/pre-commit.sh --install     put it in .git/hooks/pre-commit
#     tools/pre-commit.sh --uninstall   take it out again
#     tools/pre-commit.sh --check       say whether it is installed
#     tools/pre-commit.sh               run the gates now (what the hook does)
#
# **Why a hook and not a note in a file.**  `card:cheap-gates.md` is the
# day this was paid for: eight checks costing seventeen seconds ran once
# in a shift, at the end, and died on a breakage that had been in the
# tree for hours — landing as a chore on the author with half an hour
# left in his day.  A rule in `board/README.md` would have been read by
# the same session that had already skipped it four times.  Henri,
# 2026-08-19, answering the card's open question: *"lets start and
# implement the cheap-gates.  It could be a git hook."*
#
# **And the twelve seconds are not a cost.**  Henri, 2026-08-19, when
# the hook was running: *"as a git hook card:cheap-gates.md also gives
# some time to think before committing.  I think it's a quality
# assurance."*  Which turns the one argument against a hook — that it
# is slower than no hook — into the second argument for it.  A commit
# is the end of a card on this board, not a punctuation mark inside
# one, and there was nothing between deciding to make one and having
# made it.
#
# **It fires on his commits too, and that was the objection.**  The
# answer is not to make it clever about who is committing — it cannot
# know — but to make it cheap, loud about what failed, and trivial to
# remove.  Hence `--uninstall`, named in the failure message.
#
# **It checks the working tree, not the index**, which is a real gap
# and a deliberate one: a `git add -p` that stages half a rename can
# pass here and still commit a broken tree.  Stashing to test the index
# exactly is the standard fix and it is *not* worth it — it moves a
# session's uncommitted work through a stash on every commit, and the
# gates check whether the tree's documents agree with each other, which
# is a property of the tree the next reader opens rather than of the
# diff.  What is caught is the case that actually happened.
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

# The shim, rather than a symlink: it survives the repository being
# moved or checked out somewhere else, and it works from a worktree,
# whose hooks directory is not two levels under the top.  The marker on
# the second line is how --check and --uninstall recognise their own
# work and refuse to touch anybody else's hook.
MARKER='gestate:tools/pre-commit.sh'

hookdir=$(git -C "$root" rev-parse --git-path hooks 2>/dev/null || echo '')
case "$hookdir" in /*) ;; *) hookdir="$root/$hookdir" ;; esac
hook="$hookdir/pre-commit"

case "${1:-}" in
--install)
    if [ -e "$hook" ] && ! grep -q "$MARKER" "$hook" 2>/dev/null; then
        echo "pre-commit: $hook exists and is not ours — not overwriting it." >&2
        echo "            look at it, then move it aside if you want this one." >&2
        exit 3
    fi
    mkdir -p "$hookdir"
    cat > "$hook" <<'SHIM'
#!/bin/sh
# gestate:tools/pre-commit.sh — installed by `tools/pre-commit.sh --install`.
# Not tracked (hooks never are); remove with `tools/pre-commit.sh --uninstall`.
exec "$(git rev-parse --show-toplevel)/tools/pre-commit.sh"
SHIM
    chmod +x "$hook"
    echo "pre-commit: installed at $hook"
    echo "            every commit now runs the gates first (about 12s)."
    exit 0
    ;;
--uninstall)
    if [ ! -e "$hook" ]; then
        echo "pre-commit: nothing installed at $hook"
    elif grep -q "$MARKER" "$hook" 2>/dev/null; then
        rm -f "$hook"; echo "pre-commit: removed $hook"
    else
        echo "pre-commit: $hook is not ours — left alone." >&2; exit 3
    fi
    exit 0
    ;;
--check)
    if [ -x "$hook" ] && grep -q "$MARKER" "$hook" 2>/dev/null; then
        echo "✓ pre-commit hook installed — the gates run at every commit"
        exit 0
    fi
    echo "✗ no pre-commit hook — run tools/pre-commit.sh --install"
    exit 1
    ;;
-h|--help)
    sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
    ;;
"") ;;
*)  echo "pre-commit: unknown argument \`$1\`" >&2; exit 2 ;;
esac

cd "$root"

# **The venv, if there is one.**  `python3` on `PATH` is whatever the
# caller's shell has.  With the venv activated that is the right
# interpreter and this changes nothing; without it — git runs hooks with
# the environment it was given, and a session's shell activates nothing —
# it is `/usr/bin/python3`, which has no `pytest`, so every gate dies as
# "No module named pytest" and the commit is refused for a reason that
# has nothing to do with the commit.  Found 2026-08-24, refusing one.
PY=python3
[ -x "$root/.venv/bin/python" ] && PY="$root/.venv/bin/python"

if "$PY" tools/suite.py --gates; then
    # The one check the fenced gates cannot make: the private memory
    # index lives outside the repository, and the suite binds only the
    # repository.  This hook is run by git, unfenced, so it can look.
    # Exits 0 where there is no index (another machine, a seed).
    "$PY" tools/memoryindex.py --check || {
        echo >&2 ""
        echo >&2 "pre-commit: the boot index is behind doc/memory/README.md; run:"
        echo >&2 "            $PY tools/memoryindex.py"
        exit 1
    }
    # A lamp, not a gate: the install is behind the leash and is Henri's,
    # and a red a session cannot clear is a red that gets muted
    # (card:backlinks.md).  So it prints and never refuses.
    "$PY" tools/backlinks.py --check || true
    exit 0
fi

cat >&2 <<'MSG'

pre-commit: a gate failed, so this commit was refused.

  Named above, and in test/gates.md.  These eight take seconds and are
  about documents rather than behaviour — the board's contract, the
  citations, the consent file, the atlas, doc/ref/, the complaints page,
  the two example rosters.  A red one nearly always means an edit in
  this commit left a page behind the tree it describes, and fixing it
  belongs in this commit rather than in somebody's morning.

  To commit anyway:      git commit --no-verify
  To stop this entirely: tools/pre-commit.sh --uninstall

  If you use --no-verify, say in the commit body which gate you skipped.
  A skipped gate nobody wrote down is the state this hook was built to
  end.

MSG
exit 1
