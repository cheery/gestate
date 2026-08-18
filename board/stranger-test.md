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

### Amended before it started — what Janne actually is

*Henri, 2026-08-18, minutes after the plan above was written:* **"Janne
is available but he's online.  Also he has seen it already once and I
think I messed up.  He knows how the program roughly operates.  Your
attitude is deserved though.  We need to seriously prepare."*  And:
*"We agreed to clone the tree and try it.  He already reports that he
got it installed."*

Three things changed at once and they pull in different directions.  The
honest accounting, before any of it is spent:

**1. The discovery question is gone for him, and it was the expensive
one.**  He knows roughly how the program operates, so he cannot answer
*is the corner findable*.  Nothing recovers that.  Writing it down is
the point — the failure mode this card exists to prevent is running him
anyway and reading the result as if it answered the question it no
longer can.

**And "I think I messed up" is the right instinct with the wrong
target.**  What was spent was not carelessness at the keyboard; it is
that **a stranger is consumed by any contact, including a friendly one
that was never framed as a run.**  The supply drains whether or not
somebody was measuring.  That is a property of the instrument, and the
only defence is deciding *before* showing somebody, which nobody does,
which is why this paragraph is here.

**2. Being online is an upgrade, not a loss.**  The recording problem —
rule 5, the cheapest available improvement — is solved by the medium: a
chat log is verbatim, ordered and timestamped, which is strictly better
than reconstructing afterwards from photographs of a window.  **The log
is the transcript.  Keep it whole, including his hesitations and the
questions he asks**, and paste it into the write-up rather than
summarising it.

**3. The install already happened, unobserved.**  He cloned the tree and
reports it installed.  That measurement is spent *as a live
observation*, but the install is the repeatable half of this card, so
almost nothing is lost — and what remains is free: ask him, in his own
words, what he had to do and what he had to look up.  Retrospective
self-report is weak evidence and is recorded as such.

### What is still spendable, and what to ask

**Everything past the door.**  Rule 1 counts the unit as *friend × one
first contact*, and his first contact stopped at the surface.  Whether
he can open a file, hear it, change it and hear the change — the four
verbs of the claim under test — is untouched.  So is the list's
vocabulary, and so is `apply`.

**The one question that changes the design, asked of Henri and not of
Janne: is he the same friend as 2026-08-17** (F150, F155,
`board/done/button.md`)?

- **If yes**, this is precisely the run this card already planned —
  *hand the same friend the window with the list open and watch what he
  does with `apply`.  He never saw it.*  It costs no new stranger, and
  it is the highest-value thing available today.
- **If no**, he is a *partly spent* new person: the corner is
  contaminated, the four verbs are not, and he must be counted as
  consumed afterwards either way.

### Predictions for the run that is left

*Written before he is asked anything, same rule as above.*

- **The four verbs succeed unaided.**  He opens something, hears it,
  changes a number, hears the change.  Then the vision's top claim
  survives its first honest contact with a person, weakened only by his
  prior exposure to the surface — which is recorded beside the result
  rather than argued away.
- **He stalls on hearing it.**  Sound is the one thing that cannot be
  photographed, has the most machine-specific failure modes, and is the
  hardest to debug over chat.  If this happens it is worth more than the
  rest of the run and should be pursued in full.
- **He stalls on changing it** — finds a number, edits it, and nothing
  audible follows, or he cannot tell whether it followed.  That is the
  auto-audition question arriving in the place it was always going to.
- **He stalls on the list's words.**  He opens the command list and
  cannot tell which entry is the one he wants.  This is what
  `command-categories` was answered about, and this run would be its
  first outside test.

### How to ask, so the answer is worth having

- **No leading.**  The task, verbatim and complete, is *open a file, hear
  it, change it, hear the change* — and nothing else is said until he
  stops.
- **Every answer given to him is recorded verbatim** with the point at
  which it was given, and it ends the unaided portion of the run.
- **Do not defend the program.**  An explanation offered in the chat is
  the same as help at the keyboard.
