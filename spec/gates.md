# Gates on will — `gateOn`

*Written as a proposal; the surviving half is built now.  A second
name, `gateRepeat`, was drafted, verified and dropped — the end of this
file says why.*

## The observation

`doc/beginner.md`, lesson 3, used to apologise for teaching envelopes
with a `wrap` trick:

> The library also has proper envelope tools — `Adsr`, `adsr`, `perc` —
> that read a note's timing from a keyboard; they arrive at the end of
> this course, **because they need notes to react to.**

The emphasis was the untruth.  `adsr` and `perc` need a **`Sig Gate`**,
and a `Gate` is two integers — `Gate := Gate Int Int`, the sample a
note began and the sample it was released, 1-based, zero meaning
*nothing* (`audio.ges`).  Only the machinery that *produced* gate
signals needed notes: the `voices` bank's `gateAt`/`offAt` channels,
filled by a score or a keyboard.  The envelope itself is on the record
as not caring — `adsrOf`'s own docstring calls it "the whole envelope,
as arithmetic", and `sine.ges` demonstrates by holding one note between
two constants.

So the *scalar* path existed and was documented.  What did not exist
was the **signal** path: no public name made a `Sig Gate` out of
anything but a played note.  The consequence ran through the whole
beginner course — every rhythm built from `wrap`-arithmetic phase
tricks, and the library's envelope vocabulary deferred to the final
lesson not because it is advanced but because there was nothing to
feed it.

## What shipped

One name, in `synth.ges`'s public "Gates" section, beside the
envelopes that consume it:

    gateOn : Sig Bool -> Sig Gate
    gateOn bs = scan gateEdge (Gate 0 0) (zip (n b => GateEdge n b) ticks bs)

Any condition, as a note: a rising edge is a press, a falling edge a
release.  The fold's state is the `Gate` it is emitting; only the
edges do anything.  Its machinery — `GateEdge` (the zip record,
`SvfIn`'s precedent), `gateEdge`, `gateHeld` — is below `internal`,
and naming a helper from a program is refused with "reach for
`gateOn`", the faces derived by `internals.py` with no table to
maintain.  One `scan` over one flat record: in the static fragment,
and one node for stage 5 to migrate.

Everything a program has is now a note source:

* a metronome is a comparison on the ramp the lessons already teach —
  `gateOn (!(x => x < 0.5) (phase 2.0))` presses twice a second and
  holds each press a quarter of one (and the spelling leans on
  `spec/exclamation.md`'s repaired `!`: the marker takes the lambda as
  its head and lifts it over the ramp);
* a note that plays while an LFO is high is
  `gateOn (!(v => 0.5 < v) lfo)`;
* a threshold over a follower turns *audio* into notes.

The condition true at the first sample presses at the first sample, so
a clock-derived gate plays from the program's start, exactly as the
lessons' hand-drawn envelopes do.  The `on = 0` never-played
convention is untouched.

Lesson 3 keeps the exponential `wrap` envelope as its spine and now
teaches `perc` and `adsr` beside it, fed by `gateOn` of that same
ramp; the finale's `adsr` became "lesson 3's, unchanged — a played
gate and a generated one are the same thing to an envelope."  To the
envelopes there is deliberately no marker distinguishing the two,
which is the fact the lesson used to talk around.  Tests:
`test_a_phase_comparison_is_a_metronome`,
`test_a_gate_holds_and_releases`, `test_a_condition_is_a_note`
(`test/test_synthlib.py`).

## The name that was dropped

The draft had a second name, `gateRepeat p hold` — a metronome with a
note length, as a pure `map` of `ticks`.  It was implemented, tested
and then withdrawn, for reasons worth keeping:

* **It is one comparison away from `gateOn`.**  The `wrap` spelling of
  a metronome is not a workaround; it is the lesson — timing as
  arithmetic on time is the course's own idea, and a second name would
  have hidden the connection rather than taught it.
* **Its edge case lied.**  With `hold >= p` the release never arrives —
  the next trigger replaces `on` before the instant reaches
  `on + hold`, so `adsr`'s release phase never plays and nothing in
  the types says so.  (Verified by probing the `off` field: all zeros
  at `hold = p`.)  `gateOn` has no such region: the release is the
  falling edge, and where the falling edge is, is visible in the
  condition the author wrote.
* One general name that composes beats two names where one is a
  special case of the other; `dust` earned its name by being
  irreducible, and `gateRepeat` was not.

What is given up: the pure-`map` form had no state, so a live edit
could never reset its phase, while `gateOn`'s fold is one node of
migrated state.  Accepted — the state is the gate itself, and stage 5
carrying it across an edit is a *held note surviving the edit*, which
is the behaviour a player wants anyway.
