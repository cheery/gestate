"""Reactive driver — implements Rizzo's ticked / advance / step semantics.

This runs *above* the G-machine's ``evaluate`` loop.  It owns the outer
κ ↦ w ⇒ sequence: each instant triggers a sweep over all live signals,
advancing those whose tails are ``ticked`` and leaving the rest
unchanged.  When ``advance`` reaches a ``tagExists5``-wrapped function
application it re-enters the G-machine to run user code.

**An instant is a set of arrivals, not one.**  The paper writes κ ↦ w —
a single channel and a single value per step — and this driver generalises
it to a map from channel id to value, ``Arrivals`` below.  One arrival is
the paper's rule unchanged, and that is the case every FRP test exercises;
several arrivals in one instant is what a *block boundary* is, where an
audio clock and a control clock tick together.  Without it `sync` can never
report ``SyncBoth`` from the driver — the two clocks arrive as two instants,
and everything downstream of the slower one takes an extra step that the
faster one never asked for.  `spec/frp.md` §"Several arrivals in one
instant" states the extension and what it must degenerate to;
`spec/liveaudio.md` open question 3 is why it was built.
"""

from __future__ import annotations

from .gmachine import (
    GmState, GmError,
    NCon, NSig, NChan,
    TAG_WAIT, TAG_WATCH, TAG_SYNC, TAG_NEVER, TAG_TAIL, TAG_EXISTS5, TAG_DELAY,
    TAG_JUST, TAG_SYNC_L, TAG_SYNC_R, TAG_SYNC_BOTH,
    _update_sig, _deref,
    step, run,
    Mkap, Eval, Unwind,
)


#: complaint  machine — the reactive machine's own invariants, and the host's use of its instants
class ReactiveError(Exception):
    pass


# ---------------------------------------------------------------------------
# Arrivals — what an instant is
# ---------------------------------------------------------------------------
#
# ``Arrivals`` is ``{channel id: input node}``: the channels that ticked in
# this instant, each with the value it carried.  It replaces the ``k: int``
# that ``ticked``/``advance``/``updateOne``/``reactiveStep`` used to thread,
# and it is the *only* change to their rules — every one of them asked
# exactly two questions of ``k``, "is this channel the one that ticked" and
# "what did it carry", and both have per-channel answers now.
#
# A channel may appear at most once: two values on one channel in one
# instant is two instants, and `_check_arrivals` rejects it rather than
# letting the second silently win.

Arrivals = dict[int, object]


# ---------------------------------------------------------------------------
# Reactive state
# ---------------------------------------------------------------------------

class GmReactive:
    """Mutable reactive state wrapping a G-machine ``GmState``.

    ``earlier`` — signals being processed this step (consumed left-to-right).
    ``gm.now`` — signals accumulated so far (initially, then rebuilt per step).
    ``clocks`` — each earlier-heap signal's clock, taken *before* the sweep
    began (see ``reactive_step``); empty when ``check_clocks`` is off.
    """

    __slots__ = ("gm", "earlier", "clocks", "check_clocks")

    def __init__(self, gm: GmState, *, check_clocks: bool = True):
        self.gm = gm
        self.earlier: list = []
        self.clocks: dict = {}
        self.check_clocks = check_clocks

    @property
    def chans(self) -> dict:
        """The channel context Δ: channel id → element type, as allocated.

        Lives on the ``GmState`` because ``NewChan`` writes it, including
        from the sub-evaluations ``advance`` runs — the GUI pattern mints a
        channel per widget at run time.
        """
        return self.gm.chans


# ---------------------------------------------------------------------------
# ticked  — Fig. 10 prediction
# ---------------------------------------------------------------------------

