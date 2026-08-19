"""The day's clock — `spec/timer.md`, `card:timer.md`.

**What these hold is the arithmetic, not the drawing.**  The row itself
is four lines of Rust; what can be silently wrong is what counts as
work, what counts as a break, and whether a week of days survives being
written down — and every one of those is a decision with a reason
attached, which is what a test is for.
"""

from __future__ import annotations

import time

import pytest

from gestate.presence import (CALM, LOUD, NONE, NOTABLE, Day, Presence,
                              mark, spell, WORKED)


HOUR = 3600.0


def at(day: str, hour: int, minute: int = 0) -> float:
    """A local wall-clock stamp on a named day.

    Built through `mktime` rather than from a constant, because the
    module reads the clock through `localtime` — a test that hard-coded
    epoch seconds would pass in one timezone and fail in the next.
    """
    y, m, d = (int(p) for p in day.split("-"))
    return time.mktime((y, m, d, hour, minute, 0, 0, 0, -1))


class Hand:
    """A clock a test moves by hand."""

    def __init__(self, now: float):
        self.now = now

    def __call__(self) -> float:
        return self.now


@pytest.fixture()
def kept(tmp_path):
    """A presence with its own file, and a clock the test owns.

    **A fresh file per call**, because the record is real: a second
    `kept(...)` in one test would otherwise load the first one's day and
    continue it, which is exactly right for a workbench reopened on the
    same afternoon and wrong for two independent scenarios.
    """
    made = []

    def make(when: float) -> tuple:
        hand = Hand(when)
        made.append(hand)
        path = tmp_path / f"presence-{len(made)}.tsv"
        return Presence(root=tmp_path, path=path, clock=hand), hand
    return make


# ── what counts, and what does not ───────────────────────────────────


def test_a_listen_is_worked_and_a_lunch_is_not(kept):
    """The threshold is the whole design: gestate is a program you
    *listen to*, so a piece played through without a keystroke must
    count, and an hour away must not."""
    p, hand = kept(at("2026-08-17", 9))
    p.touched()
    hand.now += 120.0                        # a two-minute piece
    p.touched()
    assert p.today.worked == pytest.approx(120.0)

    hand.now += HOUR                         # lunch
    p.touched()
    assert p.today.worked == pytest.approx(120.0), \
        "an hour away is not an hour worked"
    assert p.today.touches == 3


def test_the_first_touch_of_a_day_costs_nothing(kept):
    """There is no gap before the first gesture, and counting from
    midnight — or from whenever the window opened — is the mistake the
    card names: *elapsed since the workbench opened is easy and
    wrong*."""
    p, _hand = kept(at("2026-08-17", 6))
    p.touched()
    assert p.today.worked == 0.0
    assert p.today.first == "06:00"


# ── the day that the total cannot see ────────────────────────────────


def test_a_day_of_check_ins_shows_its_span(kept):
    """Henri's own failure mode, asked for by name: *"I probably don't
    sleep, just rest and occasionally check in, so the timer should
    count this as well and warn about it."*

    Six check-ins over fourteen hours sum to nothing under any idle
    threshold.  The span is the only thing that sees it."""
    p, hand = kept(at("2026-08-17", 6))
    for _ in range(6):
        p.touched()
        hand.now += 2.8 * HOUR

    assert p.today.worked < 60.0, "check-ins are not hours"
    assert p.today.span >= 14 * HOUR
    said = p.reading()
    assert said.startswith("you 0m " + CALM), \
        "almost none of it was worked, but the day was not a rest day"
    assert said.rstrip().endswith("since 06:00 " + NOTABLE), said

    # And the day the card is named after — 08-11 ran 00:03 → 23:48.
    p, hand = kept(at("2026-08-17", 5))
    for _ in range(8):
        p.touched()
        hand.now += 2.3 * HOUR
    assert p.reading().rstrip().endswith("since 05:00 " + LOUD), \
        "a day with no night in it is the loudest mark there is"


