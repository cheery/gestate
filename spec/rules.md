# rules.md — the method is capped at 2000 lines, and the cap is measured

*Written as a contract, 2026-08-20, at Henri's ask, at five in the
morning.  The cap is stated here and nowhere else; the count is
`tools/rulecount.py`; the gate that fails a commit over the cap goes in
when the count is first under it, and `card:working-standard.md` owns
getting it there.*

`spec/` is where this belongs.  A spec in this tree tells about a
contract written in software, and this is one: the method that runs the
project has a size, the size is finite for a reason that is not taste,
and a number that nobody measures is a mood.

---

## The rule

**The rules set is five documents and it may not exceed 2000 lines
total.**

| file | what it is |
|---|---|
| `board/README.md` | how a task is worked |
| `manifesto.md` | how an instrument fails |
| `spec/author.md` | what the author spends attention on |
| `doc/instruments.md` | what a session already has to work with |
| `vision.md` | what any of it is for |

*2000 for now* — Henri, 2026-08-20.  The number is allowed to move,
by him, in writing, with the date.  It is not allowed to move because a
session found it inconvenient on a Tuesday.

## Why there is a cap at all

*At Henri's ask, reworded on 2026-08-24.  The paragraph it replaces is
quoted below, because it was the premise of this whole spec and it was
measured false.*

> Because a session reads **all five, every time**, before it knows what
> it is working on.  That is what makes them rules rather than
> reference.  `spec/` is 16,000 lines and costs nothing until you touch
> the part it describes; the rules cost their full size on every single
> shift, and they come out of the same window the work has to fit in.

**Nothing loads the five.**  Measured 2026-08-23, `journal.md`
§"Nothing was loading the rules": no `CLAUDE.md`, no `AGENTS.md`, no
hook that injects a document.  What a session reads unasked is the
memory index and, since that evening, the one-line pointer to
`board/README.md`.  So the five are reference in the sense the old
paragraph reserved for `spec/` — they cost nothing until opened — and
`doc/notes/`' name for them, *the method files*, carried the same
false assumption and is retired with it.

**What the cap measured all along was growth**, and that is what it
is for.  Session narration accretes into a rule document because the
session that arrived at the rule was proud of the arriving, and the
document stays true while getting longer and harder to *find a rule
in*.  A pointer sends a stranger to `board/README.md`; a rule that
cannot be found in it is a rule that does not reach the moment.  The
cap is a lamp on that — one number, measured at every commit, that
says the set is getting fatter.

**And the cap's second reason is the keeper's, not a stranger's** —
`card:memory-atrophy.md`, move 3, 2026-08-24: *a method he could recite
is worth more than a longer one he can search.*  The 2,000 lines and
`vision.md`'s deliberate shortness are atrophy controls for the person
who has to hold the shape of this in his head, and whoever is tempted
to raise the number should know it is holding both things.

**And two of the five are pieces, not documents.**  `board/README.md`
is where `status blocked` is real, and `spec/author.md` is the
author's own; `tools/seedaudit.py` names both and refuses their loss.
The other three — `manifesto.md`, `doc/instruments.md`, `vision.md` —
are cited from the tree more than any `spec/` file and read on pull.

Growth is not hypothetical.  Measured the night the cap was set:

| | 2026-08-18 | 2026-08-20 |
|---|---|---|
| `board/README.md` | 483 | 700 |
| `doc/instruments.md` | 210 | 457 |
| `spec/author.md` | 379 | 410 |
| `manifesto.md` | 408 | 409 |
| `vision.md` | — | 74 |
| **total** | **1,554** *(four files)* | **2,050** |

**+422 lines in two days**, and `doc/instruments.md` more than doubled.
The cap was over the moment it was written.  That is the finding, not a
detail: it was set as a guardrail and it landed as a debt.

## What the fat is

**Session narration.**  Henri, 2026-08-20: *"The rules have gotten
narration from sessions that belongs into the journal."*

A rule document accumulates the story of how each rule was arrived at,
because the session that arrived at it was proud of the arriving.  The
story is worth keeping — it is why `journal.md` exists — but it is not
the rule, and it is charged to every future session at full price.  The
test is whether a stranger who never saw the incident needs the
sentence in order to *follow* the rule.  If they only need it to
*believe* the rule, it is journal.

The other known fat is restatement: one rule stated three times inside a
single file, recorded in `card:working-standard.md` on 2026-08-18 and
still true.

## The three cheats

Named because they are the ways the cap gets met without the context
getting smaller, and all three are easier than trimming.

