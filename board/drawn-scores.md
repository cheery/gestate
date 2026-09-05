# drawn-scores — a graphical score format with .ges's whole power

    status   doing — 2026-09-05.  Off the shelf at his word, the spec
             written, and **the first slice built the same day**: the
             parser, the `include` door, `arc.notes`, and 219 notes of
             `arc.ges` played from a flat file — §"Day one, landed".
             What is left is the roll
    because  "Minä koin että .ges tiedoston muokkaaminen näkemättä mitä
             on tekemässä oli aika raskasta hommaa. .ges on hyvä
             formaatti syntetisaattoreihin, mutta ehkä ei sittenkään
             sitä mitä haluaisi musiikkinotaatiolta." — writing a score
             is done blind, in MIDI numbers and duration arithmetic,
             and nothing sounds or draws until a render is asked for;
             said the day it was paid for, over together.ges
    asked    Henri, 2026-08-29 (Claude wrote the card at his ask)
    see      spec/drawnscores.md — the contract, written 2026-09-05
             doc/notes/notes-on-writing-a-piece.md — the piece written
             by hand to find out what a format has to carry
             doc/memory/ges-is-not-music-notation-yet.md — the verdict
             doc/memory/the-language-goal.md — optimised for reading,
             easy to model-check; both bear directly on this
             examples/audio/together.ges — the sitting that found the pain
             examples/audio/arc.ges — the piece the format has to beat
             spec/scorebox.md — the roll that draws, today, as a *view*
             spec/annotations.md — the mark the voice interprets, built

**What this is:** *(rewritten 2026-09-05, when the card came off the
shelf; the paragraph it replaces is at §"What this was, while it was
shelved".)*  The card for a **flat note file** — a sub-language a `.ges`
score includes, holding the part of a piece that is data, poor enough
that a simple editor can own it whole.  `spec/drawnscores.md` is its
contract.  **What it is not:** a graphical format, and not a format with
`.ges`'s full power — the ask it arrived as, which its own author has
since withdrawn (§"The restriction is the design").  Not a replacement
for `.ges` synths, which he judged good.  **When it runs:** at assembly,
like a prelude — and it is not built.  What stands today is the spec and
the piece it has to beat.

## The ask

> .ges:in hieno piirre on että sillä pystyy tekemään loputtomia
> träkkejä, sekä sellaisia jotka muuttuvat ja elävät. mutta olisiko se
> mahdollista tehdä graafinen formaatti jolla on täysin samat
> ominaisuudet?

And, on where this card should live:

> kirjoita tuo graafisen formaatin idea jonnekin puuhun, ehkä me voimme
> jokin päivä kokeilla tätä ideaa.. ehkä se voisi olla kortti later/
> -taulussa.

## The idea, as said in the room

**The picture must denote a program, not a recording.**  A piano roll
in the ordinary sense is data — a finite list of events — and no such
format can be endless or alive, because nothing in it *generates*.
What makes `.ges` scores endless and living is not the note syntax but
the combinators: `cycle`, `unfold`, `draw`, `sown`.  In `together.ges`
the split was visible in the file: the phrases were finite data, all
the structure came from the operators between them.

That split gives the format two layers, and each solves one half of
the problem:

* **Leaf level: phrases as rolls.**  A finite phrase is exactly what a
  piano roll draws well — seen, dragged, audible on a click.  This is
  the half that was written blind as numbers.
* **Structure level: a graph between phrases.**  An arrow is `++`,
  side-by-side is `||`, a loop edge is `cycle`, a weighted branch is
  `draw` with the probability written on the arrow, a transform node
  on an edge is transpose / thin / reverse.  Endlessness is *a loop in
  the picture*; living is *a weighted edge in the picture*.

**Within that boundary the properties are exactly the same**, because
the picture compiles to the same `[: a :]` expressions the dynamic path
already plays — a new drawable syntax for the existing algebra, no new
semantics.  *The bold claim that stood here until 2026-09-04 was that
they were exactly the same **without** a boundary, and that is the
sentence its author struck; §"The restriction is the design" is what
replaced it.*  And the picture is the *source*, not a view that can
disagree, which is the second-source-of-truth mistake this project has
twice designed against.

Two honest caveats, said at the time:

1. **"Täysin samat ominaisuudet" at the full language's power** means
   drawing arbitrary functions — recursion, `case`, `do` as boxes.
   That is a visual programming language, and those are historically
   *worse text* by the very measure the language goal sets: optimised
   for reading.  Max/PD prove endless-and-living works graphically,
   and prove what unreadability looks like.  The boundary worth
   drawing: phrases and structure as picture, everything else stays a
   `.ges` expression inside a box.
2. **The restriction buys analysis back.**  A finite phrase graph with
   weighted edges is a Markov chain: reachability (does the piece ever
   reach the outro?), expected length, a bank's worst-case voice count
   — decidable on the graph, undecidable on general programs.  *Easy
   to model-check*, in his own goal's words, is a property the
   restricted picture has and the full language does not.

**A constraint, his, 2026-08-29, the day after the card:**

> Formaatin pitäisi olla sellainen että sinäkin, tekstillisenä
> olentona, pystyt sitä muokkaamaan.

The format must be one a session — a textual being — can edit too.
That decides more than it looks like: the *store* is text, and the
picture is a projection over it — an editor, not the format.  A
"graphical format" whose storage is a picture would end the duet that
made `together.ges`; a textual graph notation that the workbench draws
and lets him drag, while a session edits the same file as text, keeps
both hands on one source.  It is also this project's standing shape
already: the window draws beside declarations and invents no
furniture, so the roll and the graph would be drawn beside the text
that means them — and the second-source-of-truth danger above is not
merely avoided but structurally impossible, because there is only the
text.

Nearest existing relatives, for orientation rather than imitation:
Ableton's session view with follow actions (a clip grid that is a
drawn Markov chain, but not composable into a language), and tracker
order-lists (the same idea, poorer).

