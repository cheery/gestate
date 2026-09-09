#: asked-by: Henri, 2026-09-09 — card:gui-is-difficult.md — "mittaa se"
"""What it costs when every note is its own pressable element.

    python tools/pressable.py            # the stacked roll of line 127, 88 notes
    python tools/pressable.py --page     # every roll of arcnotes.ges at once
    python tools/pressable.py --n 291    # the rows repeated up to a size

`card:gui-is-difficult.md`'s clean-board sitting asks whether an
element can carry *what it is* — a note — instead of a pad carrying
*where you touched it*.  Everything else about that question is
readable in the tree; this is the one number that is not: the roll
draws hundreds of notes, and today exactly one invisible `Gap 0 0`
over the whole body is pressable.

**Three pictures of the same notes, differing only in what is
attached**, drawn from the real rows of `examples/audio/arcnotes.ges`:

| | what it is |
|---|---|
| `padded` | today's shape — the notes by recursion over a list, one pad over the lot |
| `marked` | one extra `Sub` node per note (a `Sized` that changes nothing) — the **floor**: what `On <meaning>` would cost the walk, the wire and the hit test |
| `channelled` | a `TouchY`/`TouchX` and two `chan` declarations per note — the **ceiling**: per-note pressability with today's only mechanism |

The floor and the ceiling are two different questions and both are
worth having.  `On` carries a *value*, so it travels inside the
recursion that draws the notes; a `Chan` is a **declaration** — its
identity is where it is written (`doc/ref/language.md`) — so it cannot,
and `channelled` has to be one literal expression with a parenthesis
per note.  `scorebox.py` already records what that costs: *"chopin's
hundred and forty overflowed the parser"*.  So a failure in the
`channelled` column is a result, not a broken run.

`--n` repeats the rows to reach a size, so the copies **coincide**: it
measures growth honestly and the grab count there is an artefact of the
repetition.  The box and the page are the real pictures.

Measured per picture: the compile, then per frame `tick`, `picture` and
`_shapes` (the wire), then `ask` — the press, which is the walk that
collects every attachment and the filter that keeps the ones containing
the point (`gui.py` `_attachments`/`_grabbed`).  Ask is timed on the
note centres, so it is the press that must find a note among all of
them.
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gestate import notes                                  # noqa: E402
from gestate.gui import Substrate                           # noqa: E402
from gestate.scorebox import (SEMI_H, asks, build_rolls,    # noqa: E402
                              rows_of)
from gestate.workbench import _shapes                       # noqa: E402

PIECE = Path(__file__).resolve().parent.parent / "examples" / "audio" / "arcnotes.ges"
RATE = 22050
FRAMES = 40
WARMUP = 5
NOTE_H = SEMI_H - 2
BOX = 2                       # the stacked roll of line 127, as queryframe uses


def num(v: int) -> str:
    """A literal the language reads — it has no unary minus."""
    return str(v) if v >= 0 else f"(0 - {-v})"


def rolls_of_piece() -> list:
    source, _origins = notes.expanded(PIECE.read_text(), PIECE.parent)
    found = [(i + 1, m.group(1))
             for i, line in enumerate(source.splitlines())
             for m in [re.match(r"^notes\s+(\S.*)$", line)] if m]
    return build_rolls(source, found, RATE, 0)


def rows_for(rolls: list, page: bool) -> list:
    """`(x, y, w)` per note — where the picture puts it."""
    which = rolls if page else [rolls[BOX]]
    return [(x, y, w) for rl in which if not isinstance(rl, Exception)
            for (_i, x, y, w, _t, _d, _m) in rows_of(rl)]


HEAD = """dummy : Chan Float
dummy = chan

clock : Sig Float
clock = 0.0 ::: mkSig (wait dummy)

ink : Colour
ink = RGB 122 200 235

back : Colour
back = RGB 20 22 28

body : Chan Float
body = chan

rail : Chan Float
rail = chan
"""

TAIL = """
substrate : Sig Sub
substrate = map (u => pic) clock

sound : Sig Float
sound = 0.0
"""


def listing(rows: list) -> str:
    items = ["(%s, %s, %s)" % (num(x), num(y), w) for x, y, w in rows]
    return " :: ".join(items + ["Nil"]) if items else "Nil"


def walked(rows: list, extra: bool) -> str:
    """`padded` and `marked`: the notes by recursion over a list, one
    pad over the lot.  `extra` puts one more `Sub` node around each
    note — the shape an `On` would have, and the only difference
    between the two."""
    one = ("one (x, y, w) = Shift x y (Sized w %d (Rect w %d ink))"
           if extra else "one (x, y, w) = Shift x y (Rect w %d ink)")
    one = one % ((NOTE_H, NOTE_H) if extra else (NOTE_H,))
    return HEAD + f"""
