# timer — see when the day has been too long

    status   open — first in the order, 2026-08-16
    because  nine days at thirty commits a day, and nothing said so
    asked    Henri, 2026-08-16
    see      spec/summary.md §"The clock" — the measurement
             spec/author.md §"The thing that will actually get you"
             GESTATE_EDITOR_TIME, GESTATE_BUILD_TIME — the precedent

## The ask

> timer: see in gestate when I've been too long on it.

Moved to the front of the order on 2026-08-16, at his ask, after reading
`spec/summary.md` through: *"I have had that exact problem that this
turned out into lots of hours… I really overworked myself here."*

## Found by looking, before it was taken

This one has a caller and it is the person reading it.
`spec/summary.md` ends: *"the pace itself was never instrumented; every
other cost in this project has an oracle.  This one did not."*  It was
asked for the same day that sentence was written.

The parts are precedented — `GESTATE_EDITOR_TIME` and
`GESTATE_BUILD_TIME` already measure and report, and the status bar
already carries multiple lines.

### What the measurement actually shows

From `spec/summary.md`, read on 2026-08-16 in the evening:

- **Nine calendar days, no rest day.**  Seven of them whole.
- **No hour of the clock without a commit in it.**  Fifteen fall between
  midnight and 05:00.
- **08-11 ran 00:03 → 23:48** — 23h45m, which is not a long day but a
  day with no night in it.  08-10 was 17h10m.  08-15 began at **02:49**.
- Eighty commits fall between 05:00 and 09:00.  "The mornings are the
  spine of this project" means starting before six, on days that also
  end at 23:xx — the sleep window compressed from both ends.
- And the file says it itself: those spans are *"a floor and not a
  measurement"*.  The real hours are worse than the table.

### The part the summary does not say, and the reason this card is first

Read the daily commit counts as a **trend** rather than as a calendar:

    7 → 26 → 26 → 33 → 18 → 42 → 43 → 60

**It was still accelerating at the point it was measured.**  Not a
plateau and not a taper: the largest day in the project was the
second-to-last one, and it started at 02:49.  That is the shape of
something that ends by breaking rather than by finishing.  It stopped
because he noticed, not because a limit was reached.

**This has a direct design consequence, and it is the whole of what the
elaboration adds.**  A gauge showing *today* would not have caught this.
Any single day here is defensible on its own — a long day is a long day,
and every one of these had a reason.  What is undeniable is the
*sequence*: the fourth long day in a row, still climbing.  So:

> **The timer must show the trend, not the reading.**  A number for
> today is a number that can be justified every day for nine days.

### Half the instrument already exists

The measurement in `spec/summary.md` was derived entirely from `git log`
— the commit timestamps *are* the historical record of the pace, and
they are already in the repository, already accurate, and already
unforgeable in the way a self-reported timer is not.

So the work splits cleanly:

- **The past** is a reading of `git log`: days, spans, the daily count,
  and the trend across the last week.  Nothing to instrument; it is
  arithmetic on data that exists.  This is also the half that answers
  *"how has this week been"* rather than *"how long have I sat here"*.
- **The present** is the only part that needs measuring: today's
  keystroke-active time, which nothing records today.

## Questions

**Answered, 2026-08-16 evening — the status line, and nothing else.**  A
quiet amber in the multiline status bar carrying the **day's** total,
not the sitting's.  Ignorable by design.  Escalation was offered and
declined, which is the right call for a program that would otherwise
interrupt its author mid-take.

**Still open, and cheap to decide when the work starts:**

- **What counts as a break?**  Elapsed since the workbench opened is
  easy and wrong — it counts a lunch.  Keystroke-active time with an
  idle threshold is closer; the threshold is a number to pick, not a
  design.
- **Where the day's total is persisted**, and — given the trend finding
  above — that the file keeps **days**, not just today.  A history of
  one day cannot show a sequence.
- **What the trend is shown as.**  `spec/rocks.md` is the precedent
  worth spending here: *"a number a person has to read is a number a
  person will not read"* — weigh by kind, a few marks and no more, the
  ink growing with the quantity.  A rising week wants a mark, not a
  figure.

## The honest note

This is the one card on the board whose value depends on the author
rather than on the work, which is exactly why it is the easiest one to
leave at the bottom of the order.  It was at the bottom until he moved
it.

And the finding that makes it worth building at all: in nine days this
project built an instrument *before* touching anything it meant to
improve — `lagcheck`, `GESTATE_BUILD_TIME`, the loop's stopwatch, every
single time.  The one thing never instrumented was the person doing it.
