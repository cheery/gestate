# stranger-test — run the vision's own top claim

    status   open
    because  the first line of vision.md is a test nobody has ever run
    asked    Henri, 2026-08-16
    see      vision.md §"Ease of use and efficiency"
             spec/workbench.md — the brief this sentence comes from
             fixme.md — where the findings go
             journal.md §"Run two, minute by minute" — the log

**Preparing the next run?  §"Run three — booked" is the whole of what to
do**, and the two ways to waste it are both free to avoid.  Everything
above it is why the test exists and what two runs have already taught;
everything below it is what to carry into the room.

## The ask

`vision.md` opens with a claim that is unusual in being **falsifiable**:

> Somebody who has never read this repository should be able to open a
> file, hear it, change it, and hear the change without being told
> anything first.

It is the project's top-level goal, it is checkable, and in nine days
nobody has checked it.  This card is *genchi genbutsu* aimed at the
vision rather than at the code: go and see whether the claim is true.

## What the test is not

**Not the examples.**  Henri's own correction, written into `vision.md`
the same evening: nearly every program in `examples/` was written by an
AI with no prior knowledge of gestate, and *"this is not a stranger test
of the Ease of use, however it tells that the language is learnable."*

The distinction is the whole design of this card, because getting it
wrong produces a false green:

| | reads | tests |
|---|---|---|
| the AI stranger | everything — 36,000 lines of docs in one gulp | is the **language** learnable |
| the human stranger | nothing — opens a window and expects it to make sense | is the **tool** approachable |

§1 is about the second one.  A fresh session that swallows the whole
`doc/` tree and then succeeds has proved something real, but not this.

## What the work is

A fresh reader, given the repository and **nothing else**, asked to do
exactly the four things the sentence names: open a file, hear it, change
it, hear the change.  What is recorded is not pass or fail — it is:

1. **Everything it had to be told**, in order.  Each of these is either a
   documentation gap or an interface gap, and which one it is will be
   obvious from where it got stuck.
2. **Everything it had to read** before it could act, and how much.  The
   claim is *without being told anything first*, so the amount of
   reading required **is** the measurement.
3. **Where it guessed**, and whether the guess was right.  A wrong guess
   that worked is worse than a stumble; it means the window taught
   something false.
4. **Where it gave up.**

Findings become `fixme.md` entries.  If it produces none, that is worth
knowing too — and the run itself becomes the regression test, because it
is repeatable after every change that touches the first five minutes.

## The hazards, which decide whether the result means anything

- **Memory leaks the answer.**  A session on this machine has a memory
  directory holding a great deal of gestate — where the workbench is,
  how it is started, what the fast paths are.  A stranger with that is
  not a stranger.  The run must be in a clean environment with no
  project memory available, and the card should say how that was
  ensured, or the number is worthless.
- **A reader who knows it is being tested performs.**  Some of this is
  unavoidable; what helps is recording the transcript rather than a
  self-report, so the stumbles are evidence rather than testimony.
- **It is still not a human.**  A careful reader who cannot ask
  questions is the closest cheap approximation, and it is much closer
  than the examples were.  The honest write-up says so.  The real
  version of this test is Henri's friend, once, with nobody helping.

## Why it is worth doing early

Every other claim in `vision.md` is a direction.  This one is a
**measurement**, and it is the one the whole §"Gestate as a generic
working platform" section was told to defer to: *"In case that this will
conflict with the ease of use.  Then the ease of use is preferred."*

A preference that has never been measured cannot be preferred in
practice.  This is what makes that sentence enforceable.

## The instrument is consumed by use

*Henri, 2026-08-17, after the first run happened by accident: "The
second run with a stranger is possible, I have plenty of friends.  What
we need to do is to examine and think on this because they're precious
moments to show this to a stranger and it's like they run out
eventually."*

**This is the only measurement in the project that cannot be repeated.**
Every other instrument here can be re-run: the suite, the golden
buffers, the photographed window, `GESTATE_BUILD_TIME`.  A stranger can
be used once, and using one destroys it — there is no way to un-show
somebody a program.  The supply is finite and social, and it is spent
whether or not the run was designed.

So the discipline is design-of-experiments, and it is the same
discipline as `manifesto.md` §"Set-based, not point-based" pointed at a
scarce test.  Five rules, in the order they bite:

**1. The unit is not a friend.  It is a friend × one first contact.**
The first run is not fully spent.  He was stopped at *find the control*
and never reached what is behind it, so **everything past the door is
still virgin for him** — he can be asked, later, to do the thing he
never got to, and only the discovery question is gone forever.  Count
the resource honestly and there is more of it than "one friend, one
run" suggests.

**2. Never spend one on something already believed.**  If every
alternative in the set predicts the same outcome, the run carries no
information.  The run is worth its cost only where the theories
*disagree* — which is why the set has to be written down first, and why
the two defects fixed on 08-17 were fixed rather than tested: nobody
needed a person to establish that a sentence naming a deleted button is
wrong.