def ticked(arrivals: Arrivals, node, reactive: GmReactive) -> bool:
    """Predict whether a ⃝∃ node's tail fires on this instant's arrivals."""
    node = _deref(node)
    if isinstance(node, NCon):
        if node.tag == TAG_NEVER:
            return False
        # No case for TAG_DELAY: `delay t : ⃝∀A` is never a signal tail
        # (tails are ⃝∃(Sig A)), so it cannot reach `ticked`.  An earlier
        # revision fired unconditionally here, which made an empty clock
        # behave like a universal one.
        if node.tag == TAG_EXISTS5 and len(node.args) >= 2:
            _, w = node.args
            return ticked(arrivals, w, reactive)
        if node.tag == TAG_WAIT and len(node.args) >= 1:
            chan_node = _deref(node.args[0])
            if isinstance(chan_node, NChan):
                return chan_node.chan_id in arrivals
            return False
        if node.tag == TAG_WATCH and len(node.args) >= 1:
            sig = _deref(node.args[0])
            if isinstance(sig, NSig):
                # "in1 v ⟨⊤⟩" — value is Just-shaped AND updated this step
                _require_current(sig, "watch")
                return _is_just(_deref(sig.value)) and sig.ticked
            return False
        if node.tag == TAG_TAIL and len(node.args) >= 1:
            sig = _deref(node.args[0])
            if isinstance(sig, NSig):
                _require_current(sig, "tail")
                return sig.ticked
            return False
        if node.tag == TAG_SYNC and len(node.args) >= 2:
            v, w = node.args
            return ticked(arrivals, v, reactive) or ticked(arrivals, w, reactive)
    return False


def _is_just(node) -> bool:
    """Is ``node`` a ``Just v``?  ``watch l`` fires exactly when ``l`` is."""
    return isinstance(node, NCon) and node.tag == TAG_JUST


def _require_current(sig: NSig, what: str) -> None:
    """`ticked` for `watch l`/`tail l` reads `l`'s state on the *new* heap.

    Both rules in fig. 10 are stated against η_N, so `l` must already have
    been swept.  Signals are processed in allocation order and a signal can
    only reference ones allocated before it, so this holds for every
    well-typed program — see `_sighead` for the same check on `head`.
    """
    if not sig.current:
        #: complaint  author, unplaced — fixme.md F159: reading a signal out of turn is the program's mistake, and the machine has the node but not its span
        raise ReactiveError(
            f"{what} of a signal on the earlier heap: it has not been "
            f"updated yet this step.  Signals are swept in allocation "
            f"order, so a signal may only depend on ones allocated before it"
        )


# ---------------------------------------------------------------------------
# cl — Fig. 10's clock function
# ---------------------------------------------------------------------------
#
#   cl(never)    = ∅          cl(wait κ)    = {κ}       cl(watch l) = {l}
#   cl(v 5 w)    = cl(w)      cl(sync v w)  = cl(v) ∪ cl(w)
#   cl(tail l)   = cl(w)   where l ↦ v⟨U⟩w
#
# A clock is a set of *sources*: channels, written ``("chan", id)``, and
# partial signals being watched, written ``("sig", cell)``.  `v 5 w` takes
# w's clock alone because the ⃝∀ side is available whenever anything ticks
# and so contributes nothing.

def cl(node, _seen: frozenset = frozenset()) -> frozenset:
    """The clock of a ⃝∃ value, against the heap as it stands.

    Callers that need the *pre-step* clock — which is the only kind fig.
    10's invariant is stated for — must call this before any cell is
    updated; ``reactive_step`` does.
    """
    node = _deref(node)
    if not isinstance(node, NCon):
        return frozenset()
    if id(node) in _seen:
        # Rizzo's types forbid reference cycles (Thm 4.1); if one shows up
        # anyway, stop rather than recurse forever.
        return frozenset()
    seen = _seen | {id(node)}

    tag, args = node.tag, node.args
    if tag == TAG_NEVER:
        return frozenset()
    if tag == TAG_WAIT and args:
        chan_node = _deref(args[0])
        if isinstance(chan_node, NChan):
            return frozenset({("chan", chan_node.chan_id)})
        return frozenset()
    if tag == TAG_WATCH and args:
        sig = _deref(args[0])
        return frozenset({("sig", sig)}) if isinstance(sig, NSig) else frozenset()
    if tag == TAG_EXISTS5 and len(args) >= 2:
        return cl(args[1], seen)
    if tag == TAG_SYNC and len(args) >= 2:
        return cl(args[0], seen) | cl(args[1], seen)
    if tag == TAG_TAIL and args:
        sig = _deref(args[0])
        return cl(sig.tail, seen) if isinstance(sig, NSig) else frozenset()
    return frozenset()


