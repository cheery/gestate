# signals.md — where a signal does better than a message, before either is rewritten

*Written 2026-09-13 for `card:gui-is-difficult.md`, at Henri's "we
should really see, measure and compare where the signals do better than
something else", after he took the Elm-like shape with signals kept
where they have proved themselves.  `tools/prereg.sh
doc/trial/signals.md` must pass before a line of either arm is written,
and he confirms or strikes the cases below first.*

**The two forms.**  A **signal** is how the tree does it now: a value
that is always there, `Sig a`, advanced every step, fed from a channel
through `mkSig`.  A **message** is Elm's and Eve's: something that
happened, `ExL a` — the language's own event, *a value, later* — folded
into a state by an update, with nothing advancing between arrivals.
Both are writable in the language as it stands: `scan` for the first,
the one-line `scanE` of §"Would the whole thing need rethinking?" for
the second.

**question:** for each kind of thing a gestate program does over time,
is it cheaper to run and shorter to write as a signal or as a message?

**The cases — his to confirm or strike.**  Each is a program already in
the tree, so the signal arm was written on other days for other reasons
and is not built for this sheet:

| | the case | the program | one step is |
|---|---|---|---|
| 1 | a sound, per sample | `examples/audio/blip.ges` | a sample |
| 2 | an animation, per frame | `examples/gui/bounce.ges` | a frame |
| 3 | an input folded into a model | `examples/gui/tic-tac-toe.ges` | a press |
| 4 | a control read by a sound | `examples/audio/knob.ges` | a turn of the knob |

A fifth he may add: the roll's hand, whose preview moves per frame —
held back because its signal half lives in Python, and a comparison
there is a port first.

**decision:** per case, two numbers for each arm, on the reference
machine and on `crust` with one harness: **the cost of one step**, and
**code lines** by the rule that counted the tic-tac-toe (non-blank,
non-comment).  A case goes to **messages** when the message arm is
shorter by at least 10 % and its step fits the budget — a frame is
16.7 ms, a sample 22.7 µs.  It goes to **signals** when the signal arm
is shorter, or when the message arm's step misses the budget.  Anything
between is a **tie, and a tie keeps the signal**, because it is what
stands.  The line gestate draws between the two is the cases' verdicts,
and nothing else on this sheet.

**control:** one behaviour, two forms.  Before either arm is counted,
each case has a test of what the program *does* — written first where
the tree has none, taken as it stands where it has — and both arms pass
it unchanged, so the numbers compare two ways of doing one thing.  The
signal arm is the program at the commit this sheet lands in.  **The
message arm is written by a session, which is the bias:** a writer can
make the new form heavier than it need be, as the first tic-tac-toe was
25 % over.  So the message arm is shown to Henri before its numbers are
taken, and any place he points at as heavier than he would write is
rewritten first.

**n:** 5

**prediction, written before anything is built — the session's:**
1. **signals**, by the budget: a message per sample is Eve's timer at
   44,100 transactions a second, and its step will not fit 22.7 µs;
2. **tie**: a frame tick folded is the same fold either way;
3. **messages**, by lines: the tic-tac-toe's hand is a fold over
   presses, and a press is an event;
4. **tie**, and the interesting one: the turn is a message and the
   sound reads it as a signal, so both arms may come out as the same
   program — which would put the line exactly at the channel.

**What would make this sheet wrong:** the cases chosen for their
answer.  They were chosen for being the four uses of time the tree
already has in a small program — sound, motion, input, control — and
not for how they will come out; a case he adds for its likely answer
the other way is the check on that.

## Before any number — 2026-09-13

**Henri:** *"yes.  Lets do this."*

**Case 1 corrected before an arm was written.**  The sheet named
`envelope.ges`, chosen by its name and not read: its sound is a MIDI
voice bank of library calls, and what the file itself writes is a
picture of probes.  `blip.ges` is the program whose per-sample fold is
written in the file — `scan stepVoice (Voice 0.0 0) ticks` — and it has
a committed golden buffer.  The case is the same, *a sound per sample*;
the program was the wrong one for it.

**The arms, written — `doc/trial/signals/`.**  Each is the tree's
program with its fold over a signal replaced by a fold over the event,
and `scanE` appended as a library line neither arm counts:

| case | the one line that changed |
|---|---|
| `blip.ges` | `scan stepVoice (Voice 0.0 0) ticks` → `scanE stepVoice (Voice 0.0 0) (wait clock)` |
| `knob.ges` | `40 ::: mkSig (wait knobChan)` → `scanE (k turned => turned) 40 (wait knobChan)` |
| `bounce.ges` | `scan stepBall start events` → `scanE stepBall start (wait input)` |
| `tic-tac-toe.ges` | `scan (…) start ((0.0 - 1.0) ::: mkSig (wait pressing))` → `scanE (…) start (wait pressing)` |

