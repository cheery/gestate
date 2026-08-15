"""Run an extracted graph — `spec/liveaudio.md` stage 2's verification.

Naive on purpose: one sample at a time, a Python value per node, no blocks
and no buffers.  Its whole job is to say what the graph *means*, so that
`render()` and it can be compared sample for sample and the meaning of the
graph is fixed before anything depends on it.  Stage 3's `render_block` and
stage 4's generated code are then checked against this, not against a
description of it.

**The semantics come from `signal.ges` and nowhere else.**

    mapSig f s = f (head s) ::: …
    scan f z s = z ::: (delay (q2 => q2 f (f z (head s))) <*> q <@> tail s)

`map` is pointwise.  `scan` holds `z` at the first instant and

    out[t] = f(out[t-1], in[t])          for t > 0

— its own state from the previous instant, and its input from **this** one.
That asymmetry is not a choice; it is what the definition says, and reading
it wrong is the exact failure stage 2's risk names ("`scan`'s initial value
is placed an instant off").  It was read wrong here first, and the
bit-identical check caught it on the first run.

The reason it surprises: `f z (head s)` sits *inside* the `delay`, so it is
evaluated when the delay fires — one instant later — and by then `s` has
been **overwritten in place** with its next value.  A signal is a cell, not
a stream, so `head s` under a `delay` reads the new sample rather than the
one that was there when the closure was built.  The property the whole
project rests on for bounded memory turns out to decide the arithmetic too.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .audioir import Call, Case, Con, Const, Field, Graph, Let, Prim, Var
from .gmachine import MATH_FLOAT


class EngineError(Exception):
    pass


# ── The IR ──────────────────────────────────────────────────────────────────


def evaluate(e, env: dict, graph: Graph):
    """Evaluate an IR expression.  Strict, and never allocates a closure."""
    while True:
        if isinstance(e, Const):
            return e.value
        if isinstance(e, Var):
            try:
                return env[e.name]
            except KeyError:
                raise EngineError(f"unbound `{e.name}`") from None
        if isinstance(e, Prim):
            return _prim(e.op, [evaluate(a, env, graph) for a in e.args],
                         graph)
        if isinstance(e, Con):
            return (e.tag, tuple(evaluate(a, env, graph) for a in e.args))
        if isinstance(e, Field):
            base = evaluate(e.base, env, graph)
            return base[1][e.index]
        if isinstance(e, Call):
            fn = graph.funcs.get(e.fn)
            if fn is None:
                raise EngineError(f"no function `{e.fn}` in the graph")
            args = [evaluate(a, env, graph) for a in e.args]
            env = dict(zip(fn.params, args))
            e = fn.body                       # a tail call, as a loop
            continue
        if isinstance(e, Let):
            env = dict(env)
            env[e.name] = evaluate(e.value, env, graph)
            e = e.body
            continue
        if isinstance(e, Case):
            scrut = evaluate(e.scrut, env, graph)
            if not isinstance(scrut, tuple):
                raise EngineError(f"`case` on a non-constructor: {scrut!r}")
            for tag, binders, body in e.alts:
                if tag == scrut[0]:
                    if binders:
                        env = dict(env)
                        env.update(zip(binders, scrut[1]))
                    e = body
                    break
            else:
                raise EngineError(f"no alternative for tag {scrut[0]}")
            continue
        raise EngineError(f"not IR: {e!r}")


def call(graph: Graph, name: str, args: list):
    fn = graph.funcs[name]
    return evaluate(fn.body, dict(zip(fn.params, args)), graph)


def _prim(op: str, args: list, graph: Graph):
    """The G-machine's primitives, with its exact arithmetic.

    Not "the obvious Python equivalent" — *the same expression*
    `gestate/gmachine.py` evaluates, so that a bit-identical comparison is
    a real test of the graph rather than a test of two people's arithmetic
    agreeing.  `//` and `%` floor here because they floor there.
    """
    try:
        fn = _PRIMS[op]
    except KeyError:
        raise EngineError(f"no primitive `{op}`") from None
    return fn(args, graph)


def _bool(b: bool, graph: Graph):
    return ((graph.true_tag if b else graph.false_tag), ())


def _checked(name, f):
    def go(args, _graph):
        if args[1] == 0:
            raise EngineError(f"{name}: division by zero")
        return f(args[0], args[1])
    return go


_PRIMS = {
    "prim_add_int": lambda a, _g: a[0] + a[1],
    "prim_sub_int": lambda a, _g: a[0] - a[1],
    "prim_mul_int": lambda a, _g: a[0] * a[1],
    "prim_div_int": _checked("DivInt", lambda x, y: x // y),
    "prim_mod_int": _checked("ModInt", lambda x, y: x % y),
    # Addition, subtraction and multiplication are shared with the integer
    # instructions in the G-machine too — Python's operators are already
    # right on either kind of number, and the separate names keep generated
    # code honest about which type it meant.
    "prim_add_float": lambda a, _g: a[0] + a[1],
    "prim_sub_float": lambda a, _g: a[0] - a[1],
    "prim_mul_float": lambda a, _g: a[0] * a[1],
    "prim_div_float": _checked("DivFloat", lambda x, y: x / y),
    "prim_mod_float": _checked("ModFloat", lambda x, y: x % y),
    "prim_eq_int": lambda a, g: _bool(a[0] == a[1], g),
    "prim_lt_int": lambda a, g: _bool(a[0] < a[1], g),
    "prim_eq_float": lambda a, g: _bool(a[0] == a[1], g),
    "prim_lt_float": lambda a, g: _bool(a[0] < a[1], g),
    "prim_to_float": lambda a, _g: float(a[0]),
    "prim_floor_float": lambda a, _g: math.floor(a[0]),
    # The transcendentals go through the same `math` the G-machine does, so
    # this renderer and the oracle cannot drift; the generated code calls
    # the same libm underneath (`spec/liveaudio.md` open question 2).
    **{f"prim_{fn}_float": (lambda f: lambda a, _g: float(f(a[0])))(
        getattr(math, fn)) for fn in MATH_FLOAT},
    "chr": lambda a, _g: a[0],
    "ord": lambda a, _g: a[0],
}


# ── The graph ───────────────────────────────────────────────────────────────


@dataclass
class State:
    """Everything a graph carries between blocks.

    Separate from the graph on purpose, and it is the shape stage 5's
    migration moves: a new graph, the old `values`, and one decision per
    node about whether its slot survives.  Stage 4's generated code is this
    as a struct.
    """
    values: list
    #: How many instants have been produced.  The engine needs it because a
    #: `scan` behaves differently at the very first one, and because the
    #: audio clock's value *is* the instant number.
    t: int = 0

    #: `node id → its ring buffer`, for the `line` nodes and nothing else.
    #: Empty for every graph without a delay line in it, which is why it is
    #: a dict rather than a second parallel list.
    lines: dict = field(default_factory=dict)

    @classmethod
    def initial(cls, graph: Graph) -> "State":
        return cls([None] * len(graph.nodes))

    def ring(self, graph: Graph, node) -> list:
        """This line's buffer, made on first use."""
        buf = self.lines.get(node.id)
        if buf is None:
            buf = line_zero(graph, node)
            self.lines[node.id] = buf
        return buf


