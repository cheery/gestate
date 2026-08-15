# rocks.md — what a file weighs, said in one character

*Companion to `spec/workbench.md` §"The list, and the laws it keeps"
(where the marks are read) and to `manifesto.md` §"make problems
visible", which this is a small instance of.  The ask is Henri's, on
the evening of 2026-08-15, and so is the occasion: he had committed a
**6.5 MB gif of a five-second recording** and found out days later,
from a stranger's clone being slow.  "I am a dummy who uploads a 6MB
gif without a clue of its size."  He was not.  Nothing had ever told
him.*

## The claim

A file's size is a fact the machine has and the person does not, at
exactly the moment the person could act on it.  So the editor says it,
in a number and **one character**:

    wrote dub.wav — 31.7M ▪
    chopin.gif                       213.0K ▪
    a-render-nobody-wanted.wav         2.1G ▲

## The law

> **A size means nothing without knowing what the file is.**

Six megabytes is unremarkable for a rendered piece and absurd for a
picture in a README.  A single scale for both would cry wolf at every
export and stay silent at the one that mattered — which is worse than
saying nothing, because a mark that is always on is a mark nobody
reads.

So the weighing is **by kind**, and every threshold carries the
sentence that justifies it:

| kind | calm below | notable below | the reason |
|---|---|---|---|
| text | 64 K | 512 K | a page is 4 K; a long source file is 40 |
| sound | 32 M | 128 M | a minute of stereo at 44.1 kHz is 10 M |
| sight | 512 K | 4 M | past half a megabyte is a picture somebody waits for |
| else | 4 M | 32 M | a plugin, an object — no opinion, only a scale |

`gestate/session.py`: `WEIGHTS`, `WEIGHT_ELSE`, `KINDS`.

## The marks

    ▪   calm — nothing to think about
    ◆   worth knowing
    ▲   look twice

**Three, and no more.**  A scale a person has to *count* is a number
wearing a costume; the point of a mark is to be read before it is
read.  Three is the smallest set that says *fine*, *note this* and
*something is wrong*, which are the only three decisions the reader
has.

**The ink grows with the number**, and that is the whole of why these
three glyphs.  `▪` is a few pixels, `◆` fills more, `▲` is the largest
shape of the set — so the mark carries its meaning in its *area*,
before the eye reaches the digits.  Henri, seeing it for the first
time: *"They even visually seem different size, telling what size the
file is!"*  It also means the scale survives a terminal with no
colour, and a reader who cannot tell green from red.

## Where it is said, and where it is not

**Where it is said is the point of the whole thing.**  The file dialog
already showed sizes, and the dialog was never where anything went
wrong — nobody browses to a file to learn how big the thing they just
made is.  The writers were the silent ones:

* an export answers with what it wrote and what that weighs;
* a transcript says its weight beside how many steps it holds;
* a listing's note carries it for every row.

**Not on `save`.**  A source file's size is almost never news, and a
word added to the sentence a person sees most often is the kind of
noise that teaches them to stop reading the status bar at all.

**Not in colour**, though colour was the first idea.  A row in the
palette is already coloured by its *kind* — `type`, `class`, `value`,
`operator` — and a second meaning on the same channel makes both
unreadable.  If weight is ever to be coloured it needs a field of its
own beside `kind`, and the shape stays regardless, for the terminal
and for the eye that cannot use the colour.

## What it does not do, and would be worth doing

* **It weighs what exists, not what is about to.**  An export of
  forty minutes is knowable *before* it is rendered — the span and the
  rate are both in hand — and a sentence that said `about 400M ▲,
  render it? [y/n]` would stop the mistake instead of describing it.
  The overwrite question already has that shape.
* **A sound's honest measure is its duration.**  `31.7M` is right and
  `3:00 at 44.1 kHz stereo` is what a person means; the bytes are a
  proxy for a proxy.  The mark hides the difference well enough that
  this has not been worth the plumbing, and it will be the day
  somebody renders at a rate they did not intend.
* **Nothing weighs the *repository*.**  What actually bit was a
  commit, not a file, and git's own answer (`git gc` took this tree's
  `.git` from 100 MB to 43) is outside anything the editor sees.  A
  mark on the file was the part that belonged here.

## Acceptance

1. The same number reads `▪` as a rendered piece, `◆` as a plugin and
   `▲` as a picture — one call, three verdicts.
2. Every command that writes a file says what it wrote and what that
   weighs, in the sentence that reports the write.
3. A file that is not there weighs nothing and says nothing, rather
   than guessing.
4. The marks are legible with no colour at all, which is the only
   rendering the status line has.

Held by `test_a_file_is_weighed_against_what_it_is` and
`test_an_export_says_what_it_made` in `test/test_session.py`.
