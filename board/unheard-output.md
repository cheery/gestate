# unheard-output — nothing but a person can hear what the card was given

    status   open
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

## What the work is

1. Decide the three above.
2. The tap, and a test that it captures what the loop actually wrote —
   an oracle that has only ever passed is a claim (`manifesto.md`
   §"The three ways an instrument fails"), so it must be shown failing.
3. Point it at F147's pair and finish that hunt.
4. A row in `manifesto.md`'s instrument table, **with its blind spot**:
   it sees what was written to the device and not what the speaker did
   with it, which is the half that stays a person's job.