## The restriction is the design — 2026-09-04

**Henri, re-reading the sitting this card was written from**, and
withdrawing the ask it was written for:

> *"alkuperäinen ideani siitä että formaatilla olisi täysin samat
> ominaisuudet, ei oikeastaan toimi.  Jotta formaatti on
> käyttökelpoinen, sen täytyy olla rajattu johonkin jota sellaisella
> tekee hyvin."*

So the restriction is not a caveat on the design, it **is** the design,
and the card had it the wrong way round: it led with *täysin samat
ominaisuudet* in bold and demoted the boundary to a reservation
underneath.  That is this board's own most expensive lesson arriving in
a new place — a card that leads with the ambition hides the finding,
and the finding is the part a reader can build.

**What the ask was and what it becomes.**  *Would a graphical format be
possible with completely the same properties?* — answered, and the
answer is no in the way that matters: possible, and unusable, because
full generality means drawing recursion, `case` and `do` as boxes,
which is a visual programming language and worse text by the very
measure the language goal sets.  The question this card now carries is
the one worth money: **what is the thing such a format does well, and
where exactly is its edge.**

## Measured against the piece that produced the pain — 2026-09-04

*A session's measurement, and it reaches the same conclusion from the
other side.*  This card rests on `together.ges`, and the card claims
the split was visible there — *"the phrases were finite data, all the
structure came from the operators between them."*  Half of that holds
and the other half is where the design question actually lives.

**The leaf level is as described.**  Thirteen named phrases, each a
finite list — `scoreLead "intro" = '65 ++ (quad ('54 ++ '52)) |/ 8 ++
'65 ++ '77` — which is exactly what a roll draws well.

**The structure level is not a graph of phrases.  It is function
application.**

    (sing "intro" 100 || padc 50 57 62 || hatBar || walk 38 45)

`padc a b c` takes three pitches, `walk` takes two, `sing` a name and a
velocity.  So a node cannot be a phrase; it is a *function with its
arguments*.  That is the boundary question made concrete: **is a node
`padc 50 57 62`, or is `padc` a node with three drawn inputs?**  The
first stays readable and gives up composition; the second is Max/PD,
which caveat 1 already names as the failure.

**And `together.ges` is neither endless nor living:**

| combinator | uses in `together.ges` |
|---|---|
| `cycle`, `unfold`, `draw`, `sown`, `chance` | **0, 0, 0, 0, 0** |
| `++`, `\|\|`, `\|*`, `\|/`, `>>=` | 70, 77, 19, 8, 12 |