**A sixth document is a cheat.** *(Henri, 2026-08-20: "Agreed, sixth
document is cheat.")*  Splitting `board/README.md` in two gets the
per-file numbers down and leaves the reading identical — worse than
identical, because now a session must find both halves.  The cap is on
the **set**, and the set is closed at five.  A sixth needs a caller,
the same rule the atlas closed at five sheets under.

**Dropping dates is a cheat.** *(Henri, 2026-08-20: "Dates are not the
fat, agreed.")*  A rule without its date cannot be argued with later —
you cannot tell a standing decision from a leftover, and the thing that
makes this method work is that a rule can be taken back by the person
who set it.  Dates are the cheapest lines in the corpus and the last
ones to go.

**Pushing text into another rule is a cheat.**  Moving narration out of
`doc/instruments.md` and into `board/README.md` changes no total.  The
only honest destinations are `journal.md`, a card, or deletion.

## The proof

A cap that is not measured is a mood — `manifesto.md`'s rule, the same
one `spec/sandbox.md` applies to the fence.

    python tools/rulecount.py

prints the five files, the total, and the room left.  It is the pull
version, for when somebody wants to know where the lines are.

**Over the cap is an andon, not a refusal.**  Henri, 2026-08-20: *"make
it light the andon."*  `tools/suite.py` puts the count on
`test/gates.md` — as a row when there is room, as a red section when
there is not — and prints it at every commit through the hook.  **The
exit code does not change.**

The reason is not leniency.  A genuine amendment to the method is
exactly the change that arrives with a good argument and no room, and a
gate that refuses it does not prevent the growth — it teaches the next
session to make the method *worse in smaller words*, which is the one
outcome this cap exists to avoid.  Growth has to be **seen**.  It does
not have to be **stopped**.

What the suite still refuses is the **loss of one of the five**, which
is not the method growing but the cap being abandoned; `test/test_rules.py`
holds that half, and tests that the lamp itself can light — a signal
that cannot fire is indistinguishable from a tree that is fine.

## What the count does not cover

*Added 2026-08-20, found while moving the memory corpus into the tree.*

A session also reads a private `MEMORY.md` index every time, before it
knows what it is working on — 29 lines that morning, holding the hooks
for a corpus whose bodies now live in `doc/memory/`.  The bodies are
`spec/`-shaped and cost nothing until one is opened; the index is
rules-shaped, and it is not counted here.

The corpus behind it was **2,386 lines**, larger than this whole capped
set, and until 2026-08-20 it was outside the tree where nobody could
weigh it at all.  Whether the index joins the five is Henri's call, in
writing, with the date — the same as moving the number.

## The journal rotates

*Added 2026-08-21, at Henri's ask.  The mechanism is
`tools/journalroll.py`, the lamp is `tools/suite.py`, and
`test/test_journal.py` is the half that refuses.*

**The journal has a budget, and it is not a reading cost.**  Nobody
reads `journal.md` end to end; they `grep` it.  That is precisely the
charge: at 530 KB every search pays attention over ten thousand lines of
closed months to reach the one paragraph it wanted, and a small model
reading the same file pays it in the only window it has.  Henri,
2026-08-21: *"not because the journal is sick but because at 530K every
session that greps it is paying attention-tax for no return, and if
small models ever join the loop, unrotated is unusable."*

So the shape is the opposite of the cap's.  The rules are trimmed
because they are read; the journal is **moved** because it is searched.
Nothing here ever asks for less journal.

| | |
|---|---|
| `journal.md` | the open month, plus the index |
| `journal/YYYY-MM.md` | a closed month, append-only |
| budget | **8,000 lines** on the open journal |

*8,000 for now* — proposed by a session, 2026-08-21, and Henri's to
move, in writing, with the date, the same as the 2000.  The anchor is
the **skim**: the budget is the size of a month one person can pass over
in a sitting, because a month that cannot be skimmed does not get
rotated, it gets postponed.  At the measured pace — 10,450 lines in the
thirteen days from 2026-08-08 — the lamp lights before the month ends,
and that is the mechanism reporting that the month wants more than one
cut, not a number set wrong.

## Archive, don't airbrush

**A closed month is never edited again.**  A cut is appended at the
bottom of its file and nothing above it is touched.  Henri, 2026-08-21:
*"nothing is rewritten, because git already remembers and a journal that
gets retroactively edited becomes a second source of truth about the
past."*

That is also the answer for the **grudge class** — an entry whose facts
belong in the record and whose heat does not.  Henri, 2026-08-20: *"I
don't think it's worthwhile to carry grudges in a journal."*  The
handling is not deletion and not rewriting: **the fact stays in the
archive and the heat gets no index line.**  What is being decided at the
rotation is what the month is *pointed at as*, and a month is not owed a
theme it would rather not have.

**A citation says `journal.md` whatever month it landed in.**  The name
is the journal's; the archive is where its closed months live.  Same
separation as a card's id and its shelf, same reason — a citation must
not rot because time passed — and `test/test_citations.py` searches the
open month and the archive as one corpus.  Rewriting twenty-eight
citations every month was the alternative and it is the spelling that
rots.

## The index is the whole point

One line per closed month, in `journal.md`'s head, **naming its
themes** — so a session looking for June's audio work opens
`journal/2026-06.md` and nothing else.  Without it the rotation has only
hidden the journal.

The block is generated by `tools/journalroll.py --index` and checked by
`test/test_journal.py`, because an index behind its directory is the
defect class the gates already exist for: a generated page behind its
source, like the atlas behind its modules.

## The rotation is an act of the fire

Not of a gate.  The fire is the keeper's evening — the standing proposal
that this tree's metabolism needs an appointment rather than a reminder
— and **the rotation is the first thing folded into it**, which is what
took the evening from proposed to adopted on 2026-08-21.  `keeper.md` is
that evening's standard work and the rotation is its fifth act.  Once a
month:

1. **Skim the closing month once.**  Not read — skim, at heading level.
2. **Promote the two or three lines that pass the earning test** up into
   the method files.  The test is the one in §"What the fat is", run the
   other way round: a sentence earns a rules line when a stranger who
   never saw the incident needs it in order to *follow* the rule.  Most
   of a month promotes nothing, and that is the expected result.
3. **Write the index line**, naming the themes and leaving out the heat.
4. **Close the file** — `tools/journalroll.py --roll --themes "…"`.

**The lamp's meaning is *rotation is due*, not *stop writing*.**  Henri,
2026-08-21.  It never changes an exit code, and a missed evening is not
a red gate: `vision.md` says gestate won't demand your presence, and a
metabolism that punishes an absence breaks the line that makes the tree
safe to own.

**And a session proposes; the author approves.**  The split and the
index line are a session's to draft — the promotion pass is not, because
it edits the five documents and `spec/author.md` is his.
