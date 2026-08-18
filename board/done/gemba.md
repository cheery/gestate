# gemba — walk the factory floor

    status   done — 2026-08-18 (items 1–2; 3–5 named below)
    because  today I read sixteen commit messages Claude wrote; I want
             to be where the work is while it happens
    asked    Henri, 2026-08-16
    see      spec/scorebox.md, spec/panel.md — content boxes are the
             drawing half, already built
             gestate/session.py:446 — the colouring cache
             card:git-viewer.md — the second idea, which waits on
             card:command-categories.md

## The ask

> gemba: a program in the workspace that lets me walk the factory floor —
> Claude presents and comments to the editor, I see it through the
> workspace.  Requires python & rust syntax support.

## Found by looking, before it was taken

*Genba*, 現場, "the actual place" — the lean practice of going to where
work happens instead of reading a report about it.  The inversion is the
point: today Henri reads sixteen commit messages Claude wrote; a gemba
walk is him arriving where the work is while it is happening, with Claude
narrating.

**Most of the machinery exists.**  Content boxes already put a live thing
in the text — the notes roll, the scope, the spectroscope, the canvas —
and a box is already "a picture, not code".  A gemba box would be another
of those, fed by whatever Claude is doing rather than by the file.  **The
unbuilt part is the channel**: no path exists from a Claude session into
a running workbench, and that is the real work, not the drawing.

### The syntax support, resolved 2026-08-16 evening

Henri: *"Isn't the workbench using tokenizer from python side… I recall
it was python-side tokenizer."*  He is right, and it settles most of that
half of the card.

`furniture.rs:133` says it outright — *"sent by the model because the
tokenizer is the model's, and a second lexer in the window would be a
second front end that could disagree with the compiler."*  The window
receives `Vec<Run>` per visible line and **never tokenizes**;
`session.py:3665` calls `painted(text)` and ships `col:len:class`.

| language | tokenizer | the rule |
|---|---|---|
| `.ges` | the compiler's own, via `painted()` | load-bearing |
| `.py` | stdlib `tokenize` — also a *real* one | satisfied for free |
| `.rs` | a small lexer, deliberately coarse | **does not apply** |

**Python needs no Rust change whatsoever.**  Point `painted()` at
`tokenize` for `.py` and emit the same runs; the window is already
language-agnostic.

**And the rule was never about foreign files.**  Its stated danger is a
lexer that *"could disagree with the compiler"* — real for `.ges`,
because gestate's compiler tokenizes `.ges` and a second lexer can drift
from it.  There is no gestate compiler for `.rs` to disagree with, and
nothing downstream reads those colours: they are a reading aid, not a
claim about the program.  A `.rs` lexer is therefore ~80 lines (strings,
raw strings, chars, line and block comments, numbers, keywords,
lifetimes), and its docstring must say *reading aid* so a later session
does not mistake it for a front end.  Colouring a nested `/* /* */ */`
wrong is a cosmetic bug, not a correctness one.

**What is actually left of the syntax half is the cache.**
`session.py:446`: `_PAINTED` is keyed by the line's own text, because in
gestate *"a line that has not changed cannot have changed colour"* — the
only cross-line state is `INDENT`/`DEDENT`, which carries none.  That is
false for a Python triple-quoted string and for a Rust `/* */` or raw
string, where a line's colour depends on lines above it.  The
37 µs-per-line edit cost is bought by an invariant these languages do not
have.  Either the cache learns a per-line start state, or it is bypassed
for foreign files and the cost measured before anyone calls it slow.

## Found on the way, 2026-08-16 evening

The sound card is already a channel from Claude's work to Henri's ear —
he noticed a headless test run playing `noted.ges` into the room and
said *"if I hear sounds, I can respond… you can use that for your
advantage."*  Not the channel this card needs, but worth knowing it
exists: unattended work can already say something audibly.

## Elaborated further, 2026-08-17 — the channel, and the rate

### The transport is nearly decided, and the fence decides it

**Nothing reaches a running workbench from outside today.**  Measured:
no socket, no fifo, no signal handler, no watcher anywhere in
`workbench.py`, `session.py` or `audioeditor.py`.

But the loop already watches the filesystem, and carefully.
`Session._outside()` keys a `Path` question on its directory's **mtime**
— one `stat`, no re-listing until something really moved — polled at
`OUTSIDE_EVERY` (0.2 s) with `MTIME_SETTLES` (0.05 s) for the kernel's
coarse clock, which is F124's whole finding.  The instinct is built and
tested.