The piece that produced the complaint is finite and deterministic
throughout.  **So the pain and the ambition are two different
problems**, and the card had fused them: what was written blind was a
fully-written-out finite score, and endlessness was wanted from `.ges`'s
general capability rather than from anything this piece needed.  Which
is the same verdict as the section above, arrived at by counting
instead of by re-reading — and it says which half to restrict *to*.

## What the notation turned out to be — 2026-09-04

**Henri, thinking it through at the terminal:** *"I think that I'd want
something like a real score-notation, with annotations.  But it could
be simplified somehow."*  And on what an annotation is for, given three
readings — exact (a number with a pretty face), inert (a comment), or
**a hint an interpreter reads** — he took the third: *"I think the
third option would be interesting."*

**That is the one that makes it notation rather than syntax**, and his
own instrument is the argument.  He plays violin, three years, and on a
violin staccato is not "shorter" — it is a bow stroke whose shortness
is a *consequence*; accent is bow speed and pressure, not a velocity
number.  A pad voice has no bow.  So a mark compiling to `duration ×
0.5` would be wrong for the violin **and** wrong for the pad.  A mark
names an **intention** and each voice realises it in its own terms,
which is what an orchestra does and what `lantern.ges` already says of
its own notes: *the score decides which step, the voice decides what
that sounds like.*

**And it needs no new language mechanism.**  The payload is the
author's datatype and the voice already pattern-matches it, so the work
is convention, drawing and gesture.  Henri picked the convention over
the per-file field — *"2. convention the tree names once"* — for the
reason he gave a paragraph earlier: **the score has to be readable by a
session too.**  With a per-file field, *readable* means parseable; with
a named convention it means understood.  `audio.ges`'s `Notable a`
class (`noteKey`/`noteVel`) is the same move already made once, and is
the shape to copy.

**Three marks, his: staccato, accent, portamento.**  The type is
`Manner` — his pick, and `Mark` was unavailable because `Score a`
already spends it on `Mark String`, a named point zero wide.

**Both roll and staff**, and his reason is better than the `because`
this card was written with: *"what I have available changes what I
create.  I've noticed that when working on score."*  The tool has been
shaping the music and he can feel it.  The roll is standing and already
writes back (`spec/north_star.md`, built); the staff is a second
renderer and the expensive half, so marks land on the roll first and
the staff is its own slice.

**And a preview tone**, his ask — which is half built: `north_star`
acceptance 5 already gates *the sound moved with it*, and
`session.py`'s transpose sounds where it was dropped.  The gap is that
it sounds **only while something is playing**; annotating is not
performing, so the stopped case is a decision the spec owes.

### Points, not spans — a session's call, 2026-09-04

Asked whether a span mark like portamento is stored as a span or as a
point, Henri said *"I don't know.  answer to this one."*  So this is
the session's, marked as such.

**Points.  A span is a pair of points, and the drawing pairs them.**
Lilypond attaches slurs to notes, MusicXML writes `slur type="start"`
and `type="stop"` on two notes, MIDI has only events at points; the
field converged here.  `spec/editor.md`'s law admits a field of one
constructor and not a relation between two.  And `manners : a -> [Manner]`
is a function of one payload, as `Notable a` is.

**The decisive one is the algebra.**  `Score a` carries `Retro`
(reverse), `Sow` (re-root a seed) and `Draw` (the notes are not known
until a seed arrives).  **A span stored as "note 3 to note 7" has no
stable referent under any of them** — reversed it dangles, re-sown the
notes differ, drawn they do not exist yet.  A point mark rides with its
payload through all three for free: reverse the phrase and *slide into
this note* still means slide into this note, arriving from a different
predecessor, which is musically right.

*The cost, stated rather than discovered:* a chancy score can produce a
start whose stop never comes.  **An unpaired start ends at its `Clip`
boundary** — `long n s` already declares a span, so the score's own
bracket supplies the ending, and an unclosed crescendo is defined
rather than refused.

