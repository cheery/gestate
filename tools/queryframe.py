#: asked-by: Henri, 2026-09-08 — card:gui-is-difficult.md — "lets try the query-as-picture on the notes"
"""One frame of the roll as a query — `card:gui-is-difficult.md` Q1's
first kill condition, measured.

    python tools/queryframe.py            # the page of arcnotes.ges: every roll's rows
    python tools/queryframe.py --box      # the stacked roll of line 127 alone

The rows `rows_of` gives the picture today — `(i, x, y, w, tone, dim,
mark)` a note — become a **relation**, a set literal of 7-tuples; the
picture becomes a `for` over it (every note, its hue) unioned with a
join against a selection (the selected notes, shifted and lit).  That
query is timed **forced whole**, on the reference machine and on
`crust`, beside the frame the generated program costs today for the
same rolls on the reference.  Every evaluation is whole (there is no
retraction — `card:relations-at-frame-rate.md`), so the frame number
is what a picture recomputed every frame would cost, and what one
recomputed on change would cost per change.

**Two traps this file already paid for.**  The compiler takes the
pipeline's deep stack itself, so it must never be called from inside
`_deep_stack` — nested, the two deadlock silently (found twice,
2026-09-08).  And the language has no unary minus: a negative pixel is
written `(0 - 12)`, as the generator writes it.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import retraction as R                                   # noqa: E402
from gestate import notes                                # noqa: E402
from gestate.crust import serialize                      # noqa: E402
from gestate.gui import Substrate                        # noqa: E402
from gestate.scorebox import (build_rolls, page_program,  # noqa: E402
                              rows_of, rows_reading)

PIECE = Path(__file__).resolve().parent.parent / "examples" / "audio" / "arcnotes.ges"
T7 = "(Int, Int, Int, Int, Int, Int, Int)"


def num(v: int) -> str:
    """A literal the language reads — it has no unary minus."""
    return str(v) if v >= 0 else f"(0 - {-v})"


def program(rows: list) -> str:
    literal = "{" + ", ".join("(" + ", ".join(num(v) for v in r) + ")"
                              for r in rows) + "}"
    return f"""rows : Set {T7}
rows = {literal}

sels : Set Int
sels = {{3, 17, 40, 77, 120}}

hue : Int -> Int -> Int
hue t d = t * 2 + d

pic1 : Set (Int, Int, Int, Int)
pic1 = for (r in rows) (case r of
    (i, x, y, w, t, d, m) -> {{(x, y, w, hue t d)}})

pic2 : Set (Int, Int, Int, Int)
pic2 = for (r in rows) (for (s in sels) (case r of
    (i, x, y, w, t, d, m) -> case i == s of
        True -> {{(x + 7, y - 3, w, hue t 0)}}
        False -> {{}}))

frame : Set (Int, Int, Int, Int)
frame = pic1 \\/ pic2

main : Int
main = 0
"""


def rolls_of_piece() -> list:
    source, _origins = notes.expanded(PIECE.read_text(), PIECE.parent)
    asks = [(i + 1, m.group(1))
            for i, line in enumerate(source.splitlines())
            for m in [re.match(r"^notes\s+(\S.*)$", line)] if m]
    return build_rolls(source, asks, 22050, 0)


def rows_for(rolls: list, box: int | None) -> list:
    if box is not None:
        return rows_of(rolls[box])
    # Every roll's rows, keys kept distinct across boxes.
    return [(i + 1000 * k, x, y, w, t, d, m)
            for k, rl in enumerate(rolls) if not isinstance(rl, Exception)
            for (i, x, y, w, t, d, m) in rows_of(rl)]


def reference(src: str) -> dict:
    """Milliseconds on the reference machine: the whole frame forced from
    a fresh state, then each part on its own fresh state — a global is a
    CAF, so a part timed after the frame would read as cached."""
    from gestate.pipeline import _deep_stack

    out = {}
    for name in ("frame", "rows", "pic1", "pic2"):
        state = R.compile_program(src)          # outside the deep stack
        def one(state=state, name=name):
            took, _ = R._timed(state, state.globals[name])
            out[name] = took * 1000
        _deep_stack(one)
    return out


def on_crust(src: str) -> dict:
    """Milliseconds on `crust`, best of three, process start subtracted."""
    crate = Path(__file__).resolve().parent.parent / "crust"
    subprocess.run(["cargo", "build", "--quiet", "--release",
                    "--target-dir", str(crate / "target")],
                   cwd=crate, check=True)
    binary = crate / "target" / "release" / "crust"

    def timed(main_decl: str, label: str, tmp: str) -> float:
        text = src.replace("main : Int\nmain = 0\n", main_decl)
        path = Path(tmp) / f"{label}.crust"
        path.write_text(serialize(R.compile_program(text), "main"))
        best = None
        for _ in range(3):
            began = time.perf_counter()
            subprocess.run([str(binary), str(path)], capture_output=True,
                           text=True, check=True)
            took = time.perf_counter() - began
            best = took if best is None else min(best, took)
        return best

    head4 = "main : Set (Int, Int, Int, Int)\n"
    with tempfile.TemporaryDirectory() as tmp:
        zero = timed("main : Int\nmain = 0\n", "zero", tmp)
        return {
            "rows": (timed(f"main : Set {T7}\nmain = rows\n", "rows", tmp) - zero) * 1000,
            "pic1": (timed(head4 + "main = pic1\n", "pic1", tmp) - zero) * 1000,
            "frame": (timed(head4 + "main = frame\n", "frame", tmp) - zero) * 1000,
        }


def today(rolls: list, box: int | None) -> tuple:
    """The generated program's frame on the reference, for the same
    rolls: `(ms, items)`."""
    text, _regions, entries = page_program(rolls, stacked=True, live=True)
    views = Substrate.several(text, 22050, entries)
    which = [box] if box is not None else [k for k, e in enumerate(entries) if e]
    for k in which:
        views[k].write(f"__nb_rc_{k}__", rows_reading(rolls[k]))
    best, items = None, 0
    for _ in range(3):
        began = time.perf_counter()
        items = sum(len(views[k].picture()) for k in which)
        took = time.perf_counter() - began
        best = took if best is None else min(best, took)
    return best * 1000, items


def main(argv=None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    box = 2 if "--box" in args else None
    rolls = rolls_of_piece()
    rows = rows_for(rolls, box)
    src = program(rows)
    what = "the stacked roll of line 127" if box is not None else "every roll of the page"
    print(f"{PIECE.name}, {what}: {len(rows)} rows")
    ref = reference(src)
    print(f"reference — frame {ref['frame']:.1f} ms  "
          f"(rows {ref['rows']:.1f} + every note {ref['pic1']:.1f} + join {ref['pic2']:.1f})")
    cr = on_crust(src)
    print(f"crust     — frame {cr['frame']:.1f} ms  "
          f"(rows {cr['rows']:.1f}, every note {cr['pic1']:.1f}); a frame at 60 Hz is 16.7 ms")
    ms, items = today(rolls, box)
    print(f"today     — the generated program, same rolls, on the reference: "
          f"{ms:.1f} ms a frame, {items} items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