**The control holds.**  Both audio arms equal their golden buffers,
600 of 600 samples each, rendered as the golden tests render them.
`bounce.ges` gives every frame equal on the seven event lists
`test/test_gui.py` uses.  `tic-tac-toe.ges` gives every picture equal on
five games, the tests' presses and drags among them.

**And what writing them found, which the sheet did not foresee.**  In
this language a signal fed by a channel *is* a fold over arrivals — the
audio clock itself is `ticks = 0 ::: mkSig (wait clock)`, a channel
written once a sample — so the two forms are one line apart in every
case, and `mkSig` is the whole of the difference.  Prediction 1's
reason was wrong before its number: a message per sample is not Eve's
timer, it is the same arrivals the signal already has.  In Elm 0.16 a
signal was a runtime of its own; here it is not, which makes the Elm
contrast smaller than the sheet assumed.  **So the sheet may decide
four ties, and that would be a finding and not a failure** — but the
difference Elm actually removed may lie somewhere these cases do not
reach: in *how many* folds a program has over *how many* channels,
where Elm's shape is one update over one type of message.

*Not yet taken: the cost of a step and the line counts.  The arms go to
him first, per the control.*

## Case 5, added before its arm — 2026-09-13

**Henri:** *"add the many-channels case first."*

| | the case | the program | one step is |
|---|---|---|---|
| 5 | many channels into one sound | `examples/audio/twoknobs.ges` | a sample, or a turn of either knob |

**Why this program.**  Its sound is three channels — the sample clock,
`pitchChan`, `cutoffChan` — met by two `mkSig`, three `zip` and two
`scan`, and three records (`Knobs`, `Reading`, `Sample`) that exist, by
its own comment on the one-knob version, to carry signals through a
`zip`.  It has a committed golden buffer, rendered with every control
channel fed every 64 samples, so a turn and a sample arrive together.

**The message arm is Elm's shape:** one model, one message type, and
one update — the three channels merged by `sync` into messages, the
sound read off the model.  The same rule decides it, and the same
control: the golden buffer, 600 of 600.

**What counts as library, said before anything is counted.**  A line
that names nothing of this program — `scanE`, and a helper that turns
nested `Sync` values into a list of arrivals — is library, as `scan`,
`zip` and `mkSig` are for the signal arm, and neither arm counts it.
Every line that names this program's messages, model or knobs counts.

**prediction, written before the arm — the session's:** **messages, by
lines.**  The message arm drops `Knobs`, `Reading`, `Sample` and the
four small functions that build and unpack them (`pairUp`, `readAt`,
`withCutoff`, `cutoffOf`), because a model record holds all four values
at once; it adds a message type and an update with one case per
message.  The session expects the first to outweigh the second by more
than 10 %.  *What would make the prediction wrong:* the update's cases
for simultaneous arrivals — a turn landing on the same sample as the
clock is `SyncBoth`, and the golden was rendered with exactly that
happening every 64 samples, so the order the update applies them in
must match the signal arm's or the buffer will differ.

### Case 5's arm, written — 2026-09-13

`doc/trial/signals/twoknobs.ges`: a `Model` of the phase, the filter's
memory and the two knobs; `Msg := Tick Int | Pitch Int | Cutoff Int`;
one `update`; the three channels merged by `sync`, and `merge3`/`merge2`
as the uncounted library that turns nested `Sync` into a list.
**It equals the golden buffer, 800 of 800.**

**It took three drafts, and the golden caught both wrong ones** — which
is the part of this case the line count will not show:

1. the filter read the phase *before* the sample's step: **1 of 800**;
2. a turn landing on a sample was applied *after* it: **64 of 800**,
   broken at the first turn;
3. the knobs first and the clock last, in the `sync`: **800 of 800**.

Both mistakes were about **when a value is read**.  The signal arm never
says either thing — it falls out of which signal reads which through
the `zip`s.  The message arm has to *state* the order of simultaneous
arrivals and which value each step sees, and a wrong statement compiles
and plays: exactly the kind of silent step
`card:gui-is-difficult.md` §"His reading of the working program" named.
The prediction's own *what would make it wrong* was this, and it came
true twice before it was right.

**And two costs the sheet's rule cannot see, recorded before any number
is taken:**

- **The drafts.**  Three against the signal arm's none, found only
  because a golden buffer existed.  A program without one would have
  shipped draft 2.
- **Live coding.**  The tree's file argues for several channels over one
  record because state migrates by shape: a third knob added to `Model`
  changes its type, and the knobs already turned snap back.  Not
  measured here; measurable, by adding a parameter to a running program
  in each arm and reading whether the other two keep their values.

