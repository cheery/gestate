# ungated-fixes — a defect closes, and nothing fires if it comes back

    status   open
    because  "we need computer systems that are learning from their
             failures and get stronger and stronger by same mechanism
             that they are pummeled" — 79 of `fixme.md`'s 161 entries
             have no test anywhere that names them, so a fix closed on a
             photograph can quietly reopen and nobody is told
    asked    Henri, 2026-08-18 (Claude wrote the card, from his own
             statement of the problem, and measured it)
    see      fixme.md — the 161 entries, 141 of them marked resolved
             card:interface-oracle.md — the same gap, one domain deep
             test/test_citations.py — already counts `fixme.md`'s entries
             manifesto.md — the three ways an instrument fails
             vision.md — "Gestate won't ever be untested"

## The ask

Henri, 2026-08-18, asked for two cards and was questioned about the need
behind them.  He started somewhere else entirely:

> I start from the problem.  I see that AI is improving all the time.
> It is more and more capable of finding vulnerabilities in computers.
> Therefore, we need computer systems that are learning from their
> failures and get stronger and stronger by same mechanism that they are
> pummeled.

The measurement below was made to test that claim against this tree,
and it is what turned a general statement into a card.  His answer when
it was put in front of him:

> put the 97-of-161 into board/, it deserves that, it should not wait
> our goal of zero new cards being passed.

*The figure is 79, not 97 — his transcription of a number said once in
conversation.  The card carries the measured one.*

## Found by looking

**79 of `fixme.md`'s 161 entries have no test that names them.**

    grep -oE '^### F[0-9]+' fixme.md | sort -u   →  161 entries
    grep -rhoE '\bF[0-9]{1,3}\b' test/ | sort -u →   82 distinct
    the difference                               →   79 unnamed

141 of the 161 are marked resolved.  So this is not a backlog of open
defects; it is the **closed** ones, and that is the part that matters —
a defect nobody has fixed yet is honest about itself, and a defect that
was fixed and left no gate looks finished from every angle.

**Read the number as a proxy, and mark it suspected rather than shown.**
It measures whether a fix left an *address* pointing back at the
failure, not whether a test would catch the failure.  A gate can exist
and never name its F-number, and some of these certainly do.  The
board's own lesson applies — `board/README.md` says an elaboration's
mechanism guess is the part a reader trusts most and the part most
likely to be wrong.  Before anything is built here, **the 79 have to be
read**, and the honest expected outcome is that the list shrinks.

### The tail is the worrying half

F149, F153, F154, F155, F156, F157, F158, F160, F161 — the nine most
recent entries in the file, and not one of them is named by a test.
They are also the ones found by **people rather than by the compiler**:

- **F153** — the `Ctrl-K` hint taught the key only to people who had
  already found the control.  Closed on photographs of a window nobody
  had touched, then after one keypress, then after the list closed.
- **F155** — the one control was a glyph nobody could find.  Closed on
  **24 lit pixels counted off a screenshot**, after Janne was handed
  the editor and failed to find it.

Both closures are good evidence and neither is repeatable.  Change
either tomorrow and the suite agrees with you.

### Why the security framing sharpens it

Gestate's own attack surface is thin, and Henri put the surface itself
below this project — the operating system and the kernel.  No session
working this board can touch that.  What *is* workable here is the
mechanism he described, and under that framing an ungated fix stops
being a tidiness problem: it is a hole that can reopen **without anybody
being told**, which is the one thing `vision.md` says gestate will never
do — *"Gestate won't ever do anything unexpected silently."*

### What this is not

Not a demand that all 161 grow tests.  A large share of the file is
**spec divergence** rather than repaired failure — F5, F26, F32, F33,
F34, F35, F38 are features the spec decided and nobody built, and a test
for an unbuilt feature is a different argument.  The card is about
**closure**: what has to be true before an entry may be marked
`[resolved]`.

### The overlap with `card:interface-oracle.md`, stated exactly

