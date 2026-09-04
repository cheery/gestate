# backlinks-ranges — the citers of the passage being read, not of the file

    status   shelved — 2026-09-04, on arrival; the lamp it waited on was
             retired the same day and the measurement refused the fix —
             §"The lamp tripped, and the measurement refuses the fix"
    because  "The C host has 58 citers.  The journal, the ledger and the
             board README have hundreds, and most of those citations are
             the file's name in passing.  A hook that shows twenty lines
             of that trains the reader to skim past it, which is how an
             andon gets muted."  — Claude, 2026-09-04, asked whether the
             hook improves anything; and Henri, the same hour: "Not all
             citations are equal."
    asked    Henri, 2026-09-04 — "Can you write the potential fix
             somewhere, and write something that ensure you will correct
             the issue if it becomes an issue."
    see      card:backlinks.md — the hook this refines, and §"Q1, reasoned"
             tools/backlinks.py — `TIERS`, `lamp`, the fire log
             doc/instruments.md §"`tools/backlinks.py` — who cites this?"
             doc/memory/sediment-versus-debt.md — this waits on an event,
             not on a decision

## What this is, what it is not, and when it runs

**The hook answers for a file; a session reads a passage.**  `Read`
carries an `offset` and a `limit`, and a session reading forty lines of
`spec/types.md` is shown every citer of the whole file, most of them
about some other section.  The fix is to answer for the range: a
passage citation — `types.md §"The spine"` — names a heading whose line
is known, and a citer of a heading inside the range is what the reader
most wants; a citer of the file at large is what they get today.

It is **not** a change to the ranking already built (`TIERS`) and not a
second index.  It runs, when it runs, inside the same hook.

**It is shelved on arrival, and that is the point.**  Nothing is built
until the hook's own log says the cut has become the rule, and the
thing that says so is a lamp every session sees at every commit.  A fix
built before that is a session guessing that its twenty lines were
noise, and the tree's rule is that a guess gets measured first.

## The trigger, which is the mechanism

Every fire appends a line to `~/.local/state/gestate/backlinks.log` —
epoch, file, citers, shown.  `python tools/backlinks.py --check`, which
`tools/pre-commit.sh` prints at every commit, trips when over the last
fourteen days there were at least thirty fires and a third or more of
them were cut at twenty.  When it trips it prints this card's id, and
exits 2, and the pre-commit still commits — a lamp, not a gate, because
the correction is a build and not a one-line fix.

**The three numbers are the session's** — fourteen days, thirty fires,
a third — picked 2026-09-04 with nothing behind them but the shape of
the sitting-limit precedent.  They are Henri's to change, in `LAMP_*`
at the top of the tool, and the first thing to check when the lamp
trips is whether it tripped for the right reason: `--report` lists the
most-read files with their counts, and if the cut fires are all the
ledger and the journal, the fix below is the right one; if they are
cards and memory, the cut is too low and the fix is a number.

So the correction is ensured the only way the tree knows how: the
session that next commits after the lamp trips reads this card's id in
the lamp, and this card is the design.  It does not depend on anybody
remembering.

## The fix, designed

1. **Index the section, not only the key.**  `scan` already resolves
   `file.md §"heading"` to the target file; it should also keep the
   heading text, so a row is `[line, key, text, explicit, section]`.
   Cache format bumps to v3.
2. **Resolve headings to lines at query time.**  For the target file,
   flatten it the way `test_citations._named` does, and for each cited
   section find the line its words first occur on.  A citation whose
   words are not found resolves to the whole file, as today.
3. **Read the range from the hook input.**  `tool_input.offset` and
   `tool_input.limit`, both optional.  No range means the whole file
   and nothing changes.
4. **Rank by range.**  A passage citer whose heading lies inside the
   range goes to the front, ahead of every tier; a passage citer of a
   heading outside the range drops behind the mentions; file-level
   mentions keep their tier order.  So a session reading §"The spine"
   sees who cites the spine first, then who cites the file.
5. **Say what was done.**  The first line of the context becomes
   *`spec/types.md` lines 40–80 are cited by 3 places, the file by 41*.
