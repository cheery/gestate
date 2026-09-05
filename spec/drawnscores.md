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
rewritten as `arc.notes`, included by one line, playing the same 219
notes.**  *Built 2026-09-05, and this file was revised from the code
afterward — three things the building taught are folded in where they
belong, each marked **as built**, and the rest stood.*

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

**When it runs:** at the door, when an author's `.ges` file is read.
`include` is expanded there, the notes become ordinary score
declarations, and nothing downstream — the type checker, the extractor,
the renderer, the window — sees anything it did not already understand.

***As built:*** at the *reading* of the file and not inside
`audio.assemble`, which is where the design assumed it would go.  The
reason is that `has_score` parses the author's text to decide *which*
assembly to build, so an unexpanded `include` breaks the question before
the answer picks a door.  `gestate/notes.py`'s `read` is that one door
and eight callers go through it.

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

**What was not standing, 2026-09-05:** the parser, the `include`
keyword, the class in §"What the score gets back", the four gate checks,
and the roll knowing that a note came from another file.  **All but the
last landed the same day** — `gestate/notes.py`, `audio.ges`'s
`FromNote` and its eight dynamics, `examples/audio/arc.notes`,
`examples/audio/arcnotes.ges`, `test/test_drawnscores.py`.  The roll is
the slice after.

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

## The payload nobody had to declare — 2026-09-05

