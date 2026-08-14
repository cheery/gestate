"""The graph a synth extracts to, and the first-order IR inside it.

`spec/liveaudio.md` stage 2.  This is the structure the engine is generated
from, and it is deliberately *small*: an ordered list of nodes, a table of
first-order functions, and nothing that needs a heap.

Two things are worth reading before the dataclasses.

**Why the IR is not `gestate/expr.py`.**  An `Expr` carries everything the
language has — laziness, signals, boxes, dictionaries, polymorphism — and
the whole point of the fragment is that a step function needs none of it.
Translating into a form with eight cases is what makes stage 4 a
transliteration rather than a compiler: every node here has an obvious C
equivalent, and anything without one cannot be built.

**Why values are tuples.**  A constructor value is `(tag, (field, …))` and a
`Bool` is one too, because that is what the G-machine does — `prim_lt_float`
pushes `NCon(true_tag, ())`.  The reference interpreter has to agree with
the oracle bit for bit, and the cheapest way to agree is to represent things
the same way.  In the generated engine a flat constructor is a struct and
the tag is a discriminant; that translation belongs to stage 4.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class IRError(Exception):
    """A graph that cannot mean anything — the IR's own complaint.

    Raised where the *shape* of the graph is wrong rather than where a back
    end fails to emit it, so the message is the same whichever back end
    asked.
    """

# ── The IR ──────────────────────────────────────────────────────────────────
#
# First-order, strict, allocation-free.  Eight forms, and each one exists
# because a step function in the fragment can contain it.


@dataclass(frozen=True)
class Const:
    """A literal, or a constant folded at extraction time."""
    value: object


@dataclass(frozen=True)
class Var:
    """A parameter of the enclosing function, or a `let` binder."""
    name: str


@dataclass(frozen=True)
class Prim:
    """A machine primitive: `prim_add_float`, `prim_mod_int`, …"""
    op: str
    args: tuple


@dataclass(frozen=True)
class Call:
    """A call to another first-order function in the same graph."""
    fn: str
    args: tuple


@dataclass(frozen=True)
class Con:
    """Build a flat constructor value — a struct, in the engine."""
    tag: int
    args: tuple


@dataclass(frozen=True)
class Field:
    """Read field `index` out of a constructor value."""
    base: object
    index: int


@dataclass(frozen=True)
class Case:
    """Switch on a constructor tag.

    `alts` is a tuple of `(tag, binders, body)`; `binders` names the fields
    the alternative brought into scope, in order, and an empty tuple is the
    ordinary enum case.  A `Bool` test is this with two alternatives.
    """
    scrut: object
    alts: tuple


@dataclass(frozen=True)
class Let:
    name: str
    value: object
    body: object


# ── The graph ───────────────────────────────────────────────────────────────


@dataclass
class Func:
    """A step function: parameters in, one flat value out.

    `params` is `[state, input]` for a `scan`, `[input]` for a `map`, and
    `[left, right]` for a `zip` — the argument order the combinator has,
    so the engine's call sites need no convention of their own.
    """
    name: str
    params: tuple
    body: object

    def to_dict(self) -> dict:
        return {"name": self.name, "params": list(self.params),
                "body": _ir_to_dict(self.body)}


#: A scope's window, in samples — ~93 ms at 44.1 kHz, a few cycles of
#: anything audible.  Fixed rather than declared (`spec/scope.md`): a
#: window is the reader's concern, and the first argument a scope grows
#: should be earned by somebody needing it.
SCOPE_LEN = 4096


@dataclass
class Node:
    """One node of the signal graph.

    `origin` is the **stable identity** across recompiles, and it is a path
    of the definitions the node was inlined through rather than an index or
    a source position — see `spec/liveaudio.md`, stage 5.  Editing a step
    function does not move it, which is exactly the case live coding cares
    about: change the waveform, keep the phase.
    """
    id: int
    kind: str                     # source | map | scan | zip | line | tap | loop
    inputs: tuple = ()
    step: str | None = None       # a name in `Graph.funcs`
    init: object = None           # `scan`'s z, and a source's value at t=0
    type_: str = ""               # the element type, for reading and for 4
    origin: str = ""
    #: **How far back a `line`, `tap` or `loop` reaches**, in samples, and
    #: `0` for every other kind.
    #:
    #: A `line` is a `scan` with a longer memory: where a `scan` holds one
    #: value and its step sees the previous instant's, a `line` holds `n`
    #: and its step sees the one from `n` instants ago.  That is the whole
    #: difference, and it is why a delay line needs no change to the
    #: graph's acyclicity — the loop is *inside* the node, exactly as a
    #: `scan`'s is, rather than an edge that closes a cycle.
    #:
    #: Fixed before the program runs, like everything else the state layout
    #: depends on: the slot is `length` words wide and the engine has no
    #: allocator.  `spec/delaylines.md` is the design.
    length: int = 0
    #: "audio" — advances every sample — or "control", once per block.
    #:
    #: **Meaningful on a `source` and on nothing else.**  Every other node
    #: keeps the default and no reader consults it: the engine and the code
    #: generator both test `clock` only inside their `kind == "source"`
    #: branch, so a `map` over a control-rate source says "audio" and is
    #: evaluated every sample — correct, and more work than necessary.
    #:
    #: This field used to claim that a node "inherits its inputs'", which
    #: it does not (`fixme.md` F93).  Propagating it is what a per-block
    #: evaluation of control-rate subgraphs would need, and nothing asks
    #: for that yet; until something does, the honest reading is that only
    #: a source has a clock.
    clock: str = "audio"
    #: For a `source`, the name of the `Chan` global it waits on — `""` for
    #: every other kind.
    #:
    #: **The one name the interpreter and the engine share.**  `origin` is a
    #: path of *signal definitions* and `id` is an artefact of extraction
    #: order; neither means anything to `audio.render`, which drives
    #: channels.  A schedule that has to produce the same sound through both
    #: needs a key both can resolve, and this is it.
    chan: str = ""

    def to_dict(self) -> dict:
        return {"id": self.id, "kind": self.kind, "inputs": list(self.inputs),
                "step": self.step, "init": _value_to_dict(self.init),
                "type": self.type_, "origin": self.origin,
                "clock": self.clock, "chan": self.chan,
                "length": self.length}


@dataclass
class Graph:
    """A synth, flat.

    Serialisable on purpose: stage 4 hands this to a code generator that
    need not import anything of the compiler, and a graph that can be
    written out can be diffed between two compilations — which is what
    stage 5's state migration compares.
    """
    nodes: list = field(default_factory=list)
    funcs: dict = field(default_factory=dict)
    out: int = 0
    #: The constructor tags a `Bool` uses — user constructors are numbered
    #: first, so these are not constants (`fixme.md` F68).
    true_tag: int = 0
    false_tag: int = 0
    #: The sample rate the graph was extracted at.  It is folded into the
    #: constants, so a graph is *for* one rate and says which.
    rate: int = 0
    #: Data type name → its constructors, `{tag, name, fields}` with field
    #: types named.  **The state layout**, which stage 2's deliverable asked
    #: for and stage 4 turned out to actually need: a `type_` of `"Voice"`
    #: is enough to read and not enough to emit a struct for.
    layouts: dict = field(default_factory=dict)

    def node(self, i: int) -> Node:
        return self.nodes[i]

    def words(self, type_name: str) -> int:
        """The size of a type, in 8-byte words.

        Every leaf is 8 bytes — `i64` or `double` — and a constructor is its
        tag followed by its fields, so a struct's layout needs no padding
        and its offsets are word counts.  That is what makes reading a
        running state back out of the engine a matter of arithmetic rather
        than of asking a debugger about ABI.

        Here rather than in `audiollvm.py`, where it started, because two
        other readers need it now: the extractor decides whether a control
        channel is a scalar, and the engine lays out the control buffer.
        A layout is a property of the IR, not of one back end.
        """
        if type_name in ("Int", "Float"):
            return 1
        fields = self.layouts[type_name][0]["fields"]
        return 1 + sum(self.words(f) for f in fields)

    def channels(self) -> int:
        """How many `Float`s one instant of this graph's output is.

        A `Float` output is one channel and is what almost every graph has.
        A **record whose fields are all `Float`** is one channel per field,
        in field order, which is how a synth says stereo: `Stereo := Stereo
        Float Float` is left then right because that is how it is written.

        Here beside `words` and for the same reason — three back ends need
        it and it is a property of the IR, not of one of them.  The engines
        already carry the record: a `zip` node whose type is `Stereo` is
        built, stored and migrated like any other node.  What is
        multi-channel is only the *output boundary*, and this is the number
        that boundary loops over.
        """
        name = self.node(self.out).type_
        if name == "Float":
            return 1
        cons = self.layouts.get(name)
        shapes = {tuple(c["fields"]) for c in cons} if cons else set()
        fields = next(iter(shapes)) if len(shapes) == 1 else None
        if not fields or any(f != "Float" for f in fields):
            raise IRError(
                f"`{name}` cannot be a synth's output: a multi-channel "
                "`sound` is a signal of a record whose fields are all "
                "`Float`, one field per channel")
        return len(fields)

    def frames(self, values: list) -> list:
        """Output node values as frames: floats if mono, tuples if not.

        The engines hand back what the output node *is*, and for a record
        that is `(tag, fields)`.  A driver wants samples, and one place to
        turn one into the other keeps the two block engines and the oracle
        agreeing about what a frame is.
        """
        if self.channels() == 1:
            return list(values)
        return [tuple(v[1]) for v in values]

    def control_sources(self) -> list:
        """The control-rate sources, in node-id order.

        **This order is the control buffer's layout**, and every reader of
        it has to agree: the Python engine, the generated code, and whatever
        host supplies the values.  Taken from one place so they cannot
        disagree — and node-id order rather than declaration order because
        that is what the generated code can index without a table.

        Ids shift when a definition is added above, so a host must ask again
        after a rebuild.  That is not a hazard for *state*, which stage 5
        migrates by `origin`; it is only the wire format for one block.
        """
        return [n for n in self.nodes
                if n.kind == "source" and n.clock == "control"]

    def scopes(self) -> list:
        """The scopes, as `(label, length, node)` in node-id order.

        The order is also `read_scope_<i>`'s numbering — one place, so
        the generated readers and the Python that calls them cannot
        disagree about which window is whose (`spec/scope.md`).
        """
        return [(n.chan, n.length, n) for n in self.nodes
                if n.kind in ("scope", "spectro")]

    def control_by_chan(self) -> dict:
        """Channel name → its control source node.

        What a schedule is keyed by: the interpreter drives channels and the
        engine drives nodes, and a comparison between them is only possible
        through a name they both have.
        """
        return {n.chan: n for n in self.control_sources() if n.chan}

    def to_dict(self) -> dict:
        return {
            "rate": self.rate, "out": self.out,
            "true_tag": self.true_tag, "false_tag": self.false_tag,
            "layouts": self.layouts,
            "nodes": [n.to_dict() for n in self.nodes],
            "funcs": {k: v.to_dict() for k, v in sorted(self.funcs.items())},
        }

    def show(self) -> str:
        """The graph as a reader wants it: one line per node, in order."""
        lines = []
        for n in self.nodes:
            bits = [f"{n.id:>3}  {n.kind:<6}"]
            if n.inputs:
                bits.append("<- " + ", ".join(str(i) for i in n.inputs))
            if n.step:
                bits.append(f"step {n.step}")
            if n.init is not None:
                bits.append(f"init {_show_value(n.init)}")
            bits.append(f": {n.type_}")
            lines.append("  ".join(bits) + f"   [{n.origin}]")
        lines.append(f"     out = {self.out}, {len(self.funcs)} function(s), "
                     f"rate {self.rate}")
        return "\n".join(lines)


# ── Serialisation ───────────────────────────────────────────────────────────


def _value_to_dict(v):
    if isinstance(v, tuple):
        return {"tag": v[0], "fields": [_value_to_dict(f) for f in v[1]]}
    return v


def _show_value(v) -> str:
    if isinstance(v, tuple):
        inner = " ".join(_show_value(f) for f in v[1])
        return f"#{v[0]}({inner})" if v[1] else f"#{v[0]}"
    return repr(v)


def _ir_to_dict(e) -> dict:
    if isinstance(e, Const):
        return {"const": _value_to_dict(e.value)}
    if isinstance(e, Var):
        return {"var": e.name}
    if isinstance(e, Prim):
        return {"prim": e.op, "args": [_ir_to_dict(a) for a in e.args]}
    if isinstance(e, Call):
        return {"call": e.fn, "args": [_ir_to_dict(a) for a in e.args]}
    if isinstance(e, Con):
        return {"con": e.tag, "args": [_ir_to_dict(a) for a in e.args]}
    if isinstance(e, Field):
        return {"field": e.index, "base": _ir_to_dict(e.base)}
    if isinstance(e, Case):
        return {"case": _ir_to_dict(e.scrut),
                "alts": [{"tag": t, "binders": list(b), "body": _ir_to_dict(x)}
                         for t, b, x in e.alts]}
    if isinstance(e, Let):
        return {"let": e.name, "value": _ir_to_dict(e.value),
                "body": _ir_to_dict(e.body)}
    raise TypeError(f"not IR: {e!r}")
