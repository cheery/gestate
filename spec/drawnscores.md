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

***And whether it is written as `68` or as `gis4` is still open.***  Those
are two decisions and this one only made the first: a note *name* is a
bijection with a key number, not a computation, so the argument that
killed degrees does not touch it.  `doc/trial/pitch-spelling.md` put the
question to sixteen arms on 2026-09-05 and **could not decide it** —
both spellings scored 99 of 99 — which voided the trial by its own
ceiling condition and, more usefully, showed the premise was wrong: the
faults this tree has met were never unreadable, they were unasked.

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
    note  section C  bar 8  at 0    len 96  voice melody  key 73  spell cis5  vel ff

| field | what it says |
|---|---|
| `section`, `bar`, `voice` | where this note lives.  All three on every line, which is what makes the line self-contained |
| `at` | ticks from the **start of its bar**.  `0` is the downbeat |
| `len` | ticks.  96 is a beat, 32 a triplet eighth, 24 a sixteenth |
| `key` | the MIDI key number, written out.  **Always a literal** |
| `spell` | *optional* — the letter this note is, where the rule would pick the other one.  `cis5`, not `des5`.  Read by the views, by nothing that sounds |
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

### The tempo record — 2026-09-06

    bpm 120

At most one, anywhere in the file; the canonical writer puts it first,
as the one fact about the whole file, and its prose belongs to it as
any record's does.  **Henri, Q2 of `card:notes-editor.md`:** *"tempo
could still live in .ges, but allow tapping it … .notes could also have
bpm marking, but it's not used if .ges has one."*  So a `.notes` played
alone goes at its own `bpm`, `notes.wrapper` writing the number into
the `.ges` it generates and saying where it came from, and at
`WRAPPER_BPM` when the file is silent; an including `.ges` keeps its
own `bpm`, the include bringing notes only.  A whole number of at least
one; twice, or with two numbers, is refused by name.

### The prose belongs to the record below it — 2026-09-06

**A `.notes` file may carry comments, and a rewrite gives them all
back.**  `fixme.md` F200 is what it could not do before: the parser
stripped `#` to end of line and the writer never emitted one, so the
first tool to write a hand-annotated file back deleted every word
explaining the music — in the same gesture that was supposed to be
byte-exact.

**The rule is one sentence.**  A comment belongs to the **record below
it**, or to the record it shares a line with.  Which is how a doc
comment attaches in every language, and it means the prose names its
owner instead of depending on a position in the file:

    # arc.notes — three sections, bright to dark          <- section A's
    section A  key D  mode lydian  bars 8  beats 4  voices melody,bass  # G# is the mode

    #: the melody opens on the tonic and reaches the sharp fourth
    note  section A  bar 1  at 0   len 96  voice melody  key 62  vel ff
    note  section A  bar 1  at 96  len 96  voice melody  key 68  vel f  # the sharp fourth

**Why not a trailing field, which was the shape F200 preferred.**  That
was chosen on a property and the count refuses it: `arc.ges` carries
**169 whole-line comments and 0 trailing ones**, so a trailing field
would have held none of the prose the defect is about.  Both shapes are
one rule here, so neither is given up.

**And a remark about a section cannot jump**, which was F200's other
worry: it belongs to the `section` record, and that record never moves.

**The one limit, stated rather than discovered.**  A remark written
above the first note of a *bar* belongs to that note, and a drag takes
it along.  There is no bar record for it to belong to and this spec
refuses to invent one — §"What is deliberately not here" — so the
honest thing is to say where prose about a bar goes: on the section, or
beside the note it is really about.

**And a blank line inside a run of prose is not kept, nor is a
comment's indentation.**  The house spelling for a blank row is a bare
`#`, which `arc.ges` uses throughout; indentation means nothing in a
format with no nesting, and keeping it would leave one file with two
rules about whitespace — true for the records, false for the prose.
`write()` is the canonical writer, not a formatter.

**Where a comment starts, which had to be settled first.**  A `#` opens
a comment **where a token could start** — the beginning of a line, or
after whitespace.  `fixme.md` F203 is why: the old rule cut at any `#`,
and five of the seventeen tonics this format offers end in one, so
`key C#` was unwritable and the refusal blamed the author for the
`bars` it had just eaten.  Every value here is one `\S+` token, so
there is no other reading to lose.

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
| **a stable order** | two writings of one phrase are byte-identical, so a diff shows what changed and nothing else | the writer emits section, then bar, then the section's own **voice** order, then `at`, then key; writing a file it just read is a no-op |

**The third gate is why every note line names its section and bar.**  A
header that opened a block would be cheaper to type and would make a
line's meaning depend on a line above it — which is nesting wearing
indentation, and the reflow check would fail.  The verbosity is the
gate, paid on purpose.

**And the fourth gate is what makes the roll safe.**  `spec/north_star.md`
already holds the roll to writing back byte-exactly; here that is not a
careful implementation but a property of the format, so a drag that
moves one note cannot rewrite the file around it.

***As built, and the order was chosen twice.***  It sorted by `at`
before the voice until 2026-09-05, which read like a score — everything
sounding at beat one together — and cost what `fixme.md` F199 measured:
**a note dragged in time moved five lines**, because it changed places
in the order.  Voice before tick keeps a voice's notes contiguous inside
its bar, and the rule becomes exact: **one line per position the note
moves past, plus one** — 1 for a pitch drag, 2 for half a beat, 3 for a
whole one, all of them inside that note's own voice.

*What was given up is that the file no longer reads bar-wise*, and it is
recoverable where the property was not: `tools/bars.py` and its Read
hook reassemble a bar across voices from the **parsed** file, not from
its line order.  A view can restore a reading; nothing restores a
property of the bytes.

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

## The three spellings, and two of them are derived — 2026-09-05

**Henri, after the preference trial:** *"That we'd have all three
notations?  MIDI, functional harmony, and some ascii-notation for
pitches?"*

**Three views, one storage.**  They are not three spellings competing
for the file:

| | |
|---|---|
| `key 68` | **stored** — the literal a drag rewrites and the roll points at |
| `gis4` | a function of the number **and the declared key and mode** |
| `♯4`, `vi` | a function of the same two, read as scale position |

Storing all three would be one fact written three ways in one file,
which is what `card:` notation, `Manner` against `Mark`, and the
shadowing rule all exist to stop — and it would bring the round-trip
problem back three times over.  Views over one storage cost nothing,
because **nothing round-trips through a view**.

