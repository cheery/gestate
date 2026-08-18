"""How long the day has been — `spec/timer.md`, `board/done/timer.md`.

**The one thing this project never instrumented was the person doing
it.**  In nine days it built an oracle before touching anything it meant
to improve — `lagcheck`, `GESTATE_BUILD_TIME`, the loop's stopwatch,
every time.  Then `spec/summary.md` read the commit log and found nine
calendar days with no rest day in them, no hour of the clock without a
commit in it, and a daily count that was **still accelerating** when it
was measured: 7 → 26 → 26 → 33 → 18 → 42 → 43 → 60.

So this module measures two things and keeps them apart, which is
Henri's own answer (2026-08-17) to the question of whose hours a timer
should count:

    you 6h12m ◆ [▪▪◆▲▲ ◆]   project 31 ◆ [▪▪◆▲▲▲◆]   since 04:52 ▲

(the gap in the first strip is a day he rested — see `NONE`)

* **`you`** — the hand at the workbench.  Gestures, with an idle
  threshold, so a lunch is not counted and a listen is.
* **`project`** — commits, from `git log`.

They used to be the same number and they are not any more.  Every commit
in this repository is authored by Henri including the ones a session
makes while he is elsewhere:

    git log --format=%an -200 | sort | uniq -c   →   200  Henri Tuhola

so the commit log measures *the project's* pace and always did — it read
as his only because he was the only one there.  From 2026-08-17 he is
not: *"with the new system I don't need to be around all the time."*  An
instrument that kept reading commits as his hours would begin lying on
exactly the days the new arrangement is working.

**The trend, not the reading.**  A number for today is a number that can
be justified every day for nine days — each of those days was defensible
on its own, and the sequence was not.  So the week is drawn as seven
marks and the day is drawn beside it, never alone.

**And the span, separately from the sum.**  Henri, asked what to count:
*"I probably don't sleep, just rest and occasionally check in, so the
timer should count this as well and warn about it."*  Six check-ins over
twelve hours sum to almost nothing under any idle threshold and are the
day that breaks him.  What catches that is not the total but *first
touch to last* — `since 04:52` is the day that never ended, and no
amount of idle-trimming can see it.

The marks are `spec/rocks.md`'s, for its reasons: three of them, the ink
growing with the quantity, legible with no colour at all — which is the
only rendering the status bar has.
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

__all__ = ["Presence", "mark", "spell", "state_path"]

#: Calm, worth knowing, look twice — `spec/rocks.md` §"The marks", and
#: the same glyphs deliberately: a second scale in the same window would
#: be a second thing to learn for the same three decisions.
CALM, NOTABLE, LOUD = "▪", "◆", "▲"

#: A day with nothing in it: **no ink at all**, which is `spec/rocks.md`
#: read to its end — the ink grows with the quantity, and the quantity
#: here is zero.  Not a fourth grade of concern; the absence of the
#: thing being graded.
#:
#: It began as `·` and that was **wrong on the screen**, which is the
#: only place it matters.  In misc-fixed at 10×20, `·` is a 3×3 dot and
#: `▪` is a 4×4 one, a pixel apart on each side: the rest day — the one
#: mark this whole instrument hopes to see — was indistinguishable from
#: a light day at the size it is actually read at.  Found by opening the
#: window and photographing the bar, not by any test.
#:
#: **A no-break space rather than a plain one**, because the bar wraps
#: by splitting on `' '` (`view.rs::wrap`): a rest day in an ordinary
#: space would let a narrow window break the week in half. U+00A0 is
#: carried by all five sizes of the font and draws nothing in any of
#: them, so the strip is one unbreakable word whatever the window does.
NONE = "\u00a0"

#: How long a hand may rest before it has stopped working.  Ten minutes,
#: and it is a picked number: this is a program you *listen to*, so a
#: two-minute piece played through without a keystroke is ordinary work
#: and must not read as a break.  Shorter than a coffee, longer than a
#: take.
IDLE = 600.0

#: Past eight hours the ink grows.  **Henri's number, picked from
#: outside the data on 2026-08-17**, and that is the whole point of it:
#: the nine-day record *is* the overwork, so a threshold fitted to it
#: would read calm at noon on a twelve-hour day.  Against the record,
#: several of those days trip this before lunch.
WORKED = (8 * 3600.0, 10 * 3600.0)

#: First touch to last.  Twelve hours is a long day with a life around
#: it; sixteen is a day with no evening in it; past that is 08-11, which
#: ran 00:03 → 23:48 and is the shape this exists to name.
SPAN = (12 * 3600.0, 16 * 3600.0)

#: Commits in a day.  Also picked from outside: twenty is a full day at
#: a commit per substantial step, forty is two of them, and the record's
#: worst day was sixty.
MADE = (20, 40)

#: How many days the strip shows.  A week, because the finding that made
#: this card first was a *sequence* and one week is the shortest one a
#: person reads without counting.
WEEK = 7

#: How often the commit log is re-read.  It is a subprocess and the
#: description is derived every tick.
MADE_EVERY = 300.0

#: How long the record may go unwritten while the hand is moving —
#: **wall-clock seconds, not worked ones**.  A crash costs at most this,
#: and the file is touched twice a minute rather than once a gesture.
FLUSH_EVERY = 30.0

_HEAD = ("# gestate presence — one line a day, written by the workbench.\n"
         "# date\tfirst\tlast\tworked(s)\ttouches\n")


def state_path() -> Path:
    """Where a workbench keeps what should outlive it.

    XDG's state directory, which is the one meant for *"state that
    should persist between restarts but is not important enough for the
    data directory"* — a record of hours is exactly that.  Deliberately
    **not** in the repository: it is personal, it would stand in
    `git status` all day, and a clone of gestate is not a clone of
    anybody's week.

    First user of this directory; `board/done/persistent-workbench-state.md`
    wants the same one, and should take this function rather than
    inventing a second home.
    """
    root = os.environ.get("XDG_STATE_HOME") or "~/.local/state"
    return Path(root).expanduser() / "gestate"


def mark(value, calm, notable) -> str:
    """One character for a quantity — `spec/rocks.md`'s scale."""
    if value >= notable:
        return LOUD
    return NOTABLE if value >= calm else CALM


