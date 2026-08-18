"""Where the workbench was — `board/done/persistent-workbench-state.md`.

*"I'd like that when the editor closes, it could open to about the same
state where it was.  As if that state was a document in itself."*  And
the hazard he named with it: *"we would need to decide where the
information is placed, and how do we handle multiple workbenches."*

**A saved position, not a replayed history.**  `sessionlog` already
records every session, so reopening *could* be a replay — and should not
be.  Replaying re-executes: it makes sound, it writes files, and it
costs what the session cost.  History and position are different jobs,
and running them together gives you a reopen that plays a piece nobody
asked for.  So this is a small declarative document that nothing
executes, and `sessionlog` stays what it is.

## Two documents, because there are two kinds of state

Only one of them is the piece's, and that is the whole shape of this
module.

`<piece>.desk`, beside the `.ges`
    The caret, the zoom, the seed, the loop span, the knob values, which
    boxes stand.  All of it is about *this piece*, it means the same
    thing to anybody who opens it, and it belongs beside the file — so
    it travels with the piece, and can be committed, diffed and handed
    to somebody else.  *"As if that state was a document in itself"* is
    a file with a name, not a hidden dot-directory, which is why this
    one is readable and why the format below is plain.

`~/.config/gestate/zoom`, the rung you read at
    **The one exception, and F165 is why it is here.**  The zoom looks
    like the others and is not: a caret, a seed and a loop describe the
    *piece*, while a zoom describes the reader's screen and the reader's
    eyes.  Kept only against the piece, it meant somebody who fixed
    unreadable text on a laptop met it again on the next file they
    opened — which happened, on a first install, to the author.

    So the piece still wins wherever it names a rung, and this fills the
    **silence** that used to mean *scale 1*.

`~/.config/gestate/desk`, the desk record
    Which piece you were last working on, and which windows are open.
    **This is about nobody's piece.**  It cannot live beside any one of
    them because it is a fact about the set, and it should not be
    committed, because your window layout is not the project's.

## Nothing supervises the set

`workbench.main` takes a single optional file, so three windows are
three processes with no parent between them.  Nothing is in a position
to write down "there were three" except the three themselves — so a
window **adds itself to the record when it opens and takes itself out
when it closes**, and two things follow that are worth knowing before
reading any of the code:

* **A window that dies leaves its row behind.**  A crash, a `kill`, a
  machine that lost power.  So the record is read as *best-effort* —
  a row is believed only while its process is alive (`_alive`), and a
  stale one costs at worst a place claimed by nobody.
* **Two windows on one piece both want to write `<piece>.desk`**, and
  the second is refused (`write`, below).  That refusal is safe rather
  than lossy only because this record is where the refused window's own
  position goes — which is the other half of why the split earns its
  keep, and why a second view of a long piece comes back where it was.

## What is never restored

A transport that was playing, and a build.  A window that reopened
playing would be a program making noise nobody asked for; a build
restored from a document would be a stale instrument wearing a current
one's face.  Neither is written down here at all, which is a stronger
guarantee than remembering not to apply them.

## The format

One `name value…` a line, `#` for a comment, unknown names ignored.
Plain because it is meant to be read — and forgiving because it is meant
to be *edited*: a desk file from a newer gestate opens in an older one
with the fields it knows, which is the same manners the furniture wire
keeps.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

#: What a piece's document is called.  `sauna.ges` → `sauna.desk`.
SUFFIX = ".desk"


def zoom_path() -> Path:
    """Where **your** zoom lives — beside the desk record, not beside a
    piece.

    **F165, and it is a question of what a field describes.**  Every
    other field of a `Desk` is a place *in the piece*: a caret, a seed,
    a loop, the knobs the piece declares.  The zoom is not.  It
    describes **the reader's screen and the reader's eyes**, and storing
    it against the file meant a person who fixed unreadable text on one
    piece met it again on the next one — which is what happened on a
    laptop, on the first install, to the author.

    So it goes where the module already says a person's own things go:
    `~/.config/gestate/desk`'s directory, outside any tree, needing no
    `.gitignore` rule and travelling with nobody's project.
    """
    return record_path().parent / "zoom"


def mine() -> int | None:
    """The rung this person reads at, or `None` if they never said.

    Silent about every failure on purpose: a missing file is the
    ordinary case, and a corrupt one must not stop a window opening.
    """
    try:
        return int(zoom_path().read_text().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def remember(zoom: int | None) -> None:
    """Write down the rung this person reads at.

    Called on the way out, beside the piece's own document.  **Nothing
    here may raise** for the reason `_remember` gives: a window that
    could not write down a preference must still close.
    """
    if zoom is None:
        return
    try:
        where = zoom_path()
        where.parent.mkdir(parents=True, exist_ok=True)
        where.write_text(f"{zoom}\n")
    except OSError:
        pass


def opening(path) -> "Desk | None":
    """The piece's desk as a window should open it — **with your own
    zoom filled in when the piece does not name one.**

    The piece always wins where it speaks: a `.desk` that names a rung
    was written by somebody looking at *that* piece, and this is not
    second-guessing it.  What this fixes is the silence, which used to
    mean *scale 1* and now means *the size you read at*.
    """
    desk = read(path)
    rung = mine()
    if rung is None:
        return desk
    if desk is None:
        return Desk(zoom=rung)
    if desk.zoom is None:
        desk.zoom = rung
    return desk


def beside(path) -> Path:
    """The desk document for a piece."""
    return Path(path).with_suffix(SUFFIX)


def record_path() -> Path:
    """The desk record — yours, not the project's.

    `XDG_CONFIG_HOME` when it is set, because that is the rule on the
    platform this runs on, and `~/.config` when it is not.
    """
    root = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(root) / "gestate" / "desk"


@dataclass
class Desk:
    """Where a window was, in one piece.

    Every field is a *place*, never a state of the instrument: there is
    no `playing` here and no build, on purpose (see the module's own
    §"What is never restored").
    """

    #: 1-based, the way a gutter counts.
    line: int = 1
    column: int = 0
    #: Which rung of the zoom ladder, or `None` for "leave it alone".
    zoom: int | None = None
    #: `"source"` or `"canvas"`.
    showing: str = "source"
    #: Which take of a chancy piece — a seed is a *choice*, and losing
    #: it means the piece you were listening to yesterday is gone.
    seed: int | None = None
    #: `(from, to)` in bars, or `None`.
    loop: tuple | None = None
    #: Where the piano was.
    octave: int = 4
    #: Knob name → value.  A knob is declared in the file and its value
    #: is not, so this is the only place a turned knob survives a close.
    knobs: dict = field(default_factory=dict)

    def text(self) -> str:
        """The document, as it is written down."""
        out = ["# Where the workbench was.  Written by gestate when the",
               "# window closed; safe to edit, and safe to delete.",
               f"line {self.line}",
               f"column {self.column}"]
        if self.zoom is not None:
            out.append(f"zoom {self.zoom}")
        if self.showing and self.showing != "source":
            out.append(f"showing {self.showing}")
        if self.seed is not None:
            out.append(f"seed {self.seed}")
        if self.loop is not None:
            out.append(f"loop {self.loop[0]} {self.loop[1]}")
        if self.octave != 4:
            out.append(f"octave {self.octave}")
        for name in sorted(self.knobs):
            out.append(f"knob {name} {self.knobs[name]:g}")
        return "\n".join(out) + "\n"


def parse(text: str) -> Desk:
    """A desk document, read.

    **Forgiving on purpose.**  A name this version does not know is
    skipped rather than refused, and so is a line that does not parse:
    the worst a broken desk file may do is put you somewhere unhelpful,
    and refusing to open a piece because the note about where you were
    is malformed would be the cure being worse than the disease.
    """
    desk = Desk()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        name, rest = parts[0], parts[1:]
        try:
            if name == "line" and rest:
                desk.line = max(1, int(rest[0]))
            elif name == "column" and rest:
                desk.column = max(0, int(rest[0]))
            elif name == "zoom" and rest:
                desk.zoom = max(0, int(rest[0]))
            elif name == "showing" and rest:
                desk.showing = rest[0]
            elif name == "seed" and rest:
                desk.seed = int(rest[0])
            elif name == "loop" and len(rest) >= 2:
                desk.loop = (int(rest[0]), int(rest[1]))
            elif name == "octave" and rest:
                desk.octave = max(0, min(9, int(rest[0])))
            elif name == "knob" and len(rest) >= 2:
                desk.knobs[rest[0]] = float(rest[1])
        except ValueError:
            continue
    return desk


def read(path) -> Desk | None:
    """The document beside a piece, or `None` when there is none."""
    where = beside(path)
    try:
        return parse(where.read_text())
    except OSError:
        return None


def stamp(path) -> str:
    """What a document looked like when we read it — for §"refuse to
    clobber".

    Its text rather than its mtime, because mtime is a second-resolution
    lie on some filesystems and two windows closing together is exactly
    the case this is for.
    """
    try:
        return beside(path).read_text()
    except OSError:
        return ""


def write(path, desk: Desk, was: str = "") -> bool:
    """Write the piece's document — **unless somebody else has.**

    `was` is what `stamp` said when this window opened.  If the file has
    changed since, another window has closed on this piece and written
    where *it* was, and this one does not overwrite it: you would find
    out that last-writer-wins was the wrong rule by losing yesterday's
    place, which is the thing this card exists to prevent.

    Answers whether it wrote, so the caller can put the position
    somewhere else instead — which is what `keep` is for.
    """
    where = beside(path)
    if stamp(path) != was:
        return False
    try:
        where.write_text(desk.text())
        return True
    except OSError:
        return False


# ── The desk record — yours, and about the set ──────────────────────────────


def _alive(pid: int) -> bool:
    """Is that process still running?

    A window that died did not take its row out, so a row is believed
    only while the process that wrote it is there to mean it.
    """
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:            # somebody else's, and running
        return True
    except OSError:
        return False
    return True


def _rows() -> list:
    try:
        return [l.split() for l in record_path().read_text().splitlines()
                if l.strip() and not l.startswith("#")]
    except OSError:
        return []


def _put(rows) -> None:
    where = record_path()
    try:
        where.parent.mkdir(parents=True, exist_ok=True)
        where.write_text(
            "# gestate's desk: which piece you were last in, and which\n"
            "# windows are open.  Yours, not the project's.\n"
            + "".join(" ".join(r) + "\n" for r in rows))
    except OSError:
        pass


def last_file() -> str | None:
    """The piece you were last working on, or `None`.

    What a bare `workbench` opens — *Henri, 2026-08-18: "the workbench
    `filename.ges` should land to that file, but without arguments
    workbench should restore the file it last worked on."*

    **Somebody who has never opened a file has no last file**, and so
    still meets `untitled.ges` — which is the starter, and the screen
    `board/done/button.md` and `fixme.md` F150 are the account of.  The
    first screen survives on exactly the person it was built for.

    A piece that has since been deleted or moved is not offered, because
    an editor opening on a file that is not there is a worse answer than
    the starter.
    """
    for row in _rows():
        if row[0] == "last" and len(row) >= 2 and Path(row[1]).exists():
            return row[1]
    return None


def opened(path) -> int:
    """Say a window is open on this piece, and answer **which one**.

    `0` for the first window on it, `1` for the second, and so on —
    counted over the rows still alive, so a crashed window's row does
    not push the next one along.  The number is what decides whose
    position a window takes: the first has the piece's own document, and
    the rest have theirs kept here (`keep`).
    """
    me, path = os.getpid(), str(Path(path).resolve())
    rows = [r for r in _rows()
            if not (r[0] == "open" and (len(r) < 3 or not _alive(int(r[1]))))]
    nth = sum(1 for r in rows
              if r[0] == "open" and r[2] == path and int(r[1]) != me)
    rows = [r for r in rows if not (r[0] == "open" and int(r[1]) == me)]
    rows = [r for r in rows if r[0] != "last"] + [["last", path]]
    rows.append(["open", str(me), path])
    _put(rows)
    return nth


def closed(path) -> None:
    """Take this window's row out again."""
    me = os.getpid()
    _put([r for r in _rows()
          if not (r[0] == "open" and len(r) >= 2 and int(r[1]) == me)])