- **Ask the install question retrospectively and openly**: what did you
  have to do, and what did you have to look up or guess — not *did it
  work*, which invites a yes.

### 13:25 — what this run is actually measuring, decided while it ran

*Henri:* **"Janne is telling that he's listening violin.ges at the
moment.  But I do not know whether he got the editor open yet, or using
audioperform."**

`../README.md` §"Hear it" ends by naming `examples/audio/violin.ges`, and
§"Edit it while it sounds" is the section immediately after it.  So the
likeliest reading is that he is **following the README top to bottom and
is one section short of the editor** — which has to be written down now,
because it changes the claim under test:

| | reads | tests |
|---|---|---|
| the AI stranger | 36,000 lines of `doc/` | is the **language** learnable |
| **Janne, today** | `README.md`, in order | is the **way in** navigable |
| the run this card was written for | nothing | is the **tool** approachable |

**A reader following the README is not testing the window's
self-evidence.  He is testing the documentation**, and reading it *is*
being told.  A success here does not license the vision's opening
sentence, and reading it that way would be the false green this card was
designed against.

It is still worth having — the way in is what F162 just came out of, and
nobody had measured it either.  But it is a **different instrument** and
the write-up must say so.

**The question that costs nothing and must not lead**: *how are you
playing it — paste what you typed.*  That establishes which tool he is
in without teaching him that another one exists.  Asking *did you open
the editor?* would hand him the answer and end the most interesting
thing still running.

### The crossing to watch for

The claim under test needs four verbs and `audioperform` supplies two:
he can **open** and **hear**, and he cannot **change and hear the
change**.  The README's next section is the bridge.

- **He crosses on his own** — the way in works as a path, and what is
  measured from there is the editor with a warm reader.
- **He stops at hearing**, satisfied, and reports success.  Then the way
  in delivers a *player* and the vision's claim is unmet by the
  documented route, which nobody has noticed because nobody who knows
  the editor exists could ever stop there.
- **He goes looking for how to change it** and lands somewhere other
  than §"Edit it while it sounds" — whatever he tries first is the
  finding, and it is worth more than either of the above.

### 13:28 — `EditorError`, and a prediction written before the picture

*Henri:* **"it produced EditorError, I ask for a picture."**

So he crossed to the editor on his own, which answers the crossing
question above: **the way in works as a path.**  What it delivered him
to is a Python exception.

`gestate/editor.py` raises `EditorError` in exactly three places, and
the text of each says which:

1. **"no libgestate_editor.so and no cargo to build it"** — `cargo` is
   not on his `PATH`.
2. **"the editor did not build:"** followed by cargo's stderr — the
   crate failed to compile, and the stderr names why (a missing `-dev`
   package, or a toolchain too old).
3. **"the editor window would not open"** — the library loaded and the
   window did not, which is a display problem.

**Predicted, before the picture arrives: the first.**  The install block
carries the sourcing step as a *trailing comment* —
`curl … | sh   # then: . "$HOME/.cargo/env"` — so a reader who stays in
the same shell has `rustup` installed and `cargo` invisible.  A comment
at the end of a long line is the weakest position a required step can
occupy.

If it is the second instead, the finding is a missing package in the
`apt` list, and that list has only ever been tested by its author.  If
it is the third, it is the only one of the three that is not a way-in
defect.

**And a fourth thing this exposes regardless of which it is**: the first
time a person opens the workbench, it **compiles Rust**, in release
mode, with no progress output and no warning that it is about to. Nobody
has measured what that costs a newcomer, because nobody who has run this
project twice ever pays it.

### 13:35 and 13:37 — the help, verbatim, and what asking for it revealed

The rule this card sets is that every answer given is recorded with the
point at which it was given, because it ends the unaided portion and
because *the help itself is the finding*.  Both were in Finnish, which
is the language the run was conducted in while every word of the
documentation is English — recorded as a property of the measurement,
not as a defect.

**13:35, Henri → Janne:** *"avaa terminaali uudestaan ja kokeile ajaa
komento «cargo»."* — open the terminal again and try running the command
`cargo`.

