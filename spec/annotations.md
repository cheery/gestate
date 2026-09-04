# annotations.md — a mark the voice interprets

*Specified before it is built, the way `spec/scorebox.md` and
`spec/north_star.md` were, and for their reason: the mechanism is
standing, so what is left is decisions, and a decision written down can
be argued with before it hard-codes anything.  The decisions were taken
in conversation on 2026-09-04 and are transcribed in
`card:drawn-scores.md` §"What the notation turned out to be"; this file
is the contract that follows from them.*

**The star, in one sentence:** a score carries marks that say *how* a
note is played, and each voice decides for itself what that means.

**And the first slice, in one sentence:** **staccato on the roll,
honoured by one voice and ignored by another, added by a command,
sounding when you add it.**

---

## Why this is notation and not syntax

An annotation in a real score instructs a *person*, and it is
deliberately imprecise — a performer interprets it.  Here the performer
is a program, so a mark could land in three places, and which one
decides what this document is:

1. **Exact** — `mf` means velocity 80.  Then it is a number with a
   pretty face and nothing is interpreted.
2. **Inert** — a note to whoever reads the file.  Real and useful, but
   that is a comment with better placement.
3. **A hint an interpreter reads** — the voice decides how much.

**Three is the one taken**, Henri 2026-09-04, and his own instrument is
the argument.  He plays violin: **staccato is not "shorter"**, it is a
bow stroke whose shortness is a *consequence*, and accent is bow speed
and pressure rather than a velocity number.  A pad voice has no bow.  So
a mark that compiled to `duration × 0.5` would be wrong for the violin
**and** wrong for the pad, which is the cleanest available proof that
one is not the answer.

A mark names an **intention**; each voice realises it in its own terms.
That is what an orchestra does, and it is what this tree already says of
its own notes — `lantern.ges`: *a note is a degree and a weight, not a
pitch: the score decides which step of the scale, and the voice decides
what that sounds like.*  **The score/voice split is already the
notation/performer split**, and this document extends a seam rather than
opening one.

## What is standing

Nothing below needs a compiler change, and saying which parts exist is
the whole of *grounded to what can be delivered*.

| the part | where | state |
|---|---|---|
| a payload the voice pattern-matches | `Tone := Tone Float Int` in any piece | built |
| a class the tree names for reading a payload it did not define | `Notable a` — `noteKey`, `noteVel` (`audio.ges`) | **built, and the shape to copy** |
| a roll that draws a score's take | `spec/scorebox.md`, `gestate/scorebox.py` | built |
| the roll writing back to the text, byte-exact | `spec/north_star.md`, the `transpose` command | built |
| a gesture sounding what it did | `session.py`, `north_star` acceptance 5 | built, **playing only** |
| the primitive portamento needs | `slew` (`synth.ges:335`) | built |
| a voice that already plays portamento | `examples/audio/violin.ges` | built — the reference |
| an `Int` field on a bank's payload, and the voice reading it | measured 2026-09-04 — §"The vocabulary" | **built; a list or an enum is not** |

**What is not standing:** the manner names and `asks`, the class, the
drawing, the command, and one decision about the preview tone.  That is
the work — and it is smaller than the first draft of this file thought,
because §"What the compiler refused" removed a language change it had
quietly assumed.

## What is decided

**1. A convention the tree names once, not a field each file invents.**
Henri, given both: *"2. convention the tree names once."*  His reason
came a message earlier and is the load-bearing one — **the score must be
readable by a session too**.  With a per-file field, *readable* means
parseable; with a named convention it means understood, because a reader
who has not read this file's own datatype still knows what a staccato
is.

**2. The type is `Manner`.**  His pick.  `Mark` was unavailable:
`Score a` already spends it on `Mark String`, *a named point, zero
wide*, and two spellings of one idea is what the `card:` notation was
invented to stop.

**3. Three manners: `Staccato`, `Accent`, `Portamento`.**  His, and
`Portamento` is spelled out rather than `Slide` because `slide` is
already a delay-line signal function (`signal.ges:152`).