def _tap_read(buf: list, t: int, back: float):
    """`back` samples ago, interpolated — the tap's whole arithmetic.

    Clamped to 1 .. n-1.  The lower bound is what keeps the value a
    function of the *state*: slot `t % n` still holds the sample from `n`
    instants ago and has not yet been overwritten, so reading zero back
    would hand out the wrong sample *and* let a cycle close with no delay
    in it.
    """
    n = len(buf)
    if n < 2:
        return buf[0]
    if not isinstance(back, float):
        back = float(back)
    if back < 1.0:
        back = 1.0
    elif back > n - 1:
        back = float(n - 1)
    whole = int(back)
    frac = back - whole
    near = buf[(t - whole) % n]
    far = buf[(t - whole - 1) % n]
    return near + (far - near) * frac


def line_zero(graph: Graph, node) -> list:
    """A delay line's ring: `length` values of its element type.

    **Beside `State.values` rather than in it.**  Every other node's value
    *is* its state; a `line` has a sample downstream reads and a buffer
    only it reads, and putting the buffer in the value slot would hand the
    next node a list where it expected a number.

    The cursor is the instant number: every node advances once per instant,
    so `t % length` is where the ring is, and a stored cursor would be a
    second copy of `State.t` that could disagree with it.

    A `loop`'s ring holds *states* and starts at its `init`, which is what
    makes both of its arms read `z` before anything has been written — a
    `line`'s and a `tap`'s hold samples and start at silence.
    """
    start = node.init if node.kind == "loop" else zero(graph, node.type_)
    return [start for _ in range(max(1, node.length))]


