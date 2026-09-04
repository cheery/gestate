# drawn-scores — a graphical score format with .ges's whole power

    status   shelved — 2026-08-29
    because  "Minä koin että .ges tiedoston muokkaaminen näkemättä mitä
             on tekemässä oli aika raskasta hommaa. .ges on hyvä
             formaatti syntetisaattoreihin, mutta ehkä ei sittenkään
             sitä mitä haluaisi musiikkinotaatiolta." — writing a score
             is done blind, in MIDI numbers and duration arithmetic,
             and nothing sounds or draws until a render is asked for;
             said the day it was paid for, over together.ges
    asked    Henri, 2026-08-29 (Claude wrote the card at his ask)
    see      doc/memory/ges-is-not-music-notation-yet.md — the verdict
             doc/memory/the-language-goal.md — optimised for reading,
             easy to model-check; both bear directly on this
             examples/audio/together.ges — the sitting that found the pain
             spec/scorebox.md — the roll that draws, today, as a *view*

**What this is:** a sketch of a drawable score format, **deliberately
restricted**, that makes the writing visible.  **What it is not:** a
format with `.ges`'s full power — the ask it arrived as, which its own
author has since withdrawn (§"The restriction is the design").  Not a
feature request with a design ready to build, and not a replacement for
`.ges` synths, which he judged good.  **When it runs:** never yet; it is
an idea to try some day, and it arrived shelved.

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

## Questions

*Open, for whenever it is unshelved.*

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
