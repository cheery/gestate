# button — the one affordance, and nobody found it

    status   open
    because  The program would not currently pass the stranger test.
    asked    Henri, 2026-08-17
    see      board/stranger-test.md — this is that test's first real result
             vision.md §"Ease of use and efficiency"
             shell/editor/src/view.rs — `burger_box`, `burger_frame`
             board/command-categories.md — the second half of the report

## The ask

Henri's words, 2026-08-17:

> I tried it with my other friend without explaining how it works.
> He was unable to find the small gray-tinted button from the program.
>
> Once I helped he got the button open, he had very little idea what is
> behind it.
> This is probably a problem with multiple factors.

## Found by looking

Two failures, and they are not the same failure.

**1. The button was not seen.**  `view.rs`'s `burger_frame` draws the
whole of it: one character cell, the glyph `≡`, no ground, no border,
flush in the top-right corner, in `FAINT`.  Against `BG` that is a
contrast ratio of **2.3:1** — under the 3:1 floor that any interface
guidance puts on a control, and the *lowest* contrast the window paints
anything at.  The text beside it sits at 13.2:1.

The colour is also load-bearing elsewhere: `FAINT` is what the **gutter
line numbers** are drawn in, and the summary line under the command
list, and the fold labels.  It is the window's word for *there, but not
for you*.  The one control a person with no keys can use is painted in
the colour that means ignore me.

The comment above the drawing says why, and it is worth quoting because
it names the trade that was made:

> The glyph alone, no ground — the corner is the document's, and a grey
> box standing on it read as furniture rather than a button.

That is a real observation and the fix went one step too far: it stopped
reading as furniture by ceasing to read as anything.  **Suspected**, and
it is the whole shape of the work: the button needs to be found without
becoming chrome, and the current answer optimised only the second half.

**2. What is behind it did not explain itself.**  Opening the burger
opens the command list — a flat list of entries, the picked one in
`INK`, the rest in `FAINT`, and a single elided summary line under it.
Nothing groups it and nothing says what kind of thing you are looking
at.  This is exactly the evidence `command-categories` was written on,
now with a person attached to it: he opened the one door the window has
and found a list of names.

**What this is the first result of.**  `stranger-test` says, in its own
last paragraph, *"The real version of this test is Henri's friend, once,
with nobody helping."*  That run has now happened by accident, and it is
worth more than the card expected to get, and it arrived cheaper.

*~~It stopped before open.~~  **Corrected the same day** by looking at
the screen he was on: open and hear had already happened by themselves.
He stopped at step three.  See the second pass below.*

## Found by looking, second pass — at the window itself

*2026-08-17, at Henri's ask to explore before deciding anything, and
explicitly not to assume the answer is "make the button bigger".  What
follows is from the running window rather than the source: the icon's
own launcher opened, photographed with `tools/lagcheck.py`'s `shot`
and `find_window`, and the pixels counted.*

### The one instruction on the first screen points at a deleted control

The window a bare click opens has no file, so it opens on `STARTER`
(`audioeditor.py`), and lines 6–7 of it are the only guidance anywhere
on the screen:

> `` `doc/ref/index.md` `` is what is in scope; the **[ref] button top
> right** is the same pages in here.

**There is no `[ref]` button and there has not been one for a while.**
It belonged to `gestate/audiopygame.py` — the pygame editor — and went
with it in `71b90af` *"vastly improved editor coming"*.  The text
survived the UI it describes, the same way the canvas lost its callers
in that deletion.

What stands in that corner now is `≡`, which opens the command list.
So the only sentence on screen that names a control names the wrong
one, in the right place: a stranger who follows it and finds the
burger has been taught that this is the reference, and it is not.
`stranger-test` has the rule for exactly this — *"a wrong guess that
worked is worse than a stumble; it means the window taught something
false."*

**And it makes the contrast finding worse, not better.**  The screen
already says *top right*.  He was, in effect, told where to look, and
still did not see it.  Which is the strongest available argument that
the current drawing is under the floor of *findable* — and, at the same
time, the strongest argument that finding it is not the whole problem.

### The control is twenty-four pixels of ink

