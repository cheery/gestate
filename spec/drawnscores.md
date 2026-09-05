# drawnscores.md — a flat note file the score is written in

*Specified before it is built, the way `spec/scorebox.md`,
`spec/north_star.md` and `spec/annotations.md` were, and for their
reason: the mechanism is standing, so what is left is decisions, and a
decision written down can be argued with before it hard-codes anything.
The decisions were taken in conversation on 2026-09-04 and 2026-09-05
and are transcribed in `card:drawn-scores.md`; this file is the contract
that follows from them.*

**The star, in one sentence:** a piece's notes live in a flat text file
where **one note is one line**, so a person can drag them on a roll, a
session can edit them as text, and the two are looking at the same
bytes.

**And the first slice, in one sentence:** **`arc.ges`'s twenty-four bars
rewritten as `arc.notes`, included by one line, rendering to the same
audio, and every note of it editable on the roll.**

---

## What this is, what it is not, when it runs

**What this is:** a **sub-language**, included into a `.ges` score, that
holds the part of a piece which is *data* — which note, how long, how
loud, played how — in a format deliberately poor enough that a simple
editor can own it whole.  Henri's word for the shape, 2026-09-04:

> *"we create a sub-language meant to be editable by simpler editor.
> Manner is in that direction already.  And we would include these
> sub-language files by `(include "thing.manner")` or similar, into the
> score."*

**What it is not:** a graphical format, and not a second way to write
`.ges`.  The card this comes from asked for a drawn format with `.ges`'s
full power and its author withdrew that ask — *"Jotta formaatti on
käyttökelpoinen, sen täytyy olla rajattu johonkin jota sellaisella tekee
hyvin"* — so **the restriction is the design**.  Everything that
*generates* — `cycle`, `unfold`, `draw`, `sown`, every function and every
combinator — stays in `.ges` and is not expressible here.  A `.notes`
file cannot be endless and cannot be alive.  It is the leaves.

**And it is not a second source of truth.**  The refusal this project
has made twice over stands, and this does not cross it: a phrase file is
not a second *rendering* of something the program also says, it is the
**only** place those notes exist.  That is a module boundary, and two
files that each own their content cannot disagree.  The constraint of
2026-08-29 is kept whole — *"Formaatin pitäisi olla sellainen että
sinäkin, tekstillisenä olentona, pystyt sitä muokkaamaan"* — the store
is text, and a session edits it with the same tools it edits everything
else.

**When it runs:** at assembly, like a prelude.  `include` is read when
the program is put together, the notes become ordinary score values, and
nothing is different at render time.  Not built yet; this file is the
argument for building it.

## Why, in one number

`card:drawn-scores.md` §"The editing surface, measured" counted what the
score box can actually edit today:

| piece | notes | the box can edit |
|---|---|---|
| the three files written for the box | 4–140 | **100%** |
| `moon_sonata.ges` | 120 | **5%** |
| `undertow.ges` | 366 | **0%** |
| `together.ges` | — | **will not draw** |

Henri's verdict on it: **"the scorebox and existing north_star is a cool
demo, but doesn't solve many things that one meets in a full fledged
note editing tool.  Also we still have the problem that it's just as
inaccessible for editing as what it supplements."**

**The cause is that provenance is guessed by value.**  `pitch_atom`
looks for the one numeric literal in a leaf whose value *is* the note's
key; where the pitch was computed, no literal equals it and the answer
is *not written*.  Carrying provenance through the arithmetic was
refused, and rightly — *"lets forget about provenance idea.  It's the
sauce that is least likely to work everywhere"* — because a pitch
written as `45 + stepOf d` has no literal to point at, so the repair
would work on the easy files and silently fail on the rest.

**A `.notes` file makes the question disappear rather than answering
it.**  A note *is* a line; the line *is* where it is written.  There is
nothing to search for and nothing to guess.

> **The format's whole claim, and it is checkable: every note of a
> `.notes` file is editable on the roll, by construction, at 100%, on
> every file, forever.**

That is the thing the restricted format does well, which is the question
the card was left carrying.

## What the piece that was written says it must carry