**And what the arms produced says which view matters.**  They did not
only convert to letters; they wrote *"G minor in first inversion over a
Bb bass"*, *"vi of Bb"*, *"the raised fourth giving the lydian
shimmer"*.  Letters were the substrate and **function was the
content** — so the report prints both columns, because a report has
room and a `key` field does not.

**The section header is what makes either derivable.**  `key` and `mode`
went in as a lamp (§"What is decided" 3); they turn out to be the whole
input to the spelling.  `notes.spell` is the rule and `notes.degree_of`
the other, both written and tested — nearest degree first, then the
smallest accidental, both halves found by getting them wrong.

**The one arbitrary choice, and it is the trigger.**  Where two
spellings cost one accidental each — D♯ against E♭ in D — the rule takes
the flat.  A piece that needs the other is **the case that would put
names in the file**, and until one turns up the spelling is a report's
business, correctable by re-running it.

### The spelling a rule cannot guess — 2026-09-06

**The trigger fired, in the only `.notes` file there is.**  `arc.notes`'
last bar is `73 → 69 → 62` in D phrygian: a leading tone resolving up to
the tonic, which is a **C♯** and cannot be a D♭.  The rule spelled it
`des5`, and the report's own degree column beside it said `7` — two
views of one file, disagreeing about one note, at its cadence.  Three
notes of 291 are in that position:

| | | the rule | written |
|---|---|---|---|
| `arc.notes:222` | B, G locrian, bass | `ges3` | **`fis3`** — the bass walks A–E–B–F♯, and B to G♭ is not a fifth |
| `arc.notes:301` | C, D phrygian, middle | `des4` | **`cis4`** — held under bar 7, resolving up to `d` in bar 8 |
| `arc.notes:308` | C, D phrygian, melody | `des5` | **`cis5`** — the cadence |

**And the answer is Henri's own, from before this project.**
`doc/memory/henri-prior-tools.md` item 1: in `oscillseq` a musical pitch
is a **`(pitch, accidental)` pair held beside the MIDI number**, not
derived from it — *a rule cannot know where the line is going and a
stored accidental does not have to.*  That is the whole argument, and it
was reached once already on a working sequencer.

**What is stored is still one fact.**  `spell` is not a fourth spelling
competing with the three; it is the **tie-break**, written down only
where the rule has to guess and the guess is wrong.  Three lines of 291
carry one, every other note is derived exactly as before, and nothing
round-trips through a view — which is the section above, unchanged.

**Three properties make it safe to store rather than dangerous:**

* **A spelling that does not name its own key is refused**, by one rule
  the parser and the record both call — so a hand-written file, a drag,
  and anything that rebuilds a note all meet it, and each says the place
  it knows.  `spell des5` on `key 60` will not load.  A file may choose
  the letter and may not choose the note.
* **It is per note, not per file.**  Key 61 is `des4` in section B and
  `cis4` in section C of the shipped file — G locrian's flattened fifth
  and D phrygian's leading tone, one pitch and two notes.  A table per
  file could not say that.
* **A drag in pitch drops it, and says so.**  The letter is an intention
  about the pitch that *was*; no rule carries it to the note the drag
  made.  So `notes.retune` removes the field with the key it belonged
  to and names the loss in what the gesture says, and the person writes
  the new one if they meant one.  A drag in time, in velocity or in
  manner keeps it, because none of those change which note it is.

**What is deliberately not done:** the rule is untouched.  It still
takes the flat on a tie, and it is still right on 288 of 291 notes.  The
field exists so the three cases a rule cannot reach are writable, not so
the rule can be tuned by hand.

### And a view has to be in the loop, or it is a command nobody runs

*Henri, the same day:* **"It needs a 'view', just like how I look toward
to that score being rendered in the editor."**

He is right and it is the sharper half.  `spec/scorebox.md`'s principle
is *a widget is a view over a span of source* — and `tools/bars.py` is
exactly that widget for a reader with no eyes.  But **his roll is beside
the text he is editing and this is a command somebody has to think of**,
which is the gap both trials of 2026-09-05 found from opposite sides: a
session asked to check is exact, and a session not asked does not look.

So the report is not finished as a tool.  It is finished when it appears
without being asked — and `card:the-first-jam.md` item 1 already names
the shape, for a different number: *"a `ceiling: X%` line after a render
would put the criterion into every run's own mouth."*  The same move
here is the report riding on a render, or beside a `notes` ask in the
window.  **Not built, and named so the tool is not mistaken for the
answer.**

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

## The slices after — the view, one rung at a time

*Henri, 2026-09-05: "I'm realising I'd need the .notes editor, fully
featured.  But we should go slice at a time because it's a tall order."*
So it is a ladder, each rung usable on its own, each with its blocker
named.

**0 — the roll you already have, and it costs nothing.**  `notes
A.melody` written into the `.ges` **after** the include.  No code: the
dotted rewrite reaches the ask line too, so it names the generated
binding and `scorebox` draws it.  Measured 2026-09-05: **32 of 32 notes
editable on every voice tried — 100%**, against the 0–5% §"Why, in one
number" counted for real `.ges` pieces.  Its job is to answer by use the
questions the later rungs would otherwise settle by taste: voices
stacked or one at a time, degrees or names in the margin.

**1 — `expand()` returns its origins.**  ***Built 2026-09-05.***
`notes.expanded` returns `(text, {line of the text: (file, line of it)})`
and `expand` is a thin wrapper on it.  The concatenation and the counting
are one loop, so nothing does arithmetic it cannot check — which is the
whole lesson: the offset was reconstructed from outside first, by
counting the author's lines and adding one for a separator, and it was
**wrong by one on the fourth note** while three of four still resolved.

Measured after: **32 of 32 notes of a roll resolve to the `arc.notes`
line that wrote them**, and each of those lines really says that pitch —
checked, not assumed.  291 origins for 291 notes, and none for the
`long 4 (` that opens a bar or the `))` that closes it, because those
were written by nobody and answering for them would be inventing a
provenance.

**2 — the region budget.**  ***Built 2026-09-05, and it was not the rung
that was specified.***  The plan here was a strip at the include line, a
table of contents for a box that cannot grow.  Typing rung 0's ask
showed that was the wrong work twice over: **a section stacks today
without any code** — `notes (A.melody || A.upper || …)`, because the ask
takes an expression — and what actually stopped it was
`scorebox.MAX_LEAVES = 48`.