Measured off the capture, not estimated: the glyph's ink occupies an
**8 × 7 box and lights 24 pixels**, `FAINT` `#4a5260` on `BG`
`#14161a`, 2.3:1.

**And it is drawn inside the document, not beside it.**  `burger_box`
puts it at `y = 0` of the text area — the same row as line 1, in the
column where the line's own text would be if the line were long enough.
It is not in a strip, a bar, or a margin of its own.  That is a
*placement* fact and it is separate from size and colour: the corner
comment says a grey box there "read as furniture rather than a button",
but the reason the glyph reads as neither is that it is standing in the
document's own space, where everything else is text.

### The window teaches the key, but only after you no longer need it

`view.hint` puts `Ctrl-K` in the status bar — and it is set *by the
burger press* and cleared when the list closes.  So the bar teaches the
key to somebody who has just demonstrated they can find the button, and
says nothing to somebody who cannot.  **The teaching is downstream of
the discovery it exists to make unnecessary.**

### What is behind it opens on the command that does nothing

The list, photographed: a `>` prompt, then twelve entries with the
first one selected, and one summary line under them.  The selected
entry is **`skip`**, and the summary line reads:

> Do nothing — the identity of `++`.

Because the palette is derived from `command.ges` in **declaration
order**, and `skip` is declared first — as the identity of the command
monoid, which is a fact about the language's algebra and not about
anything a person wants to do.  So the list is ordered by the
language's internal logic, the first thing it offers is the command
that has no effect, and the single sentence of explanation on screen
explains that one in terms of a monoid.

The rest of the visible entries are `apply`, `audition`, `play`,
`stop`, `seek`, `loop`, `loopAll`, `loopOff`, `set`, `learn`,
`listen`.  Nothing groups them and nothing on screen says what kind of
thing they are.  `command-categories` is the card for that half, and
this is the picture to attach to it.

### Two of the four steps already happen by themselves

The status bar says `playing untitled.ges at 44100 Hz — no parameters`
with a running clock.  From the icon, **open** and **hear it** are
free — the program is sounding before anybody does anything.

So the friend was not stuck before step one.  He was stuck at **hear
the change**: typing needs no affordance at all, and what has no
affordance is the *apply* that makes an edit audible (`apply · Ctrl-S`,
second in the list).  That reframes the card: the button is not the
first move, and the missing sentence is not "there is a menu here" but
**"your change is not in the sound yet."**

**A (Henri, 2026-08-17).**  *"My friend was on the starter screen. The
basic sine function giving a tone."*

So it is the sharper of the two readings, and every part of the account
above applies to what he was actually looking at: **the tone was
already sounding**, the screen told him *top right*, the thing in that
corner was 24 grey pixels, and the sentence that sent him there named a
button deleted a week earlier.  He was not stuck at *open* or at *hear
it* — both had already happened before he touched anything.  He was
stuck at **change it, and hear the change**.

### There is a great deal of room and nothing is said in it

Over half the window is empty ground below eleven lines of text.  The
one line that does speak — the status bar — spends itself on
`at 44100 Hz — no parameters`, which is machine state, in the same
`FAINT` as the button.

## Questions

*To ask in one sitting — the board's rule — and none of these is
blocking; the work can start on the contrast alone.*

0. ~~**Which screen was he on?**~~  **Answered above**: the starter
   screen, with the sine already sounding.

1. **How far may the corner change?**  The current design spends one
   cell and no ground on purpose.  Is a bordered or filled button in
   the corner acceptable now that the quiet version has been measured
   against a person, or is the constraint *stays out of the document's
   way* still the harder one?

2. **Should the window ever say something first?**  A first-run line in
   the status bar — one sentence naming the button or the key — would
   have carried him past both halves of this.  It is also the first
   thing in this project that would talk to you unbidden, so it is a
   line to cross deliberately or not at all.

3. **Is the friend available for a second run?**  A fix to this is
   testable in about a minute by the only oracle that counts, and the
   value of a second run drops the more he learns about the program.

## Six answers, and what each one believes

*Written because Henri declined to name the fix — "not necessarily the
whole answer to it, or correct answer" — and the board's own most
expensive lesson is that a card naming a fix hides the problem.  These
are not alternatives to choose one of; they are **theories of what went
wrong**, and the evidence above supports different amounts of each.*