def clock_fires(arrivals: Arrivals, clock: frozenset) -> bool:
    """Fig. 10's invariant, read left to right (§4.3, p. 17):

        ticked^κ_{η_N}(u)  iff  κ ∈ cl_η(u), or some l ∈ cl_η(u) has
                                η_N(l) = in1 v₁⟨⊤⟩v₂

    i.e. the input arrived on a channel this value waits on, or a partial
    signal it watches has just updated to a ``Just``.

    With several arrivals the left disjunct is asked of each: a value fires
    if *any* channel it waits on ticked.  At one arrival this is the rule
    above, unchanged.
    """
    if any(("chan", k) in clock for k in arrivals):
        return True
    return any(
        kind == "sig" and src.ticked and _is_just(_deref(src.value))
        for kind, src in clock
    )


# ---------------------------------------------------------------------------
# advance  — Fig. 10 advance semantics
# ---------------------------------------------------------------------------

def _apply(gm: GmState, fn, arg):
    """Evaluate ``fn arg`` to WHNF, leaving ``gm`` as it was found.

    The advance semantics is the one place the scheduler re-enters the
    evaluator, so it runs on a scratch state rather than splicing code and
    dump frames into the live machine: a ``GmError`` raised in here would
    otherwise leave the machine wedged mid-frame.  The heap is shared —
    nodes are objects — so the result and any signals allocated along the
    way belong to the same graph.
    """
    scratch = GmState([Mkap(), Eval()], [fn, arg], gm.globals, [],
                      now=gm.now, chanCounter=gm.chanCounter, chans=gm.chans)
    run(scratch)
    gm.chanCounter = scratch.chanCounter
    return _deref(scratch.stack[0])


def advance(arrivals: Arrivals, tail_node, reactive: GmReactive) -> tuple:
    """Advance a ⃝∃ tail node one step.

    Returns ``(new_value_node, updated_reactive)``.

    The input is no longer a single node handed down the recursion: `wait κ`
    reads *its own* channel out of ``arrivals``.  With one arrival the two
    are the same value and the old signature was right; with two, handing
    the same node to both sides of a `sync` would give the control clock
    the audio clock's sample.
    """
    tail_node = _deref(tail_node)
    if not isinstance(tail_node, NCon):
        raise ReactiveError(f"advance on non-NCon: {type(tail_node).__name__}")

    tag = tail_node.tag
    args = tail_node.args

    if tag == TAG_DELAY:
        # Unwrap delay — a ⃝∀ value is available whenever any clock ticks.
        if not args:
            raise ReactiveError("advance TAG_DELAY: empty node")
        return (_deref(args[0]), reactive)

    if tag == TAG_WAIT:
        chan_node = _deref(args[0]) if args else None
        if not isinstance(chan_node, NChan):
            raise ReactiveError("advance TAG_WAIT: argument is not a channel")
        if chan_node.chan_id not in arrivals:
            # `ticked` gates every call, so this is unreachable from the
            # sweep; it is here because the two must not be able to drift.
            raise ReactiveError(
                f"advance TAG_WAIT on channel {chan_node.chan_id}, which did "
                f"not arrive this instant (arrived: "
                f"{sorted(arrivals) or 'none'})")
        return (arrivals[chan_node.chan_id], reactive)

    if tag == TAG_WATCH:
        sig = _deref(args[0])
        if isinstance(sig, NSig):
            _require_current(sig, "watch")
            value = _deref(sig.value)
            if _is_just(value) and value.args:
                return (value.args[0], reactive)
        raise ReactiveError("advance TAG_WATCH on non-Just or non-NSig")

    if tag == TAG_TAIL:
        return (_deref(args[0]), reactive)

    if tag == TAG_EXISTS5:
        # ⟨v 5 w⟩ ⇒ f ⟨w⟩ where v = delay f.  The ⃝∀ side carries no clock
        # of its own, so it is simply unwrapped; the ⃝∃ side supplies the
        # value and the clock.
        d_node = _deref(args[0])
        v_node = _deref(args[1])
        v_new, reactive = advance(arrivals, v_node, reactive)
        if not isinstance(d_node, NCon) or d_node.tag != TAG_DELAY:
            raise ReactiveError("advance TAG_EXISTS5: dNode not TAG_DELAY")
        if not d_node.args:
            raise ReactiveError("advance TAG_EXISTS5: empty delay node")
        f_node = d_node.args[0]
        return (_apply(reactive.gm, f_node, v_new), reactive)

    if tag == TAG_SYNC:
        v, w = _deref(args[0]), _deref(args[1])
        tv = ticked(arrivals, v, reactive)
        tw = ticked(arrivals, w, reactive)

        if tv and not tw:
            v_new, reactive = advance(arrivals, v, reactive)
            return (_pack_left1(v_new), reactive)
        elif tw and not tv:
            w_new, reactive = advance(arrivals, w, reactive)
            return (_pack_left2(w_new), reactive)
        else:
            # Both ticked simultaneously.  Before arrivals were a set this
            # was reachable only when the two sides shared one channel; a
            # block boundary — an audio clock and a control clock arriving
            # together — is now the ordinary way to get here.
            v_new, reactive = advance(arrivals, v, reactive)
            w_new, reactive = advance(arrivals, w, reactive)
            return (_pack_both(v_new, w_new), reactive)

    raise ReactiveError(f"advance: unknown tag {tag}")