Its reason had stopped being true.  It said each leaf was *"a nested
`Over` in the generated picture, which is a parenthesis the parser has
to hold open"*, describing the design `page_program` replaced: notes
travel as a **list** now, and a leaf reaches the picture as an integer
in it.  Measured on the whole of `arc.notes`, five voices on one roll:

    cap  48   291 notes,  48 leaves,  47 placeable, picture 18963 chars, 5.0s
    cap 512   291 notes, 291 leaves, 291 placeable, picture 18963 chars, 4.4s

**Byte-identical picture, no slower.**  What 48 cost was provenance —
244 notes that drew, jumped to a line that was not theirs, and could not
be dragged, which is `pitch_atom`'s own failure shape in a new place.
`MAX_HANDS` stays 48 and should: those are nested `Over`s and are about
drag *columns*, not notes.

*And a strip is no longer worth building.*  The `notes` expression says
what a section holds, and the Read hook gives a session the whole file
already.

**3 — the roll names the right file.**  ***Built 2026-09-05.***  Two
halves.  A **drag** on a note this file did not write is refused by
name — *"that note is written in arc.notes:5"* — which Henri met the
hour rung 0 shipped, as `transpose: line 57 is not in this file any
more`: the roll is drawn from the expanded program and the rewrite
landed in the author's text, identical for every program written before
today and divergent past an `include`.

And a **click** now answers at all.  `spec/scorebox.md` says *"the one
gesture it owns is a click that jumps to source"*; a hand let go where
it began returned `""`, so that sentence was true of the design and of
nothing else.  It reveals the note's place, and jumps there when the
note is this file's own.  **It does not switch files** — opening another
document out from under a click is a large answer to a small gesture,
and the window has one buffer, so it says the place and lets `open` be
the person's next move.

**4 — the drag writes into the `.notes`.**  ***Built 2026-09-05.***
`notes.retune` rewrites one named field of one line byte-exactly —
`spec/north_star.md`'s law, and easier here than in a `.ges` because the
field is *named*, which is gate two met from the other side: the
property that stops two fields telling apart by position is what lets an
editor find one without counting.

**And one thing is genuinely different, so it is said and not hidden.**
There is no buffer for an included file, so the edit **reaches the disk
at once** where a `.ges` drag waits for `Ctrl-S`.  The gesture names the
file it moved, because writing something a person is not looking at,
silently, is the one thing an editor must not do.  Then the program is
rebuilt from the unchanged buffer: the expansion re-reads the file, so
the roll redraws with the note where it was dropped.

Refused where the drag cannot be resolved — `notes.doubled`, the
constraint that moved from the bytes to the gesture the same day.  Still
open: the two-writers rule, if that `.notes` is open in another window.

*And one thing this rung owes rather than inherits:* `notes.doubled`
names the places a drag cannot resolve — one voice, one bar, one tick,
one key, written twice — and **the gesture must refuse those, because
the file no longer does.**  That constraint moved from the bytes to the
gesture on 2026-09-05, after refusing at `parse` stopped Henri
mid-sketch and took a whole test file's collection with it.  A file may
say a thing the editor cannot act on; the editor says so at the moment
it cannot.

**5 — the view that takes the window.**  *Decided 2026-09-06 — §"The view — rung 5, the seam as decided".*  Sections and voices stacked,
the margin columns `tools/bars.py` already computes.  Henri's own word
for it, 2026-09-04: *"a separate editor view that pops up for them.."*
Expensive, and for a named reason rather than its size: a new furniture
kind crosses `furniture.rs`, `window.rs` and the verb table — the three
seams that lost `touch` when the pygame editor went, none of which
failed loudly (`doc/memory/gestate-canvas-unwired.md`).

What the view has to do, whichever rung reaches it: **open a `.notes`
file to a roll rather than to text**, honour the drag
`spec/north_star.md` already built, and sound the note it moved.

**And the stopped case is a decision it will owe.**  `north_star`
acceptance 5 gates *the sound moved with it*, and `session.py`'s
transpose sounds where it was dropped — but only **while something is
playing**.  Annotating is not performing, so a preview tone with the
transport stopped is a thing that has to be decided rather than
inherited.

## The view — rung 5, the seam as decided — 2026-09-06

*Henri chose the view that takes the window over the score box beside
each section line, on the condition that the seam be talked through
first.  One round each; `card:drawn-scores.md` §"Rung 5, the seam"
carries both verbatim.  This is what the round decided.*

**The three seams that lost `touch` do not move.**  No new furniture
row, no new gesture, nothing new for `Furniture::read` or the window
to learn about the wire: coordinates never cross it and meanings do
(`spec/workbench.md` §"The canvas walks over crust"), the roll already
crosses as a picture the window hit-tests off its own walk — which is
mide's requirement met by construction, *one place says where a note
is* — and `onTouchX` stands beside `onTouchY` in `gui.ges`, a pad
being two touches on one element.  What changes:

| where | what | his word |
|---|---|---|
| the bench's file kind | a `.notes` opened in the window builds through a wrapper whose own picture is its page; `Ctrl-Tab` is the view | — |
| the roll program | sections stacked in one picture; the margin words `tools/bars.py` computes drawn as labels; a **rail** for time (below: why not `onTouchX` on the note); a **`selected`** channel a press writes | *"Give roll a selected -channel"* |
| the model | the `touched` fraction snapped to the section's grid, off the wire | *"allow grid snap"* |
| the verb table | a time drag becomes **`move`** beside `transpose`: one line rewritten, the file re-ordered under the canonical order it was chosen for | *"commands are generated for mouse gestures"* |
| the window | the canvas view grows a **vertical scroll** — the one thing it learns | *"I'd like view to grow a vertical scroll"* |
| the wrapper | a `.notes` opened alone binds every voice to a **default, piano-like** synth, so *play from the dragged note* (§"The slices after", 5) has something to play through | *"something that sounds piano-like"* |

**Every gesture is a command**, and the drag is what makes it a rule
rather than a description: the window sends `touched` and `released`,
the model turns them into `move <region> <note> <at>` or `transpose …`,
and that line is what the transcript records and what a person or a
session can type.  Nothing routes on a coordinate.

### The first slice, built — 2026-09-06