*And the one that reaches furthest:* portamento constrains **voice
allocation**.  Staccato and accent are read entirely inside the voice
function; a slide needs the *same* voice to carry both notes or there
is nothing to slide from.  `slew` exists (`synth.ges:335`) and
`violin.ges` already plays a portamento violin, so there is a working
reference to hold a spec against — but this mark is the expensive one
of the three and belongs last.

## The editing surface, measured — 2026-09-04

*Three slices of `spec/annotations.md` were built on the score box's
gesture before anybody counted what that gesture reaches.  Henri, after
them:* **"the scorebox and existing north_star is a cool demo, but
doesn't solve many things that one meets in a full fledged note editing
tool.  Also we still have the problem that it's just as inaccessible
for editing as what it supplements."**  The count says he is right.

| piece | notes | the box can edit | why not |
|---|---|---|---|
| `noted.ges` | 4 | **100%** | |
| `minute.ges` | 16 | **100%** | |
| `chopin.ges` | 140 | **100%** | |
| `moon_sonata.ges` | 120 | **5%** | 102 not written, 11 ambiguous |
| `undertow.ges` | 366 | **0%** | 366 not written |
| **`together.ges`** | — | **will not draw** | *No instance for Notable Key* |

**The three at 100% are the files written for the box.**  On real
pieces it is 0–5%, and the file this card's `because` came from does
not open at all.

**Why, precisely.**  The descent carries provenance *to the leaf* — it
knows which written region produced a note — and then inside that leaf
it **guesses by value**: the pitch is whichever literal equals the
note's key (`pitch_atom`, whose own docstring records that the
positional rule refused four files in five).  Where a pitch is
computed, no literal equals it and the answer is *not written*.

**And the deeper version: some notes have no written pitch at all.**
`keyHz (57 + stepOf d)` means the author wrote a **degree**.
`pitch_atom` is looking for the wrong thing — not *where is this pitch
written* but *what did the author write that this note came from*,
which may be a degree, a velocity, or an index into a table.

## Refused: provenance through the computation — 2026-09-04

The obvious repair is to carry provenance *through* the arithmetic, so
a note from `quad ('54 ++ '52) |/ 8` points at `'54`.  **Henri: "lets
forget about provenance idea.  It's the sauce that is least likely to
work everywhere."**

**And the reason is sharper than unlikely — it cannot work everywhere.**
A pitch computed as `45 + stepOf d` has no single literal to point at:
the degree is written, the pitch never is.  So provenance would answer
on the easy files and fail on the rest, which is the worst shape a
feature can have — a gesture that works until it silently does not.
Recorded here rather than deleted, because it is the first thing the
next person will think of.

## The direction: a sub-language, included — 2026-09-04

**Henri, proposing it:** *"we create a sub-language meant to be
editable by simpler editor.  Manner is in that direction already.  And
we would include these sub-language files by `(include "thing.manner")`
or similar, into the score.  The layouter references the files relative
to the score that included them.  and we create a format that is
LLM-friendly, and specific editor support for editing these files,
maybe a separate editor view that pops up for them.. or maybe something
pluggable.. a plugin."*

**This is not the second source of truth this card refused earlier**,
and the difference is worth stating because the earlier refusal reads
as if it covered this.  A phrase file is not a second *rendering* of
something the program also says — it is the only place those phrases
exist.  That is a module boundary, and two files that each own their
content cannot disagree.  The constraint of 2026-08-29 is kept whole:
the store is text, and a session can edit it.

**What is standing, and it is more than half.**  The language has **no
source include** — `open` is an editor command — so `(include …)` is
new.  But `audiospans.py` already merges `prelude.ges` as a *module*,
parsed separately, *"so its spans are in its own coordinates and start
again at 1"*, and every `Site` names its file and carries a line
**within that file**.  Multi-file provenance — an error or a gesture
pointing at the right line of the right file — is built.  What is
missing is the door.  And resolving a path relative to the including
file is solved too: `session.py` does it for `open`, nearest first.

## What is decided, and what is not

**1. What a phrase file is for** — one voice's line, or a bar across
voices?  **Answered 2026-09-05, and the experiment is what answered
it.**  *Henri, given both shapes:* **"I think it could contain several
sections, voices side by side, yeah."**  So a file holds several
sections and a section holds its voices side by side on one declared
bar grid — `spec/drawnscores.md` §"What is decided" 1.