def keep(path, desk: Desk, nth: int) -> None:
    """Keep a window's place here, when the piece's document is not its
    to write.

    The second view of a long piece is a real thing to have open, and
    the whole reason refusing to clobber is safe rather than lossy: the
    shared document holds one position and this holds the others.
    """
    if nth <= 0:
        return
    path = str(Path(path).resolve())
    rows = [r for r in _rows()
            if not (r[0] == "also" and len(r) >= 3
                    and r[1] == path and int(r[2]) == nth)]
    rows.append(["also", path, str(nth), str(desk.line), str(desk.column)])
    _put(rows)


def kept(path, nth: int) -> tuple | None:
    """The place a second window left, as `(line, column)`, or `None`."""
    path = str(Path(path).resolve())
    for row in _rows():
        if (row[0] == "also" and len(row) >= 5
                and row[1] == path and int(row[2]) == nth):
            try:
                return int(row[3]), int(row[4])
            except ValueError:
                return None
    return None


# ── Gathering it, and putting it back ───────────────────────────────────────


def _line_and_column(text: str, offset: int) -> tuple:
    """A character offset as the gutter counts it — 1-based line, 0-based
    column.

    The window answers `caret()` as an offset, and a *document* wants
    the two numbers a person reads in the corner: an offset is meaningless
    beside a file somebody has since edited, and a line is roughly right
    even then.
    """
    head = text[:max(0, offset)]
    line = head.count("\n") + 1
    return line, len(head) - (head.rfind("\n") + 1)