*Henri: "Yes, reading 1 matches, take that first slice."*  The same
code under every reading of *plugin-like*: the roll's selection, the
second axis, the snap, and the command under the gesture — inside the
score box that exists, so `arc.notes` proves the drag in time before
the window learns to scroll.

**A press writes one attachment, so time got its own element.**  The
plan above said `onTouchX` on each note beside its `onTouchY`, and the
substrate spec says a pad is two touches on one element.  Measured
before building: a press writes the deepest attachment containing it
and no other, in both machines — `fixme.md` **F204**.  The walk is the
parity seam, walked by the editor and the CLAP panel alike, and this
day's contract was that no seam moves.  So the roll grew a **rail**: one
full-width `TouchX` strip along its top, drawn as a faint track, written
into the picture *before* the columns so it wins where a column reaches
over it.  Press a note to select it; drag the rail to carry it in time.
Two motions where a pad would be one, stated rather than hidden, and
the rail retires the day F204 is repaired the first way.  *(It did, the same day — §"The sixth slice, built".)*

| built | where |
|---|---|
| `selected` and `slide`, two readings the model writes; the selected note wears an outline and a marker on the rail | `scorebox.roll_program` |
| the rail, a `Region` with `hand == RAIL`; `x_of`/`tick_at` as `y_of`/`key_at`'s siblings — one arithmetic, two readers | `scorebox.x_of`, `tick_at`, `regions_of` |
| the grid: the largest tick dividing every onset and length in the roll, never finer than a thirty-second | `scorebox.grid_of`, `GRID_MIN` |
| a press selects and the selection outlives the click; a hand on the rail moves the selected note by whole grid steps, relative, previewed, and commits as **`move`** on release | `session._note_touched`, `_rail_touched`, `released` |
| `move <rail> <was> <at>`: one `at` field rewritten on one `.notes` line, and `bar` with it past a bar line; refused by name for nothing selected, a `.ges`-written note, a note leaving its section, or a double | `command.ges`, `session.do_move`, `_move_included` |

**Measured on `arc.notes`, `A.melody`:** the grid reads 96, one beat;
a drag of one grid step changes **one line** of the file, its `at`
field only, and the transcript holds it as `move`.  Ten tests in
`test/test_drawnscores.py` under *Rung 5, the first slice*.

**What this slice does not do, said now:** nothing sounds with the
transport stopped — decision 2's *play from the dragged note* is the
next slice, with the piano-like default voice; the canvas view does not
scroll; a `.notes` opened alone still compiles as a `.ges`.

### The second slice, built — the sound with the transport stopped — 2026-09-06

*Decision 2, (a), and Henri's "(a)" again on the voice.*  A drag that
commits with the transport stopped now plays the piece from the note —
`transpose` on a `.ges` note, `transpose` on an included note, and
`move` from where the note *went* — the road the mark gesture opened
(`session._hear_at`).  Nothing changes while something plays: the edit
is auditioned in place, as before.

**And a `.notes` opened alone is lent a piano.**  `notes.wrapper(path)`
is the `.ges` it is played through, generated and never written to
disk: it includes the file, binds every voice its sections declare to
`chopin.ges`'s hammer — the envelope and the timbre verbatim, reading
`Tone` because that is what `fromNote` builds — concatenates the
sections in the order written with a rest for a voice a section lacks,
says a tempo the file does not carry (`WRAPPER_BPM`, 100, in a comment
a person can see), and asks a roll of every section.  Measured:
`arc.notes` plays **291 of 291** notes through it, one bank per voice.
Not yet wired to the window — that is the file-kind slice, reading 1 —
but built and held by four tests so the slice after it is a
registration and not a design.

### The third slice, built — a file kind is a registration — 2026-09-06

*Henri: "take the next slice."*  `audioeditor.KINDS` is the table
reading 1 asked for: a row says how a suffix builds its program and
what its page is, and the bench branches on nothing else.  `.notes` is
the first row, `NotesKind`.  A `.ges` is the default and needs no row;
an inert suffix stays in `INERT`; the next sub-language is a second
row and no new seam.

**What the row says.**  The document is the note file; the program is
`notes.wrapper` expanded over the window's own buffer — `expanded`
takes the file's text from the buffer rather than the disk, so what a
person is looking at is what plays, the rule a `.ges` already keeps.
The page is the file's own picture: `page_program(rolls, stacked=True)`
declares `substrate` as every section's roll in one `Column`, and the
bench takes that entry as the file's canvas, so **`Ctrl-Tab` shows the
sections stacked** and a hand on any of them writes that box's own
channels.

**And a drag on the document writes the buffer.**  Rung 4 wrote an
included file to disk at once because there was no buffer for it; when
the `.notes` is the document there is one, so `transpose` and `move`
rewrite the buffer through the same door a `.ges` drag uses — one undo
entry, `Ctrl-S` to keep — and a click goes to the line, since the line
is the whole answer in one's own file.  The disk road stays for a
`.notes` a `.ges` includes.

Measured on `arc.notes` opened alone: three boxes, one per section; a
page with three captions at three heights; three rails; a pitch drag
changes one line of the buffer and none of the disk.  Four tests.

**Still not built:** the scroll.  The stacked page is three rolls tall
and the canvas view centres it; the window's one line is the slice
after this.

### The fourth slice, built — the scroll — 2026-09-06

*Henri: "lets do the scroll."*  The one thing the window learns, and
it is one number: `canvas_scroll`, how far the canvas view's picture
is carried up.  The painter hands the walk its origin lower by that
much, so the display the walk produces — which the press and the drag
already hit-test in window coordinates — moves with the picture and
needs no second transform; the wheel changes the number and nothing
else.  `view::canvas_scroll` is the arithmetic, pure and tested: a
picture that fits never moves, and one that overhangs stops at its own
ends.  `view::canvas_opening` places a page at its top when the view
opens and the page is taller than the window, once; a drag rebuilds
the page and a rebuild keeps the scroll where the wheel left it.

**Driven, not only tested.**  `test/driven/20260906-085009-notes-page-scroll`
on the desk that ran it — `test/driven/` is not tracked, so what a
clone gets is this paragraph and the numbers in it: `arc.notes` opened alone on a virtual screen, the
window shrunk to 260 pixels under a three-section page, the wheel
turned down and back.  The page opened at its top, moved under the
wheel, and came back to the pixel.  And the driving found three things
the headless tests had not:

* **The wrapper was expanded twice.**  Every reader hands `program` the
  buffer, and some hand it a program it already produced; for a `.ges`
  a second expansion is the first, for a `.notes` it parsed the
  wrapper as the note file — *`env` is not a record*, at line 7, in the
  status bar (`test/driven/20260906-083403-notes-page-scroll`).
  `NotesKind.program` is idempotent now, and a test says so.
* **The canvas command refused the page.**  Its guard asked the
  program's text for a `substrate`, which a `.notes` never declares —
  the page does — so `Ctrl-Tab` before the page had built answered
  *this file draws nothing* (`…083625`).  A registered kind whose page
  is the file's picture draws by registration.
* **The page took 88 s to appear in two runs and 2 s in two others**,
  the same script in the last three — `fixme.md` F205.  The first
  suspicion, that opening the view before the build slowed it, was
  falsified by the last run; the cause is unrecorded, and the next move
  is a driven run that writes down the load it ran under.  Not fixed
  here: the scroll was the slice and this is the start.

**Rung 5 is built.**  What the ladder named — open a `.notes` to a
roll, honour the drag, sound the moved note — is in the window, with
the seam untouched where the round said it would be: nothing new
crosses the wire.  What is not done is not on the ladder: the seven
candidate questions for the fire, F204's pad *(repaired that afternoon)*, F205's wait.

### The fifth slice, built — the editing scale — 2026-09-06, the second sitting

*Henri, opening a second sitting: "I'd like us to continue the
drawn-scores.. make it more like what it's supposed to be."*  What it
is supposed to be is `card:notes-editor.md`'s league, and the
photographs said where the gap was: rung 5 opened a `.notes` to the
score box's *glance* — 384 by 116, a note three pixels tall, no keys,
no bars, `NOTES` on every section — where Reaper fills the window,
names the keys and numbers the bars.  **The postcondition, written
before the code:** *a person opening a `.notes` sees each section at a
size where a note can be taken by the hand, with the keys named down
the side and the bars numbered along the top.*

**Two scales, one arithmetic.**  A `Roll` now carries a `Geometry` —
its box, the three margins around the body, and how tall a note is —
and `y_of`/`x_of` draw from it while `key_at`/`tick_at` read back
through it, so the picture and the gesture cannot disagree at either
scale.  `COMPACT` is the box beside a line of a `.ges`, **held to the
pixel**: the pictures of `chopin.ges`, `minute.ges`, `noted.ges` and
`arcnotes.ges` were snapshotted before the change and are item-identical
after it, hands included.  `editing` is what a `.notes` roll gets from
the data road, and its numbers are fixed rather than fitted to a window,
so a section is the same picture on every desk and a test can hold it:

| | |
|---|---|
| a semitone | 8 px — a row a hand can take; a note is 6 px tall |
| a beat | 32 px — a sixteenth is 8 px, the finest thing `GRID_MIN` asks a hand to hit |
| the keys | 30 px down the left, a key per semitone of the file's range, the octaves named on the Cs |
| the ruler | 16 px along the top — the rail *is* the ruler: the bar's number at every bar line, a tick at every beat |
| the body | the black-key rows striped across it, a line under every C, a beat line and a brighter bar line where the section declares them |
| the caption | the section's name, key and mode — `A D lydian` — where `NOTES` said only what kind of box it was |
| `arc.notes` | 1054 by 376 a section, 128 columns of 8 px, three sections 1128 px tall under the scroll |

**The bars are the section's.**  A `Roll` carries the ticks its bar
lines fall on and its beat, known for a `.notes` roll and `None` for a
`.ges` take, which has no bars to draw.  And a roll asked for the voices
of *two* sections draws the second after the first now — every section
began at tick 0 before and only the span was summed, which the page
never showed because it asks one section a roll.

**The hands folded balanced.**  A chain of `n` `Over`s is `n`
parentheses held open, which is what overflowed the parser on chopin's
notes and what `MAX_HANDS = 48` was for; `_overs` folds the same list
into a tree of depth `log n` in the same order — the walk paints in
order and records attachments in order, and an in-order walk of a
balanced tree is the list — so a page's 128 columns cost eight levels
and the bound is 256.  The reference walk is held to it: every note's
own rectangle pressed lands on a column that names that note, and a
press in the ruler lands on the rail, rail first as the chain had it.

**Measured.**  The page's program grew from 19 k to 80 k characters —
the furniture is unrolled — and compiles once in 3.9 s (live) where the
glance took about 3 s; a moved note is still a lookup under the 1.5 s
the slice-3 test holds it to, because the text holds still.  Then the
real window on `Xvfb :99`, `arc.notes` opened alone:
`test/driven/20260906-141355-notes-page-editing-scale` on the desk
that ran it — the page appeared 2 s after `Ctrl-Tab`, the run aimed at
a whole-bar note of the `upper` voice by reading its rectangle off the
reference walk and the page's ground off the photograph, carried it
three semitones with the picture following, dropped it, and `Ctrl-S`
changed **one line** of the copy: `key 57` to `key 60`.  The drop
played the piece from the note through the sound card for a few
seconds, as decision 2 says it should.  Four tests under *The editing
scale* in `test/test_drawnscores.py`; 131 in the file, green.

**What this slice does not do, said now.**  The numbers are not fitted
to the window: a section wider than the view is cut at the view's
edge, and there is no horizontal scroll — a section of more than eight
bars of four is the case that would ask for one.  The rail is still the
second axis (F204 stands — *until the slice below, the same afternoon*);
the ruler only gives it a face.  No playhead
crosses the page while the transport runs — the picture reads no
transport position — and the margin words `tools/bars.py` computes are
not drawn yet.  And the run photographed F208, two fields of the status
row painted over each other under the page.

### The sixth slice, built — one hand, both axes — 2026-09-06

*Henri: "go with the default, repair the walk."*  F204's first repair,
and the sentence `spec/substrate.md` §"S3" had promised all along: **a
pad is two on one element.**

**The walk, in both machines.**  A press grabs the deepest attachment
containing the point **and every attachment around it**, innermost
first — `gui._grabbed` and `Display::grabbed`, each reading *around*
off its own hit table as a later attachment whose region holds the
grabbed one's whole region, which is what enclosing looks like from a
table the walk fills innermost-first.  A hand writes each grab a
fraction of *its own* extent, and a release lets go of each by name:
`Substrate.touch_all` answers every write, `Walker::release` names
every grab, the window says `released` for each.  Two faders side by
side share no extent and a press on one still leaves the other alone;
`touch` still answers the innermost, so nothing that read one answer
reads a different one.

