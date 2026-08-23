"""tools/sittings.py — the meter over the sittings ledger.

**Every log here is written by the test.**  The real one lives outside
the repository at `~/.local/state/gestate/sittings.log` because when
Henri is at the desk is his, and a test that read it would put a
person's week into a suite report on somebody else's machine.

*And the blindness that costs is the one that comes with that.*
`doc/memory/gestate-testing-standard.md` names it from the `gemba`
tests: every one of them set the environment variable to a temp file,
which was correct, and is exactly why none of them ever asked what
happens when nobody says.  So the fixtures below are shaped from the
events `tools/limit.sh` actually writes — `grant`, `open`, `block`,
`prompt`, `close` — and the tool was also run once against the real log
by hand, which is where its first defect turned up.
"""

import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "sittings", ROOT / "tools" / "sittings.py")
sittings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sittings)

#: 2026-08-22 09:00:00 local, so the fixtures read like a morning.
NINE = 1755846000


def log(tmp_path, rows):
    """A ledger in the tool's own format: epoch, event, detail."""
    p = tmp_path / "sittings.log"
    p.write_text("".join(f"{t}\t{e}\t{d}\n" for t, e, d in rows))
    return p


def test_a_sitting_runs_from_its_grant_to_the_last_thing_typed(tmp_path):
    """The span, and the reason it is a floor.

    Walking away leaves no event, so the end of a sitting is the last
    prompt and never the moment the chair was empty.  A meter that
    presented that as *time at the desk* without saying so would be
    over-claiming in the direction that flatters the reading.
    """
    p = log(tmp_path, [
        (NINE, "grant", "min=45 gap=0"),
        (NINE + 600, "prompt", "gap=10 elapsed=10 limit=45"),
        (NINE + 1800, "prompt", "gap=20 elapsed=30 limit=45"),
    ])
    got = sittings.sittings(sittings.read(p))
    assert len(got) == 1
    assert got[0]["end"] - got[0]["start"] == 1800
    assert got[0]["declared"] == 45


def test_the_limit_reached_and_the_desk_taken_again_is_counted_exactly(tmp_path):
    """`sat again` is the one number a nag cannot give, so it is exact.

    A sitting counts as *again* when the event immediately before it was
    a `block` — the limit was reached and a new one was granted with
    nothing in between.  Anything looser would be an inference, and this
    column is the one that decides whether the limit is mis-sized.
    """
    p = log(tmp_path, [
        (NINE, "grant", "min=15 gap=0"),
        (NINE + 900, "block", "elapsed=15 limit=15"),
        (NINE + 960, "grant", "min=45 gap=1"),        # straight after: again
        (NINE + 3600, "prompt", "gap=44 elapsed=44 limit=45"),
        (NINE + 99999, "open", "gap=1600"),           # a fresh day: not again
    ])
    got = sittings.sittings(sittings.read(p))
    assert [s["override"] for s in got] == [False, True, False]


def test_a_block_before_the_first_sitting_is_still_counted(tmp_path):
    """**The defect this file was written after.**

    The first version attached each `block` to whichever sitting was
    open, so a block landing before the log's first `grant` — an
    ordinary thing, since the log starts whenever the hook was installed
    — was dropped.  Against the real ledger it printed *"the limit was
    reached 8 times and the desk was taken again straight after 9 of
    them"*: a number that cannot be true, on the first run, in the line
    the whole tool exists to print.

    Counting both from the same stream is what makes the second
    incapable of exceeding the first, and that is the property worth
    holding rather than the arithmetic that happened to be wrong.
    """
    p = log(tmp_path, [
        (NINE, "block", "elapsed=20 limit=15"),       # before any start here
        (NINE + 60, "grant", "min=45 gap=1"),
        (NINE + 3600, "block", "elapsed=59 limit=45"),
    ])
    rows = sittings.read(p)
    hits = sittings.blocks_by_day(rows)
    again = sum(1 for s in sittings.sittings(rows) if s["override"])
    assert sum(hits.values()) == 2
    assert again <= sum(hits.values())


def test_an_undeclared_sitting_is_still_a_sitting(tmp_path):
    """`open` is the hook noticing an arrival nobody declared.

    That is the case `tools/limit.sh` exists for — *logging in to ask one
    small thing* — so a meter that counted only declared sittings would
    be blind to the behaviour that motivated the tool.
    """
    p = log(tmp_path, [
        (NINE, "open", "gap=120"),
        (NINE + 300, "prompt", "gap=5 elapsed=5 limit=15"),
    ])
    got = sittings.sittings(sittings.read(p))
    assert len(got) == 1 and got[0]["declared"] is None


def test_a_missing_log_says_so_and_does_not_raise(tmp_path, capsys):
    """A machine where the hook was never installed is not an error.

    `requirements.txt`'s pattern for every optional backend: say what is
    absent and name what would write it.
    """
    rc = sittings.main(["--log", str(tmp_path / "nothing.log")])
    said = capsys.readouterr().out
    assert rc == 0
    assert "no log" in said and "limit.sh" in said


def test_a_corrupt_line_is_skipped_rather_than_fatal(tmp_path):
    """The ledger is appended by a shell hook under `|| true`.

    A half-written line during a crash must cost the reading of that one
    line and nothing else — a meter that dies on it is a meter nobody
    can run on the day they most want to.
    """
    p = tmp_path / "sittings.log"
    p.write_text(f"{NINE}\tgrant\tmin=45\n"
                 "rubbish\n"                       # too few columns
                 "\n"                               # empty
                 "notanepoch\tprompt\tgap=1\n"     # first column unparseable
                 f"{NINE + 60}\tprompt\tgap=1\n")
    assert len(sittings.read(p)) == 2


def test_the_totals_can_never_say_more_agains_than_blocks(tmp_path, capsys):
    """The invariant, asserted on the printed line rather than inside.

    The defect was visible in the output and correct in the parts, which
    is the failure mode `test_covercount.py` was extended for the same
    day: a tool whose pieces are each right can still print a sentence
    that cannot be true.
    """
    p = log(tmp_path, [
        (NINE, "block", "elapsed=20 limit=15"),
        (NINE + 60, "grant", "min=45 gap=1"),
        (NINE + 3600, "block", "elapsed=59 limit=45"),
        (NINE + 3660, "grant", "min=90 gap=1"),
    ])
    sittings.main(["--log", str(p)])
    said = capsys.readouterr().out
    assert "reached 2 time(s)" in said
    assert "straight after 2 of them" in said
    assert "question for the fire" in said