**This closes the unaided install measurement.**  Everything it could
give has been given: F162 and F163.

**13:37, Henri → Janne:** *"mitä optioita ja commandeja cargo:lle pitää
antaa — ei mitään.  cargo komento vain tarkistaa että onko cargo
paikallaan.  gestate kääntää itse itsensä kun ajat sen ensimmäisen
kerran."* — what options and commands should be given to cargo — none;
the `cargo` command just checks whether cargo is there; gestate compiles
itself when you run it the first time.

Two findings in one message, and neither is about cargo:

**1. "Run `cargo`" was not actionable.**  He asked what to pass it.  A
bare command name reads as a *fragment* to somebody who has never used
the tool, and the answer — *nothing, it is a check* — is knowledge the
instruction assumed.  This is the same shape as F162: an instruction
that is complete only to a reader who already knows the thing it is
teaching.

**2. He had to be told the program compiles itself.**  Predicted an hour
earlier as *a fourth thing this exposes regardless of which of the three
it is* — that the first workbench run builds Rust in release mode with
no warning and no progress — and here is a second person needing to be
told it, out loud, by the author.  The new error message says it now,
but **only a reader whose build fails ever sees that message.**  A
reader whose setup is correct meets the same multi-minute silence with
nothing to explain it, which is the more common case and the one still
unfixed at 13:37.

### 13:42 — the window opened, and the delay named itself

**Janne:** *"kokeilin uudelleen tuota workbench:iä, aukesi melko pitkän
viiveen jälkeen"* — I tried the workbench again, it opened after a
fairly long delay.

**Unprompted, and it is the third finding stating itself.**  Nobody
asked him about speed.  He had been told at 13:37 that the program
compiles itself, so he was not confused by the wait — he simply
volunteered that it was long, which is what a cost feels like when it
has been explained but not removed.

That is the sequence worth keeping: the silent first build was predicted
at 13:28 from reading the source, needed at 13:37 as something a person
had to be *told*, and reported at 13:42 by the person as the thing he
noticed most. Three independent arrivals of one defect inside fifteen
minutes, each by a different instrument.

**The number is worth one question and it is not help**: how long. He
holds it now and will not tomorrow, and asking costs nothing he could
learn from — the program has already done the thing being measured.

### From here the run is first contact, and the rule is silence

Everything from 13:42 is the part this card was written for and the
part that cannot be redone: **open a file, hear it, change it, hear the
change**, in a window, with nobody helping.  He is contaminated on the
corner and on nothing else.

What to watch, in the order it would happen:

- whether he finds the control without being told (weak evidence — he
  has seen it before, and this is the one question his prior exposure
  spent)
- whether he gets a sound out of the window at all, as against the
  terminal, where he already has one
- **whether he changes something and hears the change** — the two verbs
  no run of this test has ever reached, and the whole of the claim under
  test
- what he tries *first* when he wants to change something, because that
  is the interface's own vocabulary being read back

### 13:44 — the answer that changed the fix

**Janne:** *"oisko jotain 10-15 sekuntia"* — maybe ten to fifteen
seconds.

**Ten seconds, and he called it long.**  That is the most useful single
sentence the run has produced, and it produced it by being asked one
neutral question at the one moment the answer still existed.

It falsified a documented number — both ways in claimed *a minute or
two*, which was the author's impression and had never been measured on
anybody else's machine — and, more than that, it **moved the defect**.
The wait was not too long.  The wait said nothing.  A fix aimed at speed
would have been expensive, plausible and useless, which is the specific
failure this card's rule 4 exists to prevent: without the pre-registered
predictions and this one question, *"the first build is too slow"* is
exactly what would have been written down.

### 13:46 — the corner, judged by the person who failed the old one

**Janne, unprompted:** *"nyt tuo [command] oikeassa yläkulmassa näkyy
hyvin."* — now that `[command]` in the top right corner shows up well.