**The roll, rearranged around it.**  The columns went *inside* a
`TouchX` the body's whole width and the columns' whole height, so the
press that takes a note writes the column — which note, how far in
pitch — and the body — how far along, a fraction of the width
`tick_at` already read.  The rail retired to being the ruler: drawn,
listening to nothing.  In the model the body's grab stands beside the
column's (`holding_x` beside `holding`), each preview keeps the other
axis's reading, and **the first `released` commits both** — `move` and
`transpose`, two lines in the transcript, each replayable alone — so the
second arrives to nothing held.  A press on an empty column drops the
selection, so the body has nothing to carry off in time.

**And the window found what no bench could.**  Driven, the first run
moved the key and not the tick.  The reason was the door, not the
walk: `ged_set_text` is picked up on the window's next frame and
`ged_text` reads what the window last published, so the second command
read the document from before the first and the last write won.  Every
headless view is synchronous, which is why 131 tests had not seen it.
`workbench.Window.text` answers its own replacement until the document
has taken it, and one test holds that with an editor whose setter lands
a frame late.

**Measured.**  The six-line pad program writes `cy` and `cx` from one
press, 0.625 each.  The page: every note's own rectangle pressed lands
on its column and the body.  Driven on `Xvfb :99`,
`test/driven/20260906-145334-notes-both-axes-one-drag` on the desk
that ran it: a whole-bar note carried up three semitones and along one
beat with the picture following in both axes, dropped, and one line of
the copy changed in both fields — `key 57` to `60`, `at 0` to `96`.
Four grab cases in `shell/panel/src/list.rs`, panel and editor crates
green; five new Python tests under *F204 repaired*.

**What this slice does not do, said now.**  A diagonal drag is two
rewrites and two rebuilds, not one; the transcript says `move` then
`transpose`.  A press in the ruler strip lands on the column reaching
under it, since the columns are `DRAG_REACH` taller than the notes,
and takes a note there by aim — the ruler is not yet a control.  F208
was photographed again.

### The seventh slice, built — select several, carry them as one — 2026-09-06

*Henri: "take the next slice, multi-select and move as a group."*
`card:notes-editor.md` slice 4's first two tools, and no new word on
the wire: both are gestures the walk already delivers, turned into
commands the transcript already holds.

**A band, swept over empty roll.**  A press that lands on no note —
*beyond reach* of any, `BAND_REACH` three semitones, because a column
is the roll's whole height and before this a press anywhere in a
column with one note took that note — starts a band: the column's
hand carries one corner in keys, the body's the other in ticks, the
picture draws the rectangle as it grows (`__nb_band_k__`, a list
reading), and the release commits **`select <rail> tick0 key0 tick1
key1`**.  A note the band touches is in, Reaper's rule; the corners
are the roll's own ticks and keys either way round, so a typed or
replayed `select` picks what a sweep did.  The group outlives the
sweep: every selected note wears an outline (`__nb_sels_k__`, the
group as a list), and a press on any of them keeps it, a press on any
other note is a selection of one, a press on nothing clears it.

**A hand on any note of the group carries them all.**  The picture
moves every selected note with the hand in both axes, and the release
commits **`carry <rail> semitones ticks`**: `transpose` and `move` for
a group in one rewrite — every selected line changes by the same two
numbers, one text edit, one undo entry, one rebuild.  Refused whole
rather than half-done: a note written in a `.ges`, a note that would
leave the keyboard or its section, a note that would land where the
file already says one is (`notes.doubled`).  The selection is spent
with the commit, as `move`'s is — the rebuild renumbers the roll.

**A list-valued reading crosses as a trace**, the word a scope's window
and a live roll's rows already use; `observe` writes it to the
reference views as before, and the workbench turns it into a `trace`
line rather than a `reading`.

**Measured, headless:** bar 1 of section A swept from key 78 to 62
selects 6 notes — the melody's four and two held under them; carried
up two semitones, 6 lines change by `+2` through one `replace`;
carried along one beat as well, the whole is refused because the
melody's last note would land on bar 2's first, and the group stands.
Eight tests under *Slice 4* in `test/test_drawnscores.py`.

**Driven, first time.**  `test/driven/20260906-154518-notes-band-select-and-carry`
on the desk that ran it: `arc.notes` opened alone on `Xvfb :99`, the
hand pressed above the melody in bar 1 and swept to below it — the band
drawn as it grew — let go, and six notes wore their outlines; then it
took the first of them and carried it up three rows, and `Ctrl-S`
changed six lines of the copy, each `key` by two, nothing else.

**What this slice does not do, said now.**  A group is spent with its
commit, where Reaper keeps it; a band selects by touching, with no way
yet to add or drop one note from a group; the compact box beside a
`.ges` line sweeps bands too, on a roll three pixels a semitone where
three semitones is five pixels — honest, and not much use there.  And
`test_the_page_after_a_moved_note_is_a_lookup_not_a_compile`'s 1.5 s
bound tripped at 1.63 s inside the full-file run and passed five times
alone at well under it, with and without this slice: a bound written
for a lookup measured in a process that had just run 170 tests.  Left
as it is, and said here.

### The eighth slice, built — a note resized by its end, and the selection with it — 2026-09-06

*Henri: "take the next slice, resize a note and the selection."*  Slice
4's *adjust offset* and *resize selection*, on the same two hands and
with no new word on the wire.

**A press in a note's last column takes its end** — the column the
note's offset falls in, when the note is wider than one column, so a
beat-long note at editing scale has an eight-pixel end and a whole-bar
one the same.  The reveal says *its end*; pitch is not carried while
an end is held, because a hand on an end is on an end.  The body's
hand then carries the end along, by whole grid steps and never under
one, the picture drawing the held selection longer or shorter from its
start (`__nb_grow_k__`, pixels), and the release commits **`resize
<column> key len`** for one note — named as `transpose` names one —
or **`stretch <rail> ticks`** for a group, every selected line's `len`
by the same ticks in one rewrite.  A length past the bar line is
written as it is: the format allows it and the bar clips it when it
sounds.  Refused by name: a `.ges`-written note, a length under a
tick, and for a group the whole if any one of them would be.

