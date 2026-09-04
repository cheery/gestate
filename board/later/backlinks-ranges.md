# backlinks-ranges — the citers of the passage being read, not of the file

    status   shelved — 2026-09-04, on arrival; wakes when the lamp trips
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

## Shelved

Waits on the lamp — an event, not a decision.  Henri, 2026-09-04, on
what this card is for: *"write something that ensure you will correct
the issue if it becomes an issue."*  The lamp is that something; this
card is what it points at.
