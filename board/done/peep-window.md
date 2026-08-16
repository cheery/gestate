# peep-window — where the caret is when it is off screen

    status   done — 2026-08-16
    because  a note drag rewrites text I cannot see
    asked    Henri, 2026-08-16
    see      spec/workbench.md §"The peep"
             journal.md §"The evening the caret got a window of its own"
             tools/dragcheck.py

## The ask

> Make a small window that shows where the cursor is when it's
> off-screen.  This is intended mainly for situation when workbench user
> uses the north star's features and moves the notes.

## Found by looking, before it was taken

The editor already scrolls to follow the caret on every key
(`shell/editor/src/keys.rs:143`, *"always"*), so the off-screen case is
not typing — it is the **north star drag**, where a note moves under the
hand and the thing you want to watch is not where the caret is.  The
window already knows which rows are visible (`furniture.rs:606`, *"the
first visible row and how many fit"*) and that belongs to the window's
thread, so the parts exist.  The work is a small overlay plus a decision
about what it shows.

## Questions

**Q (Claude).**  When a note is dragged off-screen, what should the small
window show — the note's new position, the line of text being rewritten,
or both?  My inclination is the text line, because the drag's whole point
is that it writes text and that is the thing you cannot otherwise see.

**Henri, 2026-08-16:**

> It could show 5 lines and their numbers.  Your inclination is correct.
> Cursor should show in that window and line numbers should always show
> themselves.  It could be clickable so that user can move in that
> window.
>
> It's kind of specific to north star.  I would have not come up with the
> idea without it.

**Henri, 2026-08-16 evening**, on where it stands:

> similar to the palette's page, a rounded rectangle that pops above if
> cursor above equator, below if below equator.

That machinery already existed — `shell/editor/src/palette.rs:1175`,
*"The page goes where the room is (F133)"* — so the peep is that
placement plus five lines, their numbers, the caret, and a click that
moves the real one.  Reuse rather than invent.

## Done

`view::peep_box` / `peep_frame` / `peep_hit`, five tests in
`shell/editor/tests/view.rs`, contract in `spec/workbench.md` §"The
peep".  It appears when the caret's row is not in the view's own row
table, stands **toward** the caret (the opposite of the palette panel's
rule, and for the opposite reason), draws its line numbers always, and a
click in it moves the real caret without scrolling.

**It came with a defect nothing had caught.**  A press on a note in a
score box sends a `goto` to where that note is written — `noted.ges`
rolls `score` on line 142 out of an atom on line 94 — and the window
revealed it, so the box scrolled out from under the finger pressing it
and the drag ran on against the pixels the grab remembered.  Fixed as
one rule at the end of `obey`, where every drawn order passes:
**nothing scrolls on the model's account while a hand holds a picture**
(`EditorWindow::pinned`), with `take_text` no longer chasing a caret
that was already off screen.

`tools/dragcheck.py` is the oracle — a real window, a real press, a
photographed strip of text across it — and it was run against a
deliberately sabotaged build first, because a check that cannot fail
says nothing.

**What is left, and it is Henri's original phrasing**: *"and edit
through it."*  Typing goes to the caret and the keystroke's own `follow`
brings the view with it, so today the peep shows a place and offers to
move you there.  Editing *inside* the band is the same question
`spec/workbench.md` §"Content boxes" answers about the third focus — it
waits for the first gesture that genuinely wants to type into a band
rather than at a caret.