# `sync v w` produces a value of `Sync A B`, an ordinary data type that
# user code pattern-matches — not another delayed computation.  Building a
# TAG_SYNC node here instead would hand `case` a tag it has no alternative
# for.
def _pack_left1(v) -> NCon:
    return NCon(TAG_SYNC_L, (v,))


def _pack_left2(w) -> NCon:
    return NCon(TAG_SYNC_R, (w,))


def _pack_both(v, w) -> NCon:
    return NCon(TAG_SYNC_BOTH, (v, w))


# ---------------------------------------------------------------------------
# updateOne — process one signal from ``earlier``
# ---------------------------------------------------------------------------

def _update_one(arrivals: Arrivals, reactive: GmReactive):
    """Pop the first signal from ``earlier``, advance if ticked, update in place."""
    sig = reactive.earlier.pop(0)
    if not isinstance(sig, NSig):
        raise ReactiveError(f"updateOne: expected NSig, got {type(sig).__name__}")

    tail = _deref(sig.tail)
    fires = ticked(arrivals, tail, reactive)

    if reactive.check_clocks and sig in reactive.clocks:
        predicted = clock_fires(arrivals, reactive.clocks[sig])
        if predicted != fires:
            raise ReactiveError(
                f"ticked/cl disagree on channels {sorted(arrivals)}: cl says "
                f"{'fires' if predicted else 'does not fire'}, ticked says "
                f"{'fires' if fires else 'does not fire'}.  The clock was "
                f"taken before the sweep, as §4.3 requires; a mismatch "
                f"means the two are reading different heaps"
            )

    if not fires:
        _update_sig(sig, sig.value, sig.tail, False)
        reactive.gm.now.append(sig)
    else:
        # Running user code can allocate signals of its own (`switch` and
        # friends build new dataflow), and `SigCons` registers each on the
        # now heap as it goes.  Hold them aside: `l` keeps its identity —
        # everything already pointing at it must see the update — so the
        # signal `advance` returns is folded into `l` in place and must
        # not also survive as a cell of its own.
        now = reactive.gm.now
        mark = len(now)
        l_new, reactive = advance(arrivals, tail, reactive)
        allocated = now[mark:]
        del now[mark:]

        if isinstance(l_new, NSig):
            _update_sig(sig, l_new.value, l_new.tail, True)
            allocated = [n for n in allocated if n is not l_new]
        else:
            # advance returned a plain value — wrap in signal with `never` tail
            _update_sig(sig, l_new, NCon(TAG_NEVER, ()), True)
        now.append(sig)
        now.extend(allocated)


# ---------------------------------------------------------------------------
# reactiveStep — full sweep
# ---------------------------------------------------------------------------

