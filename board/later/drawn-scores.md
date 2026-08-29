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

**What this is:** a sketch of a drawable score format that keeps the
two properties Henri named as `.ges`'s fine ones — endless tracks, and
tracks that change and live — while making the writing visible.  **What
it is not:** a feature request with a design ready to build, and not a
replacement for `.ges` synths, which he judged good.  **When it runs:**
never yet; it is an idea to try some day, and it arrived shelved.

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

**The properties are exactly the same, not nearly the same**, because
the picture compiles to the same `[: a :]` expressions the dynamic
path already plays — a new drawable syntax for the existing algebra,
no new semantics.  And the picture is the *source*, not a view that
can disagree, which is the second-source-of-truth mistake this project
has twice designed against.

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

## Questions

*Open, for whenever it is unshelved.*

* **Where exactly does the picture end and the expression begin?**
  The hard part is not endlessness or living — one edge each — but
  this boundary, and it is language design and taste: his, and named
  by him as needing peace.  One answer arrived 2026-08-29 and is
  transcribed above: wherever the boundary falls, the store is text,
  because a textual being must be able to edit it too.
* What does a session do on day one?  Suspected answer: a compiler
  from a small graph description to `[: a :]` score expressions,
  proven against `together.ges` rewritten as a graph — the semantics
  exist, so the first day is syntax and a parity test.  Marked
  *suspected*; the elaboration has not been done.

## Shelved, 2026-08-29

Arrived shelved, at his word — *"ehkä me voimme jokin päivä kokeilla
tätä ideaa"* — and it waits on an event rather than a queue: his
thinking, which he reserved for himself the day before this card in
the same breath as the `because`: *"Tätä täytynee miettiä silleen
rauhassa."*  It comes back the way every card does: by him saying so.
