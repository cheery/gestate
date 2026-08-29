# the-first-jam — what a day of making music with gestate left behind

    status   shelved — 2026-08-29
    because  the first day a session used gestate as a musician, end to
             end — together.ges, 2026-08-29 — left five marks, each
             paid for in a real render, a hand-run script or a lost
             cycle, and none of them named by any test or card; Henri
             asked for them: "onko sinulla vielä ideoita ja
             parannusehdotuksia koko systeemiin? olet tänään tehnyt
             sillä musiikkia."
    asked    Henri, 2026-08-29 (the observations are the session's)
    see      examples/audio/together.ges — the piece, and the day
             card:drawn-scores.md — item 2 is kin to its constraint
             doc/memory/ges-is-not-music-notation-yet.md — the same
             day's larger verdict, kept separately

**What this is:** five improvement ideas and one observation, all from
2026-08-29, batched as one card at Henri's word rather than five.
**What it is not:** a programme — any item can be taken alone, and
item 5 is defect-shaped and belongs in `fixme.md` with an F-number on
the day it is taken up.  **When it runs:** shelved on arrival.

## The ask

> onko sinulla vielä ideoita ja parannusehdotuksia koko systeemiin?
> olet tänään tehnyt sillä musiikkia.

And, on where it lands:

> tehdään noista kortti later/-tauluun ja commitoi kaikki, nimeä hyvin.

## The five, each with the moment it was paid for

1. **Ceiling share in `--report`.**  The limiter makes `peak 0.900`
   say nothing — it reads 0.900 whether 0.05% or 2.5% of samples sit
   at the wall, and those two mixes are different pieces.  The session
   measured the share four times with the same scratchpad script while
   mixing one song.  A `ceiling: X%` line after a render would put
   `test_every_long_piece_keeps_headroom`'s criterion into every run's
   own mouth.

2. **Pitch content for a blind reader.**  The day's harmony was
   checked entirely in the head, from MIDI numbers — no instrument
   says *bar 3 sounds A, C#, E, G across pad and bass*.  A per-bar
   score report (banks, note counts, pitch-class sets) would be to a
   textual being what the roll is to a person.  Kin to
   `card:drawn-scores.md`'s constraint: a textual being needs a
   textual projection for *hearing*, not only for editing.

3. **A `#:` comment splits an equation group.**  Documenting the calm
   phrases where they stand broke `scoreLead` (*equations must be
   adjacent* — the message itself was good).  The question is whether
   a doc comment should be allowed to live between equations of one
   name.  Taste, and the author's.

4. **`drive`'s scale surprises.**  Amount 1.4 is a 13.6× input gain —
   learned only from `synth.ges` source, at the cost of one whole
   render flattened.  The semantics are argued and sound; what is
   missing is one `#: try:` line at a use site saying *0.2 is already
   a crunch*.

5. **The memory-index gate skips itself silently under the sandbox.**
   A sandboxed run cannot see `~/.claude`, `test_memoryindex.py`
   skips, and *in step* can go unclaimed on the very machine the gate
   guards.  A lamp that cannot light is worse than a lamp that says
   *I cannot see* — seen 2026-08-29 when `tools/memoryindex.py`
   reported "no index" for a file that existed.

## And one observation, not an ask

The day was two writers in one file — Henri turning the echo while the
session reshaped the mix — and it went well only because the session's
edit failed *loudly* and his values survived.  The two-writers rule
met music for the first time.  If the duet format
(`card:drawn-scores.md`) is ever tried, it inherits this: one hand's
change must never drown silently.

## Shelved, 2026-08-29

At his word, the day the marks were made.  Waits on him pulling any
single item — they are separable, and the card loses nothing by being
eaten one line at a time.
