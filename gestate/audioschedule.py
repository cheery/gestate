"""A schedule of control-channel changes, and the two ways to play it.

`render(control_every=n)` drives every control channel with the sample
index.  That is enough for a knob — the point there was only that the
control clock *ticks* — and useless for anything with a shape.  A note
schedule has a shape: `gateAt` becomes 1200 at some particular moment and
nothing else changes.

**This exists so notes can be checked at all.**  Every stage of
`spec/liveaudio.md` is verified by rendering the same program through the
interpreter and through the engine and comparing samples, and neither the
voice bank nor the `Score` scheduler can be built to that standard until
both sides can be handed the same schedule.  So it comes first.

The key is the **channel name**.  The interpreter drives channels; the
engine drives nodes; `Node.chan` is the one name both can resolve, which is
why it was added.

    schedule = Schedule()
    schedule.change(0,    "g0", 1)         # voice 0 on, from the start
    schedule.change(4096, "g0", 0)         # and off again

    render(source, seconds, rate, control_every=64, schedule=schedule)
    run(graph, samples, block=64, control=schedule.control_for(graph))

**Values are held**, exactly as a control source holds its value across a
block: `value_at` is the most recent change at or before the instant asked
about, and a channel with no change yet reads as `None` — which the callers
turn into the source's own initial value rather than 0, for the reason
`audiomidi` records.

**Delivery time is not event time.**  A note that starts at sample 1200
wants its `gateAt` *delivered* at the block boundary at or before 1200, so
the voice can compare its own `ticks` against 1200 and begin mid-block.
`deliver` does that arithmetic; `change` takes a delivery time directly.
Keeping them separate is deliberate — conflating them is how an engine
ends up quantising every onset to a block.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field


class ScheduleError(Exception):
    pass


@dataclass
class Schedule:
    """Control-channel changes, in delivery order.

    Not a stream of events: a *step function per channel*.  That is what a
    control source is, so a schedule that recorded anything richer would be
    recording something the engine cannot represent.
    """

    #: Channel name → `([sample], [value])`, both sorted by sample.
    changes: dict = field(default_factory=dict)

    # -- building -----------------------------------------------------------

    def change(self, sample: int, chan: str, value) -> "Schedule":
        """`chan` reads as `value` from `sample` onwards.  Returns self."""
        if sample < 0:
            raise ScheduleError(f"a change at sample {sample}, before the start")
        samples, values = self.changes.setdefault(chan, ([], []))
        i = bisect_right(samples, sample)
        if i and samples[i - 1] == sample:
            values[i - 1] = value           # same instant: the last one wins
            return self
        samples.insert(i, sample)
        values.insert(i, value)
        return self

    def deliver(self, sample: int, chan: str, value, *,
               block: int) -> "Schedule":
        """Deliver `value` at the block boundary at or before `sample`.

        The one piece of arithmetic that keeps onsets sample-accurate: the
        *value* names the instant the note starts, and this makes sure the
        voice is holding it before that instant arrives.  A note in the
        first block is delivered at 0.
        """
        if block <= 0:
            raise ScheduleError(f"a block size of {block}")
        return self.change((sample // block) * block, chan, value)

    # -- reading ------------------------------------------------------------

    def channels(self) -> list:
        return sorted(self.changes)

    def value_at(self, chan: str, t: int):
        """What `chan` reads at instant `t`, or `None` before its first change."""
        entry = self.changes.get(chan)
        if entry is None:
            return None
        samples, values = entry
        i = bisect_right(samples, t)
        return None if i == 0 else values[i - 1]

    def horizon(self) -> int:
        """One past the last change, so a caller knows how long to render."""
        return max((s[-1] for s, _v in self.changes.values() if s), default=0) + 1

    # -- playing it ---------------------------------------------------------

    def control_for(self, graph, default=None):
        """The `control(node_id, t)` the engine and generated code take.

        A channel this schedule says nothing about falls back to the
        source's **own initial value** — the synth's declared default —
        rather than to zero.  `audiomidi` records why: a host answering 0
        silently overrides what the program said it sounds like.
        """
        by_node = {}
        for chan, node in graph.control_by_chan().items():
            by_node[node.id] = (chan, node.init)
        unknown = set(self.changes) - set(graph.control_by_chan())
        if unknown:
            raise ScheduleError(
                "this schedule names channels the graph does not have: "
                + ", ".join(sorted(unknown)) + ".  It has "
                + (", ".join(sorted(graph.control_by_chan())) or "none"))

        def control(node: int, t: int):
            entry = by_node.get(node)
            if entry is None:
                return 0
            chan, init = entry
            value = self.value_at(chan, t)
            if value is not None:
                return value
            return init if default is None else default

        return control

    def arrivals_at(self, t: int, channels: dict) -> list:
        """`[(channel id, value)]` for the interpreter, at instant `t`.

        `channels` maps a channel *name* to the id the running program
        allocated it, which is a runtime fact — see `fixme.md` F91 for what
        happens to code that guesses it.
        """
        out = []
        for chan, cid in channels.items():
            value = self.value_at(chan, t)
            if value is not None:
                out.append((cid, value))
        return out