They are neighbours and not duplicates.  The oracle covers one module —
`shell/editor/src/view.rs`, the largest drawing file in the crate and
the only one with no `#[cfg(test)]` block — and it names F150, F151 and
F153 as the three that shipped unheld.  This card is the general rule
across the whole file.

**The dependency runs one way**: the interface-shaped entries *cannot*
be gated until the oracle exists, so the oracle is a prerequisite for
one slice of this card, which is why it sits directly above it in the
order.

## The postcondition, offered

*Written before anything is built, derived from the `because`, naming no
function.  Henri corrects it in a line, or does not.*

> A defect that was fixed once cannot come back without something in the
> tree going red first.

## Questions

*Collected for one sitting, not asked one at a time.*

**1. What counts as a gate?**  A test is the obvious answer and it is
too narrow: F153 and F155 were closed on photographs, and
`card:interface-oracle.md` argues the photograph catches things the
display list cannot.  Golden `.samples`, transcripts and example rosters
are all gates already.  Is the rule *every closure names a test*, or
*every closure names an instrument that runs unattended*?

**A (Henri, 2026-08-18).**  *"I think I agree, those count as a gate."*
So it is the wider rule: **an instrument, not only a test.**  Which
means the 79 is an upper bound on the problem and the first work here is
reading it, not writing tests — a closure held by a golden sample or a
photographed window was already gated and only failed to say so.  What
the rule then demands is that the entry **name** its instrument, because
an unnamed gate cannot be checked and cannot be found by the next
person.

**2. Retroactive, or from here on?**  Converting 79 closures is a
different size of task than binding the next one.  A defensible middle
is: bind every new closure, and walk the tail backwards as far as it
pays.

**A (Henri, 2026-08-18).**  *"From now here on I think."*  **Not
retroactive.**  The 79 stay as they are and are read rather than
converted; the rule binds closures made from today.  Which settles
question 3 as well — an enforcing check takes today's file as its
accepted baseline, and the baseline may shrink and never grow.

**3. Does the suite enforce it?**  `test/test_board.py` is the model —
the board's rules are executable and live in the suite rather than in
the window.  The equivalent here refuses an entry marked `[resolved]`
that no test names.  It would fail 79 times on the day it was written,
so it needs an accepted baseline, and a baseline that only shrinks is
the usual shape.

**4. Is there a fifth verdict — *nothing does, but something could*?**
*Open, 2026-08-19, left open at Henri's ask.*

The first batch reached F161 and **none of the three readings of it could
be spelled with the four.**  The entry is a repair, so *not a repair* is
out; and *nothing can* is false — deleting `fresh.walk = _walk_for(…)`
from `workbench._carry` and running the Python suite `-m "not golden"`
gives **2817 of 2818 passing**, so a test would catch it and none exists.
The three spellings offered were `none — not yet built`, `none — nothing
can` (wrong, by the measurement above) and `none — and nothing in the
tree would say so`.

So the four verdicts distinguish *gated* from *ungateable*, and this
file's most common case is neither: **ungated, gateable, and cheap.**
That is a different fact about the tree than *nothing can*, and it is the
one that tells somebody where to spend an afternoon.

**And the same gap arrives from the other side at F153**, where the
rendering is held by `view.rs` and the decision that feeds it is not
(`window.rs:1860`, in the one file in the crate with no `#[cfg(test)]`
block).  One reading invented `partial` for it on the spot.  Whether that
is the same fifth verdict or a sixth is part of the question.

**Not answered here on purpose.**  A verdict vocabulary that grows
whenever a batch finds it awkward is one that stops meaning anything, and
the honest moment to widen it is after more than one batch has pushed on
it.

**A (Henri, 2026-08-21): "add them."**  The condition set above is met.
Three batches have pushed on it — F161 in batch 1, F132 and F128 in batch
2, and three of batch 3's five — so the vocabulary goes to **five**, not
six, and the difference is worth stating because the first draft of this
answer got it wrong:

* **`none — not yet built` is a ratification, not an addition.**  F161
  wrote it on 2026-08-19, before there was a rule permitting it.  It is
  the spelling the file already reached for when the four ran out, and
  writing it into the list records what happened.
* **`partial` is the one genuine addition**, and it is the class with the
  worst failure mode: a gate that holds one branch of a two-branch fix
  reads, from its name, as though it holds both.  Batch 2 found two of
  them; batch 3 found a third at F118, where `do_open` closes the list in
  two places and the test held one.  **A gate believed to exist is worse
  than a gap known about, because nobody looks at it again.**

*And the number was the right question to ask.*  Six verdicts would have
been a fifty per cent widening on a **16 per cent sample** — ten entries
of sixty-two — which is exactly the growth this section warned about,
arriving with a good argument.  Five survives that objection only because
one of the two was already in use.

### And a named test is not yet a gate — 2026-08-20, batch 2

**Two of that batch's five named a test that passed with the defect put
back.**  F132's assertion excused any rect starting at `y >= tall`, which
is precisely a box painting entirely on the status bar's ground; F128's
fixture was built on the boundary the *fix* reads, and `duet.ges`, its
other half, has been edited since and no longer straddles anything.  Both
were tightened the same morning and both now fail on the defect.

So the verdict *a test, named* has a check under it, and the check is a
**mutation**: put the defect back, watch the test go red, put it away
again.  Reading the entry against the test's name gets this wrong two
times in five, and gets it wrong in the direction that costs most — a
gate believed to exist is worse than a gap known about, because nobody
looks at it again.

**This is retroactive.**  Batch 1's *gated all along* verdicts were
made by reading; only the F149 line records a mutation.

*Corrected 2026-08-21, in the first Friday review, and the correction is
the review's first finding.*  **That sentence was already false when it
was written.**  F155, F160 and F153 each carry a dated 2026-08-19
measurement, and F155's landed in `2b2aef1` — *"the gates get measured,
and one of them turns out to be half a gate"* — the day **before** batch
2 wrote this.  F161 is the only one that flags its own measurement as
reported-and-not-reproduced.  So the line has stood since as a to-do
pointing at work already done, and a session reading the card cold would
have redone it.  They are candidates
for the Friday sample rather than something to redo now — the whole point
of the schedule is that a burst is what degrades judgement — but the rate
found here is the reason to look.

### Batch 3, and the first Friday — 2026-08-21

**F125 F123 F121 F119 F118.**  Four of the five are ungated and the fifth
was half-gated, which is the highest rate any batch has returned — and
it is not a worse batch, it is the first one made entirely of entries
whose fix lives in `shell/editor/src/window.rs` or in the walk that feeds
it.  Every verdict below was made by **mutation**, none by reading.

| | verdict | put back | result |
|---|---|---|---|
| F125 | `none — not yet built` | `editor.load` for a missing name | 2977 of 2977 pass |
| F123 | `none — not yet built` | three halves, separately | 2977, 256, and 346 pass |
| F121 | `partial` | `follow_past` → `follow` at the call site | 346 of 346 pass |
| F119 | `none — not yet built` | the reflow guard dropped | 346 of 346 pass |
| F118 | a test, named | `close_list()` out of each branch | **red on both, after widening** |

**`window.rs` is the finding, not the entries.**  Three of the five put
their defect back inside the one file in the crate with no `#[cfg(test)]`
block, and in every case the whole workspace stayed green.  F153 named
that file in batch 1 as a one-off; it is now four entries, and it is the
reason `card:interface-oracle.md` sits above this card in the order
rather than beside it.

**F118 is the third half-gate**, after F132 and F128, and the first found
in a *branch* rather than in an assertion: `do_open` closes the list in
two places and the test held one.  The bare branch is the one F125 walks
into.  Widened the same morning, both branches now red on their own —
batch 2's precedent, and the reason `partial` was worth a word.

