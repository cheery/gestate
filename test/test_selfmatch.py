"""No `pgrep -f` or `pkill -f` in this tree matches its own line.

**The bug is this tree's and the countermeasure came back from tend's.**
2026-08-18, here: `pgrep -f "no:randomly"` matched the watcher's *own*
command line, so every wait loop waited for itself and twelve polling
shells accumulated on the machine being listened on — which is also why
the audio was crackling, diagnosed as hardware first
(`journal/2026-08.md`, the mechanism-flare afternoon).  The `[p]ytest`
bracket guard existed and had been dropped when the match moved from the
process name to its flags.  2026-08-24, in `~/tend`: a session that had
read that entry an hour earlier ran `pkill -f 'while :; do'` and killed
the shell it was running in, and wrote this gate there.

**It comes back on 2026-08-25 at Henri's ask — "add a selfmatch gate to
gestate too" — and it is the first mechanism to travel tend → gestate**
rather than the other way.  It arrives the same way things go the other
direction: the file, named as borrowed, and not the prose around it.
The occasion was a third instance, in a session's own shell the same
morning: `pgrep -f "no:randomly"` again, to hunt an orphaned suite run,
returning the two PIDs of the pipeline that asked — a `kill -9` on that
answer would have killed the shell that typed it.

**Three times in a week, twice by a session that had just read about
it.**  Reading a post-mortem does not install a reflex; a gate does, for
everything that lands in the tree.  What it cannot reach — a pattern
typed straight into a shell, which is what all three actually were — is
the honest limit, and the answer for that case is to kill by PID or by
scope and never by pattern.

The guard is the bracket: `'[w]hile'` matches `while` and does not match
the literal `[w]hile` sitting in the caller's own command line.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

#: `pgrep -f PATTERN` / `pkill -f PATTERN`, with any flags between and
#: `-f` possibly bundled (`-af`), capturing the pattern's first character
#: after an optional quote.  The bundled form was the detector's own
#: first miss in tend: `pgrep -af '[p]ytest'` is exactly what a session
#: types, and the first regex read `-af` as not `-f`.
CALL = re.compile(r"""\bp(?:grep|kill)\b(?:\s+-\S+)*?\s+-\w*f\s+["']?(.)""")

#: Where a pattern would be *run* by this tree rather than written about
#: by it.  `journal/`, `doc/` and `fixme.md` quote the unguarded shape on
#: purpose — that is the ledger, and a gate that policed prose would make
#: the incident unwritable.
SCANNED = ["tools", "test", "gestate"]


def sources() -> list[Path]:
    """Every shell and Python file under the scanned directories, except
    this one — it quotes the unguarded shape in order to test the
    detector, the same exemption `test_seedaudit.py` takes."""
    return sorted(p for d in SCANNED for p in (ROOT / d).rglob("*")
                  if p.suffix in (".sh", ".py") and p.is_file()
                  and p.name != "test_selfmatch.py")


def unguarded(path: Path, shown: str | None = None) -> list[str]:
    """The lines of `path` whose pattern kill can match its own line.

    Separate from the test so the planted-file check below can call the
    *same* loop rather than a copy of it — a detector tested through a
    reimplementation is testing the reimplementation.
    """
    shown = shown or path.name
    bad = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        for m in CALL.finditer(line):
            first = m.group(1)
            if first not in "[$":     # a bracket, or a variable the caller guarded
                bad.append(f"{shown}:{n}: {line.strip()}")
    return bad


def refuse(bad: list[str]) -> None:
    assert not bad, (
        "a pattern kill that can match its own command line — bracket the "
        "first character ('[w]hile'), or kill by PID or scope instead:\n  "
        + "\n  ".join(bad))


@pytest.mark.parametrize("path", sources(), ids=lambda p: p.name)
def test_every_pattern_kill_is_bracket_guarded(path: Path):
    refuse(unguarded(path, str(path.relative_to(ROOT))))


def test_the_detector_sees_an_unguarded_one():
    """**An oracle that has only ever passed is a claim** (`manifesto.md`
    §"The three ways an instrument fails").  This tree has no `pgrep` in
    any scanned file today, so the check above passes on an empty
    question and would pass just as loudly if the regex were nonsense.
    """
    assert CALL.search('pgrep -f "no:randomly"').group(1) == "n"
    assert CALL.search("pkill -TERM -f '[s]leep 3'").group(1) == "["
    assert CALL.search('pgrep -af "$marker"').group(1) == "$"
    assert CALL.search("pgrep -x python") is None, "-x is not -f"


def test_it_would_fail_on_a_file_that_carried_one(tmp_path):
    """The detector, run the way the gate runs it, over a planted file.

    `test_the_detector_sees_an_unguarded_one` checks the regex; this
    checks the loop around it — the skip for comment lines, the
    bracket and `$` exemptions, and the message naming the line.
    """
    planted = tmp_path / "watcher.sh"
    planted.write_text(
        "#!/bin/sh\n"
        "# pgrep -f no:randomly   <- a comment, and not a call\n"
        "until ! pgrep -f \"no:randomly\"; do sleep 5; done\n"
        "pgrep -f '[p]ytest' && echo guarded\n")
    with pytest.raises(AssertionError) as caught:
        refuse(unguarded(planted, "watcher.sh"))
    said = str(caught.value)
    assert "watcher.sh:3" in said, said
    assert "watcher.sh:2" not in said, "a comment was read as a call"
    assert "watcher.sh:4" not in said, "the bracket guard was not honoured"