**Measured, headless:** the whole-bar `upper` note of bar 1, its end
carried back a beat, `len 384` to `288` on one line; bar 1 swept and
a melody note's end carried along a beat, six lines' `len` by `+96`
through one `replace`, the four beat-long notes to `192` and the two
held ones to `480`, past their bar line as written.  Seven tests under
*Slice 4, continued*.

**Driven, first time.**  `test/driven/20260906-160458-notes-resize-end-and-stretch`
on the desk that ran it: the whole-bar note's end taken and carried
back a beat, drawn shorter before the drop, `len 384` to `288`; then
bar 1 swept, a melody note's end carried along a beat, the group drawn
longer before the drop, and `Ctrl-S` left seven lines changed in the
copy — the resize, and every selected `len` by `+96`, nothing else on
any of them.

**What this slice does not do, said now.**  A note's *start* cannot be
taken — `at` moves with `move` and `carry`, the end with `resize` and
`stretch`, and a hand on the first column is a move.  A group's ends
move by the same ticks, not to the same place.  And the end of a note
one column wide — a sixteenth at editing scale — is not a handle, the
note being too narrow to have one; a typed `resize` still reaches it.

### The ninth slice, built — the section resized on its ruler — 2026-09-06

*Henri: "take the next slice, resize the section."*  The clip of slice
4, which he answered on the card as *section resize is sufficient*: an
edit to the section record's `bars`.

**The ruler is the section's handle.**  On a roll that knows its bars
the ruler strip is a `TouchX` the body's width, recorded before the
body so it wins where the columns reach up under it — the control the
seventh slice said the ruler was not yet.  A press on it takes the
section's end; the drag along carries the end by the whole bars the
hand has travelled, never under one, the picture drawing a bright
line where the end would fall (`__nb_endx_k__`, inside the roll); and
the release commits **`bars <ruler> was now`**, one field of the
section record on one line, `was` carried so a replayed line means the
same edit.  The body's hand, grabbed by the same press, carries
nothing while the ruler has it.  The compact box beside a `.ges` line
hands out no such thing, having no section, and stays item-identical.

**A section grows freely and shrinks only past empty bars.**  Growing
is a rest for every voice; shrinking past a bar with notes in it is
refused by name, the notes being the point.  Refused too: a roll of
several sections, a `.notes` not opened alone, and a length under a
bar.  A grown section is a wider roll — the program's text changes
and is compiled once more, which is the one edit here that is not a
lookup.

**Measured, headless:** the ruler pressed at bar 5's line and carried
along one bar says `bars 8 → 9`, and the release changes the section
line of `arc.notes` and nothing else; `bars 8 → 7` is refused because
bar 8 of section A has notes; `8 → 10` and back to `8` both go, the
two bars being empty.  Three tests under *the section resized*.

**Driven, first time.**  `test/driven/20260906-162036-notes-section-resized-on-ruler`
on the desk that ran it: the ruler pressed at bar 5's line and carried
along one bar, the end drawn as it went, and `Ctrl-S` left one line of
the copy changed — the section record's `bars 8` to `bars 9`, nothing
else.  **What the photograph after the drop shows is a blank canvas
and *8.8 s to open* in the status row** — a grown section is a new
program text, and six seconds was not enough for it; the page was not
photographed rebuilt.  That a nine-bar section is 1182 pixels wide in
a window 1100 wide, and so cut at the view's right edge, is arithmetic
and not a photograph: the horizontal scroll the fifth slice said no
section of eight bars would ask for, asked for by the first section of
nine.

**What this slice does not do, said now.**  No horizontal scroll, as
above.  A section cannot be resized on a roll that draws several, nor
from a `.ges` that includes it.  `notes.retune` rewrites a section
line now as well as a note's, so a pitch drag aimed at a section line
is refused on its tonic rather than as *not a note*.

### The tenth slice, built — the tapped tempo — 2026-09-06

*Henri: "take the next slice, the tapped tempo."*  The last of slice
4's tools, and his answer to Q2 built as said: the `.ges` line's
`bpm` edited the way a knob writes its number back, a `.notes` `bpm`
record read only when no `.ges` says.

**`tap`, on `Ctrl-T`** — a chord, because tapping is done with one
finger in time and the palette is three keystrokes a beat.  A tap is a
moment on the wall clock; two or more within two seconds of each
other are a tempo, the mean of their gaps, the last eight counting,
held between 20 and 400.  **`tempo N`** is the written half: in a
`.ges` the literal of its `bpm = …` line is rewritten, and a file with
no such line is refused rather than given one, where it goes being
the author's; in a `.notes` the `bpm` record is rewritten, or written
on line 1 when the file had none.  `tap` runs `tempo` when the number
changes, so the transcript holds a `tap` whose answer a replay at
another speed will not reproduce — and says so in its report — beside
a `tempo` line that replays exactly.  The records road plays a lone
`.notes` at its own tempo now, where it went at the wrapper's constant
before.

**Measured, headless:** four taps half a second apart write `bpm 120`
on line 1 of `arc.notes` and then have nothing to do; a pause and two
taps a quarter second apart rewrite it to `240`; on `arcnotes.ges`,
`tempo 120` rewrites `bpm = 92` on line 158 and nothing else, and a
file whose `bpm` line is gone is refused.  Six tests under *the tapped
tempo*.

**Driven, and the first run was wrong by fifteen percent.**
`test/driven/20260906-163649-notes-tapped-tempo` on the desk that ran
it: four `Ctrl-T` half a second apart, and the file said `bpm 102`.
The model stamps a tap when it reads it, and a `tempo` had been
auditioning synchronously — a changed `bpm` is a changed engine, a
rebuild — so the model's thread was held through the next tap.  The
coalesced audition the typing road already uses waits for the hand to
stop and works on its own thread; through that door
(`…163812-notes-tapped-tempo`) the same four taps read `bpm 121`, and
the rest of the file untouched.

**What this slice does not do, said now.**  A tap's answer depends on
the wall clock, and a replayed transcript will say another number
where the `tempo` beside it replays exactly.  The tempo is one number
for the file: no tempo change inside a piece, which `tempo.md`'s
envelope can say in a `.ges` and this record cannot.  And a `.ges`
with no `bpm = …` line is refused rather than given one.

### The picture computed, not written — 2026-09-06, evening

*Henri, on the page's program having grown to eighty thousand
characters:* **"Se että G-kone ne laskee olisi hieman parempi kuin
että python kirjoittaisi suuret määrät .ges tekstiä."**

