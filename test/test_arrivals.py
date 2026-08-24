"""`tools/arrivals.py` — the number *question it into existence* is
measured by, drawn on `test/gates.md` at every commit."""
import datetime
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import arrivals  # noqa: E402


def test_the_first_three_days_are_the_ones_that_made_later_necessary():
    """A fixed window in the past, so the answer never moves: the
    board's own history says nineteen cards in two days on 2026-08-16
    and -17, and that is what this reads back."""
    rows = dict(arrivals.counts(3, today=datetime.date(2026, 8, 18)))
    assert rows[datetime.date(2026, 8, 16)] >= 10
    assert rows[datetime.date(2026, 8, 17)] >= 5


def test_the_window_is_zero_filled_and_the_right_length():
    rows = arrivals.counts(14)
    assert len(rows) == 14
    assert all(n >= 0 for _, n in rows)
    assert rows[-1][0] == datetime.date.today()


def test_moving_a_card_between_shelves_is_not_an_arrival():
    """`--diff-filter=A` — a rename shows as A only without rename
    detection, and git log detects renames by default."""
    # The four workflow cards moved to done/ on 2026-08-18/19 without
    # being counted twice: the 2026-08-19 count is what was minted.
    rows = dict(arrivals.counts(2, today=datetime.date(2026, 8, 19)))
    assert rows[datetime.date(2026, 8, 19)] <= 5