*The deferral it replaces, and it worked:* **"we should experiment and
write something together, then consider how it would happen with this
new format."**  The experiment was `arc.ges` and
`doc/notes/notes-on-writing-a-piece.md`, and W5 and W8 came back from it
— five lines aligned by nothing but their length, and *"if one of them
had twenty-three bars the piece would still compile."*  That is the
answer arriving from the work rather than from taste, which is what the
deferral was for.  §"The idea, as said
in the room" already names the two relatives to look at while doing it:
the weighted phrase graph as a Markov chain, and Ableton's session view
with follow actions — *the DAW whose name he could not recall, named
here so the next reading does not have to.*

**2. Flat, and the tuplet is the test.**  *Henri:* **"I'd like flat,
but only if it allows writing triplets/tuplets.. or then we say how the
staff is subdivided in each bar, and imitate musical notation / come up
with good-enough notation based on that grid."**

*And the tree already answers the second half.*  `midi.TICKS_PER_BEAT`
is **96**, and `spec/music.md` chose it *"because it divides by 2, 3,
4, 6, 8, 12, 16, 24, 32 and 48"* — a grid that carries triplets and
tuplets as whole numbers, with no fractions in the format and no
special case in the editor.  So flat **and** tuplets is not a trade;
the subdivision he proposes as the fallback is the one the tree already
counts in.

**3. What the score gets back** — a `[: Tone :]`, which needs the
author's payload type, or something generic the score adapts?  *Open,
and deliberately:* **"I think we need to see that first, how it turns
out naturally from what we have."**

*Looked at 2026-09-05, and `spec/drawnscores.md` §"What the score gets
back" carries the answer with its reasoning:* `Notable` reads a payload
and `FromMIDI` builds one from a keyboard, so the shape that turns out
naturally is `FromMIDI`'s sibling for the road a note file travels —
`fromNote key level manners` — because a keyboard cannot send a manner
and a note file can.  **Marked as the session's derivation, and named
in that spec as the part most worth striking**, since the deferral was
his and this is not him answering it.

**4. LLM-friendly, as gates rather than as an adjective.**  *His:*
**"lets make it testable on your requirements."**  The session's four,
each checkable:

* **one note per line** — an edit is a line, so a diff is the edit;
* **every field named, never positional** — the failure that made
  `manner` unfindable was two fields of one shape telling apart only by
  position;
* **no significant whitespace and no nesting** — a format whose meaning
  survives being reflowed by anything;
* **a stable order** — two writings of one phrase are byte-identical,
  so a diff shows what changed and nothing else.

## What the first piece found — 2026-09-04

*Written with him, logged in `doc/notes/notes-on-writing-a-piece.md`.
Eight frictions, and **one result that bounds this card**.*

**The eight are real and a format fixes them.**  The load-bearing ones:
a note cannot carry its own **length**, so two durations cannot sit
side by side without a bracket and the first pass came out with no
rhythm at all; the **bar** is not a thing, so a fifth note in a bar
compiles and shifts everything after it; and five voices ended up
**aligned by nothing but their lengths**, which is the plainest
requirement of the day — *a format holding voices separately must know
they are the same bars*.

**And the one that bounds it:** he took a MIDI keyboard and a DAW and
tried to write the same modal passage himself, and **could not
either**.  So the thing four passes were spent on — *the modes do not
land* — **is not a notation problem**: it stayed hard in the tool where
format and editor are already solved.  A future reading must not take
it as a requirement on this card.

**What did move it was measurement**, every time and always too late:
0 thirds in 24 bars, 46% of a bar's harmony gone by its end, 4 of 8
bars offering a perfect fifth to rest on, 3 of 32 notes touching the
tonic.  *A DAW gives you your ears and nothing else, and so did
gestate* — a session wrote each check by hand after his ear had already
found the fault.

*Which suggests a different thing to build than this card was going
toward*, marked as a proposal: **a box that answers a musical question
about the span it covers**, the way the score box draws one.  The
evidence is the wrong way round — every check was written after the
listening — so the next move is to pick a check **before** listening
and see whether it names the fault first.

## Questions

*Three stood here while the card was shelved.  All three are answered
as of 2026-09-05, and the answers are what made a spec writable —
kept below with their answers under them rather than struck, because
the reasoning is the part a reader can argue with.*