**4. Points, not spans.**  A span is a pair of points and the drawing
pairs them.  *A session's call, at his ask* — §"Points, not spans".

**5. The roll first; the staff is its own slice.**  Both are wanted —
Henri: *"what I have available changes what I create.  I've noticed that
when working on score."*  The roll is standing and already writes back;
a staff is a second renderer and the expensive half, and no part of the
mark work depends on it.

## What the compiler refused — 2026-09-04

*This section exists because the first draft of the one below it was
wrong, and one command said so before anything was built.  That is what
specifying first is for, and the refusals are more useful than the
design they corrected.*

**A payload field must be `Float` or `Int`.**  The obvious spelling —
a list of marks riding with the note — does not compile:

    Tone := Tone Float Int [Manner]
    → VoicesError: `Tone` has a field this bank cannot supply: every
      field becomes a control channel, and a control value is one slot,
      so each must be Float or Int

**And a bare enum is refused for the same reason.**  `Tone Float Int
Manner`, with `Manner` three nullary constructors, fails identically.
There is no representation trick here to find: *every field becomes a
control channel*, and a channel is one number.

**So a manner crosses as a number**, and the vocabulary below is built
around that instead of around a wish.  Nothing about §"Why this is
notation and not syntax" changes — the number is *a code the voice
interprets*, not a quantity the score chose.  What was lost is only the
pretty spelling.

**And an envelope's rate is a compile-time constant.**  `perc : Float
-> Sig Gate -> Sig Float` takes a `Float`, not a `Sig Float`, so a voice
**cannot parameterise its envelope per note**.  It blends alternatives
it computed anyway:

    perc 6.0 g * (1.0 - w) + perc 18.0 g * w        -- w is 0.0 or 1.0

*That is the shape a manner is honoured in*, and it has a price worth
stating: **each honoured manner costs one control slot per voice and
doubles whatever part of the voice it varies.**  A bank of five voices
reading one manner is five more channels and five more envelopes.

## The vocabulary

```
#: A set, not a choice — a note may be both accented and staccato, and
#: real notation writes both marks on one head.  One `Int`, because a
#: control value is one slot (§"What the compiler refused").
Plain      : Int
Plain      = 0
Staccato   : Int
Staccato   = 1
Accent     : Int
Accent     = 2
Portamento : Int
Portamento = 4

class Mannered a where
    manner : a -> Int

instance Mannered Int where
    manner _ = Plain

#: Does this note ask for that manner?  The one place the encoding is
#: read, so a voice never writes arithmetic about bits.
asks : Int -> Int -> Bool
```

**`manner`, not `marksOf` or `articulation`**, and the reason is
`Notable`'s own, quoted because it applies unchanged: *"a class must not
collide with the names its authors were taught to write."*  No file in
the tree or in `examples/audio/` uses `manner` or `Manner` today.

**A set and not a choice**, which the bitmask buys back: a note may be
accented *and* staccato, and a violinist writes both marks on one head.
A single ordinal would have made the two exclusive by accident, which is
a format deciding a musical question.

**The bare-melody instance matters as much as the class.**  A
`[: Int :]` melody carries a key number and nothing else, and
`instance Notable Int` already gives it a velocity of 64 so the box and
the renderer agree about an unmarked note.  `manner _ = Plain` is the
same promise: **an unmarked note is not a special case**, it is a note
whose set is empty, and `asks` answers `False` for every manner without
a branch anywhere else.

## What each manner asks for, and what a voice may do with it

**The list is what is written; the sound is the voice's.**  A voice that
reads no manners is not broken and is not warned about — `padVoice`
below is a correct program.

| manner | what it asks | what a voice might do | what it must not mean |
|---|---|---|---|
| `Staccato` | detached, shorter than written | blend toward a quicker envelope | a multiplier the score chose |
| `Accent` | this note is attacked harder | more drive, a brighter filter on the attack | a velocity number the score chose |
| `Portamento` | arrive at this pitch from the last one | `slew` the pitch signal instead of jumping | a fixed glide time |

**Worked, and this compiles** — it was run before it was written down,
which is the only reason it is the shape it is:

```
Tone := Tone Float Int Int          -- weight, degree, manners

