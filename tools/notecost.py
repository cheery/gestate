#!/usr/bin/env python3
"""What one read of a `.notes` file costs — the query cost under interaction.

    python tools/notecost.py [FILE.notes]

**Why this exists.**  Guest fable, 2026-09-10, on the relational model
in this tree: *"the query-cost-under-interaction problem is the one
that has actually killed relational-UI attempts, not the modeling."*
Eve is the case — a UI as a query over a record store, stopped in 2018,
and performance under interaction is the first of the four failure
modes `doc/notes/notes-on-the-model.md` already lists.

So the reader's cost is a number, on his own piece, re-runnable.  Every
line here is paid on a keystroke: the editor reparses the file it is
looking at, redraws the page's rolls and rewrites the file a gesture
touched.  A frame at 60 Hz is 16.7 ms and the whole of a read has to
fit inside one, with the drawing.

**What it caught.**  Retiring the record classes
(`card:relational-model.md` Q6) put every reader on the relations, and
the first shape of the join scanned a relation per note — O(n·m), 291
notes on `arc.notes`, and the view went from 1.6 ms to 13.8 ms.
`facts.Relation.by` indexes once instead, which is what an engine does
for a join, and the view came back to 5 ms.  The lesson is the one the
literature gives: the model is not what costs, the *query per row* is.
"""

#: asked-by: outside, 2026-09-10 — "the query-cost-under-interaction problem is
#: the one that has actually killed relational-UI attempts, not the modeling."
#: — guest fable, relayed by Henri while the readers were being moved onto the
#: relations; card:relational-model.md §"Guest fable's three"

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gestate import notes                                    # noqa: E402
from gestate.scorebox import asks, notes_rolls               # noqa: E402

#: One frame at 60 Hz.  A read that costs more than this cannot happen
#: on a keystroke without the window missing it.
FRAME_MS = 1000 / 60


def took(label: str, fn, rounds: int = 10) -> float:
    fn()                                            # warm, then measure
    at = time.perf_counter()
    for _ in range(rounds):
        fn()
    ms = (time.perf_counter() - at) / rounds * 1000
    mark = "  " if ms < FRAME_MS else " ← past a frame"
    print(f"  {label:<24} {ms:6.2f} ms{mark}")
    return ms


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else (
        Path(__file__).resolve().parent.parent / "examples" / "audio" / "arc.notes")
    if not path.exists():
        print(f"notecost: no such file: {path}", file=sys.stderr)
        return 1
    raw = path.read_text(encoding="utf-8")
    rels = notes.parse(raw, path.name, where=path)
    written = notes.notes_of(rels)
    print(f"{path.name} — {len(written)} notes, "
          f"{len(notes.sections_of(rels))} sections, "
          f"a frame is {FRAME_MS:.1f} ms\n")

    took("parse (the gate)", lambda: notes.parse(raw, path.name, where=path))
    took("relations_of", lambda: notes.relations_of(raw, path.name, where=path))
    took("notes_of", lambda: notes.notes_of(rels))
    took("sections_of", lambda: notes.sections_of(rels))
    took("write", lambda: notes.write(rels))
    took("refused (the rules)", lambda: notes.refused(rels))

    text = notes.wrapper(path)
    source, origins = notes.expanded(text, path.parent)
    page = asks(source)
    print()
    took(f"the page's {len(page)} rolls",
         lambda: notes_rolls(source, page, origins, rels))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
