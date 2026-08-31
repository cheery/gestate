"""The formatter against the tree's own sources — `fixme.md` F190, F191.

**The rule this holds is Henri's, 2026-08-31:** *"the formatter should be
idempotent, but the code doesn't need to be autoformatted."*  Nobody has to
run `gestate.fmt` over a `.ges` file.  What it writes must be the same
program, and written again must come back the same text.

**Why a corpus test and not more unit tests.**  `test_format.py` holds
shapes somebody thought of.  This holds every `.ges` in the repository,
which is where the shapes nobody thought of are actually written down: F188
survived sixty unit tests and would have been caught by one pass over
`examples/closure.ges`.

## Three properties, and they are independent

Each catches things the others cannot, which is why all three are here.

1. **The output parses.**  The first half of the formatter's own promise.
2. **The output is the same program** — the AST, with spans and comments
   set aside.  This is the half that idempotency cannot see: F46's three
   defects, and F186's and F187's, all produce output that parses *and*
   formats to itself, and is a different program.  Nothing but this catches
   them across the corpus.
3. **Formatting is idempotent.**  This is the half the AST cannot see:
   comments are trivia, so a comment that moves or is deleted leaves the
   program identical.  Two files are non-idempotent with an unchanged AST;
   four change the program while being perfectly idempotent.

## The lists, and why a gate may land with names in it

The properties are false today and the failures already have numbers, so a
gate that refused everything would land red — and a gate that arrives red
teaches the next reader to skip it.  The failures are therefore **named
rather than hidden**, and each list is a **ratchet: it may shrink and never
grow.**  Repairing a file and forgetting to delete its name fails this file,
which is what keeps a baseline from becoming a graveyard.  The shape is
`card:ungated-fixes.md`'s *accepted baseline that may shrink and never
grow*, used here for the first time.

The 58 `.ges` files the formatter cannot parse at all are **not listed and
not checked**.  They are mostly the audio subgrammar, which `pipeline`
handles before parsing and `gestate.fmt` does not, and whether `fmt` is
meant to cover that surface is an open question and Henri's, not a defect.
A source that lands unreadable therefore fails nothing.  `READABLE` holds
the other direction: a file that reads today must not silently stop.

Measured 2026-08-31: 147 files — 58 unreadable; 89 readable, of which 9
write output that does not parse (F191), 7 write a different program, and
10 are not idempotent (F190).

## What this cannot catch, measured

**A corpus gate is only as strong as its corpus.**  Reverting any of F186,
F187 or F188 leaves every test in this file green: no clean readable source
in the tree writes a parenthesised application head, a lambda with a
compound parameter, or a `Box` pattern outside the two files already listed.
Checked by reverting each fix in turn on 2026-08-31.  Those three are held
by `test_format.py`, and the division is the point — unit tests hold the
shapes somebody named, this holds the shapes the tree actually contains, and
neither substitutes for the other.

The 89 are also not a language sample: most are audio pieces, so the surface
they exercise is narrow.  A source added here widens what is held, which is
a reason to keep examples rather than a reason to trust the number.
"""

from __future__ import annotations

import dataclasses
import pathlib

import pytest

from gestate.fmt import format
from gestate.syntax import parse
from gestate.syntax.ast import Span, VComment

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


def _sources() -> list[pathlib.Path]:
    return sorted(p for p in ROOT.rglob("*.ges") if "target" not in p.parts)


def _rel(p: pathlib.Path) -> str:
    return str(p.relative_to(ROOT))


def _formats(src: str):
    """`format(src)`, or `None` if the formatter cannot read it."""
    try:
        return format(src)
    except Exception:
        return None


def _program(node):
    """The AST with everything that is *layout* removed.

    Spans move whenever a line does, and comments are trivia the formatter
    is allowed to place — so neither belongs in a comparison of *programs*.
    What is left is what a reader would call the same code.
    """
    if isinstance(node, VComment):
        return None
    if dataclasses.is_dataclass(node) and not isinstance(node, type):
        vals = {}
        for f in dataclasses.fields(node):
            if f.name == "span":
                vals[f.name] = Span()
            elif f.name in ("comments", "trivia"):
                vals[f.name] = []
            else:
                vals[f.name] = _program(getattr(node, f.name))
        return type(node)(**vals)
    if isinstance(node, list):
        return [v for v in (_program(x) for x in node) if v is not None]
    if isinstance(node, tuple):
        return tuple(_program(x) for x in node)
    return node