def reactive_step(arrivals: Arrivals, reactive: GmReactive) -> GmReactive:
    """Process one instant — all of ``arrivals`` at once — over every live signal."""
    reactive.earlier = list(reactive.gm.now)

    # Clocks are taken with respect to the heap from *before* the step
    # (§4.3): the timing a signal carries once it has been advanced
    # describes the *next* step, so a driver that recomputes clocks
    # mid-sweep is answering a different question.  Snapshotting them
    # here is what makes that mistake detectable — `_update_one` checks
    # each `ticked` call against the clock captured now.
    if reactive.check_clocks:
        reactive.clocks = {sig: cl(sig.tail) for sig in reactive.earlier}

    # Everything moves behind the ✓ frontier; `_update_sig` puts each
    # cell back on the now heap as the sweep reaches it.
    for sig in reactive.earlier:
        sig.current = False
    reactive.gm.now = []

    while reactive.earlier:
        _update_one(arrivals, reactive)
    reactive.clocks = {}
    return reactive


# ---------------------------------------------------------------------------
# react — stream processor
# ---------------------------------------------------------------------------

def react(reactive: GmReactive, inputs: list[tuple[int, object]]) -> list[GmReactive]:
    """Run a sequence of (channel_id, value) inputs, returning state snapshots.

    **One input is one instant** — the paper's `react = scanl reactiveStep`,
    unchanged.  Two channels handed to this function are two instants, which
    is the right reading when they are two independent events; when they are
    two clocks ticking *together*, use `react_instant`.
    """
    return [react_instant(reactive, [pair]) for pair in inputs]


def react_instant(reactive: GmReactive, arrivals: list[tuple[int, object]]) -> GmReactive:
    """Run **one** instant in which every channel in ``arrivals`` ticked.

    This is the driver's generalisation of κ ↦ w, and the reason it exists
    is that a block boundary is not a sequence of events: an audio clock and
    a control clock tick at the same instant, and running them one after the
    other advances everything downstream of the control clock by a step that
    produces no sample.  `sync` reports `SyncBoth` here and nowhere else in
    the driver.

    At one arrival it is `reactive_step` on that channel, which is what
    `react` calls it for.
    """
    return reactive_step(_check_arrivals(reactive, arrivals), reactive)


def _check_arrivals(reactive: GmReactive, arrivals) -> Arrivals:
    """Validate an instant's `(κ, w)` pairs, and lift each `w` to a node.

    `κ : Chan B ∈ Δ_n` is a premise of the productivity theorem (§4.6), so
    an input is only well-formed if it names a channel the program has
    actually allocated.  Δ grows as the program runs — `reactive.chans`
    picks up channels minted during a sweep as well as at start-up.
    """
    from .gmachine import NNum

    chans = reactive.chans
    out: Arrivals = {}
    for k, val in arrivals:
        if k not in chans:
            known = ", ".join(
                f"{cid} : Chan {ty or '?'}" for cid, ty in sorted(chans.items())
            ) or "none"
            raise ReactiveError(
                f"input on channel {k}, which the program never allocated "
                f"(channel context: {known})"
            )
        if k in out:
            # Two values on one channel is two instants.  Silently keeping
            # the last would drop an input; saying so keeps the caller
            # honest about which it meant.
            raise ReactiveError(
                f"channel {k} given two values in one instant: an instant is "
                f"at most one arrival per channel, so these are two instants"
            )

        elem = chans[k]
        node = NNum(val) if isinstance(val, int) else val
        if elem == "Int" and not isinstance(_deref(node), NNum):
            raise ReactiveError(
                f"channel {k} : Chan Int given a non-integer input: {node!r}"
            )
        out[k] = node
    if not out:
        raise ReactiveError(
            "an instant with no arrivals: nothing would be ticked, so the "
            "sweep would rewrite every signal unchanged")
    return out


# ---------------------------------------------------------------------------
# initProgram — initial G-machine run, collect signals
# ---------------------------------------------------------------------------

def init_program(gm: GmState) -> GmReactive:
    """Run the initial program term through ``evaluate``, producing a reactive state."""
    run(gm)
    reactive = GmReactive(gm)
    # `gm.now` was populated by SigCons during the initial run
    return reactive