def _today(strip: str) -> str:
    """The mark that goes beside the figure: **the strip's own last
    cell**, which is today.

    Taken from the strip rather than computed a second time, so the two
    cannot disagree — and they could: written twice, a day with six
    check-ins in it showed no mark beside `you 0m` (nothing was worked)
    and a `▪` at the end of the strip (something was touched), which is
    one row contradicting itself about the same day.  `bar_rows` keeps
    the same rule for the same reason, one floor up.
    """
    return "" if not strip or strip[-1] == NONE else f" {strip[-1]}"


def spell(seconds: float) -> str:
    """`6h12m`, `48m`, `0m` — minutes, because nobody acts on a second.

    Hours and minutes rather than a decimal: `6.2h` is a number a person
    has to convert, and this row is read in passing or not at all.
    """
    total = int(max(0.0, seconds) // 60)
    hours, minutes = divmod(total, 60)
    return f"{hours}h{minutes:02d}m" if hours else f"{minutes}m"


def _clock(stamp: float) -> str:
    return time.strftime("%H:%M", time.localtime(stamp))


def _day(stamp: float) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(stamp))


class Day:
    """One day's presence: when it began, when it last moved, and how
    much of the span between them was actually worked."""

    __slots__ = ("date", "first", "last", "worked", "touches")

    def __init__(self, date: str, first: str = "", last: str = "",
                 worked: float = 0.0, touches: int = 0):
        self.date = date
        self.first = first
        self.last = last
        self.worked = worked
        self.touches = touches

    @property
    def span(self) -> float:
        """First touch to last, in seconds, from the clock strings.

        Read back from `HH:MM` rather than kept as stamps, so a day
        loaded from the file and a day still being lived answer the same
        way — one code path, and the file is the only copy.
        """
        if not self.first or not self.last:
            return 0.0
        try:
            (h0, m0), (h1, m1) = (
                tuple(int(p) for p in self.first.split(":")),
                tuple(int(p) for p in self.last.split(":")))
        except ValueError:
            return 0.0
        # Never negative.  A day's last touch cannot precede its first —
        # `touched()` rolls the date over at midnight rather than
        # wrapping the clock — so a negative span is a record somebody
        # edited by hand, and the honest answer to that is *nothing to
        # say*, not a warning derived from a number that cannot be.
        return max(0.0, float(((h1 * 60 + m1) - (h0 * 60 + m0)) * 60))

    def line(self) -> str:
        return (f"{self.date}\t{self.first}\t{self.last}"
                f"\t{int(self.worked)}\t{self.touches}")

    @staticmethod
    def read(line: str) -> "Day | None":
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 5 or parts[0].startswith("#"):
            return None
        try:
            return Day(parts[0], parts[1], parts[2],
                       float(parts[3]), int(parts[4]))
        except ValueError:
            return None


