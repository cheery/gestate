# stranger-test — run the vision's own top claim

    status   open
    because  the first line of vision.md is a test nobody has ever run
    asked    Henri, 2026-08-16
    see      vision.md §"Ease of use and efficiency"
             spec/workbench.md — the brief this sentence comes from
             fixme.md — where the findings go

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
hand the same friend the window with the list open and watch what he
does with `apply`.  He never saw it.

## Run two — Janne, 2026-08-18, pre-registered before the run

*Written before he touched anything, because rule 4 is the only thing
standing between this and a result that explains itself afterwards.*

*Henri, 13:xx:* **"Janne is available.  Are the install instructions in
line?  We soon see that."**

### Two measurements, in this order, not blended

1. **The install**, from `doc/install.md`, on a machine that is not this
   one.
2. **First contact** with the window: open a file, hear it, change it,
   hear the change.

The order matters and so does the separation.  **The install is not the
perishable half** — it can be redone on another machine, in a VM, next
month.  First contact cannot.  So if the afternoon runs short, the
install is the part to sacrifice, and under no circumstances is the
first contact spent while somebody is still fixing an install problem
beside him.

### What is known-wrong, and therefore must not be spent on him

Rule 3 — a run against a window with known defects rediscovers them.
Checked before the run: **F148** (taskbar icon), **F149** (desktop entry
that did nothing), **F150** (first screen naming a deleted button) and
**F155** (the unfindable glyph) are all resolved.  **F159 is open** — a
runtime complaint carries no position — and it bites only if he writes a
program that fails at run time.  If he does, that is a known defect and
**not a finding**.

### The one uncertain thing being varied

**The corner.**  It became `[command]` on 2026-08-17 (F155) and no
stranger has met the new one.  Nothing else in the first-contact path
has changed since the first friend, so this run answers one question
rather than a bundle.

### Predictions

*If any of these is written after the run, it is worthless.  They are
here first.*

- **The corner is now findable.**  He reaches the control without being
  told, in the first minute or two, and the stumble moves *past the
  door* — to what the list contains, or what `apply` means.
- **The corner is still the problem.**  He stalls on the first screen
  the way the first friend did and has to be told the control exists.
  That falsifies the fix and not the direction; the corner would then be
  the wrong lever entirely.
- **Neither.**  He finds the control and stalls somewhere nobody has
  looked — the list's vocabulary, choosing a file, or the sound simply
  not arriving.  **This is the outcome no theory predicts and therefore
  the one worth the most**, and it is the reason the trajectory is
  recorded rather than the verdict.
- **On the install.**  If it is in line he reaches a running window
  without asking anything.  Every question he has to ask is one line of
  `doc/install.md` that assumed something, and it is recorded verbatim
  as the finding rather than answered and forgotten.

### How it is recorded, decided beforehand

Rule 5: *the cheapest available improvement to run two is recording it
better, and it costs nothing but deciding how beforehand.*  So:

- **what he was told**, in order, verbatim — including the first time
  somebody helps, which ends the measurement
- **what he read**, and how much of it
- **where he guessed**, and whether the guess was right — a wrong guess
  that worked is the worst finding available, because the window taught
  something false
- **where he gave up**
- **times**, because *the first five minutes* is the claim under test

### The hazard, restated for a human

**Henri must not help**, and the moment he does, the run is over and the
help is the result.  The first friend's run ended exactly there.  A
person who knows he is being measured performs, so what is wanted is the
trajectory as it happens, not his account of it afterwards.

*Rule 1 applies in his favour: Janne is one friend × one first contact,
and his first contact is virgin for all of it.*