def _offset(text: str, line: int, column: int) -> int:
    lines = text.split("\n")
    n = min(max(1, line), len(lines)) - 1
    return sum(len(l) + 1 for l in lines[:n]) + min(column, len(lines[n]))


def of(bench, view=None) -> Desk:
    """Where this workbench is, as a document.

    **Itemised here and nowhere else**, which is what the card asked
    for: every fact that survives a close is a line of this function,
    so the answer to *what is state* is a thing you read rather than
    infer.  What is deliberately absent is as much of the answer — no
    transport, no build (see the module's §"What is never restored").
    """
    desk = Desk()
    text = ""
    try:
        text = bench.source()
    except Exception:                                    # noqa: BLE001
        text = ""
    if view is not None:
        try:
            desk.line, desk.column = _line_and_column(text, view.caret())
        except Exception:                                # noqa: BLE001
            pass
        zoom = getattr(view, "zoom_at", None)
        if isinstance(zoom, int):
            desk.zoom = zoom
        showing = getattr(view, "showing", None)
        if showing in ("source", "canvas"):
            desk.showing = showing
    seed = getattr(bench, "seed", None)
    if isinstance(seed, int):
        desk.seed = seed
    transport = getattr(bench, "transport", None)
    span = getattr(transport, "loop", None) if transport is not None else None
    rate = getattr(bench, "rate", 0) or 0
    if span and rate:
        from .session import _looping

        desk.loop = _looping(bench)
    keyboard = getattr(bench, "keyboard", None)
    octave = getattr(keyboard, "octave", None)
    if isinstance(octave, int):
        desk.octave = octave
    values = getattr(bench, "values", None)
    if isinstance(values, dict):
        desk.knobs = {k: float(v) for k, v in values.items()
                      if isinstance(v, (int, float))}
    return desk


