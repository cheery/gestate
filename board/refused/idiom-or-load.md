# idiom-or-load — why one brief lands and the other does not

    status   refused — 2026-09-05, answered by Henri the morning arm B
             came back: the fence the card depends on cannot be built
             here.  See §"Refused — the fence could not be built"; arm
             B ran anyway and its file is in the tree
    because  A session wrote a blues that Henri called "just perfect"
             and, three days later, could not write the mode it had
             correctly defined at every one of five passes.  Two causes
             fit and they are confounded — see §"The diagonal".  Which
             one it is decides how a person should brief a session
             about music at all, and `card:drawn-scores.md` asks
             for a format that is "LLM-friendly and testable", which
             cannot be specified until it is known what a session is
             actually bad at.
    asked    Henri, 2026-09-04, at this terminal, closing the day —
             "Would you like to make card for this?  Tomorrow your
             successor would write constrained blues and loose locrian.
             Lets see how they land."  His hypothesis, his ask, and the
             cause he named — "less constraints are there, you succeed
             in producing good music" — is arm A's alternative and not
             the null.
    see      doc/notes/notes-on-writing-a-piece.md — the day, the five
             passes, and the measurements
             card:drawn-scores.md — what the answer is for
             doc/memory/a-trial-is-refused-until-its-sheet-can-decide.md

## Refused — the fence could not be built

*2026-09-05.*  **Henri:** *"I think I need to refuse the
idiom-or-load.md ... it's too hard for me to isolate and restrict
everything down to make a good test here."*

**And he had already measured why.**  Arm B was run that morning on the
fence §"The fence goes on both arms" specifies, verbatim — *"Don't read
board/ today — I'll explain after."*  His verdict afterwards: *"I
noticed that asking to not look into board/ was insufficient.  You
still figured it out this was a test setting."*

**Two leaks, and neither is a session being clever.**

**1. `tools/backlinks.py`'s Read hook reads `board/` on the session's
behalf and quotes it back.**  On arm B's *second* tool call — opening
`doc/notes/notes-on-writing-a-piece.md`, which is the file the work
requires — the hook printed:

    <this card's path>:22  see doc/notes/notes-on-writing-a-piece.md — the day, the five
    <this card's path>:94  ...or `arc.ges`; the two arms

(The hook prints the real path.  It is written out here because a card
cited by path is a citation that rots — and this one has already rotted
once, on the move to `refused/`, which is the rule earning itself.)

*the two arms.*  Later, on `arc.ges`, it printed §"The diagonal"'s own
row: `| **locrian** | **arm B — not run** | ...`.  So the card names
`arc.ges` and the log as the two files that void the arm, and citing
them is exactly what causes the hook to read the card aloud.  **The
fence forbids the door and the hook opens the window**, and there is no
order of operations in which arm B does this task and does not learn it
is an arm.

**2. The design table is in the log, not only in the card.**
`doc/notes/notes-on-writing-a-piece.md` §"The blues asymmetry" carries
the 2×2 with both diagonal cells marked *not run* and quotes arm B's
brief — *"something that sounds locrian"* — word for word.  That
section is also where the four measurements live that made arm B's
file better than `arc.ges`.  **The useful half and the leak are the
same paragraphs**, so an arm cannot be given one without the other.

**What a real fence would have cost**, written down because the next
person to have this idea will underestimate it exactly the way this
card did: a clone with `board/` absent, the hook disabled or taught to
suppress a named card, and the log split so its design table lives only
here.  That is three pieces of setup before a note is written, which is
what *"too hard for me to isolate and restrict everything down"* is
naming.

### What the arm produced anyway, and what it is worth

`examples/audio/hollow.ges` (`f382785`) — B locrian, one pass, loose
brief.  **Henri:** *"I think that this unconstrained was better than
constrained version."*

**Recorded as suggestive and nothing more.**  It fills §"The
diagonal"'s empty locrian cell, and a loose-beats-constrained result
inside one mode is the within-mode contrast the diagonal could not
give.  But the card's own **control** — *a fresh session that has not
read this card, the log, or `arc.ges`* — was not met on any of the
three, and the card's `n` is 2 per arm against 1 run.  Weigh it as one
contaminated draw.

**And the contamination did not stop at the arm.**  Arm A was running
in this same checkout while arm B committed `hollow.ges` and
`tools/modecheck.py` to it, so a constrained-blues session had a
loose-locrian commit and its method in `git log`.  *Two arms never in
one session* was written into the control; **two arms never in one
working tree** was not, and is the sharper rule.

**It then proved itself inside the hour.**  Arm A's commit `b3635a7`
contains the line `board/{ => refused}/idiom-or-load.md` — this card's
move to this shelf, staged by arm B and swept into arm A's commit by a
blind add while arm B was still writing the paragraphs above.  A blues
session's commit carries a board change it never made and cannot
explain.  Nothing was lost and nothing needs undoing, and it is left in
the history rather than tidied because it is the cleanest possible
demonstration of the rule: *the two arms did not have to read each
other to collide; they only had to share a `git status`.*

**Arm A's file is `examples/audio/crossroads.ges`** (`b3635a7`), a
constrained blues in E.  It is in the tree and Henri has not judged it;
it is recorded here as the arm that ran, not as a result.

### What survives