`doc/notes/notes-on-writing-a-piece.md` is the log of writing `arc.ges`
by hand to find this out.  Each friction below is one line of that file,
and the right-hand column is what this format does about it.  **A
requirement with no friction behind it is not in this table**, which is
how the format stays poor.

| | the friction, as met | what the format does |
|---|---|---|
| **W1** | length lives on the phrase, not the note, so two durations cannot sit side by side without a bracket — *"every note a quarter, all ninety-six of them"* | a note line carries `len` |
| **W2** | the mode is in the writer's head and nowhere in the file — *"nothing can check that 68 is the sharp fourth and not a typo for 67"* | a section declares `key` and `mode`, and a check reads them |
| **W3** | the bar is not a thing; a fifth note in a four-beat bar compiles and shifts the rest of the piece | a note names its `bar`, and a bar that overflows is refused |
| **W4** | velocity is a raw float nobody can check — *"no mf, no p, nothing a reader can check or a second writer can match"* | `vel` is a named level, as `manner` is a named intention |
| **W5 / W8** | five voices aligned by nothing but their lengths; one short line puts everything after it a bar out, and it still compiles | one section declares `bars` and its `voices`; there is no length to disagree |
| **W6** | a tool computed the voicings and the file cannot say they came from a rule | out of scope, and named so below |
| **H1** | *"tonal center is missing… harmony with open chords, voice leaded as individual voices"* — and the ground had **not one third in twenty-four bars** | voices side by side in one file, so a chord is a column and a check can read it |
| **H3** | *"At this point I'd take the editor up open, and see why locrian doesn't locrian"* | the file is what the roll edits, so examining is the same surface as writing |

**And one result bounds this file.**  He took a MIDI keyboard and a DAW
and tried to write the same modal passage himself, and could not either.
So *the modes do not land* **is not a notation problem** — it stayed hard
in a tool where format and editor are long solved — and no future
reading of this spec may take it as a requirement here.

## What is standing

Nothing below is a guess; each row was read in the tree on 2026-09-05.

| the part | where | state |
|---|---|---|
| a beat is **96 ticks**, chosen to divide by 2, 3, 4, 6, 8, 12, 16, 24, 32, 48 | `midi.TICKS_PER_BEAT`, `spec/music.md` | built — **triplets are integers already** |
| a class the tree names once for reading a payload it did not define | `Notable a` — `noteKey`, `noteVel`, `manner` (`audio.ges`) | built, **and the shape to copy** |
| the road *in*: building a payload from numbers | `FromMIDI a` — `noteOn : Int -> Int -> Int -> Maybe a` | built, **and the shape to copy in the other direction** |
| a manner as a named intention, encoded as a bit set in one `Int` | `Plain`/`Staccato`/`Accent`/`Portamento`, `asks` (`audio.ges`) | built 2026-09-04 |
| a roll that draws a score's take | `spec/scorebox.md`, `gestate/scorebox.py` | built |
| the roll writing back to the text, byte-exact | `spec/north_star.md`, the `transpose` command | built |
| a second file parsed as its own module, with its own line numbers | `audiospans.py` — `prelude.ges` is merged as a module | built |
| provenance that names **which file** a node is written in | `Site.path`, `Site.line` (`audiospans.py:47`) | built |
| resolving a path relative to the file that named it | `session.py`'s `open`, nearest first | built |
| a dotted namespace made by an ask keyword | `voices bow 4 bowVoice` → `voices.bow` | built — the spelling to copy |
| a tool that counts what a line does musically | `tools/modecheck.py` | built 2026-09-05 |

**What is not standing:** the parser, the `include` keyword, the class in
§"What the score gets back", the four gate checks, and the roll knowing
that a note came from another file.  That is the whole of the work, and
it is smaller than this document is long.

## What is decided

**1. A file holds several sections; a section holds several voices, side
by side.**  *Henri, 2026-09-05, asked whether a file is one voice's line
or a bar across voices:* **"I think it could contain several sections,
voices side by side, yeah."**

This is the direct answer to the card's question 1, which was deferred
to an experiment on 2026-09-04 — and the experiment ran.  W5 and W8 are
what came back: five lists that happen to be the same length, and *"if
one of them had twenty-three bars the piece would still compile."*  A
file that declares its bars and names its voices cannot express that
error, because there is no length being compared.

