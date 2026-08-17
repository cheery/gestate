# timer — see when the day has been too long

    status   done — 2026-08-17
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

### Whose hours? — asked and answered 2026-08-17 morning

The elaboration above says the past half is *"arithmetic on data that
exists"*.  **That was measured on 08-17 and it is only half true.**

    git log --format='%an' -200 | sort | uniq -c
    → 200  Henri Tuhola

Every commit in this repository is authored by Henri, including the ones
a session makes while he is not at the desk.  `git log` therefore
measures **the project's pace and not his**, and it always did — the
nine-day table in `spec/summary.md` was only ever a reading of him
because he was the only one there.  From today he is not: he opened the
day with *"with the new system I don't need to be around all the time."*
An instrument that keeps reading commits as his hours will start lying
on exactly the days the new arrangement is working.

**Henri, 2026-08-17:**

> Both, shown apart.  We are about to be able to measure both.  And I
> probably don't sleep, just rest and occasionally check in, so the timer
> should count this as well and warn about it.

Three things fall out of that, and the third is the one that would have
been missed:

1. **Two marks, not one** — his hours, and the project's.  They are
   different quantities now and a single figure would fuse them.
2. **The project's half stays `git log`.**  Nothing to build.
3. **A rest day with check-ins in it is not a rest day, and the timer
   must say so.**  *"I probably don't sleep, just rest and occasionally
   check in"* is a description of the failure mode, offered by the person
   in it.  Six check-ins spread over twelve hours would score as almost
   no time under any idle threshold, and would be the day that broke him.
   So presence is not only summed — its **span** counts too: first touch
   to last touch is what says the day never actually ended, and that is
   the warning he asked for.

### The line — answered 2026-08-17

The gauge needs a scale and the nine-day history cannot supply one: that
history *is* the overwork, so a scale fitted to it reads green at noon on
a twelve-hour day.

**Henri, 2026-08-17: eight hours.**  Ink starts growing past eight.
Note what that means against the record — several of the last nine days
would have tripped it before lunch, and 08-11 would have tripped it
twice.  That is the point of picking the number from outside the data.

### Still open, and cheap to decide when the work starts

- **What counts as a break?**  Elapsed since the workbench opened is
  easy and wrong — it counts a lunch.  Keystroke-active time with an
  idle threshold is closer; the threshold is a number to pick, not a
  design.  It does **not** decide the span question above, which is
  measured separately and on purpose.
- **Where the day's total is persisted**, and — given the trend finding
  above — that the file keeps **days**, not just today.  A history of
  one day cannot show a sequence.
- **What the trend is shown as.**  `spec/rocks.md` is the precedent
  worth spending here: *"a number a person has to read is a number a
  person will not read"* — weigh by kind, a few marks and no more, the
  ink growing with the quantity.  A rising week wants a mark, not a
  figure.

## Done

One row of the status bar, in a quiet amber under the sentence the last
command answered with:

    you 6h12m ◆ [▪▪◆▲▲ ◆]   project 31 ◆ [▪▪◆▲▲▲◆]   since 04:52 ▲

- `gestate/presence.py` — the record and the reading.  Two quantities
  kept apart, seven days of each, the span measured separately from the
  sum, `$XDG_STATE_HOME/gestate/presence.tsv` for the file.
- `tally` on the wire; `Furniture::tally` and `view::Ink::Spent` in the
  window, which is where the "quiet amber" landed.
- `tools/lagcheck.py::driven` — a driven window keeps no record, since
  XTEST is indistinguishable from a hand.
- `spec/timer.md` for the argument, `test/test_presence.py` and three
  tests in `shell/editor/tests/view.rs` for the contract.

**Two defects the tests could not have found**, both caught by opening
the window and photographing the bar: a day already eight hours old
reported `you 0m` until something was typed, and a rest day drawn as `·`
was a pixel a side away from `▪` and read as a light day on the screen.
A rest day is now a gap.  `journal.md` §"The screen found the bug that
mattered".

Henri, reading it: *"I can see this system saving lives.  It's like
seatbelts in a car."*

### It did not trace to `vision.md`, and now it does

`board/README.md` asks that a card's `because` be traceable to something
in the vision, and that when it is not, *"either the vision is
incomplete or the card is drift, and both are worth saying out loud"*.

This one was not drift: Henri moved it to the front himself and called
the result seatbelts.  But the nearest lines were *"won't demand your
presence"* — which is about the tool not requiring a machine or an
account, not about the project consuming its author — and *"Gestate
won't ever be dangerous to use"*, which reads as being about data and
sound.  Neither was really this.

So it was raised rather than guessed at, because `vision.md` is his own
document and its whole value is that every line in it decided something
he decided.  He answered the same morning, and the line is his, verbatim:

> **2026-08-17: Any project must not consume the person leading it.**

Filed under §"Gestate as a lean vehicle", because that section is about
how the work runs rather than about what the program does — move it if
that is the wrong shelf.  **The rule worked**: a card whose `because`
had nowhere to point turned out to be pointing at a gap in the vision,
and the way to find that was to check rather than to assume.

## The honest note

This is the one card on the board whose value depends on the author
rather than on the work, which is exactly why it is the easiest one to
leave at the bottom of the order.  It was at the bottom until he moved
it.

And the finding that makes it worth building at all: in nine days this
project built an instrument *before* touching anything it meant to
improve — `lagcheck`, `GESTATE_BUILD_TIME`, the loop's stopwatch, every
single time.  The one thing never instrumented was the person doing it.
