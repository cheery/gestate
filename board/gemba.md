# gemba — walk the factory floor

    status   open
    because  today I read sixteen commit messages Claude wrote; I want
             to be where the work is while it happens
    asked    Henri, 2026-08-16
    see      spec/scorebox.md, spec/panel.md — content boxes are the
             drawing half, already built
             gestate/session.py:446 — the colouring cache
             board/git-viewer.md — the second idea, which waits on
             board/command-categories.md

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

## What the work is

1. **The channel** — a path from a Claude session into a running
   workbench.  This is the card.
2. The box that shows it, which is a fourth reading of machinery that
   already exists.
3. Python colouring, which is `painted()` plus the stdlib.
4. Rust colouring, which is ~80 lines and marked *reading aid*.
5. The cache's per-line start state, or a measured bypass.
