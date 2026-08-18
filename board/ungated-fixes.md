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
  **24 lit pixels counted off a screenshot**, after a friend was handed
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