**3. Fix what is known-wrong first, for free; vary only the uncertain
thing.**  A run against a window with known defects in it spends the
person on rediscovering them.  But the opposite error is worse: change
five things, watch the next stranger succeed, and you have learned that
the bundle works and not which part.  **Free-and-certain changes are
unlimited; uncertain ones should be varied one at a time**, and that
constraint is what actually rations the supply.

**4. Pre-register what each theory predicts.**  Before the run, write
down what would be seen if the problem is the corner, and what would be
seen if it is what is behind the door, and what would be seen if it is
neither.  Without that, the result is explained afterwards and confirms
whatever was already thought — which spends a person to learn nothing.
This is the single highest-value habit for an instrument that cannot be
re-run.

**5. Record the whole trajectory, not the verdict.**  The first run
produced two sentences and they were enough to find three defects — but
only because the window could be photographed afterwards to reconstruct
what he must have been looking at.  What is wanted is what this card
already asks for (told, read, guessed, gave up), captured *as it
happens*.  **The cheapest available improvement to run two is recording
it better**, and it costs nothing but deciding how beforehand.

### What run two should be asked, on today's evidence

Not "is it better now".  The theories that survive 08-17 disagree about
exactly one thing a person can settle: **whether the corner is findable
at all**, once the first screen no longer lies about it.  So the run is
worth spending if and only if the corner has been changed in one
identifiable way and nothing else has — otherwise it answers a bundle.

And there is a second question that costs *no* new stranger, per rule 1:
hand Janne the window with the list open and watch what he
does with `apply`.  He never saw it.

## What run two established — 2026-08-18

*Janne, over chat, thirty minutes clone to fourth verb.  The log, the
predictions and every verbatim exchange are in `journal.md` §"Run two,
minute by minute" — this is what the next run needs to know.*

**All four verbs happened.**  `vision.md`'s opening claim was run
against a person for the first time and held — **in its documented form,
not its pure one.**  He read `README.md` in order, and reading is being
told; what was measured is that *the way in works as a path*.

**Fourteen of the thirty minutes went to the way in** — F162 and F163,
a placeholder he could not fill and a shell that could not find `cargo`.
Both are fixed and gated (`test/test_way_in.py`), so run three should not
meet them.

**The corner was judged and not discovered.**  He had seen the window
once before, socially, which spent the discovery question permanently.
He looked at the new corner unprompted — *"nyt tuo [command] oikeassa
yläkulmassa näkyy hyvin"* — which is **legibility, from exactly the right
person**, and is not findability.

**Three things nobody predicted**, kept because they are the kind only a
person produces: the first command he reached for was `stop`; he found
the piano unaided; and asked how long the first build took, he said ten
to fifteen seconds having already called it long — which moved the
defect from *duration* to *silence* and saved a fix aimed at the wrong
thing.

**What is still spendable of him** — rule 1 counts the unit as *friend ×
one first contact*.  Gone: his first contact, and the corner-discovery
question.  Not gone: any question that can be asked cold, including the
one this card wants — *which value did you change in `lowpassSvf`, and
did you know what it would do before you changed it*, which is what
`card:argument-names.md` exists to answer, aimed at the function that
motivated it.

## Moved to last, 2026-08-18

*Henri, immediately after the run:* **"I think that we need another
stranger.  move the card to the last."**

Not a demotion on value.  It is that **the card now waits on a person
nobody has**, and its one remaining question — whether the corner is
findable by somebody who has never seen it — cannot be answered by any
session at any position in the order.  Everything a session *can* do for
it has been done: the method is written, run two is logged, and the two
defects it found are fixed and gated.

**What would move it back up is a name**, not a decision.  Until then
the order is honest: cards that can be worked sit above one that cannot.

## Run three — booked, and the two ways to waste it

*Henri, 2026-08-18:* **"I am visiting platform 6 next week, I go present
gestate to my other friend and talk.  I can do stranger test with him."**

An **unspent** friend, with a date.  This is the instrument the one
remaining question needs — *is the corner findable by somebody who has
never seen it* — and it is the only kind of instrument that can answer
it.

### The order is the whole experiment

**The stranger test happens before the presentation.  Not after, and
not during.**

This card's own rule says a stranger is consumed by *any* contact, and
2026-08-18 proved it at cost: Janne had seen the program once, socially,
with nobody measuring, and that single exposure permanently removed the
discovery question from him.  *"I think I messed up"* — and the messing
up was not carelessness, it was showing somebody a program before
deciding what to learn from them.

A visit that opens with *"let me show you what I have been building"*
spends the friend in its first sentence.  The same visit that opens with
*"here is a laptop, see what you make of it, I will not say anything for
ten minutes"* keeps everything and **still ends with the presentation**,
which loses nothing at all: he can be told about it afterwards, at
length, and the talk is better for his having touched it first.

**Ten minutes of silence, then the whole conversation.**  That is the
entire protocol difference, and it is worth more than any change to the
program between now and then.