**Henri, reading the first `arcnotes.ges`:** *"The `Tone := Tone Float
Int Int` feels like ceremony in the file.  I wonder why it is necessary
there now?"*

**It was not, and the measurement is the answer.**  Twenty-four payload
declarations across `examples/audio/`, under seven names:

| | | | |
|---|---|---|---|
| `Tone Float Int` | 7 | `Kit Float Int` | 2 |
| `Key Int Int` | 4 | `Hit Int Int` | 2 |
| `Tone Float Int Int` | 3 | `Blue Int Int` | 2 |
| | | `Voice`, `Stroke`, `Note` | 4 |

**Every one is the same two or three fields** — a key, a loudness, and
since `spec/annotations.md` a manner.  Nine of them then hand-write a
`Notable` instance whose three methods differ only in the constructor's
name.  **The per-piece payload is a freedom this tree offered two dozen
times and exercised nowhere.**

**And this format made it worse before it made it better.**  Before,
a piece paid a type and one instance.  §"What the score gets back" added
a second — and `FromNote`'s body is pure repacking of the three fields
the format has already fixed:

    fromNote k lv ms = Tone (loudness lv) k ms

That line turns the format's *(key, level, manners)* into a piece's
*(loudness, key, manners)* so that five accessors can take it apart
again.  An entry fee where there should have been an escape hatch.

**So the note is named once, in `audio.ges`:**

    Tone := Tone Int Int Int              # key, dynamic level, manners

with `Notable` and `FromNote` instances and two accessors, `noteHz` and
`noteLoud`.  `include` needs no change at all: the generated binding is
already `(FromNote a) => [: a :]`, so a piece whose voice says
`Sig Tone` gets this one and a piece that declares its own gets theirs.

**`Tone` and not `Note`**, and the reason is one line of
`prelude._renames`: `Score a := Note a` already spends that constructor,
and two *libraries* wearing one name is a collision no shadowing rule
covers — a program's own name wins over a library's, and neither of two
libraries is a program.  `Tone` is the word eleven pieces reached for on
their own, and it is free in every library.

**The freedom is kept and is what keeps it honest.**
`prelude.shadow_libraries` renames constructors as well as values, so
`arc.ges`'s `Tone Float Int Int` goes on meaning `arc.ges`'s — checked
by `test_drawnscores.py`, because the failure it prevents is silent:
two constructors wearing one name, and the cons table keeping whichever.
All 59 audio examples compile unchanged.

**What stays the piece's, and must:** `bowOf`, `pushOf`, `glideOf` —
what a mark *does*.  `spec/annotations.md` is the whole argument: a
staccato is a filter and an envelope here and a bow stroke elsewhere, so
however repetitive those look they are the one part that cannot move
into a library.

**One change the expander needed.**  `audiovoices._frame` already looked
for a bank's *result* type in the program and then in the prelude —
*"`synth.ges` declares `Stereo` so that two programs mean the same thing
by a stereo frame."*  That sentence was always about the payload too,
and the payload lookup read the program alone, so a library type raised
*"neither Float or Int nor a data type declared here"*.  It now reads
the program and then the vocabulary `audio.preludes` gives it — derived
from the source rather than passed in, because `channels_of` is asked
this from ten places that hold a program and no prelude, and threading
one through all ten is ten chances to pass a vocabulary the compiler did
not use.

**What it cost `arcnotes.ges`: twenty lines of one hundred and
thirty-seven**, and the render is unchanged — 219 of `arc.ges`'s 219
notes, same tick, same length, same bank, same pitch, same loudness.

**What is not done:** the other twenty-three pieces still declare their
own.  That sweep is a bigger and better change than the one that was
asked for, and a correspondingly worse one to get wrong, so it is named
here rather than taken.

## Acceptance

Held by `test/test_drawnscores.py` — **32 tests, all green 2026-09-05** —
and the piece is `arc.ges`.

***As built:*** `examples/audio/arc.ges` is **not** replaced.  It is the
exhibit `doc/notes/notes-on-writing-a-piece.md` was written from, and
overwriting it would have destroyed the measurement, so the piece
written the new way is `examples/audio/arcnotes.ges` beside it and the
two are held to each other.  That is better evidence than a rewrite: a
person can render both and hear the difference, or fail to.

1. **Parity.**  `arcnotes.ges` plays **every note of `arc.ges` at the
   same tick, for the same length, on the same bank, at the same
   pitch — 219 of 219**, and the same `bpm`.

   ***As built:*** *sample-identical*, which this file asked for, **is
   not what was delivered and could not have been.**  `arc.ges` writes
   its velocities as raw floats and the format writes eight named
   dynamics — which is the design, not a shortfall: W4 is precisely
   that those floats were invented by their writer and checkable by
   nobody.  So the exception is measured instead of waved at: **209 of
   219 velocities moved, by at most 0.050**, and both numbers are
   asserted.  A design that quietly moved a piece would be
   indistinguishable from a bug.
2. **The bar is a thing.**  A fifth quarter note in a four-beat bar
   fails to load, and the message names the file, the line, the bar and
   how long that bar is.  A note that *lasts* past its bar is a tie and
   is allowed — the rule is about where a note starts.  *W3.*
3. **The voices cannot drift.**  Deleting every note of one bar for one
   voice leaves the piece exactly one note shorter, the same length, and
   every other voice in place.  *W5, W8.*
4. **Reflow.**  The shipped file with its lines shuffled renders
   identically, and so does the same file indented by six spaces.
   *Gate three.*
5. **Round trip.**  Writing `arc.notes` back is a byte no-op, and moving
   one note changes exactly one line of it.  *Gate four, and
   `spec/north_star.md`'s law — here a property of the format rather
   than a careful implementation.*
6. **Every note is written down.**  ***As built, and narrowed on
   purpose:*** what is executed is the property that makes the guess
   unnecessary — every one of the 219 sounding notes has exactly one
   line of `arc.notes` that wrote it, that line spells the pitch as a
   literal, and the expansion carries every one of those line numbers
   into the generated `.ges`.  **That is 100%, and it is the half the
   format is responsible for.**  Wiring the roll to *follow* the map
   into the `.notes` file is the slice after this one, and claiming the
   roll number before that wiring exists would have been the thing this
   tree calls a number nobody checks.
7. **The mode lamp reports and does not refuse.**  `arc.notes` loads
   with all 219 notes, and the lamp names **6** of them as outside their
   section's mode.

   ***As built, and it is the best thing the building found:*** the
   first of the six is `A bar 3 melody key 67`, in a section declared D
   lydian — whose fourth is 68.  That is W2's own sentence answered
   word for word: *"nothing can check that 68 is the sharp fourth and
   not a typo for 67."*  Something now can.  And it is **not** a typo —
   bar 3 is the IV chord and 67 is its root — which is exactly why this
   reports and never refuses.

## What the building taught — 2026-09-05

Three things, none of which this file had.

**1. The door leaks, and the leak is named rather than closed.**  The
expansion happens when an author's `.ges` file is *read*, so a tool that
calls `Path.read_text()` instead meets a bare `include` line and the
parser says *"expected '=', got end of line"* — a line the author wrote
correctly, blamed for a door somebody else skipped.  That is the F150
shape exactly: the symptom named, and not one word of the cause.  Four
sweeps in the tree read every audio example directly and all four now go
through `gestate.notes.read`; the fifth has not been written yet.

So `audio.assemble` and `audioscore.assemble_performance` refuse an
`include` that survives to them, and say *this program was read without
`gestate.notes.read`*.  **That is a guard and not a fix** — the fix
would be for the text to carry its own path, which it does not, and
threading one through every caller of `assemble` is a change this slice
did not earn.  Named here so it is a decision rather than a gap.

*And the guard was itself wrong for half an hour*, which is worth the
line: written once and pasted into both assemblers, it named `source`
where the score path's parameter is `synth`, so **every scored program
crashed with a `NameError`** and 34 tests were green over it.  What
found it was typing the command — `python -m gestate.audioperform
examples/audio/arcnotes.ges -o take.wav` — which is the tree's own rule
about running the thing a person runs, and there is now a test that does
exactly that.

**And the door was put on the wrong method in the editor, which is the
worst of the three.**  `Workbench.source()` fills the window's text
buffer *and* was the door every compiler went through, so expanding
there made the editor **display a program the author had not written** —
the `include` line blanked, nine hundred generated lines after it — and
a `Ctrl-S` would have written that over their file.  Henri found it by
opening `arcnotes.ges` and looking for its own `include`.

**Two needs, two methods**, and the split is now the contract:

| | |
|---|---|
| `Workbench.source()` | the author's bytes — what the window shows and what a save writes.  Expands nothing |
| `Workbench.program(text)` | what compiles — that text with its includes expanded, against the file's own directory |

*And the Workbench is the right place and nothing lower is*, which is
the answer to §"the door leaks" one paragraph up: expanding an `include`
needs the **directory** the file sits in, a compiler is handed only
text, and the Workbench is the object that has both.  A live buffer has
no path at all, so no door beneath it could have served the editor.

**And the split had to be made twice more**, because two more places
were asking one field to answer two questions.

*`apply` and `audition` take the window's buffer*, which has an
`include` in it and no path attached, so the assembler's guard fired on
the one gesture the editor exists for — Henri's log again: `audition`
→ *"not applied: `include "arc.notes"` reached the assembler."*
`_built` now expands before it compiles, and reports a bad include the
way it reports a compile error, because to the person at the window it
is one: they typed a name and it is not a file.

*And a build records two texts, not one.*  `_built_from` is the
author's bytes and answers **is the window ahead of the sound**;
`_built_program` is what the compiler saw and answers **what may this
rebuild skip**.  Holding the expanded text in the first made `behind`
permanently true for any file with an `include` — his words, *"It shows
that it's not auditioned at the start."*

**The lesson is this file's own, arriving from behind.**  A `.notes`
file is not a second source of truth because the picture and the text
are one file; a `source()` that expanded made the *window* a second
rendering of the file, which is the same mistake at one remove.  A view
that shows something other than what a save writes is the failure this
project has now designed against three times.

**And the shape of all three is one shape**, worth naming because the
next person adding a sub-language will meet it: *expansion introduces a
second text, and every field, method and comparison that held "the
program" now has to say which of the two it means.*  Three places in
`audioeditor.py` did not, and the suite was green over every one of
them, because nothing in it opened the file the way a person does.

**2. A whole voice of `arc.ges` is never played** — `fixme.md` F198.
The file writes twenty-four bars of `bass` and its `score` does not
mention it.  Found because the note counts refused to agree: the piece
has 219 events and the file has 314 written notes, and the difference is
`bass` plus the chord bank's three voices sharing a bank.  A second
number says it from the other side — 15 velocities sound and 16 are
written.

**This is W8's failure with the count removed as a defence**, and worse
than the one that log named: not five lines aligned by nothing, but a
sixth line held by nothing at all, which compiles, renders and is
silent.  The repair is Henri's, because the question is what the piece
is meant to sound like.  `arc.notes` is faithful to what `arc.ges`
*plays*.

**3. The mode lamp earned itself on its first run.**  Six of 219 notes
are outside their section's mode, and the first is a **67** in a section
declared D lydian — whose fourth is 68.  W2 asked for exactly this, in
these numbers: *"nothing can check that 68 is the sharp fourth and not a
typo for 67."*  It is not a typo, and a version of this that refused
would have refused the piece.  The lamp cost eleven lines.

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