def test_an_ordinary_day_says_nothing_about_its_span(kept):
    """A row that is always on is a row nobody reads.  On a day with an
    evening in it the span says nothing the total did not."""
    p, hand = kept(at("2026-08-17", 9))
    for _ in range(20):
        p.touched()
        hand.now += 60.0
    assert "since" not in p.reading()


# ── the line, picked from outside the data ───────────────────────────


def test_the_ink_grows_past_eight_hours():
    """Henri's number, 2026-08-17.  The nine-day record *is* the
    overwork, so a scale fitted to it would read calm at noon on a
    twelve-hour day."""
    assert mark(7.9 * HOUR, *WORKED) == CALM
    assert mark(8.1 * HOUR, *WORKED) == NOTABLE
    assert mark(11 * HOUR, *WORKED) == LOUD


def test_the_day_is_spelt_in_hours_and_minutes():
    """`6.2h` is a number a person has to convert, and this row is read
    in passing or not at all."""
    assert spell(0) == "0m"
    assert spell(48 * 60) == "48m"
    assert spell(6 * HOUR + 12 * 60) == "6h12m"


# ── the sequence, which is why the card was first ────────────────────


def test_the_record_keeps_days_not_today(kept, tmp_path):
    """*A history of one day cannot show a sequence*, and the sequence
    is the finding: the largest day in the project was the
    second-to-last one, and it started at 02:49."""
    p, hand = kept(at("2026-08-17", 9))
    for back, hours in enumerate([2.0, 5.0, 9.0, 12.0]):
        date = f"2026-08-{13 + back:02d}"
        p.days[date] = Day(date, "09:00", "18:00", hours * HOUR, 100)
    p.save()

    again = Presence(root=tmp_path, path=tmp_path / "presence-1.tsv",
                     clock=hand)
    assert set(again.days) == set(p.days)
    assert again.days["2026-08-16"].worked == pytest.approx(12 * HOUR)
    # Four worked days ending today, oldest first, and today untouched.
    assert again.week(at("2026-08-17", 12)) == \
        f"{NONE}{NONE}{CALM}{CALM}{NOTABLE}{LOUD}{NONE}"


def test_a_window_opened_late_reports_the_day_it_opened_into(kept, tmp_path):
    """**Found by opening the window and looking at it**, which is the
    only way this one was ever going to be found.

    The reading used to come from the day the first *gesture* made, so a
    workbench opened onto a day already eight hours old said `you 0m`
    until something was typed — it reported that nothing had happened on
    the very day its own record said the most had.  Every unit test
    passed, because every unit test touched first."""
    p, hand = kept(at("2026-08-17", 14))
    today = "2026-08-17"
    p.days[today] = Day(today, "05:12", "13:55", 8 * HOUR + 42 * 60, 1500)
    p.save()

    fresh = Presence(root=tmp_path, path=tmp_path / "presence-1.tsv",
                     clock=hand)
    assert fresh.today is None, "nothing has been typed yet"
    assert fresh.reading().startswith("you 8h42m " + NOTABLE), fresh.reading()


def test_a_check_in_day_is_written_down_as_it_happens(kept, tmp_path):
    """**The flush is on the wall clock, not on the seconds earned.**

    Written the other way it works on an ordinary day and fails on the
    only day the instrument is really for: a day of check-ins earns
    almost no worked time, so a rule keyed on that never fires, and
    `first`, `last` and `touches` — the whole record of that day — would
    go with the process if it died."""
    p, hand = kept(at("2026-08-17", 6))
    for _ in range(6):
        p.touched()
        hand.now += 2.8 * HOUR
    assert p.today.worked < 60.0, "nothing to speak of was worked"

    on_disk = Presence(root=tmp_path, path=p.path, clock=hand)
    kept_day = on_disk.days["2026-08-17"]
    assert kept_day.first == "06:00" and kept_day.touches == 6, \
        "the span survived without a close()"


