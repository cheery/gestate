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

**And it must arrive without being asked, or it is a command nobody
runs.**  *Henri, 2026-09-05:* **"It needs a 'view', just like how I look
toward to that score being rendered in the editor."**  His roll is
beside the text he is editing; a tool is a thing somebody has to think
of — and both trials of that day found the same gap from opposite
sides: a session asked to check is exact, a session not asked does not
look.  So there are two doors and neither is a command:

* **the render** — `audioperform` prints this after a take of any
  program that includes a `.notes` file, the way it already prints its
  seed and its channel count.  `card:the-first-jam.md` item 1 named the
  shape first, for a different number: *"a `ceiling: X%` line after a
  render would put the criterion into every run's own mouth."*
* **the read** — a `PostToolUse` hook on `Read`, so opening a `.notes`
  file shows its bars, exactly as `tools/backlinks.py` shows who cites
  what.  `.claude/settings.json` is behind the leash and a session may
  not edit it, so `--install` prints the lines and the install is
  Henri's.

**The hook never speaks about anything else.**  Only a `.notes` file,
only when it parses, only its first sections — a hook that answered on
every read would be noise, and noise is how the last one nearly died
(`card:backlinks-ranges.md`).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gestate.notes import (_MODES, NotesError, report,  # noqa: E402
                           rows_of_notes)


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


#: How many bars a hook shows before it stops.  A whole piece is a
#: hundred lines and a hook that prints one is a hook a reader learns to
#: skip; the first bars of each section are what a reader wants and the
#: command is there for the rest.
HOOK_BARS = 8

INSTALL = """\
    "PostToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          { "type": "command", "command": "~/gestate/tools/bars.py --hook", "timeout": 5 }
        ]
      }
    ]"""


def installed(settings: Path | None = None) -> bool:
    import json

    settings = settings or Path(__file__).resolve().parents[1] / ".claude" / "settings.json"
    try:
        conf = json.loads(settings.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    for entry in (conf.get("hooks") or {}).get("PostToolUse", []):
        if "Read" not in (entry.get("matcher") or ""):
            continue
        for h in entry.get("hooks", []):
            if "bars.py" in h.get("command", "") and "--hook" in h.get("command", ""):
                return True
    return False


def hook(stdin: str) -> str:
    """The PostToolUse contract: JSON in, JSON out, or nothing.

    **Silent on everything it is not about**, and silent on failure —
    `tools/backlinks.py`'s rule, and for its reason: a hook that raises
    interrupts a session over a file it was only reading.  A `.notes`
    file that does not parse gets nothing, because the reader is about
    to see the parse error from the tool they were actually running.
    """
    import json

    try:
        payload = json.loads(stdin or "{}")
        if payload.get("tool_name") != "Read":
            return ""
        path = Path((payload.get("tool_input") or {}).get("file_path") or "")
        if path.suffix != ".notes" or not path.exists():
            return ""
        rows = rows_of_notes(path)
        said: list = []
        report(rows[:HOOK_BARS], tell=said.append)
        if len(rows) > HOOK_BARS:
            said.append(f"   … and {len(rows) - HOOK_BARS} more bars: "
                        f"python tools/bars.py {path}")
        return json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "\n".join(said)}})
    except Exception as e:                                # noqa: BLE001
        print(f"bars --hook: {e!r}", file=sys.stderr)
        return ""


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--hook"]:
        out = hook(sys.stdin.read())
        if out:
            print(out)
        return 0
    if argv[:1] == ["--install"]:
        print(INSTALL)
        return 0
    if argv[:1] == ["--check"]:
        if installed():
            print("bars: the Read hook is installed")
            return 0
        print("bars: the Read hook is NOT installed — "
              "python tools/bars.py --install", file=sys.stderr)
        return 1
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