**A — where the picture ends and the expression begins.**  *Answered by
the format:* everything that **generates** — `cycle`, `unfold`, `draw`,
`sown`, every function and every combinator — stays in `.ges`, and a
`.notes` file holds only the leaves.  It is finite and deterministic by
construction, which is the boundary drawn at the one place it can be
stated in a sentence instead of by taste.  §"The restriction is the
design" said there must be a boundary; this is where it fell.

**B — what a session does on day one.**  *Answerable now, where on
2026-09-04 it was blocked on a decision:* write the parser and the
`include` keyword, rewrite `examples/audio/arc.ges` as `arc.notes`, and
hold the two to **sample-identical** audio.  `spec/drawnscores.md`
§"Acceptance" is the seven-item list, and item 6 is the one the format
exists for.

**C — what the restricted thing is worth doing well.**  *Answered, and
it is a number rather than a preference:* the score box can edit 0–5% of
the notes in a real `.ges` piece and 100% of the three files written for
it, because provenance is guessed by value.  A note file makes the
question disappear — a note **is** a line — so the answer is **the file
every note of which is editable, forever, by construction**.  The other
candidate this question named, the weighted phrase graph, is untouched
and no piece he has written needs it.

*The three as they were asked:*

* **Where exactly does the picture end and the expression begin?**
  The hard part is not endlessness or living — one edge each — but
  this boundary, and it is language design and taste: his, and named
  by him as needing peace.  Two answers have arrived.  *2026-08-29:*
  wherever it falls, the store is text, because a textual being must
  be able to edit it too.  *2026-09-04:* there **must** be a boundary,
  because the unbounded version does not work — so the question is no
  longer whether to draw one but where, and the measurement above puts
  the first hard case on the table: a bar of `together.ges` is a stack
  of *applied functions*, not of phrases.
* What does a session do on day one?  Suspected answer: a compiler
  from a small graph description to `[: a :]` score expressions,
  proven against `together.ges` rewritten as a graph — the semantics
  exist, so the first day is syntax and a parity test.  Marked
  *suspected*.  **The first piece of the elaboration was done on
  2026-09-04** and is the section above; what it found is that
  `together.ges` cannot be rewritten as a graph of phrases without
  first answering the boundary question, so day one as written is
  blocked on a decision rather than on work.
* **What is the restricted thing worth doing well?**  Added 2026-09-04,
  and it replaces the withdrawn ask.  Two candidates the tree can
  already argue about: the *finite phrase roll* — which is the pain he
  actually reported, and which `spec/scorebox.md` half-draws today as a
  view that cannot be edited — and the *weighted phrase graph*, which
  is the Markov-checkable object caveat 2 describes and which no piece
  he has written yet needs.  Naming which is his.

## Shelved, 2026-08-29

Arrived shelved, at his word — *"ehkä me voimme jokin päivä kokeilla
tätä ideaa"* — and it waits on an event rather than a queue: his
thinking, which he reserved for himself the day before this card in
the same breath as the `because`: *"Tätä täytynee miettiä silleen
rauhassa."*  It comes back the way every card does: by him saying so.

## How it came off the shelf — 2026-09-05

**By him saying so, which is the only way a card comes back.**  *Henri,
opening the sitting:* **"Today lets lift the card:drawn-scores.md out of
later/ and write a spec for drawn-scores.  I discussed this yesterday
with a session and I think we got somewhere."**

**And the event it was waiting on had happened.**  §"Shelved" says it
waits on his thinking, reserved for himself — *"Tätä täytynee miettiä
silleen rauhassa"* — which is sediment and not debt, and it wakes when
the thinking is done rather than when somebody asks again.  It was done
on 2026-09-04: the ambition withdrawn, the notation named, the
sub-language proposed, and the four gates asked for.  This card is
**five sections longer than the day it was shelved**, and every one of
them is his thinking arriving.

**What was left after that was three decisions**, put to him in one
batch on 2026-09-05 and answered in one pass — the file's grain, pitch
against degree, and how far the spec goes.  They are transcribed at
§"What is decided, and what is not" and at `spec/drawnscores.md` §"What
is decided", in his words.