def test_a_span_that_runs_backwards_says_nothing(kept):
    """A hand-edited record is the only way to get one, and the honest
    answer to a number that cannot be is silence."""
    p, _hand = kept(at("2026-08-17", 9))
    p.days["2026-08-17"] = Day("2026-08-17", "22:00", "03:00", 600.0, 12)
    assert p.days["2026-08-17"].span == 0.0
    assert "since" not in p.reading()


def test_the_figure_and_the_strips_last_cell_never_disagree(kept):
    """One row must not contradict itself about one day.

    Written as two calculations they did: a day of six check-ins showed
    no mark beside `you 0m` — nothing had been *worked* — and a `▪` at
    the end of the strip, because something had been *touched*.  So the
    figure's mark is now the strip's own last cell, and there is only
    one calculation left to be wrong."""
    p, hand = kept(at("2026-08-17", 8))
    for _ in range(4):
        p.touched()
        hand.now += 3 * HOUR
        p._said = ("", 0.0)
        said = p.reading()
        strip = said.split("[")[1].split("]")[0]
        head = said.split(" [")[0].split(" ")[-1]
        assert strip[-1] == head or (strip[-1] == NONE and head.endswith("m")), \
            said


def test_a_rest_day_leaves_a_gap_rather_than_a_small_mark(kept):
    """**The mark this whole file hopes to see**, and it must not be a
    glyph: `·` and `▪` differ by one pixel a side in the font the bar is
    drawn in, so a rest day read as a light day on the screen.  No work,
    no ink."""
    p, _hand = kept(at("2026-08-17", 9))
    p.days["2026-08-16"] = Day("2026-08-16", "09:00", "17:00", 6 * HOUR, 90)
    strip = p.week(at("2026-08-17", 12))
    assert strip[-2] == CALM
    assert strip.strip(NONE) == CALM, "one worked day, and six blanks"
    assert NONE not in (CALM, NOTABLE, LOUD)
    assert NONE.isspace(), "it draws nothing at all"
    assert NONE != " ", ("a plain space would let `view.rs::wrap` break "
                         "the week across two rows")


def test_a_rest_day_is_visible_as_itself(kept):
    """The mark this whole file hopes to see.  A day with nothing in it
    is not a fourth grade of concern — it is the absence, and a week of
    them must not read like a week of light days."""
    p, _hand = kept(at("2026-08-17", 9))
    p.days["2026-08-15"] = Day("2026-08-15", "09:00", "17:00", 6 * HOUR, 90)
    strip = p.week(at("2026-08-17", 12))
    assert strip[-3] == CALM, "the day that was worked"
    assert strip[-2] == NONE and strip[-1] == NONE, "the two that were not"


# ── the two halves, kept apart ───────────────────────────────────────


def test_the_hand_and_the_project_are_shown_apart(kept, tmp_path):
    """Henri, 2026-08-17: *"Both, shown apart.  We are about to be able
    to measure both."*  Every commit in this repository is authored by
    him including the ones a session makes while he is elsewhere, so
    one fused number would be the lie."""
    p, hand = kept(at("2026-08-17", 9))
    p.touched()
    hand.now += 300.0
    p.touched()
    p._made = {time.strftime("%Y-%m-%d", time.localtime(hand.now)): 31}
    p._made_at = hand.now
    p._said = ("", 0.0)

    said = p.reading()
    assert said.startswith("you 5m"), said
    assert "project 31" in said, said


def test_a_file_outside_a_repository_says_only_its_half(kept, tmp_path):
    """The workbench opens files outside any git tree, and a row that
    guessed a number there would be worse than a row with one half."""
    p, _hand = kept(at("2026-08-17", 9))
    p.touched()
    said = p.reading()
    assert said.startswith("you "), said
    assert "project" not in said, said


