"""MIDI rendering — the host half of `spec/music.md`.

Usage::

    python -m gestate.midi song.ges                  # writes song.mid
    python -m gestate.midi song.ges -o out.mid
    python -m gestate.midi song.ges --events         # print the layout, write nothing


The language's deliverable is `layout : [: Void :] -> [(Onset, Offset, R)]`
and nothing beyond it: `implementation_order.md` §11 puts rendering on the
host side, and says the *interface* is what the compiler owes.  So this
module reads that list out of the heap and writes a file; it decides
nothing about what music means.

Two policies live here rather than in the language, deliberately:

- **Normalisation.**  `at` may place content before the origin, so onsets
  can be negative.  A grid view may well want to *show* that a fill
  precedes bar 1; a MIDI file cannot hold a negative timestamp.  Same list,
  two readings, so the renderer shifts and the language does not.
- **Channel allocation.**  A `Rendered` carries a program number.  MIDI
  channels are a transport detail, assigned here in order of first
  appearance, skipping 9 — which is percussion by convention and would
  silently retune every note sent to it.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .gmachine import NCon, NNum, _force, is_tuple, run
from .pipeline import compile as _compile

#: `spec/music.md`'s definitions, prepended to a music program rather than
#: merged into the prelude: its eight constructors would renumber `Nil` and
#: `Cons` for every program in the language, and compile time is
#: superlinear in program size.
_MUSIC = (Path(__file__).with_name("music.ges")).read_text()

#: `spec/music.md`: 96 ticks to the beat, chosen because it divides by
#: 2, 3, 4, 6, 8, 12, 16, 24, 32 and 48.
TICKS_PER_BEAT = 96

#: Channel 9 is percussion in General MIDI; a melodic program sent there
#: plays as drums.
_PERCUSSION_CHANNEL = 9


#: complaint  machine — the score stream's shape, as the MIDI renderer walks it
class MidiError(Exception):
    pass


# ── Reading the result out of the heap ──────────────────────────────────────


def _list(node, state) -> list:
    """A cons-list as a Python list, forcing the spine cell by cell."""
    cons_tag = state.cons["Cons"].tag
    nil_tag = state.cons["Nil"].tag
    out = []
    node = _force(node, state)
    while True:
        if not isinstance(node, NCon):
            raise MidiError(f"expected a list cell, got {type(node).__name__}")
        if node.tag == nil_tag:
            return out
        if node.tag != cons_tag:
            raise MidiError(f"expected a list cell, got tag {node.tag}")
        out.append(node.args[0])
        node = _force(node.args[1], state)


def _int(node, state) -> int:
    node = _force(node, state)
    if not isinstance(node, NNum):
        raise MidiError(f"expected a number, got {type(node).__name__}")
    return node.n


def _event(node, state) -> tuple[int, int, int | None, int, int]:
    """`(onset, offset, program, key, velocity)` from one layout event.

    ``program`` is ``None`` for percussion, which has no program number —
    the kit lives on a reserved *channel*, which is this module's business.
    """
    node = _force(node, state)
    if not is_tuple(node, 3):
        raise MidiError("expected an (onset, offset, rendered) triple")
    onset, offset, rendered = node.args
    r = _force(rendered, state)
    if not isinstance(r, NCon):
        raise MidiError("expected a rendered value")
    if r.tag == state.cons["Midi"].tag:
        prog, key, vel = (_int(a, state) for a in r.args)
    elif r.tag == state.cons["Perc"].tag:
        key, vel = (_int(a, state) for a in r.args)
        prog = None
    else:
        raise MidiError(f"unknown rendered value (tag {r.tag})")
    return _int(onset, state), _int(offset, state), prog, key, vel


# ── Driving the program ─────────────────────────────────────────────────────

#: What a music program supplies, in place of `main`.
_ENTRY = ("main : (Int, List (Int, Int, Rendered))\n"
          "main = (bpm, layout score)\n")


def perform(source: str) -> tuple[int, list[tuple[int, int, int, int, int]]]:
    """Run a music program: its `bpm`, and its events in tick coordinates.

    A music program defines `score : [: Void :]` and `bpm : Int` rather than
    `main`, so `main` is supplied here.  Onsets are *not* normalised — that
    is the writer's job, and a grid view would want them as they are.
    """
    from .audio import _authored

    if "main" in _authored(source)[1]:
        #: complaint  author, nowhere — a music program declaring the wrong names; the mistake is an absence
        raise MidiError(
            "a music program defines `score` and `bpm`, not `main` — "
            "`main` is supplied by the renderer"
        )
    # `internal`, before the prelude goes on the front and the two stop
    # being separate files — see `audio.assemble`.  A MIDI program is
    # compiled against `prelude.ges` and `music.ges`, and those are the two
    # it is checked against.
    from .internals import enforce

    enforce(source, libraries=("prelude.ges", "music.ges"), text=source)
    # `Score` names `Voice`, whose constructors are generated per program
    # from its `voices` banks — a MIDI program has none, and gestate cannot
    # declare a constructor-less type (`fixme.md` F60), so it gets a stub.
    # A piece that *does* assign to banks is not a MIDI piece: its notes
    # are `Assigned`, `layout` collects `Play`, and it would render silent.
    # `write` refuses that case by name below.
    state = run(_compile(_MUSIC + "\nVoice := NoVoice\n"
                         + source + "\n" + _ENTRY))
    top = _force(state.stack[0], state)
    if not is_tuple(top, 2):
        raise MidiError("internal: the entry point did not produce a pair")
    bpm = _int(top.args[0], state)
    events = [_event(e, state) for e in _list(top.args[1], state)]
    return bpm, events


# ── Writing the file ────────────────────────────────────────────────────────


def _channels(events) -> dict[int | None, int]:
    """A MIDI channel per program number, in order of first appearance.

    Percussion (`program is None`) always gets channel 9: in General MIDI
    that channel *is* the kit, and a note sent anywhere else is pitched.
    """
    out: dict[int | None, int] = {}
    nxt = 0
    for _on, _off, prog, _k, _v in events:
        if prog in out:
            continue
        if prog is None:
            out[None] = _PERCUSSION_CHANNEL
            continue
        while nxt == _PERCUSSION_CHANNEL or nxt in out.values():
            nxt += 1
        if nxt > 15:
            #: complaint  author, nowhere — how many instruments the whole piece uses
            raise MidiError(
                "more than 15 distinct instruments; MIDI has 16 channels "
                "and one of them is percussion"
            )
        out[prog] = nxt
        nxt += 1
    return out


def write(source: str, path: str) -> tuple[int, int]:
    """Render a music program to a Standard MIDI File.

    Returns `(events written, bpm)`.
    """
    import mido

    bpm, events = perform(source)
    if not events:
        #: complaint  author, nowhere — a piece with no notes in it at all
        raise MidiError("the score is silent — no notes to write")

    origin = min(on for on, _off, _p, _k, _v in events)
    channels = _channels(events)

    mid = mido.MidiFile(ticks_per_beat=TICKS_PER_BEAT)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm)))
    for prog, chan in sorted(channels.items(), key=lambda kv: kv[1]):
        if prog is None:
            continue          # the kit is the channel; no program to send
        track.append(mido.Message("program_change", channel=chan,
                                  program=prog, time=0))

    # Absolute-time messages first, then one pass to deltas — a note's end
    # is not adjacent to its start once anything overlaps.
    timed: list[tuple[int, int, object]] = []
    for on, off, prog, key, vel in events:
        chan = channels[prog]
        # off before on at equal time, so a repeated note retriggers.
        timed.append((on - origin, 1, mido.Message(
            "note_on", channel=chan, note=key, velocity=vel)))
        timed.append((off - origin, 0, mido.Message(
            "note_off", channel=chan, note=key, velocity=0)))
    timed.sort(key=lambda m: (m[0], m[1]))

    clock = 0
    for when, _order, msg in timed:
        msg.time = when - clock
        clock = when
        track.append(msg)

    mid.save(path)
    return len(events), bpm


# ── CLI ─────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python -m gestate.midi",
        description="Render a gestate music program to a Standard MIDI File.",
    )
    ap.add_argument("file", help="a program defining `score` and `bpm`")
    ap.add_argument("-o", "--out", help="output path (default: alongside, .mid)")
    ap.add_argument("--events", action="store_true",
                    help="print the laid-out events instead of writing a file")
    args = ap.parse_args(argv)

    src_path = Path(args.file)
    try:
        source = src_path.read_text()
    except OSError as e:
        print(f"gestate: {e}", file=sys.stderr)
        return 1

    try:
        if args.events:
            bpm, events = perform(source)
            print(f"bpm {bpm}, {len(events)} event(s), "
                  f"{TICKS_PER_BEAT} ticks per beat")
            for on, off, prog, key, vel in events:
                who = "percussion" if prog is None else f"program {prog}"
                print(f"  {on:6} .. {off:<6} {who:<12} "
                      f"key {key:<3} velocity {vel}")
            return 0
        out = Path(args.out) if args.out else src_path.with_suffix(".mid")
        n, bpm = write(source, str(out))
    except MidiError as e:
        print(f"gestate: {e}", file=sys.stderr)
        return 1
    except Exception as e:                       # a compile or type error
        print(f"gestate: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    print(f"{out}: {n} event(s) at {bpm} bpm")
    return 0


if __name__ == "__main__":
    sys.exit(main())
