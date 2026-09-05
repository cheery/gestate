---
name: henri-prior-tools
description: "Three of Henri's own tools that came before gestate — oscillseq/beet the sequencer, mide the older editor, xylem the layout engine — and the four open questions here that each has already answered once"
metadata:
  type: project
---

**Shown 2026-09-05, at the end of a long day, at his offer:** *"I think
I'd want to show you things on this computer.  My old works."*  Read,
not reviewed — his rule from [[henri-lever-language]], and it holds.
They live in his own documents directory; only **oscillseq** is
published (`github.com/cheery/oscillseq`), so treat the other two as
his to name.

**The lineage.**  `mide` → `oscillseq` (its working directory is called
`beet`) → gestate.  `xylem` sits beside them, not in the line.

## What each is

* **oscillseq** — *"my repeated attempts to create a music sequencer.
  At winter 2026, I got things working and finally understood how to
  create this kind of software."*  A sequencer over SuperCollider's
  `scsynth`, driven by a **command language in a textbox** with mouse
  gestures in the minority — the same shape as gestate's session
  commands, arrived at independently.
* **mide** — an older editor whose UI is written as **logic rules**.
  `staves.ui` is datalog: `present (note K) [X-5,290-5,10,10] :- offset
  K X Onset W, order K Onset 1.` and `draggable (note K) :- order K
  Onset 1.`  A wholly different answer to the furniture problem than
  `furniture.rs`.
* **xylem** — a layout engine: a Cassowary-shaped linear-constraint
  solver (`constrainer.py`, `LinearExpr`/`flex`/`slack`/`eq`/`les`) with
  a **Knuth–Plass** line breaker and a lark stylesheet.

## The four that answer something open here

**1. Musical pitch is a `(pitch, accidental)` pair** — held *beside* the
MIDI number and the frequency, not derived from it.  That is the
answer to the question `spec/drawnscores.md` §"The three spellings"
leaves open and `notes.spell` documents as *"the one arbitrary choice…
the case that would put names in the file"*.  It arrived the same day
the case did: `arc.notes`' final cadence prints `des4` where the
leading tone is a **C♯**, because a rule cannot know where the line is
going and a stored accidental does not have to.  **He solved this
before.**

**2. `.desc` files name what a parameter *means*.**  A synthdef is
annotated `frequency: hz`, `note: pitch`, `volume: db`, from a closed
vocabulary — `boolean unipolar bipolar number pitch hz db duration`.
That is `spec/annotations.md`'s `Manner` and this format's named `vel`
generalised to every knob, and it is what
`card:the-first-jam.md` item 4 asks for: *`drive`'s amount 1.4 is a
13.6× gain, learned only from the source*.

**3. A staff was rendered, and it cost a C program.**  `mide` carries
`music/voice_separation.c` — *"Voice Separation: A Local Optimisation
Approach"*, rewritten from Python because Python was too slow — and
oscillseq reuses it.  `spec/scorebox.md` prices the staff as a fork
with three arms and takes none.  **He has built one, knows which
algorithm it needs, and says its correct implementation is very hard.**
`xylem`'s Knuth–Plass is the other half: breaking a score into systems
is line breaking.

**4. Rhythm is a source, and notes decorate it.**  A tracker there is
three pieces: a rhythm source producing `(onset, duration)`, generators
that decorate those with pitch and volume, and a view.  `.notes`
deliberately gave up generation, so this is not a defect here — but it
is the factoring that makes rhythm editable *as rhythm*, and his
**rhythm quantizer** edits it in a fractional representation and
quantizes back to a tree.  That bears on `fixme.md` F199, where a drag
in time is the awkward gesture.

## And two things worth knowing exist

* **Playback as states** — OFFLINE / ONLINE / FABRIC / PLAYING, with
  parts restartable while sound continues.  gestate's live audio has
  the same problem and no such name for it.
* **Bus allocation by biclique decomposition** — arbitrary node graph
  onto SuperCollider's fixed buses, each biclique cover one bus.

**How to apply:** read one of these *before* designing the thing it
already did — the staff, the spelling, a parameter vocabulary, a
full-window view.  Ask him first; they are his and unpublished bar one.
And do not review them: [[henri-lever-language]] is the rule, and his
verdict on that one was *"it went nowhere"*, which is his to give and
not a session's.

Related: [[gestate-salvage-week]] is the sibling and is about the
*music*; this is about the *software*.