rows : List (Int, Int, Int)
rows = {listing(rows)}

one : (Int, Int, Int) -> Sub
{one}

drawNotes : List (Int, Int, Int) -> Sub
drawNotes ns = case ns of
    Nil -> Gap 0 0
    n :: rest -> Over (one n) (drawNotes rest)

pic : Sub
pic = Over (Rect {WIDE} {TALL} back)
           (TouchY body (TouchX rail (Sized {WIDE} {TALL} (drawNotes rows))))
""" + TAIL


def channelled(rows: list) -> str:
    """The ceiling: two `chan` declarations per note and a `TouchY`/
    `TouchX` around each, which forces the picture to be one literal
    expression."""
    decls = []
    for i in range(len(rows)):
        decls.append(f"cx{i} : Chan Float\ncx{i} = chan\n"
                     f"cy{i} : Chan Float\ncy{i} = chan\n")
    drawn = [f"(Shift {num(x)} {num(y)} (TouchY cy{i} (TouchX cx{i} "
             f"(Rect {w} {NOTE_H} ink))))"
             for i, (x, y, w) in enumerate(rows)]
    return HEAD + "\n" + "".join(decls) + f"""
pic : Sub
pic = Over (Rect {WIDE} {TALL} back)
           (TouchY body (TouchX rail (Sized {WIDE} {TALL} {overs(drawn)})))
""" + TAIL


def overs(items: list) -> str:
    """One `Over` per item, balanced — `scorebox._overs`' shape, so the
    depth is log and the parser meets a tree rather than a spine."""
    if not items:
        return "(Gap 0 0)"
    while len(items) > 1:
        items = [f"(Over {items[i]} {items[i + 1]})" if i + 1 < len(items)
                 else items[i] for i in range(0, len(items), 2)]
    return items[0]


def middle(xs: list) -> float:
    xs = sorted(xs)
    return xs[len(xs) // 2]


def measure(name: str, text: str, points: list) -> None:
    chars = len(text)
    began = time.perf_counter()
    try:
        sub = Substrate(text, RATE)
    except Exception as exc:                               # noqa: BLE001
        print(f"{name:12s} {chars:8d} chars   REFUSED — {type(exc).__name__}: "
              f"{str(exc).splitlines()[0][:90]}")
        return
    built = time.perf_counter() - began

    for _ in range(WARMUP):
        sub.tick()
        sub.picture()
    pics, sers = [], []
    pic = []
    for _ in range(FRAMES):
        sub.tick()
        t1 = time.perf_counter()
        pic = sub.picture()
        t2 = time.perf_counter()
        wire = _shapes(pic)
        t3 = time.perf_counter()
        pics.append(t2 - t1)
        sers.append(t3 - t2)

    asked, grabs, hit = [], [], 0
    for (x, y) in points:
        t0 = time.perf_counter()
        said = sub.ask(x, y)
        asked.append(time.perf_counter() - t0)
        grabs.append(len(said))
        # A note's own attachment is named `cx…`/`cy…`; the pad's two are
        # not, so this counts presses that reached a note at all.
        hit += any(n.startswith(("cx", "cy")) for n, _v in said)

    print(f"{name:12s} {chars:8d} chars  compile {built:6.2f} s  "
          f"picture {middle(pics)*1000:7.2f} ms  wire {middle(sers)*1000:6.2f} ms  "
          f"{len(pic):5d} items  {len(wire):7d} B  "
          f"ask {middle(asked)*1000:7.2f} ms  "
          f"grabs {middle(grabs):.0f} med / {max(grabs)} max  "
          f"on a note {hit}/{len(points)}")


WIDE, TALL = 1000, 500


def main(argv=None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    page = "--page" in args
    want = None
    if "--n" in args:
        want = int(args[args.index("--n") + 1])

    rolls = rolls_of_piece()
    rows = rows_for(rolls, page)
    if want:
        rows = (rows * (want // max(1, len(rows)) + 1))[:want]

    points = [(x + w // 2, y) for x, y, w in rows][:60]
    what = "every roll of the page" if page else f"the stacked roll of line {127}"
    print(f"{PIECE.name}, {what}: {len(rows)} notes, "
          f"a frame at 60 Hz is 16.7 ms")
    print()
    measure("padded", walked(rows, False), points)
    measure("marked", walked(rows, True), points)
    measure("channelled", channelled(rows), points)
    return 0


if __name__ == "__main__":
    sys.exit(main())
