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
with nobody helping."*  That run has now happened by accident, and it
did not reach step one of the four — open a file, hear it, change it,
hear the change.  It stopped before *open*.  That is worth more than
the card expected to get, and it arrived cheaper.

## Questions

*To ask in one sitting — the board's rule — and none of these is
blocking; the work can start on the contrast alone.*

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
