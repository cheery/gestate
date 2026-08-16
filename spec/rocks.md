# rocks.md — what a file weighs, said in one character

*Companion to `spec/workbench.md` §"The list, and the laws it keeps"
(where the marks are read) and to `manifesto.md` §"costs, and where it
is not paid" — its rule that being wrong has to be visible — which this
is a small instance of.  The ask is Henri's, on the evening of
2026-08-15, and so is the occasion: he had committed a
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

## Before it is written, too

The first omission this file recorded is closed (2026-08-16).  **It
weighed what existed and not what was about to**, and an export of
forty minutes is knowable before a sample of it is made: the span, the
rate and the channels are all in hand, and the size is arithmetic
(`session._render_bytes` — 16-bit frames, and the 44-byte header is not
worth a mention at any scale where anybody cares).  So the export says

    about 402.8M ▲, render it? [y/n]

and stops the mistake instead of describing it afterwards.

**At `▲` only.**  A question at every export is a question nobody
reads, which is this file's own argument for three marks rather than a
number.  Under the notable threshold the sentence a render already ends
with — *wrote piece.wav — 31.7M ▪* — is the whole of what there is to
say.

**Known, never guessed.**  The length is the stated bars or the score
the bench has already laid out, the channels are the instrument that is
playing, and the rate is the renderer's own default, because that is
what the export will use.  Missing any of the three it says nothing: a
wolf cried over an invented number is worse than silence, since it
teaches the person to answer `y` without reading.

**A bar range is weighed by what is written, not by what survives.**
`exportWavAt 900 901` renders from the top and cuts the front off, so a
typo in the first number is a quarter of an hour of audio written for
one bar kept — exactly the mistake the question exists to catch, and
weighing the survivor would have said `1M ▪` about it.

**One question, one yes.**  A heavy render over a file that is already
there has two facts worth saying and a single decision to make, so the
sentence carries both — `again.wav exists, about 402.8M ▲ — overwrite?
[y/n]` — and `overwrite` answers both questions, because a second verb
for *go ahead* would be a second word for the same act.

## What it does not do, and would be worth doing

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
5. A render heavy enough to earn `▲` is asked about before it is made,
   an ordinary one is not asked about at all, and a bar range is
   weighed by the audio it writes rather than by the bars it keeps.

Held by `test_a_file_is_weighed_against_what_it_is`,
`test_an_export_says_what_it_made`,
`test_a_render_is_weighed_before_it_is_made`,
`test_a_heavy_render_over_a_file_asks_once` and
`test_a_bar_range_is_weighed_by_what_it_writes` in
`test/test_session.py`.