instance Mannered Tone where
    manner t = case t of
        Tone v d m -> m

#: 0.0 or 1.0, not a rate: an envelope's rate is a constant, so the
#: voice blends two it computed anyway (§"What the compiler refused").
stacOf : Tone -> Float
stacOf t = case asks (manner t) Staccato of
    True  -> 1.0
    False -> 0.0

#: This voice honours staccato as a bow stroke — quicker to decay, not
#: a note cut to a fraction of its written length.
leadVoice : Sig Gate -> Sig Tone -> Sig Float
leadVoice g s = lowpassSvf 900.0 0.3 (saw (!hzOf s)) * (!velOf s)
    * (perc 6.0 g * (1.0 - (!stacOf s)) + perc 18.0 g * (!stacOf s))

#: And this one ignores every manner, which is a complete program.
padVoice : Sig Gate -> Sig Tone -> Sig Float
padVoice g s = triangle (!hzOf s) * (!velOf s) * perc 1.4 g
```

**Measured, 2026-09-04, before any of this was designed further.**  The
same four notes through `leadVoice`, differing only in that third
field — `'(Tone 0.9 0 0)` against `'(Tone 0.9 0 1)` — rendered through
`run_native`:

| | |
|---|---|
| samples differing | 105,712 of 105,840 — **99.9%** |
| RMS, plain → staccato | 0.183 → 0.104, **ratio 0.57** |

Shorter notes, less energy, from a mark the score wrote and the voice
chose the meaning of.  **That is this document's claim, executed** —
and it was executed on a scratch file, which is why acceptance 5 below
asks for it as a gate rather than as a story.

## Points, not spans

Asked whether a span mark is stored as a span, Henri said *"I don't
know.  answer to this one."*  **Points**, and this section is the
session's, marked so.

* **The field converged there.**  Lilypond attaches slurs to notes —
  `c( d e f)`.  MusicXML writes `<slur type="start"/>` on one note and
  `type="stop"` on another.  MIDI has no spans, only events at points.
* **The editor's law admits it.**  `spec/editor.md`: *widgets attach to
  declarations whose body is one literal, or one constructor of
  literals.*  A point mark is a field of one constructor.  A span is a
  relation between two, which the law does not admit, and amending
  something `spec/north_star.md` calls load-bearing is a large bill for
  a format detail.
* **The class shape admits it.**  `manners : a -> [Manner]` is a
  function of one payload, as `noteKey` is.  A span needs two payloads
  or an index, and neither is a property of a payload.

**And the decisive one is the algebra.**  `Score a` is a tree, not a
list, and it carries:

```
| Retro (Score a)        -- reverse, back to front
| Sow Int (Score a)      -- re-root a subtree's seed
| Draw (Int -> Score a)  -- the notes are unknown until a seed arrives
```

A span stored as *note 3 to note 7* has **no stable referent under any
of them**: reversed it dangles or inverts, re-sown the notes differ, and
under `Draw` the notes do not exist yet to be indexed.  A point mark
rides with its payload through all three for free — reverse the phrase
and *arrive at this pitch from the last one* still means exactly that,
arriving now from a different predecessor, which is musically right
rather than merely well-defined.

**The cost, stated rather than discovered.**  A chancy score can produce
a start whose stop never comes; an unclosed crescendo is a real outcome
of a seed, not a pathology.  **An unpaired start ends at the boundary of
its `Clip`** — `long n s` already declares a span, so the score's own
bracket supplies the ending.  Defined, not refused.

## The gesture

**A command, or it does not exist.**  `spec/north_star.md`: *"A gesture
with no command behind it is a capability that does not exist."*  So,
beside `transpose : Text -> Int -> Int -> Command`:

```
mark   : Text -> Int -> Manner -> Command
unmark : Text -> Int -> Manner -> Command
```

**Named the way `transpose` is** — the region, and the key as written —
and for `transpose`'s own reason, learned by building it: a region is a
*leaf*, one written place, and a leaf can sound several notes, so the
note is named by what it **says**.  A step or a position would mean a
different note on the second reading, and a replay is the one reader
that cannot ask.

Two commands rather than one toggle, because a transcript that says
`mark` is self-contained and one that says `toggle` is not — the same
argument, one level up.

## The picture

**On the roll, in the first slice.**  A manner is drawn on the note it
belongs to: a dot under the head for `Staccato`, a wedge for `Accent`,
a line from the previous head for `Portamento` — the last being a span
*drawn* from two points, which is the whole of §"Points, not spans" made
visible.

**The staff is a second renderer and is not this slice.**  When it comes,
the presentation facts a staff needs — clef, key, beaming — do not go
into the score expression, which the compiler would have no use for.
They go where `spec/scorebox.md` already put a presentation fact: the
`notes <expr>` ask **rewrites to a comment**, read by the box and
ignored by the compiler.  One source, two readers.

## The preview tone, and the decision it needs

Henri asked for one.  **It is half built**: `north_star` acceptance 5
already gates *the sound moved with it*, and `session.py` sounds a
transpose where it was dropped — *"the same answer `audition` gives"*.

**The gap is that it sounds only while something is playing.**  That
was decided for transposing during a performance, on the argument that a
sentence about the transport over the top of one about the note is noise
where an answer should be.  **That argument does not carry here.**
Annotating is not performing: the entire content of a manner is what it
does to the sound, so a mark added in silence and heard only on the next
play is a mark added blind — which is the pain this whole line of work
started from.

*The decision this file takes, and it is open to being overruled:*
**`mark` sounds the note it marked, stopped or playing** — one note,
through the bank it belongs to, both ways so the difference is what is
heard.  It is the smallest thing that makes the mark's meaning audible
at the moment it is written.

## Refusals, each with a sentence

* **A payload with no `Mannered` instance** is not an error and is not
  warned about; it has no manners.  A warning here would punish every
  melody written as `[: Int :]`.
* **A manner a voice does not read** is silent by design.  The score
  says how it should be played and the voice says what it can do; a
  pad that cannot bow is not a fault.
* **`mark` on take ink, on a non-literal note, or on a collapsed leaf**
  refuses with a sentence and writes nothing — `north_star`'s three
  refusals, unchanged, because this gesture writes text the same way.
* **The same manner twice on one note** refuses rather than writing a
  duplicate: the list is a set in meaning, and a reader who saw
  `[Staccato, Staccato]` would rightly wonder what twice means.

## Acceptance

The first four are the slice; the fifth is the one that matters.

1. **Byte-exact.**  `mark` a note staccato and the file differs by
   exactly that note's bytes — a diff of the whole text, not of the
   parsed tree.
2. **The picture follows.**  The roll redraws with the dot under the
   head, at the same leaf.
3. **Undo is text undo.**  One `Ctrl-Z` puts back the byte and the dot
   together, because there is only one history.
4. **It sounded when it was written.**  Adding the mark plays the note
   both ways, with the transport stopped.
5. **One score, two banks, and the difference is the mark.**  The same
   `[: Tone :]` played by a voice that reads `Staccato` and one that
   ignores it: both render, both are bit-identical to `run_native`, and
   the first differs from its own unmarked rendering while the second
   does **not, sample for sample**.  **That is the claim of this
   document, executed** — a mark is an intention, and what it means is
   the voice's.  The marked half of it was measured on a scratch file on
   2026-09-04 (99.9% of samples, RMS ratio 0.57); what a gate adds is the
   *ignoring* voice, which is the half that says a manner is a hint and
   not a command.

## What waits behind this

`Accent`, then `Portamento`, then the staff.

**And `Portamento` is the expensive one**, which is why it is last and
not first despite being the most interesting.  `Staccato` and `Accent`
are read entirely inside the voice function.  A slide is not: it needs
the *same* voice to carry both notes, or there is nothing to slide from
— so it reaches into `audioalloc`'s choice of voice, which the other two
never touch.  `examples/audio/violin.ges` already plays a portamento
violin with `slew`, so the behaviour has a reference to be held against
before any of it is designed.
