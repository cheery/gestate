#: asked-by: Henri, 2026-09-14 — "Lets start looking at what we need in order to implement multiple stages/comptime/type providers" — card:strict-forms.md; the census is the session's ruler for it
"""A census of a generated program — how many of its lines are data.

`card:strict-forms.md` §"Decided — 2026-09-14": the two generators in
the tree write a `.ges` as text from values the language already holds,
and the question staging has to answer is *how much of that text is
code and how much is data wearing a `case`*.  This prints, per
definition the generated text declares, the number of non-blank lines
under it — so the number can be taken again after a table has moved
into the language, and the difference is what a stage would still have
to write.

    python tools/generated.py grid examples/audio/arc.notes
    python tools/generated.py roll examples/audio/marked.ges

A box's numbering (`__ng_word_0__`) is stripped so two boxes of one
kind count as one row.  Nothing here is a gate; it is the ruler.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def census(text: str) -> tuple[list[tuple[int, str]], int, int]:
    """`([(lines, definition)…] by size, non-blank lines, longest line)`."""
    counts: dict[str, int] = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^(\S+) :", line)
        if m:
            current = re.sub(r"_\d+__(_s)?$", "", m.group(1))
        if not line.strip() or current is None:
            continue
        counts[current] = counts.get(current, 0) + 1
    rows = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    blank = sum(1 for l in text.splitlines() if l.strip())
    longest = max((len(l) for l in text.splitlines()), default=0)
    return [(n, name) for name, n in rows], blank, longest


def grid_text(path: Path) -> str:
    from gestate import gridbox, notes

    rels = notes.parse(path.read_text(encoding="utf-8"), path.name)
    text, _chans = gridbox.grid_program(rels, 0, "note")
    return text


def roll_text(path: Path) -> str:
    from gestate.scorebox import asks, build_rolls, roll_program

    source = path.read_text(encoding="utf-8") + "\nnotes score\n"
    roll = build_rolls(source, asks(source), 44100, 0)[0]
    text, _named = roll_program(roll, 0)
    return text


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] not in ("grid", "roll"):
        print(__doc__.strip().splitlines()[0])
        print("usage: python tools/generated.py grid|roll <file>")
        return 2
    path = Path(argv[1])
    text = grid_text(path) if argv[0] == "grid" else roll_text(path)
    rows, blank, longest = census(text)
    print(f"{argv[0]} program over {path.name}: {blank} non-blank lines, "
          f"{len(rows)} definitions, longest line {longest} chars")
    for n, name in rows:
        print(f"{n:5d}  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