#: Every `.ges` the formatter could read on 2026-08-31.  One of these
#: becoming unreadable is a regression and not a scope decision, which is
#: why the unreadable ones are unlisted and these are named.
READABLE = {
    "examples/advanced/01-fold.ges",
    "examples/advanced/02-samplehold.ges",
    "examples/advanced/03-feedback.ges",
    "examples/advanced/04-loop.ges",
    "examples/advanced/05-tap.ges",
    "examples/advanced/06-noise.ges",
    "examples/advanced/07-shape.ges",
    "examples/advanced/08-filters.ges",
    "examples/advanced/09-fm.ges",
    "examples/advanced/10-canvas.ges",
    "examples/audio/bar.ges",
    "examples/audio/bell.ges",
    "examples/audio/blip.ges",
    "examples/audio/bottleneck.ges",
    "examples/audio/compressor.ges",
    "examples/audio/drums.ges",
    "examples/audio/flutter.ges",
    "examples/audio/fm.ges",
    "examples/audio/fourfloor.ges",
    "examples/audio/knob.ges",
    "examples/audio/lead.ges",
    "examples/audio/membrane.ges",
    "examples/audio/pingpong.ges",
    "examples/audio/pluck.ges",
    "examples/audio/scenery.ges",
    "examples/audio/scoped.ges",
    "examples/audio/sine.ges",
    "examples/audio/spectrum.ges",
    "examples/audio/stereo.ges",
    "examples/audio/strings.ges",
    "examples/audio/strings2.ges",
    "examples/audio/substrate.ges",
    "examples/audio/tuning.ges",
    "examples/audio/twoknobs.ges",
    "examples/audio/violin.ges",
    "examples/audio/warmdrone.ges",
    "examples/beginner/01-tone.ges",
    "examples/beginner/02-waves.ges",
    "examples/beginner/03-envelope.ges",
    "examples/beginner/04-filter.ges",
    "examples/beginner/05-lfo.ges",
    "examples/beginner/06-drums.ges",
    "examples/beginner/07-pluck-bell.ges",
    "examples/beginner/08-fm.ges",
    "examples/beginner/09-effects.ges",
    "examples/beginner/10-piece.ges",
    "examples/closure.ges",
    "examples/gui/bounce.ges",
    "examples/gui/chain.ges",
    "examples/gui/patchbay.ges",
    "examples/intermediate/04-knobs.ges",
    "examples/intermediate/07-midifile.ges",
    "examples/music/arpeggio.ges",
    "examples/music/canon.ges",
    "examples/music/chords.ges",
    "examples/music/drums.ges",
    "examples/music/duetline.ges",
    "examples/music/nocturne.ges",
    "examples/music/passacaglia.ges",
    "examples/music/scale.ges",
    "examples/records.ges",
    "examples/relations.ges",
    "examples/signals.ges",
    "examples/super/acidline.ges",
    "examples/super/bellfield.ges",
    "examples/super/breaksmith.ges",
    "examples/super/choirloft.ges",
    "examples/super/dubgate.ges",
    "examples/super/gamelan.ges",
    "examples/super/hoverdrone.ges",
    "examples/super/longpipe.ges",
    "examples/super/machinist.ges",
    "examples/super/tapeloop.ges",
    "gestate/audio.ges",
    "gestate/command.ges",
    "gestate/gui.ges",
    "gestate/music.ges",
    "gestate/prelude.ges",
    "gestate/signal.ges",
    "gestate/substrates/trace.ges",
    "gestate/synth.ges",
    "gestate/templates/canvas.ges",
    "gestate/templates/echo.ges",
    "gestate/templates/gate.ges",
    "gestate/templates/knob.ges",
    "gestate/templates/score.ges",
    "test/sessions/F104-hello.ges",
    "test/sessions/F147-ampknob.ges",
    "test/sessions/F147-freqknob.ges",
}

#: `fixme.md` F191 — read, then written as something that does not parse.
#: **May shrink, never grow.**
OUTPUT_DOES_NOT_PARSE = {
    "examples/closure.ges",
    "examples/gui/patchbay.ges",
    "examples/relations.ges",
    "gestate/audio.ges",
    "gestate/gui.ges",
    "gestate/music.ges",
    "gestate/prelude.ges",
    "gestate/signal.ges",
    "gestate/synth.ges",
}