def zero(graph: Graph, type_name: str):
    """A value of this type to start a fresh node's slot at.

    Only ever read by a `scan` or a control source, and both of those are
    given their `init` instead — so this is what fills the slots whose
    value is recomputed every sample before anything looks at it.  It has
    to be *typed* all the same, because the native engine packs the state
    into a struct and a slot has a shape.
    """
    if type_name == "Float":
        return 0.0
    if type_name == "Int":
        return 0
    cons = graph.layouts[type_name][0]
    return (cons["tag"], tuple(zero(graph, f) for f in cons["fields"]))


def shape(graph: Graph, type_name: str):
    """What a value of this type is *made of*, not what it is called.

    Migration cannot compare type names: editing `Voice := Voice Float Int`
    to `Voice Float Float` leaves the name alone and changes the layout,
    and carrying the old bits into the new slot would reinterpret an
    integer as a double — silent, and audible only as a wrong noise.  A
    name is what a reader wants; a shape is what a state struct is.
    """
    if type_name in ("Int", "Float"):
        return type_name
    return tuple((c["tag"], tuple(shape(graph, f) for f in c["fields"]))
                 for c in graph.layouts[type_name])


def migrate(old: Graph, state: State, new: Graph) -> State:
    """Carry a running state across a recompile — `spec/liveaudio.md` 5.

    **A node keeps its state when its `origin` and its type both match.**
    The origin is the path of definitions it was inlined through, decided
    in stage 2 precisely so that this could be written: editing a step
    function or a folded-in constant does not move it, so the oscillator
    keeps its phase and the filter its memory while the sound changes.

    Everything else starts at its `init` — which has to be written rather
    than left empty, because `t` carries over too and the engine's
    "first instant" branch will not fire again.

    Not a crossfade.  A crossfade is always safe and restarts every
    envelope, which is the difference between editing an instrument and
    replacing it.
    """
    was = {n.origin: (n, shape(old, n.type_), state.values[n.id])
           for n in old.nodes}
    values = []
    lines: dict = {}
    for node in new.nodes:
        before = was.get(node.origin)
        kept = (before is not None and before[0].kind == node.kind
                and before[1] == shape(new, node.type_))
        # **A delay line also has to be the same length.**  Its buffer's
        # meaning is positional — slot `k` is "k instants ago" — so a line
        # whose length changed is a different line, and carrying the old
        # ring into it would read the wrong instants.  Editing `feedback
        # 4410` to `4400` while a sound is playing restarts that line and
        # nothing else, which is the same rule a `scan` follows when its
        # type changes.
        if (kept and node.kind in ("line", "tap", "loop", "slide", "scope", "spectro")
                and before[0].length != node.length):
            kept = False
        if kept:
            values.append(before[2])
            if (node.kind in ("line", "tap", "loop", "slide", "scope", "spectro")
                    and before[0].id in state.lines):
                lines[node.id] = list(state.lines[before[0].id])
        elif node.init is not None:
            values.append(node.init)
        else:
            values.append(zero(new, node.type_))
    return State(values, state.t, lines)