The growth was unrolled repetition: 128 columns, 42 keys, 42 rows, 40
lines, each its own expression written by Python.  Now the editing
scale's furniture, ruler and columns are **recursion in the program
over a few numbers** — `_generated`: the range of keys, the span, the
beat, the bar lines, the geometry — with `y_of`, `x_of` and `hands_of`
restated to the integer, and the words the vocabulary cannot compute
(a key's octave, a bar's number) as case tables.  The ground and the
hands are top-level constants, so the G-machine computes them once and
every frame of a drag shares them; inside the picture function they
were rebuilt at every application.

| `arc.notes`, one section, live page | unrolled | computed |
|---|---|---|
| the program's text | 85,233 chars | 51,273 |
| compiled once | 4.4 s | 1.75 s |
| the first picture, once per rebuild | 84 ms | 410 ms |
| a drag's frame, three measured | 90 ms | 80 ms |
| picture and hit table | — | item-identical, 248 and 130 |

**Where the rest of the text is**: the channel declarations, one line a
column; the note-drawing functions, once per box of the page; and the
same generator definitions once per box, numbered by box.  Sharing one
copy across the boxes — a module the roll's program imports, which the
canvas prelude has no door for yet — is the next halving and is idea 2
of the evening's list, not built.  Idea 4, a `Many` constructor for a
list of pictures, turned out unnecessary here: the parser's depth was
the problem and recursion at run time never shows it a chain.

### The roll's vocabulary is a library — 2026-09-06, evening

*Henri: "Tehdään sitten se idea 2, moduuli."*  The evening's second
idea: the drawing written once, as functions of a box's few numbers,
and the page's program reduced to the numbers.

**`gestate/roll.ges`**, in front of a program that draws a roll —
`audio.preludes` puts it after `gui.ges` when the program declares a
`Body`, which is the library's own type and a hand-written canvas never
names — so the staged front end caches its analysis as one more head
and a page's compile pays for the page's own lines.  What it holds:
`Body` and `Scale`, the editing scale's three numbers stated for
themselves and held to `scorebox`'s by a test, `rollY` and `rollX`
(`y_of` and `x_of` to the integer), the furniture, the ruler, the
columns (`hands_of` restated), the notes with their marks, the band
and the section's end.  What a box's program still says:
its channels — one a column, which is what crosses — its `Body`,
`Scale`, beat and bar lines, the ground and the hands as constants,
and one picture lifted over its readings.  The compact box beside a
`.ges` line keeps the program it had, item-identical.

| `arc.notes`, one section, live page | unrolled | computed | library |
|---|---|---|---|
| the program's text | 85,233 chars | 51,273 | 32,136 |
| compiled once, cold / warm | 4.4 s | 1.75 s | 2.2 / 1.06 s |
| the first picture | 84 ms | 410 ms | 366 ms |
| a drag's frame | 90 ms | 80 ms | 84 ms |
| picture and hits | — | identical | identical |

**What is left in the text** is what differs from box to box and
cannot be a function of anything: a hundred and thirty channel
declarations a box.  A channel per column exists because a press
crosses as a name, and that is idea 3 of the evening's list, his to
decide.

### The body is one pad — 2026-09-06, evening

*Henri: "Tehdään myös idea 3, yksi käsi koko rungon yli.  Jos se yhä
kuulostaa järkevältä sinun mielestäsi."*  It did, and the reason is
the substrate spec's own sentence: *a pad is two on one element.*

**The body is `TouchY pitch (TouchX rail (Sized …))`**, the rail inner
so its press is read first: the fraction of the width is a tick, the
fraction of the height a key, and the model finds the note sounding at
that place — `note_under(roll, tick, key)`, nearest in key among the
notes sounding at the tick, ties to the earlier onset, beyond
`BAND_REACH` or at a tick nothing sounds at being empty roll.  The
columns this replaces — one `TouchY` a tile, 48 in the compact box
and 128 on the page — existed because a press wrote one attachment
(F204); they quantised the aim to a tile, cost a channel declaration
each, and could refuse a key *a column sounds twice*.  A note's end
is its last `EDGE_PX` pixels now, for a note wider than twice that,
where it was its last column.  Both boxes take the pad, the compact
one too, and both pictures are item-identical to before; the hit
table of a page's box went from 130 to 3, the ruler, the rail and
the pitch hand.

**A note is named by where it sounds.**  `transpose`, `mark` and
`resize` took a column and a key; they take a tick and a key now —
`transpose <hand> tick was key` — which is what the file and the
picture agree on, and a chord is as many names as it has keys.  No
tracked transcript held the old shape.  The model's grab is in two
halves that arrive in order: the rail's press holds a tick and names
no note, the pitch hand's press finds the note there and fills the
rail's grab in; a rail let go alone writes nothing.

| `arc.notes`, one section, live page | morning | library | pad |
|---|---|---|---|
| the program's text | 85,233 chars | 32,136 | 8,193 |
| compiled once, warm | 4.4 s | 1.06 s | 0.36 s |
| hits a box | 130 | 130 | 3 |
| picture | — | identical | identical |

### What plugin-like scopes

*"I'd like plugin-like, reusable behavior for this feature.  I think
that already scopes it a bit."*  The tree uses the word for two things
and his 2026-09-04 sentence for a third, so the reading is written down
rather than guessed at, with a default:

1. **A file kind is a registration, not a branch.**  Today
   `audioeditor.py` decides a file by suffix in one set (`INERT`); the
   view makes that a table — suffix → how it builds, what its picture
   is, which commands it adds — and `.notes` is the first row.  The
   next sub-language (`.manner` was named) is a second row and no new
   seam.  *Suspected to be what he means; the default.*
2. **Reusable across hosts, and it is free.**  The page is a
   substrate, and `shell/panel/src/substrate.rs` walks any substrate
   for the CLAP plugin as the editor does — so the same view draws in
   a DAW without a line written for it.  Taken as a dividend, not a
   goal.
3. **A separate window that pops up**, his 2026-09-04 phrasing — a
   second front end.  *Not taken unless he says so*: it is the second
   source of truth the workbench refuses twice by name, and the atlas's
   wire checks would not reach it.

**Trigger:** if undecided, 1 with 2 as it falls out, and the first
slice is the roll's `selected` channel and `onTouchX` in the box that
exists, because those are the same code under every reading.

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