**Where it stands in the priority: unplaced, at the end**, which is what
`board/README.md` §"Who writes what" says a card does when it arrives.
It is below the three that were already there and he can move it in a
sentence.

## What this was, while it was shelved

*The front paragraph this card carried from 2026-09-04 to 2026-09-05,
kept because the card's own shape is part of its argument — it led with
a sketch, and what replaced it leads with a file.*

> **What this is:** a sketch of a drawable score format, **deliberately
> restricted**, that makes the writing visible.  **What it is not:** a
> format with `.ges`'s full power — the ask it arrived as, which its own
> author has since withdrawn (§"The restriction is the design").  Not a
> feature request with a design ready to build, and not a replacement
> for `.ges` synths, which he judged good.  **When it runs:** never yet;
> it is an idea to try some day, and it arrived shelved.

## Day one, landed — 2026-09-05

**Henri:** *"lets build it — parser, include, arc.notes."*  All three,
and `spec/drawnscores.md` §"Acceptance" is the contract they are held
to — 32 tests, green.

| | |
|---|---|
| the parser, the refusals, the expansion | `gestate/notes.py` |
| eight dynamics and the road in | `gestate/audio.ges` — `Ppp`…`Fff`, `loudness`, `class FromNote` |
| the notes | `examples/audio/arc.notes` — 219 of them, 246 lines |
| the piece that includes them | `examples/audio/arcnotes.ges` |
| the acceptance | `test/test_drawnscores.py` |

**The number the card exists for:** `arcnotes.ges` plays **219 of
`arc.ges`'s 219 notes** at the same tick, for the same length, on the
same bank, at the same pitch.  Four hundred and ninety lines of
`'(Tone 0.85 62 0) ++ …` became one `include`.

**And `arc.ges` was not touched.**  It is the exhibit
`doc/notes/notes-on-writing-a-piece.md` was written from, so the two
files stand side by side and the suite holds them to each other — which
is better evidence than a rewrite, because a person can render both.

**What is not identical, and it is the design rather than a shortfall:**
209 of 219 velocities moved, by at most 0.050.  `arc.ges` writes sixteen
raw floats and the format writes eight named dynamics, which is W4
answered — *"no `mf`, no `p`, nothing a reader can check or a second
writer can match."*  Both numbers are asserted, because a design that
quietly moved a piece would be indistinguishable from a bug.

**Four things the building found**, in `spec/drawnscores.md` §"What the
building taught": the include door leaks to any tool that reads a file
directly and now says so instead of blaming the author's line; `arc.ges`
writes a whole voice its score never plays (`fixme.md` **F198**, and the
repair is his); and the mode lamp's first run found a **67** in a
lydian section, which is W2's own sentence answered in its own numbers.

**And the fourth is his, and it was three defects rather than one** —
found within the hour by opening the file and then trying to play it:

> *"arcnotes.ges … I don't find the `include` there in other than
> comments."*
>
> *"It shows that it's not auditioned at the start.  And when I try to
> audition it, it gives me an error."*

The expansion had been put on `Workbench.source()`, which fills the
editor's text buffer as well as feeding every compiler — so **the window
showed a program he had not written** and a `Ctrl-S` would have made it
true.  Then `apply`/`audition` are handed that buffer, so the
assembler's guard fired on the one gesture the editor exists for.  And
`behind()` compares the buffer to what was built, so storing the
expanded text there said *behind* forever.

One cause, three faces: **expansion introduces a second text, and every
field and method that held "the program" has to say which of the two it
means.**  `source`/`program`, `_built_from`/`_built_program`, and
`_built` expanding before it compiles — six tests on the split, four of
them driving the editor rather than a compiler.

**The suite was green over all three**, twice, because nothing in it
opened the file the way a person does.  `doc/memory/test-what-a-person-would-do.md`
is the memory that says so, and it was not enough to have read it.

**What is left is the roll** — `spec/drawnscores.md` §"The slice after".
Acceptance 6 was narrowed on purpose and says so: what is executed is
that every sounding note has one line that wrote it and the expansion
carries every one of those line numbers into the `.ges`.  Making the
roll *follow* that map is the next slice, and claiming its number before
the wiring exists would have been a number nobody checks.