def test_the_project_half_is_read_from_the_commit_log(tmp_path):
    """Nothing to instrument: the timestamps are already in the
    repository, already accurate, and unforgeable in the way a
    self-reported timer is not."""
    from pathlib import Path

    from gestate.presence import made

    tally = made(Path(__file__).resolve().parent.parent, days=3650)
    assert tally, "gestate is a git tree and has commits in it"
    assert all(len(d) == 10 and d.count("-") == 2 for d in tally)
    assert all(isinstance(n, int) and n > 0 for n in tally.values())

    assert made(tmp_path) == {}, "no git here, and no number invented"


# ── being able to switch it off ──────────────────────────────────────


def test_a_driven_window_keeps_no_record(tmp_path, monkeypatch):
    """`tools/toolbox.sh` types with XTEST, and a suite's synthetic
    keystrokes must not land in a person's week."""
    monkeypatch.setenv("GESTATE_PRESENCE", "")
    p = Presence(root=tmp_path, clock=Hand(at("2026-08-17", 9)))
    p.touched()
    p.touched()
    p.close()
    assert p.reading() == ""
    assert p.today is None
    assert not list(tmp_path.iterdir()), "nothing was written anywhere"


def test_the_record_can_be_pointed_somewhere_else(tmp_path, monkeypatch):
    monkeypatch.setenv("GESTATE_PRESENCE", str(tmp_path / "elsewhere.tsv"))
    p = Presence(root=tmp_path, clock=Hand(at("2026-08-17", 9)))
    p.touched()
    p.save()
    assert (tmp_path / "elsewhere.tsv").exists()


# ── midnight ─────────────────────────────────────────────────────────


def test_a_day_that_runs_past_midnight_becomes_two(kept):
    """08-11 ran 00:03 → 23:48.  Rolling the clock over is right rather
    than a rounding error: the question the strip answers is *did this
    day have a night in it*, and 00:03 is an answer."""
    p, hand = kept(at("2026-08-17", 23, 55))
    p.touched()
    hand.now += 600.0                        # 00:05
    p.touched()
    assert set(p.days) == {"2026-08-17", "2026-08-18"}
    assert p.days["2026-08-18"].worked == 0.0, \
        "the new day starts owing nothing"
    assert p.days["2026-08-18"].first == "00:05"


# ── the colour the row draws in ──────────────────────────────────────


def test_a_calm_week_does_not_earn_the_amber(kept):
    """Henri, 2026-08-17, having lived with the always-amber version for
    an hour: *"do the grey-when-calm colour change, I think it's a reward
    for not rushing or going breakneck speed."*

    The row is always on, and `spec/rocks.md`'s law is that a mark which
    is always on is a mark nobody reads.  So the *colour* obeys the same
    rule as the glyphs: nothing above `▪` in the week, nothing warm.
    """
    p, hand = kept(at("2026-08-17", 9))
    p.touched()
    assert p.reading()
    assert p.warm is False, "one keystroke is not a hard week"

    hand.now += 4 * HOUR
    p.touched()
    p._said = ("", 0.0)
    assert p.reading()
    assert p.warm is False, "and neither is a break"


def test_a_hard_day_earns_it(kept):
    p, _hand = kept(at("2026-08-17", 17))
    today = "2026-08-17"
    p.days[today] = Day(today, "05:00", "16:30", 9 * HOUR, 900)
    assert p.reading().startswith("you 9h00m " + NOTABLE)
    assert p.warm is True


def test_a_hard_day_last_week_still_earns_it(kept):
    """**The week, not today.**  The finding this whole instrument exists
    for is a *sequence*, so a light day after four heavy ones must not
    put the colour out — that is precisely the day the reading would be
    justified and the run would not."""
    p, _hand = kept(at("2026-08-17", 10))
    p.days["2026-08-15"] = Day("2026-08-15", "06:00", "23:00", 11 * HOUR, 2000)
    p.touched()
    assert p.warm is True, "a ▲ two days ago is still a ▲"


