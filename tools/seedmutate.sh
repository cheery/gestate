#!/bin/bash
#: asked-by: Henri, 2026-08-24 — "you could already do the mutation run" — does the audit go red when a piece is taken away
# tools/seedmutate.sh — remove one piece at a time from a copy of the tree, audit the copy.
#
#     tools/seedmutate.sh            the sweep; one line per mutation, exit 1 if any survived
#
# Tests the detector, not the tree: `seedaudit.py` had only ever been run
# against a directory where every piece was present, which cannot show
# whether it notices an absence.  Each line is one mutation and the
# audit's verdict on the copy.  A mutation that leaves the audit green
# is a piece the audit cannot see going.
#
# The copy is the working tree, not `git archive` — a clone is red on its
# own for five *generated* promises (test/gates.md, target/release/ …),
# which is a finding recorded in card:working-standard.md, not something
# this sweep should re-find every run.
set -u
SRC=$(cd "$(dirname "$0")/.." && pwd)
T=$(mktemp -d "${TMPDIR:-/tmp}/seedmutate.XXXXXX"); trap 'rm -rf "$T"' EXIT
fresh() { rm -rf "$T/t"; rsync -rlt --exclude .git --exclude .venv --exclude __pycache__ --exclude target --exclude shell/editor/target "$SRC/" "$T/t/"
          mkdir -p "$T/t/target/release" "$T/t/shell/editor/target/release"; }
verdict() { if python3 "$SRC/tools/seedaudit.py" "$T/t" --quiet; then echo GREEN; else echo red; fi; }

fresh; base=$(verdict); printf '  %-8s %s\n' "$base" "intact copy"
[ "$base" = red ] && { echo "seedmutate: the intact copy is red; nothing below can be read"; exit 2; }

survived=0
mutations=$(python3 - "$SRC" <<'PY'
import sys, importlib.util, pathlib
spec = importlib.util.spec_from_file_location("sa", pathlib.Path(sys.argv[1]) / "tools/seedaudit.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
# the pieces, then the declared gate of each — read from PIECES, never
# typed here: a list typed by hand forgets the file just added, and the
# first version of this sweep reported a survivor that was only its own
# stale list naming a test no piece declared any more.
for p in m.PIECES:
    for path in p["paths"]: print(f"rm {path}")
for g in sorted({p["gate"] for p in m.PIECES}): print(f"rm {g}")
PY
)
while IFS= read -r m; do
  [ -z "$m" ] && continue
  fresh; rm -f "$T/t/${m#rm }"; v=$(verdict)
  [ "$v" = GREEN ] && survived=$((survived+1))
  printf '  %-8s %s\n' "$v" "$m"
done <<< "$mutations"
echo; echo "seedmutate: $survived survived"
[ "$survived" -eq 0 ]