**2. Pitch, with the mode declared and checked — not degrees.**  *His
pick, 2026-09-05.*  The line writes `key 68`; the section says `key D
mode lydian`; a check reports that 68 is the ♯4 and that 67 is not in
the mode.  The alternative — writing a degree and computing the pitch —
would put this format straight back into the failure §"Why, in one
number" describes: no literal in the file would equal the sounding
pitch, and the roll would be guessing again.  **Every sounding pitch is
written down.  That is the rule the whole format hangs on.**

**3. The check reports; it never refuses.**  A ♯11 over a dominant is
the whole of `arc.ges`'s A section and it is idiomatic, not a typo.  A
mode declaration that refused out-of-mode notes would refuse the blues.
So `mode` is a **lamp**, in the tree's own sense: it names what is
outside, and the author decides.

**4. Flat, and the tuplet was the test.**  *Henri:* **"I'd like flat, but
only if it allows writing triplets/tuplets.. or then we say how the
staff is subdivided in each bar."**  It is not a trade: the tree already
counts in 96ths of a beat, so a triplet eighth is `32` and a sixteenth
is `24`.  There are no fractions in the format and no special case in
the editor.

**5. The extension is `.notes` and the spec is this file.**  *His pick,
2026-09-05.*  `notes` is the word the score box's ask keyword already
owns, so the tree has one word for notes-drawn-as-a-roll.

**6. What this spec covers: the format and the include door.**  *His
pick, 2026-09-05.*  The pluggable editor view he named — *"maybe a
separate editor view that pops up for them.. or maybe something
pluggable.. a plugin"* — is the next slice, and §"The slice after"
names its acceptance without designing it.

## The format

A `.notes` file is a sequence of **records**, one per line.  Blank lines
and lines beginning with `#` are ignored.  There are two kinds of
record, and each is **self-contained**: a line's meaning does not depend
on any line above it.

### The section record

    section A  key D  mode lydian  bars 8  beats 4  voices melody upper middle lower roots

| field | what it says |
|---|---|
| `section` | the name, and the name the score gets back |
| `key` | the tonic, spelled as a note name |
| `mode` | the mode or scale name — read by the check, by nothing else |
| `bars` | how many bars this section has.  Declared, never inferred |
| `beats` | beats per bar, so a bar is `beats × 96` ticks long |
| `voices` | the voices this section has, in the order the roll stacks them |

`key` and `mode` may be omitted; the check then says nothing rather than
guessing.  Everything else is required — an inferred bar count is the
thing W8 is about.

### The note record

    note  section A  bar 1  at 0    len 96  voice melody  key 62  vel mf
    note  section A  bar 1  at 96   len 96  voice melody  key 66  vel mp
    note  section A  bar 1  at 192  len 96  voice melody  key 68  vel mf  manner accent
    note  section A  bar 1  at 288  len 96  voice melody  key 69  vel p
    note  section A  bar 1  at 0    len 384 voice upper   key 57  vel mp
    note  section A  bar 1  at 0    len 384 voice roots   key 38  vel mf

| field | what it says |
|---|---|
| `section`, `bar`, `voice` | where this note lives.  All three on every line, which is what makes the line self-contained |
| `at` | ticks from the **start of its bar**.  `0` is the downbeat |
| `len` | ticks.  96 is a beat, 32 a triplet eighth, 24 a sixteenth |
| `key` | the MIDI key number, written out.  **Always a literal** |
| `vel` | a named level — see below |
| `manner` | zero or more names from `spec/annotations.md`'s vocabulary.  Absent means `Plain` |

**A note whose `at + len` runs past its bar is legal**; a note whose
`at` is not inside its bar is **refused**.  That is W3, exactly: a fifth
quarter note in a four-beat bar has an `at` of 384 and the file will not
load, instead of compiling and shifting the rest of the piece by a beat.
A tie across a bar line is a length, not a position, so it is the first
case and not the second.

**There are no rests.**  Silence is the absence of a note, which is what
makes the format flat: a rest is a thing you would have to keep
consistent with its neighbours.

### `vel` is a named level, and that is W4

    ppp  pp  p  mp  mf  f  ff  fff

