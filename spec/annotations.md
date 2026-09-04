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
sounding when you add it.**  *All four landed on 2026-09-04.*

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

**What is not standing:** nothing in the first slice.  The manner names, `asks`, `Notable`'s `manner`, the voice
behaviour and the dot on the roll all landed on 2026-09-04.  That is
what is left — and it is smaller than the first draft of this file thought,
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

class Notable a where
    noteKey : a -> Int
    noteVel : a -> Int
    manner  : a -> Int          -- joined here; see below

instance Notable Int where
    noteKey k = k
    noteVel k = 64
    manner  _ = Plain

#: Does this note ask for that manner?  The one place the encoding is
#: read, so a voice never writes arithmetic about bits.
asks : Int -> Int -> Bool
```

**`manner` is a method of `Notable`, and that is the third thing the
building corrected.**  This file first gave it a class of its own,
`Mannered`, arguing that the two answer to different readers: the box
reads `Notable` to *draw* a note and a voice reads a manner to *play*
one.  Then the box had to **draw the mark** — §"The picture" — and the
argument fell over.  A second class would have been two constraints on
every reader for one fact about a note.

*The cost is real and was paid:* the language has **no default
methods** — the parser refuses a body in a class declaration — so every
`Notable` instance must answer.  Six existed and each gained
`manner _ = Plain`, one line, and `instance Notable Int` carries it for
every bare `[: Int :]` melody, which is why asking costs a melody
nothing.

**`manner`, not `marksOf` or `articulation`**, and the reason is
`Notable`'s own, quoted because it applies unchanged: *"a class must not
collide with the names its authors were taught to write."*  No file in
the tree or in `examples/audio/` used `manner` before this.

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
| `Accent` | this note is attacked harder | a brighter filter for the first instant, settling back | a velocity number the score chose |
| `Portamento` | arrive at this pitch from the last one | `slew` the pitch signal instead of jumping | a fixed glide time |

**Worked, and this compiles** — it was run before it was written down,
which is the only reason it is the shape it is:

```
Tone := Tone Float Int Int          -- weight, degree, manners

instance Notable Tone where
    noteKey t = case t of
        Tone v d m -> 57 + stepOf d
    noteVel t = case t of
        Tone v d m -> floor (v * 127.0)
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

## What a written manner costs — measured 2026-09-04

*Building the gesture found two things the design had not, and both are
about the difference between a mark that is **written** and a mark that
is **computed**.*

**A manner is often not written per note at all.**  `marked.ges` writes
`line m` and calls it `line Plain` and `line Staccato`, so the manner is
a *parameter* — the roll's leaves carry **no atom for it**, and there is
nothing on the page for a gesture to replace.  That is not a fault in
the file; it is the good way to write that piece.  It does mean the
demo for the voice half is not a demo for the gesture half, which is the
same lesson `pitch_atom` records: *the obvious rule refused four real
files in five.*

**And where it is written, it is ambiguous more often than a pitch.**
`manner_atom` follows `pitch_atom` — the one literal in the leaf whose
value *is* the note's manner — and a manner is a small number from a
tiny range while a degree is a small number too.  On a written-out line
of eight notes: **seven resolved, one did not**, and the one was
`'(Tone 0.9 0 0)`, where the degree and the manner are both `0`.  Every
plain note whose degree is `0` has this shape, so the rate is not
incidental.

*A positional tie-break was considered and not taken.*  The manner is
usually the last field, so "the last atom" would resolve the case above
— but `pitch_atom`'s docstring is the argument against inventing one:
the positional rule was **measured** and refused four files in five.
Deciding here what that measurement settled there would be trading a
refusal a person can read for a wrong write they cannot see.

**So the gesture replaces and never adds.**  A payload with no manner
field is refused with a sentence rather than rewritten, because adding a
field moves every character after it and the tier-one invariant is that
one atom's bytes change and nothing else.

**The question this leaves, and it is the next decision:** should a
manner be findable by *position within the payload constructor* rather
than by value?  The instance body says which field it is — `manner t =
case t of Tone v d m -> m` names the third — so it is knowable by
reading the instance, and the descent would have to carry constructor
positions rather than a flat atom list.  That is real work and it is
what would make marking a plain note reliable.  **Not taken here.**

## What the preview costs — found 2026-09-04

The slice asks for the mark to sound as it is written, stopped or
playing, and §"The preview tone" took the decision that it should.
**The mechanism does not exist**, which the building found rather than
the design:

* `audition` **re-applies the whole file** — `apply(text, save=False)`.
  With nothing playing that starts the piece, which is not a preview of
  a note, it is a performance.
* `play_note` plays **a bare MIDI key** and carries no payload, so it
  cannot sound a *manner* at all — the mark would be inaudible in the
  one thing meant to demonstrate it.

