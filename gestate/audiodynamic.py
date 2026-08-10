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

from heapq import heappop, heappush

from .audioalloc import Allocator
from .audioscore import ScoreError, _flatten, samples_of, timed_events
from .midi import TICKS_PER_BEAT


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


# ── Stage two: the score as an unfolding value ─────────────────────────────
#
# Everything above walks a list that exists.  What follows walks one that
# is still being *decided*: `streamMain` is lazy, beat-ordered, possibly
# endless, and forcing it is work the piece may take its time over.  The
# discipline is the spec's stall rule: **a hang is absence, never
# corruption** — the engine keeps rendering, every change already emitted
# plays out, and what stops is the future.  So every forcing here runs
# under a step budget (`gmachine.StepLimit`), a blown budget is a *stall*
# recorded at the beat it happened, and a note whose beat has passed by
# the time it finally appears is dropped, and said so.


class ScoreStream:
    """`streamMain` forced cell by cell, under a fuel budget.

    `pull(horizon)` returns the events whose onset lies below `horizon`
    ticks — as many of them as the budget allowed — and keeps two facts
    honest across calls: `frontier`, the tick below which the stream is
    *complete* (nothing earlier can still appear, the stream being
    beat-ordered), and `stalled`, whether the last pull ran out of budget
    mid-thought.  A parked forcing is resumable: the next pull re-enters
    the same evaluation with a fresh allowance, so an expensive-but-finite
    section arrives late rather than never.
    """

    def __init__(self, state, root, by_tag, *, fuel: int = 200_000,
                 burst: int = 4096, patience: float | None = None):
        self.state = state
        self.by_tag = by_tag
        #: The spine: the next cell, not yet forced past WHNF.
        self.node = root
        #: One event forced but standing beyond the horizon asked about.
        self.ready = None
        self.done = False
        self.stalled = False
        self.frontier = 0
        self.fuel = fuel
        #: The most events one pull may yield, horizon notwithstanding.
        #: `fuel` guards against one expensive thunk; this guards against
        #: an endless parade of cheap ones — a score whose sections
        #: shrink geometrically piles infinitely many events *below* any
        #: horizon past its accumulation point, and a budget that only
        #: watched depth would chase them for ever.  Blowing it is the
        #: same stall as blowing `fuel`: the piece outran its budget, and
        #: absence with the beat on record is the answer either way.
        self.burst = burst
        #: Seconds one pull may take, wall clock — the third guard, for
        #: the hang the other two cannot see: a step budget counts
        #: *steps*, and a single multiply on an integer doubled once per
        #: event is one step at any width.  Checked between events and
        #: between fuel instalments; a machine mid-monster-multiply
        #: still cannot be interrupted, which is a cost model's job and
        #: therefore `spec/crust.md`'s, not a deadline's.
        #:
        #: **`None` — no deadline — is the default, because the wall
        #: clock is a *live* concept.**  An offline render's `t` is not
        #: time, it is a loop counter: a deadline there lets the counter
        #: outrun an expensive first forcing and drop the downbeat of a
        #: piece that a listener would simply have waited out.  A live
        #: caller, whose `t` really does march, sets its budget.
        self.patience = patience
        self._deadline = None
        self._scratch = None
        self._scratch_for = None

    # -- budgeted forcing -----------------------------------------------------

    def _whnf(self, node):
        """WHNF of `node` within the budget, or `None` — parked, resumable.

        The scratch machine is kept when the budget blows, so the next
        call with the same node continues where this one stopped; heap
        updates along the way are shared, so redoing a walk that parked
        costs only the unfinished part.
        """
        from time import monotonic

        from .gmachine import Eval, GmState, NInd, StepLimit, run

        if self._scratch is not None and self._scratch_for is not node:
            # The walk is deterministic, so this only happens after a
            # caller abandoned a parked read; the partial work is in the
            # heap either way.
            self._scratch = self._scratch_for = None
        if self._scratch is None:
            self._scratch = GmState([Eval()], [node], self.state.globals, [])
            self._scratch_for = node
        # In instalments rather than one call, so the wall clock gets a
        # word in between them — see `patience`.
        spent = 0
        while True:
            try:
                run(self._scratch, max_steps=min(65_536, self.fuel - spent))
                break
            except StepLimit:
                spent += 65_536
                if spent >= self.fuel or (self._deadline is not None
                                          and monotonic() > self._deadline):
                    return None
        out = self._scratch.stack[0] if self._scratch.stack else node
        self._scratch = self._scratch_for = None
        while isinstance(out, NInd) and out.target is not None:
            out = out.target
        return out

    def _flat(self, args):
        """A payload's fields, flattened like `audioscore._read_flat`."""
        from .gmachine import NCon, NNum

        out = []
        for a in args:
            node = self._whnf(a)
            if node is None:
                return None
            if isinstance(node, NNum):
                out.append(node.n)
            elif isinstance(node, NCon):
                inner = self._flat(node.args)
                if inner is None:
                    return None
                out.append(inner)
            else:
                raise ScoreError(
                    f"a payload field that is not a value: "
                    f"{type(node).__name__}")
        return tuple(out)

    def _event(self, cell):
        """`(onset, offset, bank, payload)` from one cell, or `None` — owed.

        Re-entered from the top after a park; everything already forced is
        WHNF in the shared heap, so only the unfinished field costs again.
        """
        from .gmachine import NCon, NNum, is_tuple

        head = self._whnf(cell)
        if head is None:
            return None
        if not is_tuple(head, 3):
            raise ScoreError("expected an (onset, offset, voice) triple")
        ticks = []
        for arg in head.args[:2]:
            node = self._whnf(arg)
            if node is None:
                return None
            if not isinstance(node, NNum):
                raise ScoreError("expected a number in a stream event")
            ticks.append(node.n)
        voice = self._whnf(head.args[2])
        if voice is None:
            return None
        if not isinstance(voice, NCon):
            raise ScoreError("expected a `Voice` value")
        bank = self.by_tag.get(voice.tag)
        if bank is None:
            raise ScoreError(
                f"a note assigned to a voice bank this program does not "
                f"declare (constructor tag {voice.tag})")
        payload = self._flat(voice.args)
        if payload is None:
            return None
        return (ticks[0], ticks[1], bank, payload)

    # -- the demand -----------------------------------------------------------

    def pull(self, horizon: int) -> list:
        """Every event with onset below `horizon` ticks, budget permitting."""
        from .gmachine import NCon

        from time import monotonic

        out = []
        self.stalled = False
        self._deadline = (None if self.patience is None
                          else monotonic() + self.patience)
        cons = self.state.cons["Cons"].tag
        nil = self.state.cons["Nil"].tag
        while not self.done:
            if len(out) >= self.burst or (self._deadline is not None
                                          and monotonic() > self._deadline):
                self.stalled = True         # outran a budget, not the horizon
                break
            if self.ready is not None:
                if self.ready[0] >= horizon:
                    break
                out.append(self.ready)
                self.ready = None
                continue
            node = self._whnf(self.node)
            if node is None:
                self.stalled = True
                break
            if not isinstance(node, NCon) or node.tag not in (cons, nil):
                raise ScoreError("expected a list cell in the score stream")
            self.node = node                # WHNF remembered: re-asking is free
            if node.tag == nil:
                self.done = True
                break
            event = self._event(node.args[0])
            if event is None:
                self.stalled = True
                break
            self.node = node.args[1]
            self.ready = event
        if self.done:
            pass                            # nothing more is coming; `frontier`
                                            # stops mattering
        elif self.stalled:
            if out:
                self.frontier = max(self.frontier, out[-1][0])
        else:
            self.frontier = max(self.frontier, horizon)
        return out


