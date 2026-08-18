# unheard-output — nothing but a person can hear what the card was given

    status   done — 2026-08-18
    because  when you say "be my oracle", there's actually something
             implying in that which might require "is this really not
             possible to delegate to a real oracle?"
    asked    Henri, 2026-08-17 (Claude wrote the card at his ask)
    see      gestate/host.c — `snd_pcm_writei`, the one place the samples leave
             gestate/audiohost.py — `Host.run_device`, `dry`, `worst_us`
             fixme.md F147 — the defect this is blocking
             test/sessions/F147-ampknob.ges, F147-freqknob.ges — the bisect
             journal.md §"\"Be my oracle\" is a smell"
             manifesto.md §"The instruments, and what each cannot see"

## The ask

The `because` is the general rule he stated; this card is the first place
it bit.  Chasing F147's pop cost **four listens** — four times a person
was asked to restart a workbench, listen, and report — and the search
still ended blocked, because every hypothesis left is about the first few
blocks of live execution and nothing in this tree can look at them.

## Found by looking, before it was taken

**The gap is exact and small.**  `manifesto.md`'s instrument table lists
nine things and what each cannot see.  Every audio oracle in it reads
either an *offline render* or a *counter*:

| instrument | reads |
|---|---|
| `audioperform --report` | an offline render's peak and per-bar RMS |
| the golden `.samples` | an offline render, sample for sample |
| native against the reference | two offline renders against each other |
| `Host.dry`, `Host.worst_us` | counters, not audio |
| `tools/stutter.py` | those same counters |

**Nothing reads what the device was actually given.**  And the offline
render cannot stand in for it, which F147 established the hard way: a
knob renders *at its resting value* offline and the live control path is
never exercised at all, so an entire class of defect — anything in the
first blocks, anything about a control channel, anything about the
handover between engines — is invisible to every oracle that exists.

### The tap

`host.c` writes each block to the card through `snd_pcm_writei`, and that
call is the one place every sample passes on its way out.  A tap there
hands back exactly what the device received.

That is the whole idea.  What the card owes is the design around it, and
the questions below are the ones that decide it.

### What it would have done today

F147's bisect took four listens to reach *"a control-rate signal feeding
a frequency, in the first blocks"*, and stopped there.  With a tap it is
one run and a diff: capture the first blocks of `F147-ampknob.ges` and
`F147-freqknob.ges` — which are proven bit-identical at rest — and look
at where they part.  No ears, repeatable, and it can bisect.

**And it does not expire with this defect.**  Every pop, click, dropout
and handover glitch after it is the same question, and today the answer
is always going to be *ask Henri*.

## Questions

