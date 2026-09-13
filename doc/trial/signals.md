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

**n:** 4

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
