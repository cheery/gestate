#!/usr/bin/env python3
#: asked-by: Henri, 2026-09-18 — "Start with 1." — the number behind `card:strict-forms.md` item 1's table
"""tools/stagetime.py — the game's build, cold and warm, and whether stage one re-entered the compiler with text.

    python tools/stagetime.py                 the tic-tac-toe game, twice
    python tools/stagetime.py FILE.ges        another document program

Prints one line: the cold build of the substrate, the warm one, how many
times `pipeline._compile` was entered, and how many of those carried a
text holding `__stage_` — which is the seam item 1 of
`card:strict-forms.md` closed on 2026-09-18 (one before, zero after).
The first cold number of a process also pays for a cold disk cache;
take it twice before believing it (`journal.md` §"Stage one stopped
reading its own source — 2026-09-18").
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main(argv=None) -> int:
    from gestate import notes, pipeline
    from gestate.gui import Substrate

    args = argv if argv is not None else sys.argv[1:]
    game = Path(args[0]) if args else ROOT / "examples" / "gui" / "tic-tac-toe-facts.ges"
    count = {"stage_text": 0, "compile": 0}
    real = pipeline._compile

    def spy(source, **kw):
        count["compile"] += 1
        if "__stage_" in source:
            count["stage_text"] += 1
        return real(source, **kw)

    pipeline._compile = spy
    t = time.perf_counter()
    Substrate(notes.read(game), 22050)
    cold = time.perf_counter() - t
    t = time.perf_counter()
    Substrate(notes.read(game), 22050)
    warm = time.perf_counter() - t
    print(f"{game.name}: cold {cold:.2f} s  warm {warm:.2f} s  "
          f"_compile calls {count['compile']}  of which stage text {count['stage_text']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