W4 is that `0.85`, `0.70`, `0.65` are numbers a session invented, which
no reader can check and no second writer can match.  A dynamic is the
same kind of thing a manner is — **a named intention the voice
realises** — and `spec/annotations.md` settled that argument already: on
a violin an accent is bow speed and pressure, not a velocity number, and
a pad has no bow.

So the level travels to the voice as a level, encoded the way a manner
is: one small `Int`, `Ppp = 0` through `Fff = 7`, named once by the tree
in `audio.ges` beside `Plain`/`Staccato`/`Accent`.  `Notable`'s
`noteVel` maps it to a MIDI velocity so the roll can draw a note's
weight, and a voice that wants to do better reads the level itself.
**This is the third option of `spec/annotations.md` §"Why this is
notation and not syntax", applied to loudness**, and it is that file's
argument, not a new one.

*And it is the one place this spec adds to the language's vocabulary
rather than only to its syntax.*  Named so it can be struck on its own.

## The four gates, as runnable checks

*Henri, 2026-09-04, on LLM-friendliness:* **"lets make it testable on
your requirements."**  Each of the four is a property of the format, and
each has a check that fails a commit rather than an adjective that
does not.

| gate | what it means here | the check |
|---|---|---|
| **one note per line** | an edit is a line, so a diff is the edit | every record fits on one line; no continuations |
| **every field named, never positional** | the failure that made `manner` unfindable was two fields of one shape telling apart only by position | every value is preceded by its key; a bare token is refused |
| **no significant whitespace and no nesting** | the meaning survives being reflowed by anything | a file whose lines are shuffled parses to the same score |
| **a stable order** | two writings of one phrase are byte-identical, so a diff shows what changed and nothing else | the writer emits section, then bar, then `at`, then the section's own voice order, then key; writing a file it just read is a no-op |

**The third gate is why every note line names its section and bar.**  A
header that opened a block would be cheaper to type and would make a
line's meaning depend on a line above it — which is nesting wearing
indentation, and the reflow check would fail.  The verbosity is the
gate, paid on purpose.

**And the fourth gate is what makes the roll safe.**  `spec/north_star.md`
already holds the roll to writing back byte-exactly; here that is not a
careful implementation but a property of the format, so a drag that
moves one note cannot rewrite the file around it.

## The include door

    include "arc.notes"

An ask keyword, line-level, spelled the way `voices bow 4 bowVoice` is —
which is the tree's existing shape for a line that brings names into
being.  It binds one name per voice per section, dotted:

    A.melody : [: Tone :]
    A.roots  : [: Tone :]
    B.melody : [: Tone :]

Two levels, as `voices.bow` is two.  A section name that collides with
one already bound is **refused at assembly**, named in the error, rather
than shadowing.

**The path resolves relative to the file that included it** — Henri's
own words, *"the layouter references the files relative to the score
that included them"* — which `session.py` already does for `open`,
nearest first.

**And the provenance comes free.**  `audiospans.py` merges `prelude.ges`
as a module already, parsed separately *"so its spans are in its own
coordinates and start again at 1"*, and every `Site` carries both a
`path` and a `line` **within that file**.  So an error, a gesture, or a
click on the roll points at `arc.notes:47`, and the machinery for that
is standing.  What is missing is the door.

## What the score gets back

*The card left this open on purpose:* **"I think we need to see that
first, how it turns out naturally from what we have."**  Having looked,
here is what it turns out to be — **the session's derivation, marked as
such, and the one part of this document most worth striking.**

A voice binds to `[: a :]` for the author's own payload type, because
that is what every score in the tree already is.  The file carries a
key, a level and a manner, so something must build an `a` out of those
three — and the tree already has that road in the other direction:

    class Notable a where            -- reading a payload
        noteKey : a -> Int
        noteVel : a -> Int
        manner  : a -> Int

    class FromMIDI a where           -- building one, from a keyboard
        noteOn : Int -> Int -> Int -> Maybe a

`FromMIDI` is the right shape and the wrong road: a keyboard sends
channel, key and velocity and cannot send a manner.  So the natural
answer is its sibling, named once by the tree:

    class FromNote a where
        fromNote : Int -> Int -> Int -> a
        --         key    level  manners

`Notable` and `FromNote` are then exact inverses, which is the property
that makes a round trip through the roll checkable.  `len` is not a
field of the payload — a duration is score structure, and the include
applies it with the operators that already exist.