So `mark` follows `transpose` exactly for now: heard while something
plays, redrawn when nothing does.

### The three paths, priced — 2026-09-04

*Henri: "lets look at the third path."  There are three, and the
pricing is what decides between them, so it is here rather than in a
reply.*

**1. Through the keyboard.**  `play_note` → `bench.keyboard.press` →
`audiomidi.Notes.feed`, which routes to a bank and **runs the
program's `FromMIDI` instance to build a payload**.  `noteOn` takes
*channel, pitch, velocity* — there is no manner in it and there cannot
be, because a keyboard has no marks.  So this path plays the note
**plain**.

*Which makes it worse than silence for this gesture.*  You mark a note
staccato and hear it played long: the preview would be a confident
answer to the wrong question, and a person would believe it.  **Cheap
and wrong.**

**2. Render the note offline, both ways.**  Correct, and it is what
§"The preview tone" first asked for.  It needs a compile per gesture —
`graph_of` is 0.6–1.1 s on a small piece — and a seam that does not
exist: a way to sound **one payload, with its fields, through its
bank**.  The keyboard is the only door into the engine that takes a
note, and it only takes MIDI numbers.  **Right and expensive.**

**3. Seek to the note and play.**  `Transport.seek(sample)` and
`start` are both standing, and the roll's event carries the note's
onset in ticks (`midi.TICKS_PER_BEAT` and the piece's `bpm` convert
it).  The mark is carried **because the score plays it** — no new seam,
no compile beyond the rebuild the edit already causes, and what you
hear is the marked note in its own context with its own voice.
**Right and cheap.**

**And the reason path 3 is not simply taken is that it is not a
tone.**  It *starts the piece*.  Mark five notes and it restarts five
times unless debounced the way `audition_soon` already debounces.  That
is a change to what the editor does under your hands, not a detail of
this spec, and *"a preview-tone to be played"* is not obviously the
same thing as *"the piece plays from here"*.

**Path 3, taken 2026-09-04.**  *Henri, hesitating and then choosing:*
*"this is really hard question again.  maybe play from the marked note
would work."*

**And the hesitation is answered by the design rather than argued
with.**  The objection was that marking starts the piece, so five marks
restart it five times.  The seek-and-play branch is reached **only from
a standing start**: the first mark starts it, and every mark after that
finds it playing and auditions in place, which is what `transpose`
already does.  Five marks restart it once.

*Silent about its own failures*, because it is a courtesy on top of an
edit that has already succeeded — and a refusal neither writes nor
plays, since a preview after a refusal would say the mark took.

*Path 2 stays wanted and stays unbuilt.*  Hearing a note **in
isolation, both ways** is a different thing from hearing it in context,
and the seam it needs — sound one payload, with its fields, through its
bank — is a card of its own rather than a slice of this one.

## Refusals, each with a sentence

* **A payload that answers `Plain`** is not warned about; it has no
  manners.  A warning would punish every melody written as `[: Int :]`,
  and `instance Notable Int` answers for all of them.
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

## The second slice, landed — 2026-09-04

**`Accent`, and the set.**  Read by `bowVoice` as a *faster bow* — the
filter opens for the first instant and settles back, on an envelope of
its own — rather than as a louder note, which is what a velocity number
would have done and what the score deliberately did not say.  The gate
holds exactly that distinction: the accented render differs from the
plain one in most of its samples while its **level stays within a
third**, so a voice that answered a mark by turning the note up would
fail it.

**And the set stopped being a claim.**  `Staccato + Accent` on one head
now sounds different from plain, from staccato alone *and* from accent
alone, and draws both marks.  That is the property the bitmask was
chosen for, and the first slice could not exercise it with one mark.

**The picture puts them where a score does** — the dot under the head,
the accent above it.  Different side *and* different shape, so they
read apart at a glance.  The generated program asks with the tree's own
`Staccato` and `Accent` rather than with `1` and `2`, so what is drawn
cannot drift from what a voice reads.

**And the command needed nothing.**  `mark` already takes the whole set
as a number, so `mark r 60 3` writes a staccato accent — which is why
it was specified as a set rather than as one mark per gesture.

## What waits behind this

`Portamento`, then the staff.

**And `Portamento` is the expensive one**, which is why it is last and
not first despite being the most interesting.  `Staccato` and `Accent`
are read entirely inside the voice function.  A slide is not: it needs
the *same* voice to carry both notes, or there is nothing to slide from
— so it reaches into `audioalloc`'s choice of voice, which the other two
never touch.  `examples/audio/violin.ges` already plays a portamento
violin with `slew`, so the behaviour has a reference to be held against
before any of it is designed.