class LazyPerformer:
    """A performer whose score arrives as it is forced — stage two.

    The same two questions as `Performer` — `advance(t)`, `seek(t)`, with
    `values` for a source to read — plus the two answers only an
    unfolding score needs: a **stall is absence** (rendering never stops;
    the future waits, and the `transcript` names the beat), and a note
    whose beat has passed when it finally appears is **dropped, and said
    so** — a section that lost its place rejoins at the current bar, it
    does not play the missed bars fast.

    The pending heap is what absorbs the stream's small local disorder
    (`at` with a negative offset across a seam): events are admitted as
    they appear but emitted in `(sample, releases-first)` order, and only
    up to the stream's `frontier` — the tick below which nothing new can
    appear — so nothing is emitted that a later arrival could contradict.
    """

    def __init__(self, stream, tempo, rate: int, allocators: dict, *,
                 block: int, horizon: float = 4.0):
        from .tempo import TempoEnvelope, constant

        if block <= 0:
            raise ScoreError(f"a block size of {block}")
        self.stream = stream
        self.tempo = tempo
        self._env = (tempo if isinstance(tempo, TempoEnvelope)
                     else constant(tempo))
        self.rate, self.block = rate, block
        self.allocators = allocators
        #: How many beats ahead of the clock the stream is forced.
        self.horizon = horizon
        self.values: dict = {}
        #: What the performance had to decide beyond the notes:
        #: `("stall", beat)` and `("dropped", beat, bank)` entries.
        self.transcript: list = []
        #: Every event ever pulled, in arrival order — the replay a seek
        #: walks, and stage three's log waiting for its format.
        self.history: list = []
        self.pending: list = []             # heap: (sample, order, seq, …)
        self._events = 0                    # keys handed to the allocator
        self._entries = 0                   # heap tie-break, admission order
        self._dropped: set = set()          # keys whose note-on was dropped
        self._played: set = set()           # keys sounding, off still owed
        self.position = -1                  # the last `t` advanced to
        self._stalling = False

    # -- arithmetic shared with the eager half --------------------------------

    def _boundary(self, at: int) -> int:
        return (at // self.block) * self.block

    def _tick_at(self, t: int) -> float:
        """The tick the sample clock stands at — the beat, resolved."""
        return self._env.beat_at(t / self.rate) * TICKS_PER_BEAT

    # -- taking what the stream yields -----------------------------------------

    def _admit(self, event, *, live: bool):
        onset, offset, bank, payload = event
        start = samples_of(onset, self.tempo, self.rate)
        end = max(samples_of(offset, self.tempo, self.rate), start)
        if live and self._boundary(start) <= self.position:
            self.transcript.append(
                ("dropped", onset / TICKS_PER_BEAT, bank))
            return
        key = self._events
        self._events += 1
        heappush(self.pending,
                 (start, 1, self._entries, key, bank, payload, False))
        heappush(self.pending,
                 (end, 0, self._entries + 1, key, bank, None, True))
        self._entries += 2

    def _pull(self, t: int):
        horizon = int(self._tick_at(t) + self.horizon * TICKS_PER_BEAT) + 1
        for event in self.stream.pull(horizon):
            self.history.append(event)
            self._admit(event, live=True)
        if self.stream.stalled and not self._stalling:
            self.transcript.append(("stall", self._tick_at(t) / TICKS_PER_BEAT))
        self._stalling = self.stream.stalled

    def _covered(self):
        """The sample below which the pending heap is the whole truth."""
        if self.stream.done:
            return None
        return samples_of(self.stream.frontier, self.tempo, self.rate)

    def _perform(self, key, bank, payload, at, is_off):
        allocator = self.allocators.get(bank)
        if allocator is None:
            raise ScoreError(
                f"this piece assigns notes to `{bank}` and no allocator was "
                f"given for it; there is "
                + (", ".join(f"`{b}`" for b in sorted(self.allocators))
                   or "none"))
        return (allocator.note_off(key, at) if is_off
                else allocator.note_on(key, _flatten(payload), at))

    # -- performing -------------------------------------------------------------

    def advance(self, t: int) -> list:
        """Force to the horizon, perform what is due — the spec's own loop."""
        self._pull(t)
        covered = self._covered()
        out = []
        held = []
        while self.pending:
            entry = heappop(self.pending)
            sample, order, _seq, key, bank, payload, is_off = entry
            boundary = self._boundary(sample)
            if boundary > t:
                heappush(self.pending, entry)
                break
            # Beyond the frontier a later arrival could still precede it —
            # except a note-off of something already sounding, which owes
            # order to nobody and must play out however long the stall.
            if (covered is not None and sample > covered
                    and not (is_off and key in self._played)):
                held.append(entry)
                continue
            if is_off and key in self._dropped:
                self._dropped.discard(key)
                continue
            if not is_off and boundary <= self.position:
                # Admitted in time, but gated behind a stall until its
                # beat had passed: the rejoin rule, at the other gate.
                self.transcript.append(
                    ("dropped", self._tick_at(sample) / TICKS_PER_BEAT, bank))
                self._dropped.add(key)
                continue
            (self._played.discard if is_off else self._played.add)(key)
            for chan, value in self._perform(key, bank, payload, sample,
                                             is_off):
                self.values[chan] = value
                out.append((boundary, chan, value))
        for entry in held:
            heappush(self.pending, entry)
        self.position = max(self.position, t)
        return out

    # -- the transport's questions ----------------------------------------------

    def seek(self, t: int) -> list:
        """Release what sounds, stand at `t` as if played from the top.

        The replay walks `history` — everything the stream has ever
        yielded, which laziness has memoised — so seeking is never a
        second performance of the generator.  A target beyond the
        frontier forces the stream forward first; what cannot be forced
        stalls, exactly as it would have live.
        """
        self._pull(t)
        off = []
        for allocator in self.allocators.values():
            off += allocator.all_off(t)
        self.allocators = {name: Allocator(a.channels, a.policy)
                           for name, a in self.allocators.items()}
        self.values = {}
        self.pending = []
        self._dropped = set()
        self._events = self._entries = 0
        entries = []
        for event in self.history:
            onset, offset, bank, payload = event
            start = samples_of(onset, self.tempo, self.rate)
            end = max(samples_of(offset, self.tempo, self.rate), start)
            key = self._events
            self._events += 1
            entries.append((start, 1, self._entries, key, bank, payload,
                            False))
            entries.append((end, 0, self._entries + 1, key, bank, None, True))
            self._entries += 2
        entries.sort()
        covered = self._covered()
        self._played = set()
        for entry in entries:
            sample, order, _seq, key, bank, payload, is_off = entry
            if (self._boundary(sample) < t
                    and (covered is None or sample <= covered
                         or (is_off and key in self._played))):
                (self._played.discard if is_off else self._played.add)(key)
                for chan, value in self._perform(key, bank, payload, sample,
                                                 is_off):
                    self.values[chan] = value
            else:
                heappush(self.pending, entry)
        kept = []
        for chan, value in off:
            if chan not in self.values:
                self.values[chan] = value
                kept.append((chan, value))
        self.position = t - 1
        return kept
