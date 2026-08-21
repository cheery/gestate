# manifesto.md — how this project is worked

`README.md` says what gestate is.  `roadmap.md` is future tense,
`journal.md` (with its closed months in `journal/`) is what happened,
`spec/` is why each piece is shaped the way it is, and `keeper.md` is
the author's own standard work.  This file is the method they are
written under, and it exists because the method has been rediscovered
from both ends often enough to be worth stating once.

**And `spec/author.md` is its other half** — this file says what the
*work* must do to be trustworthy; that one says what the **author** must
spend attention on when the work outruns what a person can read.  It was
written the day the volume made the question unavoidable.

**Every claim below cites the thing that proves it.**  That is not
decoration — a manifesto that cannot be checked is a mood.  Where a
sentence here has no file, test or number after it, treat it as
unfinished.

---

## Two rules, and they are one idea

> **1. Do not build what nothing needs.**
>
> **2. What is built must be able to say when it is wrong.**

The first is stated in full in `journal.md` Part I and as "The rule" in
`roadmap.md`: a feature earns its place by having a *caller* — a
program someone wants to write, an unmet spec obligation, or a defect
it fixes.  "It is in the spec" is not a caller.  It closed all of stage
4 without a line written.

The second is the same rule turned around.  A thing with a caller has
someone who will be hurt when it is wrong, so being wrong has to be
*visible* — and visible to something that is not a person's attention,
because attention is what runs out.