**Q (Claude).**  How is it turned on?  A tap in the render path is on the
one code path in this project where an allocation is a defect
(`gestate/host.c`: *"no arithmetic at all"* in the loop's own budget).

1. **Compiled out unless asked** — a `#ifdef`, so the shipping loop is
   byte-identical to today's.  Safest, and it means the instrument is
   not there when somebody needs it in a hurry.
2. **A pre-allocated ring, always present, written only when armed** —
   one branch per block, no allocation.  Costs a comparison in the
   hot loop forever, and is always available.
3. **An environment variable that swaps the write function once, at
   `open`** — no branch in the loop at all, decided before any audio
   flows.  `GESTATE_EDITOR_TIME` and `GESTATE_BUILD_TIME` are the
   precedent for the spelling.

**Q (Claude).**  What comes back, and to whom?  A `.wav` beside the file
is the thing a person can listen to; a buffer handed to Python is the
thing a *test* can assert on.  `spec/verification.md` §"Recording a host"
already records a plugin's boundary one row per `process` call, and this
is the same shape at the editor's boundary — so the answer may be *the
transcript already knows how to do this*.

**Q (Claude).**  How much is kept?  The first few blocks are what F147
needs and are a bounded, tiny amount.  A whole session is unbounded and
is a different feature.  Starting at *the first N blocks after the loop
begins* would close F147 and cost nothing to reason about.

## The postcondition

*Written before anything was built, derived from the `because`.*

> **A pop that a person can hear, a session can see — without asking
> anybody to listen.**

## Answered, 2026-08-18, from the code rather than from the card

These are the card's own three questions, and they turned out to be
answerable by reading `host.c` rather than by deciding anything a person
has to weigh.

**Q1, how it is armed — a buffer allocated at `open` when the
environment asks, and one branch per *block*.**

The card's worry was real and aimed one floor too low.  *"No arithmetic
at all"* is `gestate_host_fill`'s budget — the **per-sample** loop.  The
tap does not go there: it goes beside `snd_pcm_writei`, which is a
**syscall**, and a null check next to a syscall is not a cost anybody
can measure.  A block is 512 frames, so this is one comparison per 512
samples.

That makes option 3's function swap buy nothing it does not already
have, and it removes option 1's real defect — *the instrument is not
there when somebody needs it in a hurry* — because arming is an
environment variable rather than a rebuild.  `GESTATE_EDITOR_TIME` is
the spelling precedent.

**Q2, what comes back — one buffer, two readings.**  The tap fills
memory; the ABI hands it to Python; from there a test asserts on it and
a person writes it to a `.wav` and listens.  Building either one
separately would have been building the other one badly: an oracle that
only a person can read is the thing this card exists to stop, and one
only a test can read cannot settle *"does that sound right"*.

**Q3, how much — the first N blocks from arming, and then it stops.**
Bounded, pre-allocated, deterministic, which is what a *test* needs and
what F147 is.  **The named alternative is a ring that keeps the last N**
— *"the pop I just heard"* — and it is deliberately not built: it
answers a different question, it cannot be asserted on reproducibly, and
having both would mean two instruments with one name.

### And the tap point is after the write, not before it

`snd_pcm_writei` answers with how many frames the card **took**, which
may be fewer than were offered.  Capturing what was *filled* would be a
different claim wearing this one's name — *what we meant to send* rather
than *what the device received* — and the whole value of this
instrument is that it is the second one.

### Both loops, which is what makes it testable

`host.c` has two: the device loop and the pipe loop, and they share
`gestate_host_fill`.  A tap in the pipe loop needs **no sound card**, so
the suite can hold the instrument honestly on a machine with no audio at
all — which is most of them, and which is the difference between an
oracle that is checked and one that is asserted.

## What the work is

1. Decide the three above.
2. The tap, and a test that it captures what the loop actually wrote —
   an oracle that has only ever passed is a claim (`manifesto.md`
   §"The three ways an instrument fails"), so it must be shown failing.
3. Point it at F147's pair and finish that hunt.
4. A row in `manifesto.md`'s instrument table, **with its blind spot**:
   it sees what was written to the device and not what the speaker did
   with it, which is the half that stays a person's job.

## Done

*2026-08-18.  `journal.md` §"The samples nobody could read" tells the
story.*

**The instrument exists.**  `GESTATE_HOST_TAP=<frames>` allocates a
buffer when the host is made; `tapped()` fills it beside each write and
stops when it is full; `Host.tap()` hands the frames to Python.  In
**both** loops — the device's and the pipe's — and the pipe one is what
makes it testable, because a machine with no sound card can still hold
the instrument to what it claims.  That is most machines and every one
the suite runs on.

**Shown failing, which is the file it lives in's whole rule.**  With the
tap sabotaged to write silence instead of samples, three of its five
tests go red; restored, green.  An oracle that has only ever passed is a
claim, and this one is now known to be capable of being wrong.

**A row in `manifesto.md`, with the blind spot stated**: it reads what
the sound card was handed, and *not* what the speaker did with it.  The
driver, the mixer, the room and the ear are past that point, so *"it
sounds thin on laptop speakers"* remains a question only a person can be
asked — which is the honest half, and the half that stops somebody
trusting the tap past where it sees.

### F147: the wall moved, and the hunt is not over

**This is the part to read plainly.**  The card said *"point it at
F147's pair and finish that hunt"*, and the hunt is not finished.  What
the instrument did in its first hour:

* **Confirmed the pair is bit-identical at rest** through the pipe, in
  one run, with no ears — which took a listen each before.
* **Refuted the standing hypothesis.**  A knob whose value arrives
  *late* (which `audioeditor.control` can still produce: it answers `0`
  for a knob with no site yet, and sites are placed on a thread) makes a
  step four times the settled one, exactly at a block boundary — in the
  **amplitude** version.  The **frequency** version stays clean.  That
  is the opposite way round from what Henri heard, so the late knob is
  not the reported pop.
* **And turned up a latent one nobody has heard**: that amplitude case
  is a real click, in a program nobody has complained about, found by an
  instrument that had existed for twenty minutes.

What is left is something the *pipe* path does not reproduce, which
points at the device path — where the tap also lives, and where running
it makes noise in somebody's room.  `fixme.md` F147 carries this.

**The postcondition, honestly weighed.**  *"A pop that a person can
hear, a session can see — without asking anybody to listen."*  Met for
everything the pipe path reaches, which is where a bisect can now be run
by machine; **not yet demonstrated on the device**, because that is a
run in Henri's room rather than a run in a test.  Said here rather than
claimed, because the card's own `because` is about not asking a person
for what an instrument could answer, and the last step of this one still
does.