**The specimens are evidence, not instruments.**  Chasing F123's recorded
reproduction turned up that of `test/sessions/`'s 19 files, 14 are named
by nothing, and of the 12 recorded `-session.ges` transcripts only
`chopin-session.ges` is replayed.  A person's walk, recorded so the
defect could be reproduced, and nothing runs it again.  **Not filed as a
card** — the board is four-fewer-zero-new — but it is the largest
unclaimed instrument in the tree and it belongs in whatever
`card:interface-oracle.md` becomes.

### The first Friday review — F155, and it holds

Henri picked F155 from batch 1.  Re-run 2026-08-21 with
`cargo test --workspace --no-fail-fast`, against the two claims the entry
records:

    BURGER = "≡"    → 1 failed, 345 passed — the_corner_offers_a_word_and_not_a_glyph
    INK → FAINT     → 2 failed, 344 passed — the other two

**Exactly as written, a day and a half later, by a session that did not
write it.**  The verdict stands and it is the best-evidenced line in the
file — it is also the only one that records catching its own tautology.

*Two claims were corrected in getting there, both made by reading and
both this session's:* that F155 carried no mutation (a `head -5` that cut
the record off three lines early), and that nothing in the tree reads
`test/sessions/` (a grep for a literal slash against a path built with
`/`).  The card's own sentence about batch 1 was corrected too — see
§"And a named test is not yet a gate".  **Three reading errors in one
morning, none of which survived a measurement**, which is the argument
for the Friday sample and for the mutation rule in the same breath.

## The schedule — heijunka, adopted 2026-08-18

*Henri:* **"so it's a question of heijunka.  We need to balance the
load.  This fixme is not this week's only problem and focusing on it
would causes tremendous context rot issues… I propose, that we cut the
fixme.md list in manageable chunks over three weeks and set a fixed
schedule.  You may have noticed I bound things, eg. no more than 5 lines
shown."*

### The number, corrected first

**62, not 79.**  The `because` above counts every entry with no test
naming it, which is true and is not the working set: it includes the
spec divergences — F5, F26, F32, F34, F35, F38 and their neighbours —
which are features nobody built, not repairs that left no gate.

Counted the way the work is actually shaped: **143 repairs, 62 of them
named by no test.**  The card's headline stands as a measurement of the
file; the schedule below runs on the smaller, honest set.

### The bound

**Five entries a session, and five is a cap rather than a target.**

Sixty-two at five is **thirteen sessions**, which is four or five a week
across three weeks with room to miss days.  The cap is the whole
mechanism: this is not the week's only work, and a burst is what
produces the failure this card is most exposed to — *not* fatigue, but
**judgement degrading across a long uniform task while confidence stays
flat.**  The last forty entries of a single-pass sweep would be audited
worse than the first forty and nothing in the output would show where
the line fell.

**Zero is a legitimate session.**  A floor turns the cap into a quota,
and a quota is answered by inventing tests that pass rather than tests
that would have caught the defect — which is `manifesto.md`'s third
failure mode, and the exact way the auto-audition shipped green and
switched off.

### The order

**Newest first, and human-found before compiler-found.**  The recent
tail is where the defects a person met live — F153 closed on
photographs, F155 on 24 lit pixels — and those are the ones no compiler
will ever find again.  Today's two closures, F162 and F163, both came
from that end of the file.

### What one entry produces

One line, added to the entry: **`gate:`** — either the instrument that
fires if the defect returns, or `none`, with the reason.

Legitimate verdicts, all five — *four from 2026-08-18, the fifth added
and one spelling ratified 2026-08-21, at Henri's "add them"; see question
4 above:*

* a test, named
* another instrument — a golden `.sample`, a transcript, an example
  roster, a photographed window: Henri, 2026-08-18, *"I think I agree,
  those count as a gate"*
* **`partial — <what is held, what is not>`**, for a fix with more than
  one branch where the gate holds some of them.  Name the held part and
  the bare one, both, or the entry reads as gated.
* **`none — not yet built`**, for *ungated, gateable, and cheap* — the
  file's most common case, and a different fact about the tree than
  *nothing can*: it is the one that tells somebody where to spend an
  afternoon.  **It wants the measurement that makes it true**, the way
  F161 and batch 3's entries carry one, or it is a guess.