**"Nyt" settles the identity question this card asked and Henri never
had to answer.**  It is a comparison, so he is comparing it to something
he saw before: he is the friend of 2026-08-17, the one who could not
find the small gray-tinted button (F150, F155,
`board/done/button.md`).

### What this is evidence for, and what it is not

**It is strong evidence on legibility.**  The person who failed to find
the old corner looked at the new one and remarked on it **without being
asked about it at all**, which is the part that carries the weight — the
corner was salient enough to interrupt what he was doing.  F155 measured
24 lit pixels of `FAINT` on `BG` and replaced the glyph with a word;
this is that fix meeting the exact person it was made for, and passing.

**It is not the discovery test, and must never be written up as one.**
He was not finding the control.  He was recognising that a control he
already knew about is now visible.  Those are different questions and
his prior exposure spent the first one permanently — which is precisely
what the pre-registration warned would happen, so the warning gets to
hold: *the discovery question is gone for him, and the failure mode this
card exists to prevent is running him anyway and reading the result as
if it answered the question it no longer can.*

The corner's findability is still unmeasured, and the next friend is the
only instrument for it.

### What it does close

`board/done/button.md`'s remaining doubt about whether the replacement
reads at a glance, on somebody else's screen, at somebody else's DPI, in
somebody else's window size.  One person, one screen, one look, and he
volunteered it.  That is worth an entry in the record even though it is
not the measurement that was planned.

### 13:48 — past the door, and the first thing he wanted was silence

**Henri → Janne:** *"kiva juttu että se nyt näkyy.  jatka kertomista
mitä tapahtuu"* — nice that it shows now; keep telling me what happens.
*(Protocol-clean: it asks for narration and teaches nothing.)*

**Janne:** *"noh kokeilin stop-komentoa ja se toimi :)  ctrl-K on
kätevä"* — well, I tried the stop command and it worked :) ctrl-K is
handy.

**He is past the door.**  This is the region rule 1 called still virgin
for him, and it is the first time any run of this test has reached it.

### The first command a newcomer chose was `stop`

Out of the whole list, the thing he wanted was **to make it be quiet**.
That is worth recording before it gets explained away, because it is the
kind of fact the author can never observe: the workbench opens
*sounding*, and a person meeting it has an immediate need the interface
has never been designed around — not *what can this do*, but *how do I
stop it*.

*Marked as a reading, not a conclusion:* one person, once, and he may
simply have picked the entry he understood the word for.  The set it
belongs to — is `stop` first because it is urgent, because it is legible,
or because it is short — is not settled by one observation, and
`board/done/command-categories.md`'s ordering is what it bears on.

### "Ctrl-K on kätevä" — and one question worth asking

He knows the key.  There are two ways he could, and they are a live
question about a fix that shipped yesterday:

- **The status bar taught him** — F153's fix, *on until the key has been
  used, and then never again*, which exists precisely so somebody who
  has not used it is told and somebody who has is not nagged.  If so,
  that fix worked on the first stranger to meet it.
- **He remembered it** from 2026-08-17, when he was helped to the list.
  Then F153 is untested and this says nothing about it.

**Ask, because it costs nothing and teaches him nothing:** *mistä
huomasit ctrl-K:n?* — where did you notice Ctrl-K?  The window is
already open and the key already pressed; nothing about the answer can
change what he does next.

### Still not reached

**Change something, and hear the change.**  He has heard the program and
he has commanded it.  He has not edited it.  That is the half of
`vision.md`'s opening sentence that no run has ever touched.

### 13:50 — the third verb

**Janne:** *"koitan muuttaa arvoja satunnaisesti"* — I'm trying to
change values at random.  And: *"sain pianonkoskettimet näkyviin"* — I
got the piano keys to show.

**No run of this test has ever been here.**  The claim under test is
*open a file, hear it, change it, hear the change*; three of the four
verbs are now done by a person who was told the URL, the sourcing line,
and nothing else about the program.

Two things in one minute, and the second was not asked for:

- **He is editing values**, which is the workbench's whole premise — a
  knob drawn beside its own declaration, changed while it sounds.
