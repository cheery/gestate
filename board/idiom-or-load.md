# idiom-or-load — why one brief lands and the other does not

    status   open — 2026-09-04, written the evening the question
             appeared.  Two arms to run, both prompts held by Henri;
             §"The fence" says who may read what before running them
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