* **`none — nothing can`**, with why
* **`none — not a repair`**, for an entry that turns out to be a
  divergence rather than a fix

The last three have to be honourable, or the sweep pressures the
session into writing a guard it does not believe in.  **And `partial` is
not a softer *a test, named*** — an entry may only wear it when the gap
is stated; a `partial` with no named bare branch is the half-gate wearing
a new word.

And the field is the one `fixme.md`-as-a-directory would formalise
(`card:working-standard.md`), so doing it this way now makes that
migration mechanical rather than a re-reading.

### The trip-wire

**Two uncertain verdicts in a row ends the session.**  Not the day, not
the card — the session.  Uncertainty arriving twice is the andon for the
degradation described above, and the only cheap moment to catch it is
before the third one is written down confidently.

### And Henri's half, which is also bounded

*His own point, the same afternoon:* **"I see you've gained agency…
But it's better that I reflect on them.  Just like it's with humans.
Nobody does good decisions alone."**

So: **once a week, three verdicts picked at random, and disagree with
them.**  Three, not thirty — the load is levelled for the reviewer too,
or the review becomes the bottleneck this schedule exists to avoid.

That sample is the only measurement either party gets of whether the
other fifty-nine are worth anything.  It earned its place today: three
of this session's confident claims were wrong — two from truncated
greps, one from a stale card — and **every one of them was caught by
him reading, not by me checking.**

### The plan, fixed — 62 entries, 13 batches, 19 Aug → 4 Sep

| # | day | entries |
|---|---|---|
| 1 | Wed 2026-08-19 | F161 F160 F155 F153 F149 |
| 2 | Thu 2026-08-20 | F139 F133 F132 F128 F126 |
| 3 | Fri 2026-08-21 | F125 F123 F121 F119 F118 |
| 4 | Mon 2026-08-24 | F117 F116 F112 F111 F107 |
| 5 | Tue 2026-08-25 | F106 F102 F94 F89 F88 |
| 6 | Wed 2026-08-26 | F81 F80 F77 F74 F73 |
| 7 | Thu 2026-08-27 | F68 F65 F63 F56 F55 |
| 8 | Fri 2026-08-28 | F54 F52 F51 F49 F48 |
| 9 | Mon 2026-08-31 | F47 F46 F44 F43 F41 |
| 10 | Tue 2026-09-01 | F40 F39 F31 F25 F23 |
| 11 | Wed 2026-09-02 | F21 F20 F19 F18 F17 |
| 12 | Thu 2026-09-03 | F15 F13 F12 F10 F8 |
| 13 | Fri 2026-09-04 | F6 F1 |

**Weekdays only, and three weeks runs to 2026-09-08** — so there are
five weekdays of slack built in.  They are not spare capacity: the
platform 6 visit is next week and will take one, and a batch that turns
out to need real work will take another.  A schedule with no slack is
one that gets abandoned on its first bad day.

**A missed day is not made up by doubling.** The batch moves down and
the last one moves out.  Doubling is the burst this whole arrangement
exists to prevent, arriving with a good excuse.

**The batches get older as they go, and probably easier.**  The newest
are the ones a person met — photographs, screenshots, a stranger — and
they are both the most valuable and the most work.  The tail is early
compiler-era entries, where *`none` — not a repair* and *nothing can*
are likely to be the honest answers for many.  If the rate rises there,
that is the shape of the file and not a session cutting corners; the
weekly sample is what tells the difference.

**Henri's review lands on the Fridays**: 2026-08-21, 2026-08-28,
2026-09-04.  Three verdicts, picked at random by him, disagreed with.

### Where the verdicts go

Into the entry itself, as a `gate:` line.  **Committed per batch**, one
commit each, so the progress is visible in `git log` and a session
picking this up cold can see exactly where the last one stopped — which
is the property the schedule needs most, since thirteen sessions is more
than any one context will hold.
