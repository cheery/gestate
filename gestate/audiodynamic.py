"""A score performed as it plays — `spec/dynamicscore.md`, stage one.

`audioscore.schedule_voices` decides every note at bake time: the layout
becomes channel changes at sample indices before the first sample renders.
The `Performer` here makes the same decisions with the same code — the
same `timed_events` order, the same `Allocator`, the same delivery
arithmetic — but makes each one **as the clock reaches it**.  Nothing
about *which* notes exist changes; only when they are decided does, which
is `audioalloc`'s own sentence one floor up.

That sameness is a test, not an aspiration: `test_dynamicscore.py` holds
a performer at constant tempo to the bake change for change and sample
for sample, because two spellings of when-a-note-happens is exactly where
a note goes missing silently.

The clock is **score time in samples**.  A performer converts ticks once,
through the one `samples_of` the bake uses — the integer path for a
constant tempo, the envelope path otherwise — and its cursor compares
delivery boundaries against the `t` the engine is rendering.  A cursor
that compares *beats* directly (a DAW's `song_pos_beats`) is the Rust
shell's retelling of this file, and it copies the semantics pinned here.
"""

from __future__ import annotations

from .audioalloc import Allocator
from .audioscore import ScoreError, _flatten, timed_events


class Performer:
    """A cursor over a score's events, performed as the clock reaches them.

    `advance(t)` is the performance: every event whose delivery boundary
    has arrived is handed to its bank's allocator, and the changes land in
    `values` — the dict a control source reads, exactly as `Notes.values`
    is read.  `seek(t)` is the transport's other question, answered as the
    spec answers it: release what sounds, then a silent replay to `t`.
    """

    def __init__(self, events: list, tempo, rate: int, allocators: dict, *,
                 block: int):
        if block <= 0:
            raise ScoreError(f"a block size of {block}")
        self.allocators = allocators
        self.block = block
        #: The bake's own order — shared, not copied (`audioscore`).
        self.timed = timed_events(events, tempo, rate)
        #: Channel name → current value; what `from_performer` reads.
        self.values: dict = {}
        #: The cursor: the first entry not yet performed.
        self.pos = 0

    # -- the arithmetic the bake and the performer must share ----------------

    def _boundary(self, at: int) -> int:
        """Where a change lands: the block boundary at or before its sample.

        The same line as `Schedule.deliver` — the value names the instant,
        the delivery precedes it — because parity is exactly this integer
        agreeing in two places.
        """
        return (at // self.block) * self.block

    def _perform(self, entry) -> list:
        """One entry through its allocator; the changes, or a refusal."""
        at, _order, key, bank, payload, is_off = entry
        allocator = self.allocators.get(bank)
        if allocator is None:
            raise ScoreError(
                f"this piece assigns notes to `{bank}` and no allocator was "
                f"given for it; there is "
                + (", ".join(f"`{b}`" for b in sorted(self.allocators))
                   or "none"))
        return (allocator.note_off(key, at) if is_off
                else allocator.note_on(key, _flatten(payload), at))

    # -- performing -----------------------------------------------------------

    def advance(self, t: int) -> list:
        """Perform everything due at a delivery boundary at or before `t`.

        Returns the new changes as `[(boundary, chan, value)]`, in the
        bake's order — pour them into a `Schedule` and you have rebuilt
        it, which is precisely the parity test.  Idempotent for a `t`
        already reached: a control tick asked twice delivers nothing
        twice.
        """
        out = []
        while (self.pos < len(self.timed)
               and self._boundary(self.timed[self.pos][0]) <= t):
            entry = self.timed[self.pos]
            boundary = self._boundary(entry[0])
            for chan, value in self._perform(entry):
                self.values[chan] = value
                out.append((boundary, chan, value))
            self.pos += 1
        return out

    # -- the transport's questions --------------------------------------------

    def seek(self, t: int) -> list:
        """Release what sounds, then stand at `t` as if played from the top.

        Three moves, in the spec's order:

        * **`all_off`** on what is sounding, stamped `t` — the releases are
          the audible part, and what this returns.
        * **A silent replay**: fresh allocators walked over every entry
          delivered *before* `t` (entries at `t` itself belong to the next
          `advance`, so a seek onto a downbeat plays the downbeat).  This
          is `into_schedule`'s work done on demand — state at bar 33 is a
          pure function of what came before it.
        * **The replay wins** where the two collide: a voice the replay
          holds at `t` is a note that *sounds there*, and it resumes
          mid-envelope — which is what seek-then-perform-equals-`value_at`
          means.  A release survives only on channels the replay left
          alone, where the gate reads "never played" and the tail it
          releases is the only thing there was.

        The deliberate consequence: a pre-seek tail whose voice the replay
        re-occupies is cut, not rung out.  Ring-out across a seek would
        need per-voice grace the bake has no word for, and stage one does
        not invent words.
        """
        off = []
        for allocator in self.allocators.values():
            off += allocator.all_off(t)
        self.allocators = {name: Allocator(a.channels, a.policy)
                           for name, a in self.allocators.items()}
        self.values = {}
        self.pos = 0
        while (self.pos < len(self.timed)
               and self._boundary(self.timed[self.pos][0]) < t):
            for chan, value in self._perform(self.timed[self.pos]):
                self.values[chan] = value
            self.pos += 1
        kept = []
        for chan, value in off:
            if chan not in self.values:
                self.values[chan] = value
                kept.append((chan, value))
        return kept