def made(root: Path, days: int = WEEK, now: float | None = None) -> dict:
    """Commits per day, from `git log` — the project's half.

    **Nothing to instrument.**  The commit timestamps are already the
    historical record of the pace: already in the repository, already
    accurate, and unforgeable in the way a self-reported timer is not.

    Returns `{}` when there is no git here, which is not a failure — the
    workbench opens files outside any repository and a row that guessed
    a number there would be worse than a row with one half.
    """
    when = time.time() if now is None else now
    since = time.strftime("%Y-%m-%d", time.localtime(when - days * 86400))
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "log", f"--since={since} 00:00",
             "--date=format-local:%Y-%m-%d", "--format=%ad"],
            capture_output=True, text=True, timeout=5.0, check=False)
    except (OSError, subprocess.SubprocessError):
        return {}
    if out.returncode != 0:
        return {}
    tally: dict = {}
    for line in out.stdout.splitlines():
        date = line.strip()
        if date:
            tally[date] = tally.get(date, 0) + 1
    return tally


class Presence:
    """The day's hand, counted and kept.

    Held by the workbench loop, told `touched()` whenever a gesture
    arrives, and asked `reading()` whenever the description is derived —
    which is every tick, so the reading is cached to the minute it is
    printed at.
    """

    def __init__(self, root: Path | None = None, path: Path | None = None,
                 clock=time.time):
        self.clock = clock
        self.root = Path(root) if root is not None else Path.cwd()
        #: `GESTATE_PRESENCE=` (empty) turns the record off entirely —
        #: which is what a driven window wants: `tools/toolbox.sh` types
        #: with XTEST, and a test suite's synthetic keystrokes must not
        #: land in a person's week.  A path redirects it.
        told = os.environ.get("GESTATE_PRESENCE")
        if path is not None:
            self.path = Path(path)
        elif told is None:
            self.path = state_path() / "presence.tsv"
        elif told == "":
            self.path = None
        else:
            self.path = Path(told)
        self.days: dict = {}
        self.today: Day | None = None
        self._last = 0.0            # when the hand last moved
        self._dirty = False         # something not yet on disk
        self._saved = 0.0           # when the file was last written
        self._said = ("", 0.0)      # the cached reading, and its minute
        self._warm = False          # whether that reading earned its colour
        self._made: dict = {}
        self._made_at = 0.0
        self._load()

    # ── the record ───────────────────────────────────────────────────

    def _load(self) -> None:
        if self.path is None or not self.path.exists():
            return
        try:
            text = self.path.read_text(encoding="utf-8")
        except OSError:
            return
        for line in text.splitlines():
            day = Day.read(line)
            if day is not None:
                self.days[day.date] = day

    def save(self) -> None:
        """Write the record — every day of it, oldest first.

        **Days, not today.**  A history of one day cannot show a
        sequence, and the sequence is the finding this whole instrument
        exists for.
        """
        if self.path is None:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            rows = [self.days[d].line() for d in sorted(self.days)]
            self.path.write_text(_HEAD + "\n".join(rows) + "\n",
                                 encoding="utf-8")
        except OSError:
            return          # a record nobody can write is not a crash
        self._dirty = False
        self._saved = self.clock()

    # ── the hand ─────────────────────────────────────────────────────

    def touched(self) -> None:
        """A gesture arrived.  Count the gap since the last one, unless
        the hand had stopped."""
        if self.path is None:
            return
        now = self.clock()
        date = _day(now)
        day = self.days.get(date)
        if day is None or self.today is None or self.today.date != date:
            # Midnight, or the first touch of the day.  A day that runs
            # past midnight becomes two days here, which is right: the
            # question the strip answers is *did this day have a night
            # in it*, and 00:03 is an answer, not a rounding error.
            day = self.days.setdefault(date, Day(date))
            self.today = day
            self._last = 0.0
        gap = now - self._last if self._last else 0.0
        if 0.0 < gap <= IDLE:
            day.worked += gap
        day.touches += 1
        if not day.first:
            day.first = _clock(now)
        day.last = _clock(now)
        self._last = now
        # **Flushed on the wall clock, not on the seconds earned.**  An
        # earlier version wrote the file once `worked` had grown by 30 s,
        # which is fine on an ordinary day and fails on the only day this
        # instrument is really for: a day of check-ins earns almost no
        # worked time, so the file would not have been written at all
        # between opening the window and closing it — and `first`, `last`
        # and `touches`, which are the whole record of that day, would go
        # with the process if it died.
        self._dirty = True
        if now - self._saved >= FLUSH_EVERY:
            self.save()

    # ── what it says ─────────────────────────────────────────────────

    def week(self, now: float) -> str:
        """Seven marks, oldest first, today last — his half."""
        out = []
        for back in range(WEEK - 1, -1, -1):
            day = self.days.get(_day(now - back * 86400))
            if day is None or day.touches == 0:
                out.append(NONE)
            else:
                out.append(mark(day.worked, *WORKED))
        return "".join(out)

    def _project(self, now: float) -> str:
        if now - self._made_at >= MADE_EVERY or not self._made_at:
            self._made = made(self.root, WEEK, now)
            self._made_at = now
        if not self._made:
            return ""
        strip = ""
        for back in range(WEEK - 1, -1, -1):
            count = self._made.get(_day(now - back * 86400), 0)
            strip += NONE if count == 0 else mark(count, *MADE)
        count = self._made.get(_day(now), 0)
        return f"project {count}{_today(strip)} [{strip}]"

    def reading(self) -> str:
        """The status bar's row, or `""` when there is nothing to say.

        Cached to the minute it prints at, because the description is
        derived every tick and this row changes once a minute at most —
        which is also what keeps the window from being re-described
        sixty times a second for a string that did not move.
        """
        if self.path is None:
            return ""
        now = self.clock()
        minute = now // 60
        if self._said[1] == minute and self._said[0]:
            return self._said[0]
        # **Looked up by date, not taken from `self.today`.**  Found by
        # opening the window and reading it: `today` is set by the first
        # *gesture*, so a workbench opened onto a day already eight hours
        # old reported `you 0m` until something was typed — the reading
        # said nothing had happened on the very day the record said the
        # most had.  The date is the key everywhere else here; making it
        # the key here too also retires the midnight case for free.
        day = self.days.get(_day(now))
        worked = day.worked if day is not None else 0.0
        strip = self.week(now)
        # **Whether the row has earned its colour**, decided here rather
        # than in the window, which never reads meaning out of a sentence
        # (`furniture.rs`: the model's is the only tokenizer).  **His half
        # only**: the project's week holds four `▲` from before this
        # instrument existed, and a row that stayed amber for them would
        # be amber whatever he did — the reward would never arrive.
        warm = any(c in (NOTABLE, LOUD) for c in strip)
        parts = [f"you {spell(worked)}{_today(strip)} [{strip}]"]
        project = self._project(now)
        if project:
            parts.append(project)
        # **The span, and only when it has earned a word.**  A row that
        # is always on is a row nobody reads (`spec/rocks.md`), and on an
        # ordinary day the span says nothing the total did not.  It is
        # here for the day the total cannot see: a wide span with little
        # work in it is the resting-near-it day, and it is the one that
        # was asked for by name.
        if day is not None and day.first:
            span = day.span
            if span >= SPAN[0]:
                parts.append(f"since {day.first} {mark(span, *SPAN)}")
                warm = True          # a day with no end in it is not calm
        said = "   ".join(parts)
        self._said = (said, minute)
        self._warm = warm
        return said

    @property
    def warm(self) -> bool:
        """Whether the last `reading()` earned the amber.

        **A reward for not rushing**, which is Henri's own reading of it
        (2026-08-17): a week with nothing above `▪` in it draws in the
        chrome's own grey, and the row warms only once something has been
        worth knowing.  The glyphs carry the whole meaning either way —
        the colour is a second telling of the same fact, for the eye that
        has not read the row yet — so nothing is lost to a terminal with
        no colour or to a reader who cannot use it.

        `spec/rocks.md`'s law one channel over: the ink grows with the
        quantity, and an always-on colour is a mark nobody reads.

        **Asks for the reading itself rather than trusting that somebody
        already did.**  Written the other way this was a trap and the
        first caller after the author fell straight into it: `warm` read
        `False` for a hard week because nothing had called `reading()`
        yet, which is a silently wrong answer rather than an error.
        `reading()` is cached to the minute, so asking costs a
        comparison.
        """
        self.reading()
        return self._warm

    def close(self) -> None:
        """The window is going.  Write what has not been written."""
        if self._dirty:
            self.save()