They meet in the one exception both of them share: **a defect is always
a caller.**  That is why F64's link-time check was built rather than
closed under rule 1 — and turning it on immediately found a live crash
nothing had exercised (`roadmap.md`, the first milestone: a `Guard
Bool`'s ⊥ reaching codegen unsettled, F58 fixed with it).

---

## What "visible" costs, and where it is not paid

Visibility is not free and is not owed everywhere.  The audio path pays
nothing: no allocation per sample, no branch per integer operation,
nothing per block that is not the sound (`spec/liveaudio.md`).  So the
checks live where time is cheap and the answer is authoritative — in
the **reference**, which is a thousandth of real time and is the
definition of what a graph means.

`audioengine._within_i64` is the pattern: `Int` is a Python integer in
the reference and an `i64` in the generated code, so a program that
outgrows 64 bits diverges silently.  The check is in the reference
only, costs it 4%, and fires at exactly the instant the two engines
part company (`test_audiollvm.py`, instant 40, 0.201 against 0.585).
An oracle, not a guarantee — a program nobody renders through the
reference is not looked at, and the docstring says so.

---

## The instruments, and what each cannot see

| instrument | sees | cannot see |
|---|---|---|
| `GESTATE_EDITOR_TIME` | where a frame goes, key→pixels | anything below the window |
| `tools/lagcheck.py`, `tools/dialoglag.py` | the real window, real X events, read off the screen | correctness of what is drawn |
| `GESTATE_BUILD_TIME` (`gestate/buildtime.py`) | where a rebuild's seconds go, per phase, own time | work no phase is named for |
| `audioperform --report` | peak and per-bar RMS of a render | which notes they were |
| `audioperform.heard_note` | which note came out, against A440 | timbre, level, timing |
| the golden `.samples` | that a render has not moved | that it was ever right |
| native against the reference | that the two engines agree | a program neither runs |
| the session transcript | what a person actually did | what they meant |
| `test_panel_fixtures.py` | that the plugin's bytes are today's export | a fixture nobody regenerates |
| a photographed window (Xvfb + `import`) | **whether what is drawn is right** | anything it is not pointed at, and anything that looks right for the wrong reason |
| `GESTATE_HOST_TAP` (`host.c`) | **the samples the device was actually given** | what the speaker did with them |
| `gestate.pops` | a step a program's own motion cannot account for | whether that step is *wrong* |
| the editor's display list (`shell/editor/tests/view.rs`) | **what the window said** — every run, its colour and its place, with no window open | whether it was *legible*: F155's glyph was emitted, in the colour it was asked for, and unreadable |

The right-hand column is the load-bearing one.  An instrument whose
blind spot is unwritten will be trusted past it.

**The last two rows were each added because the column above them was
blank and nothing filled it** — the screen on 2026-08-17
(`journal.md` §"What the screen saw that the suite could not";
`spec/verification.md` §"The screen is an oracle, and it is the one this
tree lacked" is the harness), and the host tap on 2026-08-18
(`journal.md` §"The samples nobody could read", `card:unheard-output.md`).
Every audio row above the tap reads an offline render or a counter, and
an offline render never exercises the live control path at all.

**And each one's own blind spot is the honest half.**  A picture that
looks right for the wrong reason still looks right — what catches that
is changing the input and demanding the picture follow.  The tap reads
what was handed to the sound card, so *"it sounds thin on laptop
speakers"* is not a question it can be asked, and saying so is what
stops somebody trusting it past where it sees.

---

## The three ways an instrument fails

**It lies.**  `GESTATE_BUILD_TIME` reported `substrate` as the largest
phase of a start — 7.8 s on `chopin.ges` — and it was not: own time
came off a per-thread stack, and `pipeline._deep_stack` hands the front
end to a worker, so the analysis a phase was *waiting for* was counted
twice (`journal.md` §"The day the oracles arrived").  The same fact had
`‖` calling a hand-off concurrency.  Read a new instrument's first
surprising number as a fault in the instrument until it is not.

**It has never failed.**  An oracle that has only ever passed is a
claim.  Break the system and watch it notice: a `Keyboard.press` a
semitone out must read as 61, a `Workbench.control` answering 0.0 must
read as silence, a dead `_push_controls` must silence the C host
(`test_playedsound.py`, all three run by hand before the file was
committed).  The last of those also passes against the Python driver —
which is how that section proved it covers something the others do not.

**It was built from the implementation.**  A harness written by reading
the code can only confirm what the code does; it cannot find a missing
affordance, because it never reaches for one.  So the strongest
assertions are stated in a vocabulary the implementation does not own:
`heard_note`'s candidates are equal temperament from A440 rather than
whatever `keyHz` believes, and *an octave up is an octave up* survives
every mapping decision the compiler could make.

---

## How a practice gets adopted

**A good practice is adopted before it is believed.**  There is a stretch
where it is overhead carried on somebody else's say-so, and it has to
survive that stretch to ever be owned.

The test suite is this project's own case, in Henri's words
(2026-08-17): *"this whole thing runs because we have professional test
suite, that was started by certain claude who saw it was needed.  Then I
realised it myself, after tolerating the tests for a while."*  Imposed,
tolerated, owned — and the middle step is the one that is usually
skipped in the telling and never in the living.

Two things follow, and both are load-bearing:

**A practice must be cheap enough to tolerate while it is unproven.**  A
thing that is expensive *and* unbelieved is abandoned before its evidence
arrives, however right it was.

**And whoever introduces it owes the demonstration.**  Not the mechanism
— the mechanism is the easy half — but the thing that converts tolerance
into ownership: *this is what it caught, that you would have shipped.*
Three practices arrived on 2026-08-17 and each came with one: the gates
(**8 seconds to a named failure against 25 minutes**, measured on a
deliberately broken tree), the photographed window (**three defects the
suite could not see**), and the example rosters (**a bug in a file that
had already been looked at in a real window**).  That is not manners; on
this evidence it is the mechanism by which any of it survives.

The corollary is uncomfortable and worth keeping: **a practice you cannot
demonstrate is one you are asking to be trusted on**, and the honest move
is then to say so rather than to argue harder for it.

---

## Set-based, not point-based

*Henri, 2026-08-17, on the button card: "I intentionally didn't say
directly that the button should be made bigger, because it's not
necessarily the whole answer to it, or correct answer."  Then: "'set
based thinking' should be written down somewhere."*

**Point-based design picks one answer early and iterates on it.**
Set-based design keeps several alive, states what would kill each, and
converges last.  It is Toyota's, and it is the practice behind the
paper title that names the whole surprise — Ward, Liker, Cristiano and
Sobek, *The Second Toyota Paradox: How Delaying Decisions Can Make
Better Cars Faster*.  `spec/author.md` scores this project against
Liker's fourteen principles; this is the sibling of number 13, and the
half that was not written down.

**Why it matters more here than it would on a team of people.**  A
model produces one fluent, well-argued answer in seconds, and the
answer arrives already defended.  That is a point-based machine by
construction: the fluency *is* the convergence, and it happens before
anybody has seen the alternatives.  The author then reviews the answer
rather than the space — and **a review cannot see what was never
offered.**  This is the specific failure the practice guards, and it is
not a failure of correctness: the single answer is usually good.  It is
a failure of *what got considered*.

The board already had the local instance of this and did not know it
was general: **a card's `because` is a problem, never a fix.**  Naming
the fix collapses the set before anybody has looked at it, and the
board's most expensive lesson is exactly that — the card that read
"name datatypes" hid a need that had nothing to do with types.

Three rules, and the third is the one that pays today:

1. **Keep the alternatives with what would eliminate each.**  A set is
   not a brainstorm.  Six answers with no discriminating evidence is
   worse than one, because it launders indecision as rigour.
2. **Eliminate by evidence, not by preference.**  The button's own
   first screen already says *"top right"* and the stranger missed it
   anyway, which weakens "make it bigger" as a whole answer without
   anybody having to argue about taste.
3. **Act now on what every alternative agrees about.**  This is what
   makes the practice cheap enough to tolerate — the rule above.
   Delaying the *decision* does not mean delaying the *work*: whatever
   happens to that corner, the starter file should not name a button
   deleted in `71b90af`, and the command list should not open on the
   command that does nothing.  Both were fixed the same day the set was
   written, and neither commits the corner to anything.

### Henri's name for it, which is better than the practice's

*Watching it work, the same evening: "It appears that these different
voices are shaping our choices and we work a bit like logic
programmers. through unification of obviously correct choices."*

**That is the mechanism, and it is a sharper description than
"set-based".**  Each alternative is a set of constraints on what the
answer may be; what gets built now is their **unifier** — the
substitution every one of them admits.  Rule 3 above is not a
compromise or a stopgap, it is the most general thing derivable from
what is currently known, and that is why it can be shipped without
anybody having decided the open question.

The correspondence goes further than the analogy usually does, and it
is worth spelling out because it explains the *paradox* in the paper's
title:

* **Point-based design is chronological backtracking.**  Guess a
  binding, run to failure, unwind, guess again.  The rework is the
  unwinding, and it is why picking early is slower.
* **Set-based design is propagation.**  Narrow every variable by what
  the evidence rules out, and only bind when a single value remains.
  Nothing has to be undone because nothing was assumed.
* **A failed alternative is a failed unification** — it eliminates,
  which is *progress*, and it does not cost the work done for the
  others.
* And the discipline against premature convergence is exactly the
  occurs check: **do not bind a variable to a term that has not been
  derived**, however plausible it reads.

Which also says what a badly-run set looks like: a store of constraints
nobody ever propagates is not patience, it is an unsolved goal.  Rules
1 and 2 are the propagation; without them this degrades into a list.

**The demonstration this practice owes** (the rule above) is
`card:button.md`, 2026-08-17: asked to explore rather than fix, the
session photographed the window and found three things the framing *"the
button is too small"* would never have reached.  **None of them was a
size.**

---

## Go and do it

*Taiichi Ohno, the Toyota Production System.  Henri quoted it on
2026-08-18, from the Finnish edition, and asked for it in English —
because it is a rule this project keeps and that day had just broken.*

> There are many things one does not understand, and therefore we ask:
> why not just go ahead and take action?  **Do something.**  You will
> come to realise, in the doing, how little you knew — you will see your
> own failures, and you can correct those mistakes; and try again, and
> at the second trial find another mistake, or another thing you do not
> like, and correct that, and try once more.

It is the same idea as *genba* one floor down.  Going to the actual
place is worth nothing if you arrive and reason instead of touching
anything, and **a hypothesis you did not test is a hypothesis that gets
written into a commit message as though it were a finding.**

**And the second half is the part that is easy to skip.**  Ohno does not
say *act and you will succeed*; he says act and you will *see your own
failures*, and that the next mistake follows, and that this is the
method rather than a sign of doing it badly.  Both occasions are
`journal.md` §"The session that had a hypothesis and would not run the
window".

`spec/verification.md` §"The defect is in the seam, and the test is in
the module" is the same finding stated as a rule; `doc/instruments.md`'s
first section — *build the missing instrument the moment the need
arises* — is what it asks of a session that finds itself unable to look.

## What follows in practice

**"It feels slow" is not a measurement.**  Three separate things were
wrong with the editor's repaint and the instrumentation is what said
which: `present` costs 0.02 ms, so the X11 path was never the problem
and no amount of tuning it would have helped (`journal.md`; 48 ms to
3.6 ms).  Neither is a number nobody has checked the arithmetic of —
see "it lies" above.

**A number is worth more than an argument, and cheaper.**  The
workbench started its canvas, score and MIDI loaders on a side thread
to overlap `clang`.  Measured with clang forced to run, serialising
them is *faster*: `quartet.ges` 8.50/9.44/11.82 s threaded against
6.75/7.48/7.33 s serial.  Two Python threads cannot run Python at the
same time; the overlap bought less than the contention cost.  The
switch is kept so the measurement can be repeated on another machine
rather than re-implemented.

**Measure what a person would do, not what the code makes easy.**  The
workbench's twelve defects were every one of them found by a person
using it while two thousand tests passed, and 2026-08-13's two dozen
were nearly all pinned by a session transcript (`journal.md`).  The
tests were not weak; they were pointed at the wrong end.

**When an instrument disagrees with you, measure smaller.**  A hand
note and a scheduled note were 0.084 apart; the notes were measured
instead of argued about, and a decay of 1.63 per second appeared where
the envelope can only produce 3.5 — impossible, until you notice that a
*sum* of 3.5 and 0.6 is not impossible, and that a bank nobody has
spoken about listens by default (`test_playedsound.py`).  With the
second bank silenced: 0.000 apart.

**Write down what was rejected, with its number.**  `clang -O1` is bit
identical to `-O2` here and compiles faster, and is refused because it
costs render speed (`roadmap.md`).  `-fno-slp-vectorize` was taken for
the opposite reason: 56% of the optimiser, producing a bit-identical
object, because no fast-math flags means nothing may reorder a float.
A rejection without a measurement is an opinion that will be
relitigated.

**A green instruction is not a green test.**  `cargo test -p
gestate-panel` built the parity target, ran *zero* tests out of it and
reported success, for as long as the docstring told people to run it
that way (`test_panel_fixtures.py`, now `--features substrate`).  That
is the same failure the file was written about, one floor up.

---

## The shape of a good day

2026-08-15 is the example — a save of `quartet.ges` from 12.0 s to
about 2, and **not one second of it came from making something
cleverer.**  Every one was work being done twice, or for a file that had
not asked for it, or again because somebody had thrown the answer away;
all of it found by an instrument rather than by reading code, and twice
the instrument had to be caught lying first (`journal.md` §"The day the
save cycle was measured").

That is the whole method:

> **Being wrong has to be visible, and the thing that makes it visible
> has to be checked against being wrong.**

### And the shape of the end of one

*Henri, 2026-08-17: "I think this will become a ritual.  Every evening,
we will run the test and talk."*

**Two things at once, and the pairing is the point.**  The suite takes
about twenty-five minutes and nothing can be done to the tree while it
runs —
which makes it the one reliable window in a day for the conversation
that has no other slot: what today's work turned out to be about, what
the next card is really asking, what a finding generalises to.  Neither
half is filler for the other.  The run needs no attention and the talk
needs no keyboard.

It also fixes something that was drifting.  A session that commits and
stops leaves its findings in commit bodies, which is `card:gemba.md`'s
whole complaint — *"today I read sixteen commit messages Claude
wrote"*.  A ritual with a fixed end puts the summary in front of the
person while he can still argue with it.

**And the first one earned its keep before the conversation started**,
on a generated sheet a commit behind its source — `journal.md` §"The
sheet that draws itself" is what that page is for.
