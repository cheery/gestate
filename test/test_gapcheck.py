"""tools/gapcheck.py — the reader that has to settle the silence gap.

The number it exists to check (`GESTATE_LIMIT_GAP`, default 30) decides
where one sitting ends and the next begins, and nobody chose it.  These
tests cover the one operation the answer turns on: cutting a list of
arrivals into sittings at a threshold.  If that is wrong, every row of
the comparison table is wrong in the same direction and the table still
looks plausible.
"""

import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("gapcheck", ROOT / "tools" / "gapcheck.py")
gapcheck = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gapcheck)


def at(*minutes):
    """Arrival times, given as minutes from an arbitrary zero."""
    return [int(m * 60) for m in minutes]


def test_a_silence_shorter_than_the_gap_keeps_one_sitting():
    assert gapcheck.sittings(at(0, 5, 20, 29), 30) == [at(0, 5, 20, 29)]


def test_a_silence_at_the_gap_starts_a_new_one():
    """`limit.sh` cuts on `>=`, and the reader must agree with the script
    it is judging — an off-by-one here would score the wrong threshold."""
    assert gapcheck.sittings(at(0, 30), 30) == [at(0), at(30)]


def test_the_gap_is_measured_from_the_last_arrival_not_the_first():
    """The failure this catches: a long sitting of short hops being cut
    because it ran past the threshold in total."""
    assert gapcheck.sittings(at(0, 20, 40, 60), 30) == [at(0, 20, 40, 60)]


def test_a_lower_threshold_never_makes_fewer_sittings():
    times = at(0, 3, 14, 22, 51, 55, 130, 131, 190)
    counts = [len(gapcheck.sittings(times, g)) for g in (10, 15, 30, 60, 90)]
    assert counts == sorted(counts, reverse=True), counts


def test_a_close_is_not_an_arrival():
    """`close` is a session's call, not Henri typing.  Counting it would
    inflate the arrivals and shorten every measured gap."""
    rows = [(0, "open"), (60, "prompt"), (120, "close"), (3000, "prompt")]
    assert gapcheck.arrivals(rows) == [0, 60, 3000]


def test_the_log_reader_survives_a_torn_line():
    """The hook appends from a live desk; a truncated last line must not
    take the reader down with it."""
    p = ROOT / "test" / "_gapcheck_tmp.log"
    p.write_text("1000\tprompt\tgap=3\nnot a row\n2000\topen\n30")
    try:
        assert gapcheck.read(p) == [(1000, "prompt"), (2000, "open")]
    finally:
        p.unlink()


def test_an_empty_log_is_not_an_error():
    assert gapcheck.read(ROOT / "test" / "_gapcheck_absent.log") == []