*Not yet taken: the cost of a step and the line counts, for all five.
The arms go to him first, per the control.*

## The numbers — 2026-09-13, taken and not yet acted on

**Henri:** *"take the numbers for all five, but present them before
acting on them."*  Taken without his reading of the arms first — his
call, which sets aside the control's *shown to Henri before its numbers
are taken*; recorded here so the numbers are read with that known.

`python tools/signalcase.py` — agreement, code lines (the tic-tac-toe
rule, library block left out), and a step's cost by difference, fastest
of three, on the reference machine and, for sound, the native engine
that plays.

| case | agree, both arms | lines, signal → message | reference step, signal / message | native step, signal / message |
|---|---|---|---|---|
| 1 `blip` | 600/600 golden | 35 → 35 (0 %) | 781 / 780 µs a sample | 0.074 µs / **does not compile** |
| 2 `bounce` | 7/7 lists, every frame | 48 → 48 (0 %) | 0.52 / 0.50 ms a frame | — |
| 3 `tic-tac-toe` | 5/5 games, every picture | 84 → 83 (−1.2 %) | 15.6 / 15.7 ms a press | — |
| 4 `knob` | 600/600 golden | 25 → 25 (0 %) | 1039 / 1121 µs a sample | 0.131 µs / **does not compile** |
| 5 `twoknobs` | 800/800 golden | **55 → 33 (−40 %)** | 1043 / 740 µs a sample | 0.170 µs / **does not compile** |

Budgets: a sample 22.7 µs, a frame 16.7 ms.  *Not taken:* `crust`,
which steps a canvas only from a Rust host fed an exported program.

**Why the message arms do not compile for the sound card**, in the
extractor's own words: *"uses `wait` inside a step function"* (blip,
knob) and *"passes a function to `__Foldable_List_foldl__`"*
(twoknobs).  The engine plays a fixed graph built from the signal
formers `scan`, `zip` and `mkSig`; `scanE` is not one, and a list of
messages folded per sample has no layout in a state struct.  **That is
this implementation's fragment, not the form** — `scanE` could become a
former beside `scan` — and it is the difference between the two
readings below.

**What the sheet's rule says, read literally** — a case goes to messages
when 10 % shorter *and* its step fits the budget; a tie keeps the
signal:

| case | the rule | the session's prediction |
|---|---|---|
| 1 | **signals** — the message arm cannot play | signals ✓, for a reason that was wrong |
| 2 | **tie**, kept as signal | tie ✓ |
| 3 | **tie**, kept as signal — 1.2 % is not 10 % | messages ✗ |
| 4 | **signals** — the message arm cannot play | tie ✗ |
| 5 | **signals** — 40 % shorter, but cannot play | messages: ✓ on lines, ✗ on the verdict |

**And the reading the rule cannot make.**  On the one case where the
two forms really differ — many channels into one sound — the message
arm is **40 % shorter and 29 % cheaper a sample on the reference
machine**, and loses only because the native fragment has no former for
it.  On the four where they do not differ, the forms are one line apart
and cost the same.  Against it, from §"Case 5's arm, written": three
drafts to the signal arm's none, both wrong ones about *when a value is
read* and silent, and the live-coding cost of one record — neither of
which a line count or a step's cost can see.

*Nothing is acted on.  What the numbers mean for where the line runs is
his.*

## `scanE` a former — 2026-09-13

**Henri:** *"make scanE a former so the message arms compile.  I think
that primitive looks like it earns its place."*  Scope, his pick of
three: **one channel first** — `scanE f z (wait c)`; `sync` of several,
and the sum types it needs laid out, as a slice of its own.

`scanE` is in `signal.ges`, public, and a `fold` node in every machine
that plays a graph — the check (`audiograph.py`), the extractor, the
reference engine and the native emitter.  It steps on the instants its
channel arrives and holds between: every sample over `clock`, the first
sample of a block over a knob.  The arms' local definitions are gone.

**Re-taken for the two it reaches** — `python tools/signalcase.py blip knob`:

| case | lines | reference, signal / message | native, signal / message |
|---|---|---|---|
| 1 `blip` | 35 → 35 | 777 / 877 µs a sample | 0.074 / **0.078** µs a sample |
| 4 `knob` | 25 → 25 | 1139 / 1090 µs a sample | 0.136 / **0.138** µs a sample |

Both message arms now play natively, bit-identical to their goldens, and
cost what the signal arms cost.  Read by the sheet's rule, **cases 1 and
4 move from signals to ties** — which keep the signal.  Case 5 is still
refused, for its list fold and its `sync`.  *Not acted on.*

**Held by** `test/test_audiollvm.py` §"`scanE`": a fold counting a knob's
turns and the clock's ticks, oracle against engine and against native,
which went red in both when the fold was made to step on every sample.
