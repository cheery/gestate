# timer.md — how long the day has been, said in the status bar

*Companion to `spec/rocks.md`, whose marks and whose argument this
borrows whole, and to `spec/summary.md`, which is where the measurement
came from.  The ask is Henri's, 2026-08-16 — "timer: see in gestate when
I've been too long on it" — moved to the front of the board the same
evening, after reading `spec/summary.md` through: "I have had that exact
problem that this turned out into lots of hours… I really overworked
myself here."*

*He read the first working version on 2026-08-17 and said: "I can see
this system saving lives.  It's like seatbelts in a car."*

## The claim

In nine days this project built an instrument **before** touching
anything it meant to improve — `lagcheck`, `GESTATE_BUILD_TIME`, the
loop's stopwatch, `rocks`, every single time.  The one thing it never
instrumented was the person doing it.

    you 6h12m ◆ [▪▪◆▲▲ ◆]   project 31 ◆ [▪▪◆▲▲▲◆]   since 04:52 ▲

One row of the status bar, in a quiet amber, under the sentence the
last command answered with.  `gestate/presence.py`, `tally` on the
wire, `view::Ink::Spent` in the window.

## The law

> **Show the trend, not the reading.**

This is the whole of what the elaboration added, and it comes from
reading the daily commit counts as a sequence rather than as a calendar:

    7 → 26 → 26 → 33 → 18 → 42 → 43 → 60

**It was still accelerating at the point it was measured.**  Not a
plateau and not a taper — the largest day in the project was the
second-to-last one, and it started at 02:49.  That is the shape of
something that ends by breaking rather than by finishing.

A gauge showing *today* would not have caught it.  Every single one of
those days is defensible on its own; what is undeniable is the fourth
long day in a row, still climbing.  **A number for today is a number
that can be justified every day for nine days.**  So the week is drawn
beside the day, always, and the day is never drawn alone.

## Two quantities, kept apart

Henri, asked on 2026-08-17 whose hours a timer should count: *"Both,
shown apart.  We are about to be able to measure both."*

| | is | comes from |
|---|---|---|
| `you` | the hand at the workbench | gestures, with an idle threshold |
| `project` | the tree moving | `git log` |

They used to be the same number.  They are not any more, and the
measurement that says so is one line:

    git log --format=%an -200 | sort | uniq -c   →   200  Henri Tuhola

Every commit here is authored by Henri **including the ones a session
makes while he is elsewhere**, so the commit log measures the project's
pace and always did — it read as his only because he was the only one
there.  From 2026-08-17 he is not: *"with the new system I don't need to
be around all the time."*  An instrument that kept reading commits as
his hours would begin lying on exactly the days the new arrangement is
working.

## The thresholds, and why they are not fitted to the data

| quantity | calm below | notable below | the reason |
|---|---|---|---|
| worked | 8 h | 10 h | Henri's number, 2026-08-17 |
| span | 12 h | 16 h | twelve is a long day with a life around it; sixteen has no evening in it |
| commits | 20 | 40 | twenty is a full day at a commit per substantial step |
| idle | — | 10 min | shorter than a coffee, longer than a take |

`gestate/presence.py`: `WORKED`, `SPAN`, `MADE`, `IDLE`.

**The scale cannot come from the history, and that is the point.**  The
nine-day record *is* the overwork; a threshold fitted to it would read
calm at noon on a twelve-hour day.  So the line was asked for and picked
from outside the data — and against the record, several of those days
trip it before lunch.  That is the instrument working, not the
instrument being wrong.

**Ten minutes of idle, because this is a program you listen to.**  A
two-minute piece played through without a keystroke is ordinary work and
must not read as a break.  Elapsed since the window opened would have
been easier and counts a lunch.

## The span, which the total cannot see

Henri, in the same answer: *"I probably don't sleep, just rest and
occasionally check in, so the timer should count this as well and warn
about it."*

That is a description of a failure mode, offered by the person in it,
and **no amount of idle-trimming can see it**: six check-ins spread over
twelve hours sum to almost nothing under any threshold, and are the day
that breaks him.  What sees it is *first touch to last* — so presence is
measured twice, once as a sum and once as a span, and the span speaks
only when it has earned a mark:

    you 0m ▪ [      ▪]   since 06:00 ◆

The hours half stays honest — almost nothing *was* worked — and the
span says the day never ended.

**Only when earned.**  On a day with an evening in it the span says
nothing the total did not, and `spec/rocks.md`'s rule holds here too: a
mark that is always on is a mark nobody reads.

## The marks

`spec/rocks.md`'s three, deliberately — a second scale in the same
window would be a second thing to learn for the same three decisions:

    ▪   calm
    ◆   worth knowing
    ▲   look twice