And the house has one wire shape, now four times over: `crust`'s program
format, the furniture description, the session trace, and the presence
record — **flat lines, tab-separated, verb first**, readable in a
terminal when something is wrong.

So: **a file the session writes and the loop reads.**  Four reasons, and
only the last is decisive:

1. No new thread and no socket lifetime — and lifetimes at this seam
   have a history (`Workbench.stop`, the daemon-thread segfault).
2. It survives either side dying.  A session can crash and the last
   thing it said is still on the screen.
3. It is the fifth thing wearing the house's own format, so it is
   debuggable with `cat`.
4. **It is the only transport that crosses the fence for free.**
   `card:reviewing-by-running.md` puts the workbench inside
   `tools/sandbox.sh`, where *the project directory is the one writable
   thing* — so a file under it needs no new bind, while a socket or a
   fifo anywhere else needs the fence widened to admit it.  Two cards
   that compose rather than fight is worth more than a millisecond of
   latency.

A fifo wants a blocking read on a thread and drops what it cannot
deliver; a socket wants an accept loop and a bind.  Both are streams,
and what is being sent is closer to a document.

### Where it stands — answered

**Q (Claude).**  A content box stands on a *line*.  Should a gemba box
stand on the line being changed, be an ask-line you place yourself, or
be window chrome?

**Henri, 2026-08-17: one box, wherever you put it.**  So it is a
`gemba` ask-line, the same shape as `canvas` and `notes` — the machinery
is built, the manners are known (the box stands on the line, deleting the
line takes the box, no line no box), and it keeps working when the file
on screen is not the file being worked on.

### And the finding that is the real design — the rate

**Q (Claude).**  Does the box hold what is happening now, a scrollable
log, or now-plus-a-tail?

**Henri, 2026-08-17:**

> This is a hard question.  In one hand "what is happening now" would be
> great, but you're much faster than me.  I think the design should
> account for that.  Give me room that I need.

**That is not a fourth option, it is the constraint the other three were
hiding.**  A narration paced by the writer is unreadable when the writer
is faster than the reader; a log paced by the reader is a report, which
is the thing this card exists to replace.  Neither end can own the pace.

So the box is **paced to the reader**:

- Claude writes into a queue; the box shows **one** thing at a time.
- Each stands for a **minimum dwell**, so nothing can be replaced before
  it has been readable.
- When the queue backs up, **the depth is itself the reading**: the box
  says how far behind it is running.

That last line is the valuable one.  The rate mismatch stops being a
defect to be engineered away and becomes **the instrument's most useful
signal** — *he is going faster than you are following*, which is
`spec/author.md`'s standing problem (*"the volume outrunning review"*)
made visible while it is happening rather than discovered in a commit log
afterwards.  It is `card:timer.md`'s own idea one floor over: a
mark that grows with a quantity, applied to attention instead of hours.

**Picked 2026-08-18.**

**The dwell is the item's own length, not a constant.**  *Henri: "as
long as it takes to read it."*  About a word every third of a second,
with a floor so a three-word note is still catchable and a ceiling so
nothing can hold the box hostage.  The constant nobody could pick was
the wrong question: a paragraph and a word do not want the same room,
and the text already says which it is.

**A deep backlog is a mark, not a count.**  `spec/rocks.md`'s own rule,
applied: *a number a person has to read is a number a person will not
read*.  The depth is something you take in without looking at it, which
is the whole point of putting it there — it is meant to be felt at a
glance while you are reading something else.

**And this session takes the channel and the box** (items 1 and 2).
That is the part that does not exist; 3–5 are colouring for files you
can already open.

**And one rule falls out of it for the writer, not the window.**  If the
box can only carry so much, a session has to choose what is worth saying
— which is the same discipline the commit body already asks for, arriving
a few hours earlier.
## What the work is

1. **The channel** — a file the session writes and the loop reads,
   flat tab-separated lines, under the project so it crosses the fence
   for free.  Decided above.
2. The box that shows it, which is a fourth reading of machinery that
   already exists.
3. Python colouring, which is `painted()` plus the stdlib.
4. Rust colouring, which is ~80 lines and marked *reading aid*.
5. The cache's per-line start state, or a measured bypass.

## Found on the way, 2026-08-17 evening — what a session actually presented

**The channel is specified as flat text, and today's most effective
presentations were pictures.**  Worth knowing before the box is built,
because it is cheap to allow and expensive to retrofit.

Everything that moved a decision today was an image the session made
and described:

* the first screen a stranger meets, photographed and then *measured* —
  the burger's 24 lit pixels, `#4a5260` on `#14161a`, counted off the
  capture (F150);
* the command list open, showing `skip` selected over *"Do nothing —
  the identity of `++`"*;
* five status bars stacked, one per pause in typing, which is what
  finally made "chatter" mean something — *"so you mean that chatter"*;
* an **A/B pair**, the same keys driven with a change on and off, which
  is what cleared the auto-audition of causing F152.

None of that is a sentence, and prose describing any of it failed first:
the chatter was explained twice in text before a strip of five bars made
it obvious in a second.

**What this suggests, without deciding it:** the queue carries typed
lines — the house format is verb-first, so `say`, `shot <path>`,
`ask` cost nothing to distinguish — and the box already knows how to
draw a picture, because every other content box is one.  The dwell
rule then applies per item whatever its kind.

**And the tools are already here**, used ad hoc all day and worth
gathering: `lagcheck.shot` for the capture, `a_copy_of` so driving is
safe (F154), ImageMagick for crop/magnify/stack, and pixel counting in
twelve lines of stdlib.  The gap is not capability; it is that nothing
routes them to a window Henri is looking at.

**And it already goes the other way.**  Henri, the same evening: *"yes!
pictures are very important in the tool.  We've solved many problems
that way.  Sometimes I've even shown you video."*  So the picture
channel is not a new idea being proposed for this box — it is the
established medium of this collaboration, and the box is where it stops
being ad hoc.

Which splits the medium usefully:

* **A picture shows state** — the burger's contrast, a list open on the
  wrong entry, a box that did not land.  One frame answers it.
* **A sequence shows behaviour** — the chatter needed five bars in a
  row; nothing about any single one of them is wrong.

**The second is where the dwell rule and the pictures meet**, and the
house may already own the answer: `gestate.sessionlog` records and
replays a session, and a replay is what a video is for without being a
codec.  Worth asking whether a gemba item can be *"replay this"* before
anyone reaches for frames.

## Done

*2026-08-18.  `journal.md` §"The factory floor, and the pace nobody
owns" tells the story.  Items 1 and 2 — the channel and the box — at
Henri's ask: "it's not in front of the line anymore, but it helps with
the workload here if we make it right."*

**The channel** is `gestate/gemba.py`: `gemba.tsv` under the project,
flat tab-separated lines, verb first — the fifth thing in this house
wearing that shape.  A session says one thing with
`python -m gestate.gemba say "…"`, which is a command line rather than
an import because the thing narrating is usually running `git`,
`pytest` and `cargo` and the cheapest thing to reach for between two of
those is one more command.

**The box** stands on a `gemba` ask-line, `canvas`'s manners exactly.
It shows **one** item, held for **as long as that item takes to read** —
about a word every third of a second, floored at 3s so a glance catches
a short note and capped at 20s so nothing holds the box hostage.

**And the backlog is a mark.**  When the queue backs up the box grows a
bar under the sentence, one cell an item.  That is the design's most
valuable line and it is Henri's: neither end can own the pace, so the
rate mismatch stops being a defect to engineer away and becomes the
instrument's most useful signal — *he is going faster than you are
following*, which is `spec/author.md`'s standing problem made visible
while it is happening rather than found in a commit log afterwards.

**The clock lives in the model**, because how long a thing has stood is
a fact about the session and not about the window: a window redrawn
twice as often must not advance the queue twice as fast, and there is a
test that says so.

### What the running window found that reading did not

**The first version broke the program it was narrating about.**  The box
drew perfectly on the first try, and the file under it did not compile —
*expected '=', got end of line* — because a bare `gemba` line is not
`.ges`.  Every other ask-line already knew to rewrite itself to a
comment (`audiovoices._rewrite_asks`); this one was written without
asking what the compiler would make of it.

**All twenty-three tests passed while that was true**, because none of
them compiled anything.  It took one screenshot of the real window,
which is `card:reviewing-by-running.md`'s whole argument arriving
unprompted.

### Left, and named

3. **Python colouring** — point `painted()` at the stdlib tokenizer for
   `.py`.  No Rust change at all.
4. **Rust colouring** — ~80 lines, marked *reading aid*.
5. **The colouring cache's per-line start state**, or a measured bypass.

And the one the card most wants next: **`shot <path>`**.  The verb-first
format costs nothing to extend, the box already knows how to draw a
picture because every other content box is one, and the evening of
2026-08-17 is the argument — every finding that moved a decision that
day was an image, and prose describing it had failed first.