def test_the_project_alone_never_warms_the_row(kept):
    """**His half only.**  The commit log holds four `▲` from before this
    instrument existed; a row that warmed for those would be amber
    whatever he did, and the reward would never arrive."""
    p, hand = kept(at("2026-08-17", 9))
    p.touched()
    p._made = {time.strftime("%Y-%m-%d", time.localtime(hand.now)): 60}
    p._made_at = hand.now
    p._said = ("", 0.0)

    said = p.reading()
    assert "project 60 " + LOUD in said, said
    assert p.warm is False, "the project's week is not his week"


def test_a_day_with_no_end_in_it_is_never_calm(kept):
    """The span is the half the total cannot see, so it has to be able to
    warm the row on its own — a check-in day sums to nothing and is the
    day the colour is for."""
    p, hand = kept(at("2026-08-17", 6))
    for _ in range(6):
        p.touched()
        hand.now += 2.8 * HOUR
    said = p.reading()
    assert said.startswith("you 0m " + CALM), said
    assert p.warm is True, "0m worked, fourteen hours of day"


# ── The machine's half of the row ────────────────────────────────────────
#
# **`card:unseen-flare.md`.**  Henri: *"The audio is crackling without
# running audition now.  But I haven't seen the mechanism flare that is
# supposed to catch that."*  It did flare.  The status line holds one
# sentence, so it lasted until the next thing the editor had to say —
# and the observation *I haven't seen it* could not tell **it did not
# happen** from **it happened and was overwritten**.
#
# The count is durable now, and the row carries it.


def test_a_day_that_ran_dry_says_so(kept):
    """The whole point: the fact outlives the sentence that reported it."""
    p, _hand = kept(at("2026-08-18", 10))
    p.touched()
    p.ran_dry(3)
    p.ran_dry()
    assert "dry 4" in p.reading()


def test_a_quiet_day_says_nothing_about_it(kept):
    """`spec/rocks.md`: a row that is always on is a row nobody reads.
    `dry 0` every day would be exactly that mark."""
    p, _hand = kept(at("2026-08-18", 10))
    p.touched()
    assert "dry" not in p.reading()


def test_the_count_survives_the_window(kept):
    """Henri, asked whether it should outlive a restart: **yes.**  The
    count lives on the C host and dies with it, so *has this been
    happening all morning* was unanswerable — which is the half of the
    defect a sentence could never have fixed."""
    p, hand = kept(at("2026-08-18", 10))
    p.touched()
    p.ran_dry(7)
    p.save()

    again = Presence(root=p.path.parent, path=p.path, clock=hand)
    assert "dry 7" in again.reading()


def test_an_older_record_opens_unharmed(kept, tmp_path):
    """A five-field line predates the column.  A record that refused to
    read an older copy of itself would lose the week it exists to show."""
    p, hand = kept(at("2026-08-18", 10))
    p.path.write_text("# older\n2026-08-01\t09:00\t17:00\t3600\t42\n",
                      encoding="utf-8")
    again = Presence(root=tmp_path, path=p.path, clock=hand)
    day = again.days["2026-08-01"]
    assert (day.touches, day.dry) == (42, 0)


def test_a_zero_and_an_unmeasured_day_are_not_the_same_record(kept):
    """**The defect that reopened this card.**  Three days of the real
    file read `dry 0` on 2026-08-19 and not one of them could be told
    from the others: the count answers zero when there is no host, and
    the host exists only while sound plays, so a card that played six
    hours cleanly and a card that never opened printed the same glyph.

    `played` is the denominator that separates them.  Nothing about the
    row changes — Henri, 2026-08-19: *"keep it off the row"* — because
    the file answers *was it measured* and the row answers *how was the
    day*.
    """
    quiet, _h = kept(at("2026-08-18", 10))
    quiet.touched()
    quiet.played(3 * HOUR)

    silent, _h2 = kept(at("2026-08-18", 10))
    silent.touched()

    assert quiet.days["2026-08-18"].dry == silent.days["2026-08-18"].dry == 0
    assert quiet.days["2026-08-18"].played == 3 * HOUR
    assert silent.days["2026-08-18"].played == 0, (
        "a day nothing played must not look like a day nothing went wrong")
    # And neither of them says a word about it on the row.
    assert "played" not in quiet.reading() and "dry" not in quiet.reading()