def render_block(graph: Graph, state: State, n: int, control=None) -> list:
    """Fill a buffer of `n` samples, advancing `state`.

    **A block is what control rate is once per.**  A control-rate source
    updates at the first sample of the block and is held constant across
    the rest of it; an audio-rate source advances every sample.  With no
    control-rate node in the graph — which is every graph today — the block
    size is not observable at all, and that is asserted rather than assumed.

    `control(node_id, t)` supplies the value a control source takes when it
    updates.  **Per source**, because a synth may declare several control
    channels and each is its own parameter — one knob per channel, keeping
    its own value across an edit.  It defaults to the instant number for
    every source, because that is what `audio.render(control_every=…)`
    feeds and the two have to agree for the comparison to mean anything.
    In a real engine this is where a slider is read.
    """
    if n <= 0:
        return []
    if control is None:
        control = lambda _node, t: t                          # noqa: E731
    out: list = []

    for k in range(n):
        t = state.t
        prev = state.values
        cur: list = [None] * len(graph.nodes)
        #: The `tap` nodes, written once the pass is over — see the branch
        #: for why the two halves cannot happen together.
        writes: list = []
        for node in graph.nodes:
            i = node.id
            if node.kind == "source":
                if t == 0:
                    cur[i] = node.init
                elif node.clock == "audio":
                    # `ticks` is `0 ::: mkSig (wait clock)` and the driver
                    # feeds the instant number, so the clock's value *is*
                    # the sample index.
                    cur[i] = t
                elif k == 0:
                    cur[i] = control(i, t)
                else:
                    cur[i] = prev[i]              # held across the block
            elif node.kind == "map":
                cur[i] = call(graph, node.step, [cur[node.inputs[0]]])
            elif node.kind == "scan":
                # `z` at the first instant; then its own previous state and
                # this instant's input.  See the module docstring for why
                # the input is not the previous one — it is the single most
                # confusable line in the file.
                cur[i] = (node.init if t == 0
                          else call(graph, node.step,
                                    [prev[i], cur[node.inputs[0]]]))
            elif node.kind == "zip":
                cur[i] = call(graph, node.step,
                              [cur[node.inputs[0]], cur[node.inputs[1]]])
            elif node.kind == "tap":
                # **The one node whose value is a function of its state.**
                # The ring is read here, at a position that may move and may
                # be fractional; the input goes in *after* the whole pass,
                # which is what leaves a cycle through this node with a
                # sample of delay in it rather than nothing.
                buf = state.ring(graph, node)
                cur[i] = _tap_read(buf, t, cur[node.inputs[1]])
                writes.append(node)
            elif node.kind in ("scope", "spectro"):
                # Identity on the sound, a ring write on the way past —
                # `spec/scope.md`: the window the host may read.  The
                # write happens in the pass because nothing reads the
                # ring from inside the graph; only a window does.
                buf = state.ring(graph, node)
                cur[i] = cur[node.inputs[0]]
                buf[t % len(buf)] = cur[i]
            elif node.kind == "line":
                # **A `scan` with a longer arm**, and the same asymmetry at
                # the first instant: silence at `t = 0`, then
                # `out[t] = f(out[t-n], s[t])`.  That is not a choice — it
                # is what `signal.ges`'s definition says, and the definition
                # is what the graph *means*.  A former written to fire at
                # `t = 0` would need `s[0]` under the fold, and `scan` reads
                # its input from inside a `delay`, so `s[0]` never reaches
                # one.  See this module's docstring.
                #
                # One slot of the ring is read and then written, in that
                # order: `out[t-n]` lives where `out[t]` is about to go,
                # because `(t - n) mod n` is `t mod n`.  The cursor is the
                # instant number, so nothing has to store one.
                buf = state.ring(graph, node)
                at = t % len(buf)
                cur[i] = (zero(graph, node.type_) if t == 0 else
                          call(graph, node.step,
                               [buf[at], cur[node.inputs[0]]]))
                buf[at] = cur[i]
            elif node.kind == "slide":
                # **`tap`'s read closed into `feedback`'s loop.**  The ring
                # holds this node's own output; the read happens before the
                # write, at wherever the position points this instant, and
                # `_tap_read`'s clamp keeps it at least one sample back —
                # so the loop always has a sample of delay in it.  Silence
                # at `t = 0`, as the oracle's `scan` gives: `s[0]` never
                # reaches a fold.
                buf = state.ring(graph, node)
                if t == 0:
                    cur[i] = 0.0
                else:
                    read = _tap_read(buf, t, cur[node.inputs[1]])
                    cur[i] = call(graph, node.step,
                                  [read, cur[node.inputs[0]]])
                buf[t % len(buf)] = cur[i]
            elif node.kind == "loop":
                # **A `line` whose ring holds whole states**, which is what
                # brings both ends of it within reach in one read: slot
                # `t % n` is about to be overwritten and so still holds
                # `st[t-n]`, and the slot written last instant — one before
                # it, around the ring — holds `st[t-1]`.
                #
                # `z` at the first instant rather than silence, because a
                # `loop`'s state is the user's and `z` is what they said it
                # starts at.  That is `scan`'s rule, not `line`'s, and it is
                # what the oracle does: its `scan` emits the untouched ring
                # before it has read anything, and both ends of that ring
                # are `z`.
                buf = state.ring(graph, node)
                at = t % len(buf)
                cur[i] = (node.init if t == 0 else
                          call(graph, node.step,
                               [buf[at - 1], buf[at],
                                cur[node.inputs[0]]]))
                buf[at] = cur[i]
            else:
                raise EngineError(f"unknown node kind {node.kind!r}")
        for node in writes:
            buf = state.ring(graph, node)
            # Nothing enters at the first instant, which is `scan`'s own
            # asymmetry: a fold in this language reads its input from
            # inside a `delay`, so `s[0]` reaches no line.
            if t:
                buf[t % len(buf)] = cur[node.inputs[0]]
        out.append(cur[graph.out])
        _within_i64(graph, cur, t)
        state.values = cur
        state.t += 1
    return out