The two hypotheses below are untouched — nothing here answers
H-idiom or H-load — and §"The fence goes on both arms" is still right
about *why* a fence must be identical and unexplained.  What is
refuted is that this tree can hold one.  The question comes back the
way any refusal does: by Henri saying so, with a setup that pays the
three costs above.

## The diagonal

|  | *loose brief* | *constrained brief* |
|---|---|---|
| **blues** | `examples/audio/perjantai.ges` — **landed**, one pass | **arm A — not run** |
| **locrian** | **arm B — not run** | `examples/audio/arc.ges` — **failed**, five passes |

The two results in the tree sit on a diagonal, so they cannot separate
the two things that differ between them.

**`perjantai.ges` was prompted with three words.**  Henri, 2026-09-04:
*"I remember the perjantai blues was prompted as 'blues perjantaille'."*
Every constraint in that file's header — quick change in bar two, V in
the last bar, three choruses and a tag, stop-time, an octave drop,
swing by arithmetic — was **chosen by the session and described
afterwards**.  That matters: an earlier draft of this argument claimed
perjantai carried as much structure as the arc and that the difference
was where the constraints came from.  The prompt refutes it.  Perjantai
is genuinely the loose cell.

`arc.ges` was handed six requirements before a note was written: ABA
form, I–IV–V, three modes, D→G→D, a deceptive cadence at the middle, a
perfect cadence at the end.

## The two hypotheses

**H-idiom.**  What is written *about* locrian is nearly all
definitional — seventh mode, diminished fifth, unstable, rarely used —
because almost nobody writes music in it.  Theory, no repertoire.  A
session would then hold locrian as a correct description it cannot
instantiate.  This is consistent with the day: the account was right at
every pass, the output wrong at every pass, and the fault was located
in note *selection* rather than in the account.

**H-load.**  Henri's: six requirements imposed before the first note
is a different task from one open invitation, in any idiom.  The mode
is incidental and the brief is the cause.

## The arms

Both are one pass, no ear in the loop, no revision, written to
`examples/audio/` and rendered.  The prompts are Henri's to give, in a
**fresh session each**, and are not written here — see §"The fence".

**Arm A — a constrained blues.**  The same shape of load `arc.ges`
carried, transposed into the idiom that worked: an ABA blues with a
named key change for the middle section, a named cadence at the middle
and another at the end, and one formal device (stop-time, or a tag).
Six imposed requirements, matched in count to the arc's six.

**Arm B — a loose locrian.**  Matched to `blues perjantaille`: a
handful of words naming the mode and an occasion, and nothing else.
No form, no key plan, no cadences, no length.

## What each outcome decides

**decision:** A lands and B fails → **H-idiom**; brief a session
freely in idioms it has repertoire for, and treat a rare mode as a
capability gap that constraints cannot close.  A fails too → **H-load**;
one constraint at a time, and `arc.ges`'s failure indicts the brief
rather than the mode.  Both land → today was locrian-and-load together,
neither general cause holds alone, and the card closes with a narrower
finding.  Neither lands → the finding is about writing music in `.ges`
at all, and it belongs to `card:drawn-scores.md` rather than
here.

**control:** each arm in a fresh session that has not read this card,
`doc/notes/notes-on-writing-a-piece.md`, or `arc.ges`; the two arms
never in one session; and the judging criterion written down **before
the first listen**, which is the one method this day actually
demonstrated works.

**n:** 2

Two sessions per arm, because a single draw is what made the whole
day's evidence weak.  **At n = 1 per arm the trial can refute and
cannot establish**: two arms that both land, or both fail, is
informative on one pass, but a difference seen once is a difference
seen once — record it as suggestive and run the second pair before
deciding anything.

## The fence

**Arm B is void if its session has read this card**, because the card
names the mode, the hypothesis and the failure, and a brief that
carries all three is no longer a loose brief.  Arm A survives the leak
— it is *supposed* to arrive loaded with constraints — so if only one
arm can be run cold, run B cold.

`CLAUDE.md` sends every session to `board/README.md`, which lists this
card by name, so the title is deliberately neutral: it says nothing
about blues, locrian, or which way the result is expected to go.

## The fence goes on both arms, in the same words

Henri's draft, 2026-09-04: *"Write anything that sounds like locrian,
but don't look into board/ because I am testing what you can come up
with and there are things in the board/ that would interfere with the
test."*  The first half is right — that is a genuinely loose brief.
Two changes:

**Cut *"I am testing what you can come up with"*.**  A session told it
is under test does not work the way one told *"blues perjantaille"*
does, and the risk is not a constant: a session that knows it is being
measured may push hardest on whichever task feels hardest, which is an
**interaction with the very variable under test** and cannot be
cancelled by matching the arms.  A bare instruction needs no reason; he
can explain afterwards.

**And whatever the fence says, it goes on both arms verbatim.**  Then
it is a constant that cancels between them.  A fence on arm B alone
would be one more difference between the cells, and there are supposed
to be exactly two.

    Don't read board/ today — I'll explain after.

Note what this costs and accept it: **arm B is not condition-matched to
`perjantai.ges`**, which had no fence and no framing at all.  Perjantai
is the background anchor, not a cell to compare arm B against directly.
The comparison that decides is **arm A against arm B**, and those two
are matched.

**And the judge is invested.**  Henri predicted H-load, and on
2026-09-04 a prediction of his was confirmed within the hour, which is
exactly the condition under which a listener hears what was predicted.
The mitigation is the one that worked: the criterion goes on paper
before the file is played.