def test_the_denominator_survives_the_window(kept):
    """Worth no less than the count it divides: a threshold fitted from
    a file that forgets its playing time is fitted to noise."""
    p, hand = kept(at("2026-08-18", 10))
    p.touched()
    p.played(90.0)
    p.ran_dry(7)
    p.save()

    again = Presence(root=p.path.parent, path=p.path, clock=hand)
    day = again.days["2026-08-18"]
    assert (day.dry, int(day.played)) == (7, 90)


def test_a_record_from_before_the_denominator_opens_unharmed(kept, tmp_path):
    """Six fields predates `played`, the way five predated `dry`.  Its
    zero is the honest answer rather than a hole: that day genuinely has
    no measured playing time."""
    p, hand = kept(at("2026-08-18", 10))
    p.path.write_text(
        "# older\n2026-08-18\t05:07\t15:46\t2866\t1675\t0\n", encoding="utf-8")
    again = Presence(root=tmp_path, path=p.path, clock=hand)
    day = again.days["2026-08-18"]
    assert (day.touches, day.dry, day.played) == (1675, 0, 0.0)


def test_sound_in_an_empty_room_is_not_somebody_working(kept):
    """`played` is the machine's, like `ran_dry` and unlike `touched`.
    A piece left looping over lunch must not buy anybody an hour."""
    p, _hand = kept(at("2026-08-18", 10))
    p.touched()
    before = p.days[sorted(p.days)[0]].worked
    p.played(HOUR)
    assert p.days[sorted(p.days)[0]].worked == before


# ── the seam, which is where this family actually breaks ─────────────
#
# `Presence.ran_dry` was tested here and `Workbench.dry_since_kept` in
# `test_audioeditor.py`, and until 2026-08-19 **nothing covered the
# join** — both halves green, the fit between them unwatched, in the
# same tick loop that dropped three fields in one day.
# `card:carried-state.md`: the defect is in the seam and the test is in
# the module.


def test_the_tick_records_both_halves_of_the_machine(kept):
    """The real function the loop calls, driven with a bench that has
    torn and played."""
    from gestate.workbench import _machine

    p, _hand = kept(at("2026-08-18", 10))
    p.touched()

    class Bench:
        def dry_since_kept(self): return 4
        def played_since_kept(self): return 120.0

    _machine(p, Bench())
    day = p.days["2026-08-18"]
    assert (day.dry, int(day.played)) == (4, 120)


def test_a_count_cannot_be_recorded_without_its_denominator(kept):
    """**Both numbers or neither.**  A count taken at a call site that
    forgot the denominator is the defect this card was reopened for,
    reintroduced one edit at a time — so the seam takes them together
    and a bench that can only answer half of it fails loudly here
    rather than quietly in the file.
    """
    from gestate.workbench import _machine

    p, _hand = kept(at("2026-08-18", 10))
    p.touched()

    class HalfABench:
        def dry_since_kept(self): return 4

    with pytest.raises(AttributeError):
        _machine(p, HalfABench())


def test_the_tearing_machine_is_not_the_working_person(kept):
    """`worked` is what the hand did.  Crediting somebody for an
    afternoon the sound spent stuttering would be the exact lie this
    instrument exists not to tell."""
    p, _hand = kept(at("2026-08-18", 10))
    p.touched()
    before = p.days[sorted(p.days)[0]].worked
    p.ran_dry(50)
    assert p.days[sorted(p.days)[0]].worked == before