*Two things this owes and does not have:* what `include` does when the
program has no `FromNote` instance (suspected: the same refusal
`FromMIDI`'s absence already produces, named in `audiomidi.py:429`), and
whether one instance can serve a file whose voices want different
payload types.  Both are day-one questions rather than design ones.

## Acceptance

Held by `test/test_drawnscores.py`, and the piece is `arc.ges`.

1. **Parity.**  `examples/audio/arc.notes` plus a shortened `arc.ges`
   that includes it renders **sample-identical** audio to today's
   `arc.ges`.  Sample-identical, not similar: the format claims to be a
   different spelling of the same score, and anything less is a
   different piece.
2. **The bar is a thing.**  A fifth quarter note in a four-beat bar
   fails to load, and the message names the file, the line, and the bar
   it overflowed.  *W3.*
3. **The voices cannot drift.**  Deleting every note of bar 17 for one
   voice leaves the piece the same length and the other voices in
   place.  *W5, W8.*
4. **Reflow.**  A file whose note lines are shuffled renders identically
   to the same file sorted.  *Gate three.*
5. **Round trip.**  Reading a file and writing it back is a byte
   no-op, and moving one note on the roll changes exactly the bytes of
   that note's line.  *Gate four, and `spec/north_star.md`'s law.*
6. **The whole file is editable.**  The roll reports **100%** of
   `arc.notes`'s notes as writable — the number §"Why, in one number"
   measured at 0–5% for real `.ges` pieces.  *This is the acceptance
   the format exists for; if it does not hold, nothing else here
   matters.*
7. **The mode lamp reports and does not refuse.**  `arc.notes`'s A
   section loads with its ♯11 intact, and a check names that note as
   outside D lydian.

## The slice after — the view

Named, not designed, so that the format is not shaped around a guess at
it.  What it has to do: **open a `.notes` file to a roll rather than to
text**, honour the drag `spec/north_star.md` already built, and sound
the note it moved.

**And the stopped case is a decision it will owe.**  `north_star`
acceptance 5 gates *the sound moved with it*, and `session.py`'s
transpose sounds where it was dropped — but only **while something is
playing**.  Annotating is not performing, so a preview tone with the
transport stopped is a thing that has to be decided rather than
inherited.

## What is deliberately not here

* **Everything that generates.**  No loops, no chance, no branches, no
  functions.  A `.notes` file is finite and deterministic.  If a piece
  wants a weighted phrase graph, that is `card:drawn-scores.md`'s other
  candidate and it is not this.
* **A rule that computed the notes.**  W6 is real — *"edit one by hand
  and nothing knows the rule is now broken"* — and it is a different
  problem: this format holds what a tool computed and lets a person
  disagree with it, which is all it claims.
* **Bar lines as musical objects** — repeats, first and second endings,
  `D.C. al fine`.  A section is the only structure, and the score
  concatenates sections with the operators it already has.
* **Time signature changes inside a section.**  A section has one
  `beats`.  A change of metre is a new section, which is one line.
* **A staff renderer.**  *"Both roll and staff"* is his ask, and the
  staff is not a drawing job — `spec/annotations.md` §"The staff, and
  why it is not this" priced it as a fork with three arms, because a
  staff position is not a pitch and the mapping cannot be inverted for
  a hand.  Notes land on the roll first.

## Open questions

* **Does a `.notes` file name its own voices' instruments?**  Today the
  score binds a voice to a synth (`voices chord 3 chordVoice`).  The
  file names `melody` and `roots` and says nothing about what plays
  them, which keeps the format poor — but it also means the names have
  to match in two files, which is the alignment problem this format
  exists to remove, arriving one level up.  *Suspected answer: leave it,
  and let the include refuse a voice name the score never binds.*
* **How does a chord get written?**  Today it is several notes at one
  `at` in several voices, which is what H1 asked for — *voice leaded as
  individual voices* — and it is the right default.  Whether one voice
  may hold two notes at the same `at` is unanswered; nothing forbids it
  and nothing needs it yet.
* **`include` of an `include`.**  Refused for now, silently in the
  grammar because a `.notes` file has no include record.  Named here so
  the absence is a decision.