**A. The button must be findable.**  *Believes: he did not see it.*
Contrast, size, a ground, a border, a word instead of a glyph, or the
corner it stands in.  Strongly supported — 2.3:1 and 24 pixels is under
any floor there is, and it is painted in the window's own word for
*not for you*.  **But it cannot be the whole answer**, because the
screen already said "top right" and he still missed it, and because he
was still lost once it was open.  *Cheapest honest version: it is the
only control in the window, so it need not shout — it needs to stop
being drawn in the colour of the line numbers.*

**B. The first move should not need the button at all.**  *Believes:
the document is the interface.*  `STARTER` is already a teaching
document — it is what a new file *is* — and right now it teaches one
thing and that thing is false.  Rewriting those two lines to say what
actually works (type something; `Ctrl-S` puts it in the sound) costs
nothing, breaks nothing, and is owed regardless of what happens to the
corner.  **Its limit is exactly stated**: it only helps somebody who
opened a *new* file, and only somebody who reads.

**C. The bar should say the key before it has been earned.**  *Believes:
the window already has a place to speak and uses it too late.*
`view.hint` exists and works; its default is backwards.  Showing
`Ctrl-K` until the list has been opened once — and never again — is a
one-line change to a mechanism that is already built and already tested,
and it is the smallest version of question 2 that does not require
inventing a first-run overlay or anything that talks unbidden.

**D. What is behind it must explain itself.**  *Believes: he found the
door and the room was the problem.*  `command-categories`, plus the
narrower thing this session found: **the list opens on `skip`.**  The
palette follows `command.ges`'s declaration order, which is ordered by
the language's algebra, and the first thing a person meets is the
command that does nothing described as the identity of `++`.  Whatever
happens to categories, the list should not open on that.

**E. Nothing should have to be discovered, because the change should
already be audible.**  *Believes: the affordance is missing because the
behaviour is.*  This project's whole thesis is a signal that develops
while it is already alive; if editing the text moved the sound, the
fourth step would need no button, no key and no sentence.  There are
good reasons it does not work that way — half-typed programs, and a
save is a decision — but this is the answer that makes the button
*unnecessary* rather than better, and it deserves to be said out loud
before the other five are costed.  **It is also the largest.**

**F. Nothing is wrong that a second person would not have found
anyway.**  *Believes: one run is one run.*  The honest null: a single
stranger stumbling twice tells you where to look, not how big the
problem is.  Cheap to test — question 3 — and it is the only answer
that would save the work in A–E from being aimed at an audience of one.

**What this session would do first, if it took the card:** B and D's
narrow half, because both are defects rather than designs — a sentence
that names a control deleted in `71b90af`, and a list that opens on
`skip` — and neither commits the corner to anything.  Then measure A
against a person again before spending the corner on it.

## What landed, 2026-08-17 — the two that every answer agrees on

Set-based rule 3 (`manifesto.md` §"Set-based, not point-based"): act now
on what every alternative in the set agrees about.  A–F disagree about
the corner; **none of them wants the first screen to name a deleted
button, and none of them wants the menu to open on the command that does
nothing.**  So both were fixed while the corner stayed open.  `fixme.md`
F150.

* **The starter sentence.**  `[ref]` is gone; it now says that `what`
  says what a name is and `fits` says what could stand where a type is
  wanted, "the compiler answering, rather than a page" — true, reachable,
  and it names no control at all.
* **`skip` moved to the foot of `command.ges`**, under a heading that
  says why, with a pointer from the `Semigroup Command` instance it is
  the identity of.  The list now opens on **`apply · Ctrl-S`**, whose
  sentence is *"Rebuild the instrument from the text and swap it in while
  it plays"* — the exact move the friend was stuck at.

Both confirmed in the running window, photographed again after the
change.  Held by `test/test_starter_and_first_command.py`, which fails
on four of its six when either defect is put back.

**What is deliberately still open**: the corner itself (A), the hint's
default (C), categories (D), and whether an edit should be audible
without applying at all (E).  None of those should be decided on one
stranger — which is question 3, and the cheapest thing on this card.