### The second way to waste it: changing the thing being measured

Rule 3 — *fix what is known-wrong first, for free; vary only the
uncertain thing*.  The uncertain thing is the corner.  So between now
and the visit:

- **Free-and-certain fixes are unlimited** and should be made — the way
  in already took two today (F162, F163), and anything else found the
  same way should be fixed rather than saved for him.
- **The first five minutes must not be redesigned.**  Any change to the
  starter screen, the corner, the command list's vocabulary or the
  window's first frame turns his run into a test of a *bundle*, and the
  result will not say which part did the work.  If such a change is
  wanted anyway, it is a decision to trade this run for it, and should
  be made knowingly rather than by drifting into it.

### What to prepare, and it is not code

1. **Pre-register the predictions** — before the visit, not on the day.
   What is seen if the corner is findable, what is seen if it is not,
   what is seen if the stall is somewhere nobody has looked.
2. **Decide the recording.**  Janne's run was accidentally well recorded
   because it happened in a chat window.  A visit in person has no
   transcript unless somebody makes one, and *what he was told, in
   order, verbatim* is the measurement.  A phone recording the audio, or
   a second person writing times, both work; memory does not.
3. **Write the four verbs on a card and hand it to him**, so the task is
   identical to Janne's and the two runs can be compared: *open a file,
   hear it, change it, hear the change.*
4. **Decide in advance what ends the run** — the first time Henri
   speaks, or ten minutes, whichever comes first.

### The notebook, as Henri described it

*Henri, 2026-08-18:* **"So I take a notebook.  I write my observations to
it when I stay quiet and see him work on it.  I do not tell anything
about how the program works and see what he does."**

That is the protocol.  Three things today's run adds to it, each of
which cost something to learn.

**1. Hand him a machine that is already installed.**  Run two spent
**fourteen of its thirty minutes** on the way in — a placeholder and a
missing `cargo`, neither about the program.  The way in is the
*repeatable* half of this test: it can be walked again on any machine,
any week, by anybody.  The corner cannot.  **So do not spend a
non-renewable person on a renewable question**: have it installed and
sounding before he sits down, and the whole run goes to the window.

**2. Say one sentence before the silence, and only this one.**  A person
watched in silence while somebody writes in a notebook will perform, and
will apologise for being slow.  One framing sentence costs nothing and
teaches nothing about the program:

> *I am going to be quiet and take notes.  It is the program being
> tested, not you — anywhere you get stuck is the point.*

**3. Decide the answer to his questions before he asks one.**  He will
ask, and the hard part is in the moment.  Have the sentence ready:

> *I would rather not say yet — keep going, and I will explain
> everything afterwards.*

Every time it is used, write down **the question he asked**, because a
question is a finding whether or not it gets answered.

### The page to draw before going

Four columns, and times down the left.  The times matter because the
claim under test says *the first five minutes*, and a run without a
clock cannot address it.

| time | what he did | what he said, verbatim | what I told him |
|---|---|---|---|

And a box at the bottom for the two things that are easiest to lose:

- **His words for things.**  Janne said *arvo* for a number in the
  source and *pianonkoskettimet* for the drawn keys.  The window's own
  vocabulary is being tested against his, and only the verbatim words
  carry it.
- **Where he gave up**, if he did, and what he had reached for
  immediately before.

### What ends it

The first time Henri explains something, or ten minutes, whichever
comes first — decided now rather than in the room.  **Then the
presentation, at length, with everything he wants to know.**  Nothing
about the measurement stops that from being a good afternoon.

### `=command=` — held, deliberately, and turned into a question instead

*Henri, 2026-08-18:* **"On the burger menu.  It might be that
[command] should be decorated like =command= so that is is distinguished
shape compared to our signs such as [gemba] or [inert] and so on."**

**The observation is real and the change must not be made before the
visit.**  The corner is the single uncertain thing run three varies
(rule 3).  Changing its shape this week means Janne meets a corner
no stranger has ever met, and whatever he does answers a question about
*that* corner — leaving the one this card has been holding since
2026-08-17 still unanswered, with Janne spent.

**And the idea is better as a prediction than as a patch**, because it
is exactly the kind of claim a stranger can settle and nobody else can:

> `[command]` wears the same brackets as `[gemba]` and `[inert]`, which
> are *readouts*.  A control shaped like a status sign may read as
> something the program is telling you rather than something you can
> press.

So it goes into the pre-registration:

- **If the bracket shape is the problem**, he reads the corner, does not
  try it, and looks elsewhere for a way in — the tell is that he *sees*
  it and does not *press* it.  That is a different failure from not
  finding it at all, and the notebook has to distinguish them: **what he
  looked at is as much a finding as what he did.**
- **If it is not the problem**, he presses it, and `=command=` is a
  change with no evidence behind it — which is where it stays.

One run answers both, and building it first answers neither.  If the
brackets do turn out to be the problem, the fix is then a change with a
person behind it rather than a taste.
