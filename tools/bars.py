#!/usr/bin/env python3
#: asked-by: Henri, 2026-09-05 — "yes, build the report", after
#: `doc/trial/spelling-preference.md` put eight arms in front of a file of
#: MIDI numbers and all eight wrote this report themselves, in letters.
"""What each bar sounds, in words — `card:the-first-jam.md` item 2.

    python tools/bars.py examples/audio/arc.notes
    python tools/bars.py examples/audio/together.ges D dorian

**The friction this is for**, in the words of the day it was met: *"the
day's harmony was checked entirely in the head, from MIDI numbers — no
instrument says bar 3 sounds A, C#, E, G across pad and bass."*  Now one
does.

**Why letters and degrees rather than the numbers already in the file.**
Measured rather than assumed: `doc/trial/spelling-preference.md` gave
eight sessions a file of MIDI numbers and asked only for the harmony
described.  **Eight of eight converted to letters unprompted**, and said
why when asked afterwards — *"mod-12 every value by hand"*, *"that
arithmetic layer is exactly where a wrong-by-one slip would go
unnoticed"*.  This is that translation, done once and correctly, instead
of in a reader's head every time.

**And nothing is stored.**  Both columns are derived from the MIDI
number and the declared key — `spec/drawnscores.md` §"The three
spellings, and two of them are derived".  A report round-trips through
nothing, which is why names are free here and are not free in the file.

A `.notes` file declares `key` and `mode` per section and needs no
argument.  A `.ges` piece declares neither, so they are given.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gestate.notes import (_MODES, NotesError, degree_of,  # noqa: E402
                           parse, sounding, spell)


def rows_of_notes(path: Path) -> list:
    """`(section, bar, keys, tonic, mode)` from a `.notes` file's own headers."""
    out = parse(path.read_text(), path.name)
    modes = {s.name: (s.key, s.mode) for s in out.sections}
    return [(s, b, keys) + modes[s] for s, b, keys in sounding(out)]


def rows_of_ges(path: Path, tonic: str, mode: str) -> list:
    """The same, off a performed score — one nameless section.

    **A note counts in every bar it is still sounding in**, which is the
    half a list of onsets cannot say: a whole-bar chord under a melody is
    the harmony of that bar, and `together.ges`' pads are exactly that.
    """
    from gestate.audioscore import perform_voices, pitch_of
    from gestate.midi import TICKS_PER_BEAT
    from gestate.notes import read

    _bpm, events = perform_voices(read(path), "", 48000, 0)
    per = 4 * TICKS_PER_BEAT
    heard: dict = {}
    for on, off, _bank, payload in events:
        key = pitch_of(payload)
        for bar in range(on // per, max(on, off - 1) // per + 1):
            heard.setdefault(bar, set()).add(key)
    return [("", bar + 1, sorted(keys), tonic, mode)
            for bar, keys in sorted(heard.items())]


def report(rows: list, tell=print) -> None:
    at = None
    for section, bar, keys, tonic, mode in rows:
        if (section, tonic, mode) != at:
            at = (section, tonic, mode)
            head = f"── {'section ' + section if section else 'the piece'}"
            tell(f"{head} — {tonic} {mode}" if tonic and mode else head)
            tell(f"   {'bar':>3}  {'sounding':<34} {'degrees':<26} outside")
        if tonic and mode:
            names = " ".join(spell(k, tonic, mode) for k in keys)
            steps = _MODES[mode.lower()]
            marks = " ".join(degree_of(k, tonic, mode) for k in keys)
            #: **Named, not counted.**  A count says a bar is wrong; a
            #: name says which note, and the note is what an author
            #: decides about.  `arc.notes`' one out-of-mode note in
            #: section A is a `g4` where the mode's fourth is `gis` —
            #: which is `doc/notes/notes-on-writing-a-piece.md` W2's own
            #: sentence, and it is not a typo.
            odd = [spell(k, tonic, mode) for k in keys
                   if (k - _PITCH_CLASS_OF(tonic)) % 12 not in steps]
        else:
            names = " ".join(str(k) for k in keys)
            marks, odd = "", []
        tell(f"   {bar:>3}  {names:<34} {marks:<26} "
             + (" ".join(odd) if odd else "—"))


def _PITCH_CLASS_OF(tonic: str) -> int:
    from gestate.notes import _PITCH_CLASS

    return _PITCH_CLASS[tonic]


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__.strip().splitlines()[0], file=sys.stderr)
        print("usage: tools/bars.py FILE.notes | FILE.ges TONIC MODE",
              file=sys.stderr)
        return 2
    path = Path(argv[0])
    try:
        if path.suffix == ".notes":
            rows = rows_of_notes(path)
        else:
            if len(argv) < 3:
                print(f"{path.name} declares no key; give a tonic and a mode: "
                      f"tools/bars.py {path} D lydian", file=sys.stderr)
                return 2
            if argv[2].lower() not in _MODES:
                print(f"`{argv[2]}` is not a mode this knows; "
                      + ", ".join(sorted(_MODES)), file=sys.stderr)
                return 2
            rows = rows_of_ges(path, argv[1], argv[2])
    except Exception as bad:  # noqa: BLE001 — CLI boundary
        print(f"bars: {bad}", file=sys.stderr)
        return 1
    report(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