6. **Known answers first.**  A tiny tree with two headings and a citer
   of each; read the second range and the second citer is first.  Then
   the cost: the flattening of a 7,000-line file per read is the new
   expense, and the budget is still a tenth of a second warm — cache
   the heading-to-line map beside the index if it is not.

## The lamp tripped, and the measurement refuses the fix — 2026-09-04

*The card's own §"The trigger" says the first thing to do when the lamp
trips is check whether it tripped for the right reason.  It did trip —
40 fires, 20 cut, 50% — and the check says **no**, three times over.
Henri: "ok. lets do the fix that lamp points at."  This is what
happened instead.*

**The check offered two answers and the truth was a third.**  The card
expected either the ledger and journal (build the fix) or cards and
memory (the cut is too low, change a number).  The cut fires are
**spec files and libraries** — `spec/scope.md`, `dynamicscore.md`,
`north_star.md`, `gestate/audio.ges`, `music.ges`, `command.ges`,
`session.py`, `tools/suite.py` — which is neither.

**1. There is almost nothing for the range to rank.**  The fix ranks
passage citers by whether their heading falls in the range.  Of the
files that actually trip the lamp:

| file | citers | `§"heading"` citations |
|---|---|---|
| `spec/scope.md` | 37 | **0** |
| `gestate/audio.ges` | 150 | **0** |
| `gestate/music.ges` | 140 | **0** |
| `spec/scorebox.md` | 43 | 5 |

Reading a passage of `spec/scope.md` and applying the whole designed
fix would reorder **zero rows**.  The card assumed the noise was
passage citations pointing at other sections; it is bare mentions of
the filename, which name no section at all.

**2. The tiering already works — the cut is falling correctly.**

    spec/scope.md   shown 20: {documents 2, code and tests 18}
    fixme.md        shown 20: {cards and memory 20}   cut 616 lower
    audio.ges       shown 20: {cards 1, documents 19}  cut 89 code, 13 history

Nothing good is being lost.  For `spec/scope.md` the top twenty are all
low-tier **because there is nothing better to show** — no card and no
memory cites it at all.

**3. And the obvious alternative makes the good case worse.**  Capping
each tier separately was measured at three settings.  It cuts
`spec/scope.md` from 20 rows to 4 — and at *every* setting it loses
`shell/web/src/lib.rs` and `tools/pages.sh` from `card:online.md`,
which are two of the three rows a session actually followed on
2026-09-04.  A fix that damages the case where the tool works, to
improve the case where it does not, is not a fix.

### So the finding is about the lamp, not the tool

**Being cut at twenty is not evidence of noise.**  It is evidence that
many files in this tree have more than twenty citers, which is a fact
about the tree.  The cut-share cause fires on a property of the
repository rather than on a fault in the instrument, and it will go on
firing at every commit — which is how an andon gets muted
(`doc/memory/recorded-is-not-answered.md`).

**The lamp's other cause already measures the thing that matters.**
`--earned` asks whether anything the tool offered was ever opened, and
it stands at 4 of 17 followed — not zero, which is the floor that would
condemn the hook.

*The session's recommendation, and the numbers are Henri's* (§"The
trigger" says so): **retire the cut-share cause, keep `--earned`.**
**Taken the same hour** — Henri: *"retire the cut-share cause, keep
--earned"* — so `lamp` has one cause now and the share is reported
without tripping.

**And this card's trigger went with it**, which is worth saying plainly
rather than leaving the card pointing at a lamp that cannot light.  It
now waits on a *measurement*, not a counter: **the day a reader can
show that the twenty rows lost something they wanted.**  Today's
measurement is the opposite — the tiering cuts the right rows, and the
repair that shortens the lists drops two rows a session followed.  The
three tables above are what the next attempt has to beat.

## Shelved

Waits on the lamp — an event, not a decision.  Henri, 2026-09-04, on
what this card is for: *"write something that ensure you will correct
the issue if it becomes an issue."*  The lamp is that something; this
card is what it points at.