#: What an `Int` is once it has been compiled.  The reference engine
#: counts in Python, where an integer is as large as it needs to be; the
#: generated code counts in `i64`, where it is not.
_I64 = 1 << 63


def _within_i64(graph: Graph, cur: list, t: int) -> None:
    """Refuse an integer the compiled engine could not hold.

    **The hazard named when the LLVM backend was written and never
    checked** — `journal.md`, stage 7.4: *"`Int` becomes `i64`
    (measured: `drums` reaches 25.7% of its range) … the `i64`
    narrowing has not bitten and is not checked; it is the open
    hazard."*  25.7% is not a comfortable margin, it is one doubling
    away.

    Checked **here**, in the reference, and nowhere else, which is the
    whole design of it.  The generated code must not pay a branch per
    integer operation — the audio path's rule is that nothing per-sample
    happens that is not the sound.  But the reference already runs at a
    thousandth of real time and is the *definition* of what a graph
    means, so a program that overflows it says so by name in every test
    that renders, instead of diverging from the engine by 2⁶⁴ and being
    read as a mysterious golden mismatch.

    What it cannot see is a program nobody renders through the
    reference.  That is a real limit and the honest place for it: the
    check is an oracle, not a guarantee.
    """
    for node in graph.nodes:
        v = cur[node.id]
        # Floats first, because almost every slot is one and this runs
        # per node per sample.
        if type(v) is float or not _too_big(v):
            continue
        raise EngineError(
            f"integer overflow at instant {t}: node {node.id} "
            f"({node.kind}) holds {v!r}, which the compiled engine "
            f"stores as `i64` and cannot — the reference counts in "
            f"Python, where an integer grows, and the generated code "
            f"does not (`journal.md`, stage 7.4)")


def _too_big(v) -> bool:
    """Is there an integer in here the compiled state could not hold?

    Records too, and not for completeness: a `Gate` is three `i64`s and
    a note's `gateAt` is a *sample index*, which is the one integer in
    this language that grows without anybody writing a big number down.
    """
    if type(v) is int:
        return not (-_I64 <= v < _I64)
    if type(v) is tuple:
        return any(_too_big(x) for x in v)
    return False


def run(graph: Graph, samples: int, block: int | None = None,
        control=None) -> list[float]:
    """`samples` samples, in blocks of `block` (default: one block).

    The naive reference of stage 2 is `block=None`, and it stays the
    definition of what the graph means; blocks are stage 3 and must not
    change it.

    The output node's values, raw: a `Float` output is a list of floats, and
    a record output is a list of `(tag, fields)` as every other node's value
    is.  `Graph.frames` is what turns the second into sample frames, and it
    is *not* applied here — this is the reference semantics of the graph,
    and a driver's idea of a frame is the boundary's business.
    """
    if samples <= 0:
        return []
    state = State.initial(graph)
    size = block or samples
    out: list[float] = []
    while len(out) < samples:
        out += render_block(graph, state, min(size, samples - len(out)),
                            control)
    return out