- **He found the piano unaided.**  Nobody mentioned it.  It is the one
  piece of furniture in the window that is not text, and he surfaced it
  while looking for something else.

*"Satunnaisesti" — at random — is the honest description of what a
newcomer does with a program he is not afraid of*, and it is a good
sign rather than a bad one: he is not consulting anything, he is
poking. That is the state the whole interface is built for and the
state no test can simulate.

**One verb left, and it is the one the vision rests on: does he hear the
change.**  Nothing should be said to him until he says whether he did.

### 13:52 — the fourth verb, and the claim this card exists for

**Janne:** *"no nyt löytyi arvo, joka vaikuttaa merkittävästi soundiin:
stab = lowpassSvf"* — well, now I found a value that affects the sound
significantly: `stab = lowpassSvf`.

**He changed it and he heard the change.**  There is no other way to
know that a value affects the sound "significantly", and nobody told him
where to look.

`vision.md`'s opening sentence, 2026-08-16 — *somebody who has never
read this repository should be able to open a file, hear it, change it,
and hear the change without being told anything first* — has been run
against a person for the first time, and all four verbs happened.

### What it actually establishes, stated conservatively

The claim passes **in its documented form** and not in its pure one, and
the difference has to survive into the write-up or this becomes the
false green the card was built against:

- **He read `README.md`,** in order, and reading is being told.  What
  was measured is that *the way in works as a path*, not that the window
  is self-evident.
- **He was told four things**, all logged: the clone URL, *open a new
  terminal and run cargo*, *gestate compiles itself on first run*, and
  *keep narrating*.  Every one of them is a way-in defect (F162, F163)
  and none is about the program.
- **He had seen the surface before**, on 2026-08-17, which spent the
  corner-discovery question permanently and nothing else.

What is left after those subtractions is still the strongest result this
project has ever had about itself.

### The clock

Cloned around 13:22, heard his own edit at 13:52 — **thirty minutes**,
of which roughly **fourteen were spent on F162 and F163**: a placeholder
he could not fill and a shell that could not find cargo.  Neither is
about music, the language, or the window.

**So the way in cost half the run**, and both halves of that cost are
now fixed and gated.  The honest projection — untested, and marked as
such — is that the same person meeting today's tree would have reached
`lowpassSvf` in about fifteen minutes.

### One question, and it is worth asking before he moves on

He named `lowpassSvf` specifically.  That function is the origin of
`board/done/argument-names.md`, which exists because *"I do not figure
out quickly enough which argument in lowpass filters are which"* — the
author's own complaint, about this exact function.

**Ask: which value did you change, and did you know what it would do
before you changed it?**  It is a measurement, not help — the change is
already made and heard.  And it puts a shipped fix in front of the one
kind of reader it was made for.

### 13:55 — the run ended

*Henri:* **"he finished.  he's going to a walk."**

Thirty minutes, clone to fourth verb.  The story is in `journal.md`
§"Thirty minutes, and the way in took half of them"; the findings are
`fixme.md` F162 and F163; the gates are `test/test_way_in.py`.

**What was spent, and what is left.**  Rule 1 counts the unit as *friend
× one first contact*, so the accounting matters:

- **Spent, permanently:** his first contact with the way in, and the
  corner-discovery question (already spent on 2026-08-17).
- **Not spent:** every specific question that can be asked cold.  He can
  still be asked *which value did you change in `lowpassSvf`, and did
  you know what it would do before you changed it* — the question
  `board/done/argument-names.md` exists to answer, aimed at the one
  function that motivated it.  Asking it tomorrow costs nothing that
  asking it today would have saved.
- **Never available from him again:** whether the corner is findable by
  somebody who has never seen it.  That needs a friend nobody has spent,
  and it is the one thing worth designing a whole run around.

### Moved to last, 2026-08-18

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
(rule 3).  Changing its shape this week means the friend meets a corner
no stranger has ever met, and whatever he does answers a question about
*that* corner — leaving the one this card has been holding since
2026-08-17 still unanswered, with the friend spent.

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