#: `fixme.md` F191, the quieter half — the output parses and is a
#: *different program*.  **May shrink, never grow.**
PROGRAM_CHANGES = {
    "examples/audio/bottleneck.ges",
    "examples/audio/flutter.ges",
    "examples/audio/strings.ges",
    "examples/audio/strings2.ges",
    "examples/gui/chain.ges",
    "examples/records.ges",
    "gestate/command.ges",
}

#: `fixme.md` F190 — a second pass moves comments and deletes some.
#: **May shrink, never grow.**
NOT_IDEMPOTENT = {
    "examples/advanced/01-fold.ges",
    "examples/advanced/02-samplehold.ges",
    "examples/advanced/04-loop.ges",
    "examples/audio/drums.ges",
    "examples/audio/fm.ges",
    "examples/audio/twoknobs.ges",
    "examples/gui/bounce.ges",
    "examples/gui/chain.ges",
    "examples/records.ges",
    "gestate/command.ges",
}


def test_a_file_that_reads_today_still_reads():
    """The unreadable set is a scope question; losing a readable file is not."""
    lost = sorted(name for name in READABLE
                  if not (ROOT / name).exists()
                  or _formats((ROOT / name).read_text()) is None)
    assert lost == [], (
        "these formatted on 2026-08-31 and no longer do (or are gone):\n  "
        + "\n  ".join(lost))


def test_the_output_of_every_readable_source_parses():
    broken = []
    for p in _sources():
        name = _rel(p)
        if name in OUTPUT_DOES_NOT_PARSE:
            continue
        once = _formats(p.read_text())
        if once is None:
            continue
        try:
            parse(once)
        except Exception as e:
            broken.append(f"{name}: {e}")
    assert broken == [], "output does not parse:\n  " + "\n  ".join(broken)


def test_formatting_does_not_change_the_program():
    """The AST, spans and comments aside, survives a pass.

    This is the property `format`'s own docstring promises and the one no
    other check here can see.
    """
    changed = []
    for p in _sources():
        name = _rel(p)
        if name in OUTPUT_DOES_NOT_PARSE or name in PROGRAM_CHANGES:
            continue
        src = p.read_text()
        once = _formats(src)
        if once is None:
            continue
        try:
            before, after = _program(parse(src)), _program(parse(once))
        except Exception:
            continue          # held by the test above
        if before != after:
            changed.append(name)
    assert changed == [], (
        "the formatter rewrote these into a different program:\n  "
        + "\n  ".join(changed))


def test_formatting_is_idempotent():
    """What it writes, written again, comes back the same — his rule."""
    moved = []
    for p in _sources():
        name = _rel(p)
        if name in OUTPUT_DOES_NOT_PARSE or name in NOT_IDEMPOTENT:
            continue
        once = _formats(p.read_text())
        if once is None:
            continue
        if format(once) != once:
            moved.append(name)
    assert moved == [], "a second pass changed:\n  " + "\n  ".join(moved)


# ── The ratchet: a repaired file leaves its list ─────────────────────────────
#
# Passing is the failure here.  A name left behind after the repair is
# exactly how a baseline turns into a graveyard, and the only cheap moment to
# catch it is the commit that fixes the file.


@pytest.mark.parametrize("name", sorted(OUTPUT_DOES_NOT_PARSE))
def test_a_listed_output_failure_is_still_one(name):
    once = _formats((ROOT / name).read_text())
    assert once is not None, f"{name} no longer formats at all — F191's list is stale"
    with pytest.raises(Exception):
        parse(once)


@pytest.mark.parametrize("name", sorted(PROGRAM_CHANGES))
def test_a_listed_program_change_is_still_one(name):
    src = (ROOT / name).read_text()
    once = _formats(src)
    assert once is not None, f"{name} no longer formats at all — F191's list is stale"
    assert _program(parse(src)) != _program(parse(once)), (
        f"{name} round-trips now — take it out of PROGRAM_CHANGES (F191)")


@pytest.mark.parametrize("name", sorted(NOT_IDEMPOTENT))
def test_a_listed_idempotency_failure_is_still_one(name):
    once = _formats((ROOT / name).read_text())
    assert once is not None, f"{name} no longer formats at all — F190's list is stale"
    assert format(once) != once, (
        f"{name} is idempotent now — take it out of NOT_IDEMPOTENT (F190)")