And a fourth thing that is **not a mark**: a day with nothing in it
draws **nothing at all**, which is that file's law read to its end — the
ink grows with the quantity, and the quantity is zero.

**This was got wrong first, and the screen is what found it.**  A rest
day began as `·`.  In misc-fixed at 10×20, `·` is a 3×3 dot and `▪` is a
4×4 one — a pixel a side.  Photographed in a real window, the rest day
was **indistinguishable from a light day**: the one mark this whole
instrument hopes to see was the one that could not be read.  No test
caught it and no test could have; what caught it was opening the window
and looking at the bar.

The blank is **U+00A0 and not a space**, because the bar wraps by
splitting on `' '` (`view.rs::wrap`) and a rest day in an ordinary space
would let a narrow window break the week across two rows.  All five
sizes of the font carry it and none of them draws anything for it.

**The figure's own mark is the strip's last cell**, taken rather than
computed a second time.  Written twice they disagreed: a day of six
check-ins showed no mark beside `you 0m` and a `▪` at the end of the
strip — one row contradicting itself about one day.

## Where it is said, and where it is not

**A row of the status bar, and nothing else.**  Escalation was offered
on 2026-08-16 and declined, which is right for a program that would
otherwise interrupt its author mid-take.  Ignorable by design.

**Its own row, not part of the status sentence.**  The two answer
different questions and change on different clocks; fused, every answer
the editor gave would arrive with a timer in front of it.

**Last of the bar's rows, but with a row kept for it.**  A complaint is
the thing to read first and a timer never outranks one — so the tally
goes under them.  But the day the bar is full of complaints is precisely
the long day this exists to name, so the complaints give up their last
row rather than the tally being truncated away.  An instrument that goes
quiet under load is not an instrument.

**The status sentence is the exception**, and it outranks the tally
outright: what the last command answered is the line the person is
actually waiting for, and a window narrow enough to wrap that answer
across the whole bar is not one that should be shortening it to fit a
clock.  There the tally is what gives way.

**Not in the repository.**  The record lives in
`$XDG_STATE_HOME/gestate/presence.tsv`: it is personal, it would stand
in `git status` all day, and a clone of gestate is not a clone of
anybody's week.  `card:persistent-workbench-state.md` wants the same
directory and should take `presence.state_path()` rather than inventing
a second home.

**Days, not today.**  A history of one day cannot show a sequence, and
the sequence is the whole finding.

**Not for a driven window.**  XTEST types with the same X events a hand
does and nothing can tell them apart, so `tools/lagcheck.py::driven`
sets `GESTATE_PRESENCE=` for every harness that opens one — otherwise
the one instrument that measures the person would be measuring the test
suite.

## What it does not do, and would be worth doing

* **It cannot see a session it did not host.**  Time spent directing
  Claude in a terminal is time at the project and reads as zero here.
  The span partly covers it — a check-in *is* a gesture if it lands in
  the workbench — and it is the obvious next reading if the arrangement
  makes those days the common ones.
* **A week is a short trend.**  The finding that made this card first
  spanned nine days, which the strip cannot hold.  Seven is what a
  person reads without counting; the file keeps every day, so a longer
  reading is available whenever something wants one.
* **Nothing acts on it.**  It says how the week has been and stops
  there, which is the design and not an omission — but if the seven
  marks ever read `▲▲▲▲▲▲▲` and nothing happens, that is the day to
  revisit the declined escalation.

## Acceptance

1. A lunch is not worked and a listened-to piece is; the threshold that
   decides is one named constant with its reason attached.
2. A day of check-ins reads `you 0m` and still says `since 06:00 ◆` —
   the sum stays honest and the span carries the warning.  The day is
   not a rest day and its mark says so; only the *hours* are nothing.
3. A rest day is a gap in the strip, distinguishable from a light day
   *on the screen*, not merely in the string.
4. The hand's week and the project's week are two strips, and a day the
   project moved without him shows in one and not the other.
5. The record survives being written down and reloaded, keeps every
   day, and a window opened onto a day already eight hours old reports
   those eight hours before anything is typed.
6. A day of check-ins is on disk *while it is happening* — the flush is
   on the wall clock and not on the seconds earned, because a rule keyed
   on hours worked never fires on the day this exists for.
7. A bar full of complaints still has the tally in it, and a bar full
   of *answer* does not — the sentence outranks the clock.
8. A window driven by a harness leaves no trace in the record.

Held by `test/test_presence.py` and, for the drawing,
`the_days_tally_stands_in_its_own_ink`, `no_tally_is_no_row`,
`a_full_bar_still_keeps_a_row_for_the_day` and
`a_long_answer_is_not_cut_short_to_fit_the_clock` in
`shell/editor/tests/view.rs`.