def restore(desk: Desk, bench, view=None) -> list:
    """Put a window back where it was, and say what was put back.

    **Orders, not reaching in.**  The caret and the zoom are the
    *window's* state and live on the window's thread (`workbench.Window`
    says so in its own first paragraph), so this asks in the direction
    the model already talks and does not touch them.

    The scroll is not among them and does not need to be: putting the
    caret back makes the view follow it, which is what *where you were*
    means to somebody looking at the screen.
    """
    put = []
    if view is not None:
        try:
            view.goto(desk.line)
            if desk.column:
                view.col(desk.column)
            put.append("the caret")
        except Exception:                                # noqa: BLE001
            pass
        at = getattr(view, "zoom_at", None)
        if desk.zoom is not None and isinstance(at, int) and desk.zoom != at:
            # **Stepped, because the ladder is stepped.**  `zoom` takes a
            # number of rungs; the mirror is what knows where it is
            # standing, which is the same mirror `fixme.md` F110 is
            # about.
            if view.zoom(desk.zoom - at):
                put.append("the zoom")
        if desk.showing == "canvas":
            try:
                if view.show("canvas"):
                    put.append("the canvas")
            except Exception:                            # noqa: BLE001
                pass
    if desk.seed is not None and getattr(bench, "seed", None) != desk.seed:
        try:
            bench.seed = desk.seed
            put.append("the seed")
        except Exception:                                # noqa: BLE001
            pass
    keyboard = getattr(bench, "keyboard", None)
    if keyboard is not None and isinstance(getattr(keyboard, "octave", None), int):
        keyboard.octave = desk.octave
    for name, value in desk.knobs.items():
        try:
            bench.set_value(name, value)
        except Exception:                                # noqa: BLE001
            continue
    if desk.knobs:
        put.append("the knobs")
    return put
