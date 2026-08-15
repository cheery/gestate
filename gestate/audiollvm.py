"""LLVM IR for an extracted graph — `spec/liveaudio.md` stage 4.

Emits **textual** `.ll` and imports nothing, so the generator itself is
testable by reading what it wrote.  Compiling and running the result needs a
toolchain (`clang`), which `build()` shells out to and which the tests skip
without, the way the MIDI tests skip without `mido`.

**Why IR rather than C.**  The acceptance criterion for this whole plan is
bit-identity with the offline renderer, and that is a floating-point
argument.  A C compiler may contract `a * b + c` into an `fma` — it is the
*default* in both GCC and clang — which changes the value of exactly the
expressions a synth is made of.  Getting bit-identity out of C therefore
depends on remembering a flag, on every compiler, forever.  Here the
question does not arise: `fmul` then `fadd` is two instructions and stays
two, because nothing writes `llvm.fmuladd`.  No fast-math flag is emitted on
any instruction, so `-O2` may not reassociate, and nothing sets FTZ, so the
subnormals stage 0 found survive (`fixme.md` F91's neighbour, and the
reason the golden buffers are exact).

**What makes this a transliteration rather than a compiler.**  The fragment
removed closures, allocation, laziness, polymorphism and recursion, and
stage 2 reduced what remained to eight IR forms.  So:

    Float / Int / Bool      double / i64 / a one-field struct
    a flat constructor      { i64 tag, fields… }, by value
    Case                    switch on the tag, one block each, then phi
    Let                     an SSA name; no alloca anywhere
    Call                    call fastcc
    a node's state          one field of %State
    render_block            a loop over n

**Types are inferred here, not carried.**  The IR is untyped, and it can be:
everything in the fragment is monomorphic, so a function's parameter types
are fixed by the node that uses it and its result follows from its body.
Types propagate from node types down through call sites, and a function is
emitted once, at the one type it has.

    python -m gestate.audiollvm examples/audio/blip.ges
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .audioir import Call, Case, Con, Const, Field, Graph, Let, Prim, Var
from .gmachine import MATH_FLOAT

#: `prim_sin_float` ↦ `sin`, which is both Python's `math` name and LLVM's
#: intrinsic name.  The two coinciding is what the whole comparison rests
#: on, so the mapping is one dictionary rather than string surgery at each
#: use site.
_MATH_OPS = {f"prim_{fn}_float": fn for fn in MATH_FLOAT}

#: `Int` becomes a 64-bit integer, and this is a **narrowing**: gestate's
#: `Int` is a Python integer and the offline renderer computes with it
#: unbounded.  Measured on the examples, `drums.ges`'s LCG reaches
#: 2,368,169,630,722,025,925 — 25.7% of the range — so the examples are
#: safe and a wider seed would not be.  See `check_int_range` below.
INT = "i64"
FLOAT = "double"


class LLVMError(Exception):
    pass


# ── Types ───────────────────────────────────────────────────────────────────


@dataclass
class Types:
    """The graph's layouts, as LLVM types.

    A data type becomes `{ i64, fields… }` — the tag first, then the fields
    of its constructors.  **Every constructor of one type must have the same
    field types**, which covers a record (one constructor) and an enum (no
    fields) and not a genuine sum like `Maybe Float`.  That is a real limit
    and it is checked rather than assumed: a union layout is a decision, and
    nothing has needed one.
    """
    layouts: dict
    names: dict = field(default_factory=dict)

    def of(self, name: str) -> str:
        if name == "Float":
            return FLOAT
        if name == "Int":
            return INT
        if name in self.names:
            return self.names[name]
        cons = self.layouts.get(name)
        if cons is None:
            raise LLVMError(f"no layout for `{name}`")
        shapes = {tuple(c["fields"]) for c in cons}
        if len(shapes) > 1:
            raise LLVMError(
                f"`{name}` has constructors of different shapes "
                f"({', '.join(c['name'] for c in cons)}), and the engine "
                f"lays a data type out as one struct.  A union layout is a "
                f"decision nothing has needed yet")
        fields = "".join(", " + self.of(f) for f in next(iter(shapes)))
        self.names[name] = f"%{_ident(name)}"
        return self.names[name]

    def fields(self, name: str) -> list:
        return list(next(iter({tuple(c["fields"])
                               for c in self.layouts[name]})))

    def declarations(self) -> list:
        out = []
        for name in list(self.names):
            fields = "".join(", " + self.of(f) for f in self.fields(name))
            out.append(f"{self.names[name]} = type {{ i64{fields} }}")
        return out


# **A primitive's name is not its type**, and finding that out is what
# stage 4 is for.  The G-machine shares one instruction between `Int` and
# `Float` wherever Python's operator is already right on both — so
# `helpers.py` generates `prim_lt_int` for a `Float` comparison on purpose,
# and `elaborate.py`'s derived `Ord` does the same.  `drums.ges` reaches
# here through `decay`'s `t > len` at `Float` and arrives at `prim_lt_int`
# with two doubles.
#
# So the instruction is chosen from the **operand type as emitted**, never
# from the name.  A generator that trusted the name emits `icmp` on
# `double`, which is at least a build failure rather than a wrong sound.

#: op family → (integer instruction, float instruction).
_ARITH = {
    "add": ("add", "fadd"), "sub": ("sub", "fsub"), "mul": ("mul", "fmul"),
}
_COMPARE = {"eq": ("icmp eq", "fcmp oeq"), "lt": ("icmp slt", "fcmp olt")}


# ── The emitter ─────────────────────────────────────────────────────────────


class _Emit:
    def __init__(self, graph: Graph):
        self.g = graph
        self.t = Types(graph.layouts)
        self.lines: list = []
        self.n = 0
        #: function name → (param type names, result type name), once each.
        self.signatures: dict = {}
        self.bodies: dict = {}

    # -- names --------------------------------------------------------------

    def fresh(self, hint: str = "v") -> str:
        self.n += 1
        return f"%{hint}{self.n}"

    def label(self, hint: str) -> str:
        self.n += 1
        return f"{hint}{self.n}"

    def emit(self, line: str) -> None:
        self.lines.append("  " + line)

    # -- expressions --------------------------------------------------------

    def expr(self, e, env: dict) -> tuple:
        """`(value, type name)` — SSA, in the current basic block."""
        if isinstance(e, Const):
            return self.constant(e.value)

        if isinstance(e, Var):
            if e.name not in env:
                raise LLVMError(f"unbound `{e.name}`")
            return env[e.name]

        if isinstance(e, Let):
            env = dict(env)
            env[e.name] = self.expr(e.value, env)
            return self.expr(e.body, env)

        if isinstance(e, Prim):
            return self.prim(e, env)

        if isinstance(e, Con):
            return self.con(e, env)

        if isinstance(e, Field):
            base, base_t = self.expr(e.base, env)
            ft = self.t.fields(base_t)[e.index]
            out = self.fresh("f")
            self.emit(f"{out} = extractvalue {self.t.of(base_t)} {base}, "
                      f"{e.index + 1}")
            return out, ft

        if isinstance(e, Call):
            args = [self.expr(a, env) for a in e.args]
            result = self.function(e.fn, [t for _v, t in args])
            out = self.fresh("c")
            actual = ", ".join(f"{self.t.of(t)} {v}" for v, t in args)
            self.emit(f"{out} = call fastcc {self.t.of(result)} "
                      f"@{_fn(e.fn)}({actual})")
            return out, result

        if isinstance(e, Case):
            return self.case(e, env)

        raise LLVMError(f"not IR: {e!r}")

    def constant(self, value) -> tuple:
        if isinstance(value, tuple):
            # A constructor constant: `Voice 0.0 0`, built with the same
            # insertvalue chain as any other, so there is one code path.
            info = self.con_named(value[0])
            fields = [self.constant(v) for v in value[1]]
            return self.build(info, fields)
        if isinstance(value, float):
            return _double(value), "Float"
        if isinstance(value, int):
            return str(value), "Int"
        raise LLVMError(f"no constant for {value!r}")

    def con_named(self, tag: int) -> tuple:
        for name, cons in self.g.layouts.items():
            for c in cons:
                if c["tag"] == tag:
                    return name, c
        raise LLVMError(f"no layout has tag {tag}")

    def build(self, info, fields) -> tuple:
        name, con = info
        ty = self.t.of(name)
        acc = self.fresh("s")
        self.emit(f"{acc} = insertvalue {ty} undef, i64 {con['tag']}, 0")
        for i, (v, ft) in enumerate(fields):
            nxt = self.fresh("s")
            self.emit(f"{nxt} = insertvalue {ty} {acc}, "
                      f"{self.t.of(ft)} {v}, {i + 1}")
            acc = nxt
        return acc, name

    def con(self, e, env) -> tuple:
        info = self.con_named(e.tag)
        return self.build(info, [self.expr(a, env) for a in e.args])

    def prim(self, e, env) -> tuple:
        args = [self.expr(a, env) for a in e.args]
        vals = [v for v, _t in args]
        operand = args[0][1] if args else "Int"
        floating = operand == "Float"
        family = e.op.replace("prim_", "").rsplit("_", 1)[0]
        out = self.fresh("p")

        if family in _ARITH:
            # No fast-math flags, deliberately: see the module docstring.
            self.emit(f"{out} = {_ARITH[family][floating]} "
                      f"{self.t.of(operand)} {vals[0]}, {vals[1]}")
            return out, operand
        if family in _COMPARE:
            self.emit(f"{out} = {_COMPARE[family][floating]} "
                      f"{self.t.of(operand)} {vals[0]}, {vals[1]}")
            tag = self.fresh("t")
            self.emit(f"{tag} = select i1 {out}, i64 {self.g.true_tag}, "
                      f"i64 {self.g.false_tag}")
            box = self.fresh("b")
            self.emit(f"{box} = insertvalue {self.t.of('Bool')} undef, "
                      f"i64 {tag}, 0")
            return box, "Bool"
        if family == "div":
            if floating:
                self.emit(f"{out} = fdiv double {vals[0]}, {vals[1]}")
                return out, "Float"
            if e.op == "prim_div_float":
                raise LLVMError("`prim_div_float` on integers")
            return self.floor_div("prim_div_int", vals), "Int"
        if family == "mod":
            if floating:
                return self.floor_rem_float(vals), "Float"
            if e.op == "prim_mod_float":
                raise LLVMError("`prim_mod_float` on integers")
            return self.floor_div("prim_mod_int", vals), "Int"
        if e.op == "prim_to_float":
            if floating:
                return vals[0], "Float"      # `float(x)` of a float
            self.emit(f"{out} = sitofp i64 {vals[0]} to double")
            return out, "Float"
        if e.op == "prim_floor_float":
            if not floating:
                return vals[0], "Int"        # `math.floor` of an int
            floored = self.fresh("fl")
            self.emit(f"{floored} = call double @llvm.floor.f64"
                      f"(double {vals[0]})")
            self.emit(f"{out} = fptosi double {floored} to i64")
            return out, "Int"
        if e.op in _MATH_OPS:
            # `llvm.sin.f64` and friends, which lower to a call to libm's
            # `sin` — the same one CPython's `math.sin` reaches, which is
            # what makes the comparison against the oracle exact rather
            # than close.  `spec/liveaudio.md` open question 2 states the
            # assumption; `test_transcendental.py` measures it.
            arg = vals[0]
            if not floating:
                # An `Int`-typed literal reaching `sin` — the argument is a
                # double in the generated signature either way.
                arg = self.fresh("sf")
                self.emit(f"{arg} = sitofp i64 {vals[0]} to double")
            self.emit(f"{out} = call double @llvm.{_MATH_OPS[e.op]}.f64"
                      f"(double {arg})")
            return out, "Float"
        if e.op in ("chr", "ord"):
            return vals[0], "Int"       # the identity, as in the G-machine
        raise LLVMError(f"no primitive `{e.op}`")

    def floor_div(self, op: str, vals: list) -> str:
        """Python's `//` and `%`, which **floor**; LLVM's truncate.

        They agree on positive operands and differ on negative ones, which
        a phase wrapped with `mod` produces readily — so this correction is
        not a nicety.  `q - ((r != 0) & ((r < 0) != (b < 0)))`, and the
        same shape for the remainder.
        """
        a, b = vals
        q = self.fresh("q")
        r = self.fresh("r")
        self.emit(f"{q} = sdiv i64 {a}, {b}")
        self.emit(f"{r} = srem i64 {a}, {b}")
        rn, bn, differ, nonzero, adjust = (self.fresh("x") for _ in range(5))
        self.emit(f"{rn} = icmp slt i64 {r}, 0")
        self.emit(f"{bn} = icmp slt i64 {b}, 0")
        self.emit(f"{differ} = xor i1 {rn}, {bn}")
        self.emit(f"{nonzero} = icmp ne i64 {r}, 0")
        self.emit(f"{adjust} = and i1 {differ}, {nonzero}")
        out = self.fresh("d")
        if op == "prim_div_int":
            one = self.fresh("x")
            self.emit(f"{one} = select i1 {adjust}, i64 1, i64 0")
            self.emit(f"{out} = sub i64 {q}, {one}")
        else:
            add = self.fresh("x")
            self.emit(f"{add} = select i1 {adjust}, i64 {b}, i64 0")
            self.emit(f"{out} = add i64 {r}, {add}")
        return out

    def floor_rem_float(self, vals: list) -> str:
        """Python's `%` at `Float`, which **floors**; LLVM's `frem` truncates.

        The same disagreement `floor_div` corrects one type down, and for
        the same reason it is not a nicety: `frem` takes the sign of the
        *dividend* and Python takes the sign of the *divisor*, so
        `(-0.25) % 1.0` is `-0.25` in LLVM and `0.75` in the interpreter.
        A phase is exactly where a negative dividend turns up — subtract a
        detune from one near zero — and the oracle is compared against the
        engine sample for sample, so the two must agree bit for bit rather
        than nearly.

        `r + (b if r != 0 and (r < 0) != (b < 0) else 0)`, which is
        `floor_div`'s remainder branch with `fcmp` in place of `icmp`.
        `fcmp one` is false for a NaN, so a NaN remainder is left alone
        rather than adjusted — which is what adding zero to it would do
        anyway, and is the arm with no arithmetic in it.
        """
        a, b = vals
        r = self.fresh("r")
        self.emit(f"{r} = frem double {a}, {b}")
        rn, bn, differ, nonzero, adjust = (self.fresh("x") for _ in range(5))
        self.emit(f"{rn} = fcmp olt double {r}, {_double(0.0)}")
        self.emit(f"{bn} = fcmp olt double {b}, {_double(0.0)}")
        self.emit(f"{differ} = xor i1 {rn}, {bn}")
        self.emit(f"{nonzero} = fcmp one double {r}, {_double(0.0)}")
        self.emit(f"{adjust} = and i1 {differ}, {nonzero}")
        add = self.fresh("x")
        self.emit(f"{add} = select i1 {adjust}, double {b}, "
                  f"double {_double(0.0)}")
        out = self.fresh("d")
        self.emit(f"{out} = fadd double {r}, {add}")
        return out

    def case(self, e, env) -> tuple:
        scrut, scrut_t = self.expr(e.scrut, env)
        tag = self.fresh("tag")
        self.emit(f"{tag} = extractvalue {self.t.of(scrut_t)} {scrut}, 0")

        join = self.label("join")
        blocks = [(alt, self.label("alt")) for alt in e.alts]
        table = " ".join(f"i64 {alt[0]}, label %{name}"
                         for alt, name in blocks)
        # The first alternative doubles as the default: the match compiler
        # writes out every constructor, so a core `Case` is total and the
        # default is unreachable in fact — but LLVM requires one.
        self.emit(f"switch i64 {tag}, label %{blocks[0][1]} [ {table} ]")

        arms, result_t = [], None
        fields = self.t.fields(scrut_t) if scrut_t not in ("Int", "Float") else []
        for (alt_tag, binders, body), name in blocks:
            self.lines.append(f"{name}:")
            inner = dict(env)
            for i, binder in enumerate(binders):
                v = self.fresh("g")
                self.emit(f"{v} = extractvalue {self.t.of(scrut_t)} "
                          f"{scrut}, {i + 1}")
                inner[binder] = (v, fields[i])
            value, result_t = self.expr(body, inner)
            # The arm may have opened blocks of its own; a `phi` has to name
            # the block control actually came *from*, not the one it entered.
            self.emit(f"br label %{join}")
            arms.append((value, self.current_label(name)))

        self.lines.append(f"{join}:")
        out = self.fresh("phi")
        incoming = ", ".join(f"[ {v}, %{blk} ]" for v, blk in arms)
        self.emit(f"{out} = phi {self.t.of(result_t)} {incoming}")
        return out, result_t

    def current_label(self, entered: str) -> str:
        """The label of the block the last instruction was emitted into."""
        for line in reversed(self.lines):
            if not line.startswith("  ") and line.endswith(":"):
                return line[:-1]
        return entered

    # -- functions ----------------------------------------------------------

    def function(self, name: str, args: list) -> str:
        """Emit `name` at the types it is called with; return its result.

        Monomorphic, so once each.  A second call with different argument
        types would be a bug in the fragment rather than a case to handle,
        and it says so.
        """
        if name in self.signatures:
            params, result = self.signatures[name]
            if params != args:
                raise LLVMError(
                    f"`{name}` is called at two types ({params} and "
                    f"{args}); the fragment is monomorphic")
            return result

        fn = self.g.funcs.get(name)
        if fn is None:
            raise LLVMError(f"no function `{name}` in the graph")
        self.signatures[name] = (args, None)

        outer, self.lines = self.lines, []
        env = {p: (f"%{_ident(p)}", t) for p, t in zip(fn.params, args)}
        value, result = self.expr(fn.body, env)
        body, self.lines = self.lines, outer

        params = ", ".join(f"{self.t.of(t)} %{_ident(p)}"
                           for p, t in zip(fn.params, args))
        self.bodies[name] = (
            [f"define internal fastcc {self.t.of(result)} "
             f"@{_fn(name)}({params}) {{", "entry:"]
            + body + [f"  ret {self.t.of(result)} {value}", "}"])
        self.signatures[name] = (args, result)
        return result


# ── The whole module ────────────────────────────────────────────────────────


def emit(graph: Graph) -> str:
    """The graph as LLVM IR text."""
    e = _Emit(graph)

    # The state struct: `t`, then one field per node, in id order.  Every
    # node and not only the stateful ones, so that a field index *is* a node
    # id — which is what stage 5 migrates against.
    node_types = [n.type_ for n in graph.nodes]
    for t in node_types:
        e.t.of(t)

    # Step functions, at the types their nodes give them.
    for node in graph.nodes:
        if not node.step:
            continue
        inputs = [graph.node(i).type_ for i in node.inputs]
        if node.kind in ("scan", "line", "slide"):
            e.function(node.step, [node.type_, inputs[0]])
        elif node.kind == "loop":
            # Both ends of the ring, then the input: `b -> b -> a -> b`.
            e.function(node.step, [node.type_, node.type_, inputs[0]])
        elif node.kind == "map":
            e.function(node.step, [inputs[0]])
        else:
            e.function(node.step, inputs)

    # **A `line`'s field is an array**, not a scalar: its state is `length`
    # samples of ring buffer where every other node's is one value.  The
    # field index is still the node id, which is what stage 5 migrates
    # against and what `_render_block` indexes by.
    def _field(node) -> str:
        cell = e.t.of(node.type_)
        return (f"[{node.length} x {cell}]"
                if node.kind in ("line", "tap", "loop", "slide", "scope", "spectro")
                else cell)

    state_fields = ", ".join(["i64"] + [_field(n) for n in graph.nodes])
    lines = [
        f"; gestate — generated from a signal graph at {graph.rate} Hz",
        "; spec/liveaudio.md stage 4.  No fast-math flags anywhere: the",
        "; offline renderer is the oracle and the comparison is exact.",
        "",
        "declare double @llvm.floor.f64(double)",
        "declare double @llvm.minnum.f64(double, double)",
        "declare double @llvm.maxnum.f64(double, double)",
        *(f"declare double @llvm.{fn}.f64(double)" for fn in MATH_FLOAT),
        "",
        *e.t.declarations(),
        f"%State = type {{ {state_fields} }}",
        "",
    ]
    for name in sorted(e.bodies):
        lines += e.bodies[name] + [""]
    lines += _render_block(graph, e, "render_block", "double")
    lines += [""]
    lines += _render_block(graph, e, "render_block_f32", "float")
    # **The crossfade, in the engine rather than in the host.**  Same body,
    # two extra arguments and a different last instruction: it multiplies by
    # a gain ramping `g0`→`g1` across the block and *adds* into the buffer
    # instead of storing.  Two calls — the new engine ramping up, the old
    # one ramping down — mix two programs sample for sample with no Python
    # between them, which is what an audio callback with a deadline needs.
    lines += _render_block(graph, e, "render_block_mix_f32", "float",
                           mix=True)
    lines += _read_scopes(graph)
    return "\n".join(lines) + "\n"


def _read_scopes(graph: Graph) -> list:
    """`void read_scope_<i>(%State*, double* out, i64 n)` per scope.

    Copies the window **oldest-first** with the same cursor the writes
    use — slot `t mod length` is the one about to be overwritten, so
    it is where the window begins.  The generated code owns its layout
    and the host calls a function; no offsets cross the boundary
    (`spec/scope.md`).  The read races the audio thread and may seam
    at a block edge — a diagnostic tolerates what a delay line must
    not, which is why nothing may feed one back into the sound.
    """
    out: list = []
    for i, (_label, length, node) in enumerate(graph.scopes()):
        out += [
            f"define void @read_scope_{i}(ptr %s, ptr %out, i64 %n) {{",
            "entry:",
            "  %tptr = getelementptr inbounds %State, ptr %s, i32 0, i32 0",
            "  %t = load i64, ptr %tptr",
            "  %some = icmp sgt i64 %n, 0",
            "  br i1 %some, label %loop, label %done",
            "loop:",
            "  %j = phi i64 [ 0, %entry ], [ %jn, %loop ]",
            "  %shift = add i64 %t, %j",
            f"  %idx = urem i64 %shift, {length}",
            "  %ring = getelementptr inbounds %State, ptr %s, i32 0, "
            f"i32 {node.id + 1}",
            f"  %sp = getelementptr inbounds [{length} x double], "
            "ptr %ring, i64 0, i64 %idx",
            "  %v = load double, ptr %sp",
            "  %op = getelementptr inbounds double, ptr %out, i64 %j",
            "  store double %v, ptr %op",
            "  %jn = add i64 %j, 1",
            "  %again = icmp slt i64 %jn, %n",
            "  br i1 %again, label %loop, label %done",
            "done:",
            "  ret void",
            "}",
            "",
        ]
    return out


def out_channels(graph: Graph) -> int:
    """`Graph.channels` — the name this module's readers already know.

    Kept here for the reason `_words` is: a layout is a property of the IR
    rather than of one back end, and three of them ask.
    """
    return graph.channels()


def _render_block(graph: Graph, e: _Emit, name: str, out_type: str,
                  mix: bool = False) -> list:
    """`void <name>(%State*, <out_type>* out, i64 n, i64* control)`.

    A loop over the block, nodes in id order — dependency order, since the
    extractor builds a node only after its inputs.  The state is read at the
    top of an iteration and written at the bottom, which is what makes the
    `scan` recurrence "previous state, this instant's input" fall out
    without any explicit buffering.

    `control` points at one 8-byte slot per control source, in the order
    `Graph.control_sources` gives.  A pointer rather than a scalar because a
    synth may declare several parameters; passing `null` is legal for a
    graph with none, which is most of them.

    Emitted twice.  `double` is the one the bit-identical comparison uses.
    **`float` is the one a sound card wants**, and it exists so that the
    conversion happens *here* rather than in the Python that drives the
    device: an audio callback with a deadline is the last place to put an
    interpreter, which is the whole architecture in one sentence.  It
    clamps, matching `audio.write()` — a synth that goes over 1.0 should
    sound like it did rather than be quietly rescaled.
    """
    body: list = []
    e.lines = body

    #: Control source node id → its slot in the buffer the host passes.
    control_index = {n.id: i for i, n in enumerate(graph.control_sources())}

    e.n = 0
    e.emit("%n0 = icmp sgt i64 %n, 0")
    e.emit("br i1 %n0, label %loop, label %done")
    body.append("loop:")
    e.emit("%k = phi i64 [ 0, %entry ], [ %knext, %tail ]")
    e.emit("%tptr = getelementptr inbounds %State, ptr %s, i32 0, i32 0")
    e.emit("%t = load i64, ptr %tptr")
    e.emit("%first = icmp eq i64 %t, 0")
    e.emit("%blockstart = icmp eq i64 %k, 0")

    values: dict = {}
    #: `tap id -> its ring's base pointer`, and the nodes to write once the
    #: whole instant is computed.
    rings: dict = {}
    taps: list = []
    #: `loop id -> the state it held an instant ago`, loaded beside the one
    #: it held `n` instants ago because both are arms of the same step.
    prevs: dict = {}
    for node in graph.nodes:
        slot = f"%slot{node.id}"
        ty = e.t.of(node.type_)
        if node.kind in ("line", "scope", "spectro"):
            # `out[t-n]` lives exactly where `out[t]` is about to go,
            # because `(t - n) mod n` is `t mod n` — so one index serves
            # the read and the write, and no cursor is stored.
            ring = e.fresh("ring")
            e.emit(f"{ring} = getelementptr inbounds %State, ptr %s, i32 0, "
                   f"i32 {node.id + 1}")
            at = e.fresh("at")
            e.emit(f"{at} = urem i64 %t, {node.length}")
            e.emit(f"{slot} = getelementptr inbounds "
                   f"[{node.length} x {ty}], ptr {ring}, i64 0, i64 {at}")
        elif node.kind == "loop":
            # A `line` whose ring holds states, read at both ends.  The far
            # end is the slot about to be overwritten, as a `line`'s is; the
            # near end is the slot written last instant, `(t - 1) mod n`,
            # computed as `(t + n - 1) mod n` because `%t` is unsigned and
            # the first instant would otherwise wrap below zero.  At `t = 0`
            # that lands on the far end of the ring, which still holds `z`,
            # so no slot is read before it has been written.
            ring = e.fresh("ring")
            e.emit(f"{ring} = getelementptr inbounds %State, ptr %s, i32 0, "
                   f"i32 {node.id + 1}")
            at = e.fresh("at")
            e.emit(f"{at} = urem i64 %t, {node.length}")
            e.emit(f"{slot} = getelementptr inbounds "
                   f"[{node.length} x {ty}], ptr {ring}, i64 0, i64 {at}")
            back = e.fresh("back")
            e.emit(f"{back} = add i64 %t, {node.length - 1}")
            pat = e.fresh("pat")
            e.emit(f"{pat} = urem i64 {back}, {node.length}")
            pslot = e.fresh("pslot")
            e.emit(f"{pslot} = getelementptr inbounds "
                   f"[{node.length} x {ty}], ptr {ring}, i64 0, i64 {pat}")
            was = e.fresh("was")
            e.emit(f"{was} = load {ty}, ptr {pslot}")
            prevs[node.id] = was
        elif node.kind in ("tap", "slide"):
            # **The nodes whose read and write are different places.**
            # A `line` reads the slot it is about to overwrite; a tap or a
            # slide reads wherever its position points, so the base
            # pointer is what is kept and the indices are computed where
            # they are used.  A slide still writes at `t`, during the pass
            # — its read is clamped a sample back and never touches that
            # slot.
            slot = e.fresh("tapbase")
            rings[node.id] = slot
            e.emit(f"{slot} = getelementptr inbounds %State, ptr %s, i32 0, "
                   f"i32 {node.id + 1}")
        else:
            e.emit(f"{slot} = getelementptr inbounds %State, ptr %s, i32 0, "
                   f"i32 {node.id + 1}")
        held = f"%held{node.id}"
        if node.kind not in ("tap", "slide"):
            e.emit(f"{held} = load {ty}, ptr {slot}")

        if node.kind == "source":
            init, _t = e.constant(node.init)
            if node.clock == "audio":
                out = e.fresh("src")
                e.emit(f"{out} = select i1 %first, {ty} {init}, {ty} %t")
            else:
                # Control rate: the value the host handed in, taken at the
                # start of the block and held across the rest of it.
                #
                # One slot per control source, in the order
                # `Graph.control_sources` gives — a pointer rather than a
                # scalar because a synth may declare several parameters and
                # each is its own knob.
                slot_i = control_index[node.id]
                addr = e.fresh("cptr")
                raw = e.fresh("craw")
                e.emit(f"{addr} = getelementptr inbounds i64, ptr %control, "
                       f"i64 {slot_i}")
                e.emit(f"{raw} = load i64, ptr {addr}")
                given = raw
                if ty != "i64":
                    # Every control value is one word; a `double` arrives in
                    # the same slot and is reinterpreted, not converted.
                    given = e.fresh("cval")
                    e.emit(f"{given} = bitcast i64 {raw} to {ty}")
                fromhost = e.fresh("ctl")
                e.emit(f"{fromhost} = select i1 %blockstart, {ty} {given}, "
                       f"{ty} {held}")
                out = e.fresh("src")
                e.emit(f"{out} = select i1 %first, {ty} {init}, "
                       f"{ty} {fromhost}")
            values[node.id] = out
        elif node.kind == "map":
            out = e.fresh("m")
            arg_t = e.t.of(graph.node(node.inputs[0]).type_)
            e.emit(f"{out} = call fastcc {ty} @{_fn(node.step)}"
                   f"({arg_t} {values[node.inputs[0]]})")
            values[node.id] = out
        elif node.kind == "scan":
            stepped = e.fresh("sc")
            arg_t = e.t.of(graph.node(node.inputs[0]).type_)
            e.emit(f"{stepped} = call fastcc {ty} @{_fn(node.step)}"
                   f"({ty} {held}, {arg_t} {values[node.inputs[0]]})")
            init, _t = e.constant(node.init)
            out = e.fresh("sv")
            e.emit(f"{out} = select i1 %first, {ty} {init}, {ty} {stepped}")
            values[node.id] = out
        elif node.kind == "line":
            stepped = e.fresh("ln")
            arg_t = e.t.of(graph.node(node.inputs[0]).type_)
            e.emit(f"{stepped} = call fastcc {ty} @{_fn(node.step)}"
                   f"({ty} {held}, {arg_t} {values[node.inputs[0]]})")
            # Silence at the first instant, as a `scan` has and for the same
            # reason — `signal.ges`'s definition is what the graph means.
            quiet, _t = e.constant(_zero_of(graph, node.type_))
            out = e.fresh("lv")
            e.emit(f"{out} = select i1 %first, {ty} {quiet}, {ty} {stepped}")
            values[node.id] = out
        elif node.kind == "loop":
            stepped = e.fresh("lp")
            arg_t = e.t.of(graph.node(node.inputs[0]).type_)
            e.emit(f"{stepped} = call fastcc {ty} @{_fn(node.step)}"
                   f"({ty} {prevs[node.id]}, {ty} {held}, "
                   f"{arg_t} {values[node.inputs[0]]})")
            # `z` at the first instant rather than silence: a `loop`'s state
            # is the program's own and `z` is where it said to start.  That
            # is `scan`'s rule, and it is what the oracle does — its `scan`
            # emits the untouched ring, both ends of which are `z`.
            init, _t = e.constant(node.init)
            out = e.fresh("lpv")
            e.emit(f"{out} = select i1 %first, {ty} {init}, {ty} {stepped}")
            values[node.id] = out
        elif node.kind in ("scope", "spectro"):
            # Identity on the sound, a ring write on the way past —
            # `spec/scope.md`.  The pass-through is the value; the
            # shared store below writes it into the ring slot the
            # `line` arithmetic picked, which is the whole node.
            values[node.id] = values[node.inputs[0]]
        elif node.kind == "tap":
            out = _emit_tap(e, node, ty, values[node.inputs[1]], rings[node.id])
            values[node.id] = out
            taps.append(node)
        elif node.kind == "slide":
            # `tap`'s read, `feedback`'s write: fold the interpolated read
            # with the input, store the result at `t` — during the pass,
            # because the read is clamped a sample back and cannot see it.
            read = _emit_tap(e, node, ty, values[node.inputs[1]],
                             rings[node.id])
            stepped = e.fresh("sl")
            arg_t = e.t.of(graph.node(node.inputs[0]).type_)
            e.emit(f"{stepped} = call fastcc {ty} @{_fn(node.step)}"
                   f"({ty} {read}, {arg_t} {values[node.inputs[0]]})")
            # Silence at the first instant, as the oracle's `scan` gives.
            quiet, _t = e.constant(_zero_of(graph, node.type_))
            out = e.fresh("slv")
            e.emit(f"{out} = select i1 %first, {ty} {quiet}, {ty} {stepped}")
            values[node.id] = out
            at = e.fresh("sat")
            e.emit(f"{at} = urem i64 %t, {node.length}")
            where = e.fresh("sslot")
            e.emit(f"{where} = getelementptr inbounds [{node.length} x {ty}], "
                   f"ptr {rings[node.id]}, i64 0, i64 {at}")
            e.emit(f"store {ty} {out}, ptr {where}")
        else:                                                     # zip
            out = e.fresh("z")
            a_t = e.t.of(graph.node(node.inputs[0]).type_)
            b_t = e.t.of(graph.node(node.inputs[1]).type_)
            e.emit(f"{out} = call fastcc {ty} @{_fn(node.step)}"
                   f"({a_t} {values[node.inputs[0]]}, "
                   f"{b_t} {values[node.inputs[1]]})")
            values[node.id] = out
        if node.kind not in ("tap", "slide"):
            e.emit(f"store {ty} {values[node.id]}, ptr {slot}")

    # **The taps are written last**, and that is what a delay line is: its
    # value this instant came out of the state, and what goes in is this
    # instant's input, which may be computed from its own output.  Writing
    # in the pass would close a cycle with nothing in it.
    for node in taps:
        ty = e.t.of(node.type_)
        at = e.fresh("wat")
        e.emit(f"{at} = urem i64 %t, {node.length}")
        where = e.fresh("wslot")
        e.emit(f"{where} = getelementptr inbounds [{node.length} x {ty}], "
               f"ptr {rings[node.id]}, i64 0, i64 {at}")
        # Nothing enters at the first instant — `scan`'s asymmetry, which
        # the oracle's definition has and the engine has to match.
        keep = e.fresh("keep")
        e.emit(f"{keep} = load {ty}, ptr {where}")
        put = e.fresh("put")
        e.emit(f"{put} = select i1 %first, {ty} {keep}, "
               f"{ty} {values[node.inputs[0]]}")
        e.emit(f"store {ty} {put}, ptr {where}")

    # A basic block ends with a terminator, and the node computations above
    # are all in `loop:` — calls do not open blocks.
    e.emit("br label %tail")
    body.append("tail:")

    # **The output buffer is interleaved**, which is what every sound card
    # and every WAV already wants: frame `k` of a `c`-channel graph starts
    # at element `k * c`.  A mono graph multiplies by one and emits what it
    # always did, so `render_block` is unchanged for every existing example
    # down to the IR text.
    channels = out_channels(graph)
    frame = values[graph.out]
    out_ty = e.t.of(graph.node(graph.out).type_)
    if channels == 1:
        e.emit(f"%base = getelementptr inbounds {out_type}, ptr %out, i64 %k")
    else:
        e.emit(f"%kbase = mul i64 %k, {channels}")
        e.emit(f"%base = getelementptr inbounds {out_type}, ptr %out, "
               "i64 %kbase")
    if mix:
        # `g0 + (g1 - g0) * k / n` — one gain per *frame*, so the channels
        # of a stereo pair are never faded by different amounts.  A stereo
        # image that wanders during the fade is audible exactly where the
        # point was for nothing to be.
        e.emit("%kf = sitofp i64 %k to double")
        e.emit("%nf = sitofp i64 %n to double")
        e.emit("%frac = fdiv double %kf, %nf")
        e.emit("%dg = fsub double %g1, %g0")
        e.emit("%upto = fmul double %dg, %frac")
        e.emit("%gainr = fadd double %g0, %upto")
        # **Clamped, so a fade shorter than a block finishes inside it.**
        # The endpoints are handed over *unclamped* — `(done + n) / len` can
        # exceed 1 — and without this the ramp was stretched across the
        # whole block instead of arriving partway through and holding.  The
        # two complementary ramps still sum to unity: while both are inside
        # `0 .. 1` they sum by construction, and past the end one saturates
        # at 1 exactly as the other saturates at 0.
        e.emit("%gainlo = call double @llvm.maxnum.f64(double %gainr, "
               "double 0.000000e+00)")
        e.emit("%gaincl = call double @llvm.minnum.f64(double %gainlo, "
               "double 1.000000e+00)")
        e.emit(f"%gain = fptrunc double %gaincl to {out_type}")
    for c in range(channels):
        if channels == 1:
            sample = frame
        else:
            # Field `c` of the record, past the tag word at index 0.  The
            # record is an SSA value here — it was never in memory — so
            # this is `extractvalue` and costs nothing at runtime.
            sample = e.fresh("ch")
            e.emit(f"{sample} = extractvalue {out_ty} {frame}, {c + 1}")
        if out_type == "float":
            ok = e.fresh("ok")
            safe = e.fresh("cl")
            lo = e.fresh("cl")
            hi = e.fresh("cl")
            narrow = e.fresh("cl")
            # **NaN first, and the order is the whole point.**  IEEE
            # `minNum`/`maxNum` return the *non-NaN* operand, which is
            # usually the helpful thing and is exactly wrong here: a NaN
            # would come through `minnum(x, 1)` as 1 and out of the clamp
            # as **+1.0**, so one divide by zero anywhere in a synth
            # becomes sustained full-scale DC on the speaker.  That is the
            # worst signal this can emit — maximum power, and a cone that
            # does not move is a voice coil that is not cooled by moving.
            #
            # `fcmp ord x, x` is false only for NaN, so this is two
            # instructions and no branch.  Infinities need nothing: the
            # clamp already takes them to ±1.
            e.emit(f"{ok} = fcmp ord double {sample}, {sample}")
            e.emit(f"{safe} = select i1 {ok}, double {sample}, "
                   f"double 0.000000e+00")
            sample = safe
            e.emit(f"{lo} = call double @llvm.minnum.f64(double {sample}, "
                   f"double 1.000000e+00)")
            e.emit(f"{hi} = call double @llvm.maxnum.f64(double {lo}, "
                   f"double -1.000000e+00)")
            e.emit(f"{narrow} = fptrunc double {hi} to float")
            sample = narrow
        if c == 0:
            slot = "%base"
        else:
            slot = e.fresh("outp")
            e.emit(f"{slot} = getelementptr inbounds {out_type}, ptr %base, "
                   f"i64 {c}")
        if mix:
            wet = e.fresh("wet")
            was = e.fresh("was")
            sum_ = e.fresh("sum")
            e.emit(f"{wet} = fmul {out_type} {sample}, %gain")
            e.emit(f"{was} = load {out_type}, ptr {slot}")
            e.emit(f"{sum_} = fadd {out_type} {was}, {wet}")
            sample = sum_
        e.emit(f"store {out_type} {sample}, ptr {slot}")
    e.emit("%tnext = add i64 %t, 1")
    e.emit("store i64 %tnext, ptr %tptr")
    e.emit("%knext = add i64 %k, 1")
    e.emit("%more = icmp slt i64 %knext, %n")
    e.emit("br i1 %more, label %loop, label %done")
    body.append("done:")
    e.emit("ret void")

    gains = ", double %g0, double %g1" if mix else ""
    return ([f"define void @{name}(ptr %s, ptr %out, i64 %n, "
             f"ptr %control{gains}) {{", "entry:"] + body + ["}"])


# ── Helpers ─────────────────────────────────────────────────────────────────


def _ident(name: str) -> str:
    """An LLVM identifier.  Quoted, because origins contain `/` and `#`."""
    return '"' + name.replace('"', "") + '"'


def _emit_tap(e, node, ty: str, back: str, base: str) -> str:
    """`back` samples ago, interpolated — the tap's arithmetic in IR.

    Clamped to 1 .. n-1 as the reference engine clamps it, and the index
    arithmetic is done on `t + 2n - whole` rather than `t - whole` because
    `urem` reads its operand as *unsigned*: a negative `t - whole` early in
    the run would wrap to an enormous number instead of counting backwards.
    Both `whole` and `whole + 1` are at most `n`, so adding `2n` keeps the
    numerator non-negative and the remainder unchanged.
    """
    n = node.length
    lo = e.fresh("tlo")
    e.emit(f"{lo} = call double @llvm.maxnum.f64(double {back}, double 1.0)")
    d = e.fresh("td")
    e.emit(f"{d} = call double @llvm.minnum.f64(double {lo}, "
           f"double {float(n - 1)!r})")
    whole = e.fresh("tw")
    e.emit(f"{whole} = fptosi double {d} to i64")
    wf = e.fresh("twf")
    e.emit(f"{wf} = sitofp i64 {whole} to double")
    frac = e.fresh("tfr")
    e.emit(f"{frac} = fsub double {d}, {wf}")

    def at(offset: int) -> str:
        raw = e.fresh("traw")
        e.emit(f"{raw} = sub i64 %t, {whole}")
        shifted = e.fresh("tsh")
        e.emit(f"{shifted} = add i64 {raw}, {2 * n - offset}")
        idx = e.fresh("tix")
        e.emit(f"{idx} = urem i64 {shifted}, {n}")
        ptr = e.fresh("tptr")
        e.emit(f"{ptr} = getelementptr inbounds [{n} x {ty}], ptr {base}, "
               f"i64 0, i64 {idx}")
        got = e.fresh("tval")
        e.emit(f"{got} = load {ty} , ptr {ptr}")
        return got

    near, far = at(0), at(1)
    span = e.fresh("tsp")
    e.emit(f"{span} = fsub double {far}, {near}")
    scaled = e.fresh("tsc")
    e.emit(f"{scaled} = fmul double {span}, {frac}")
    out = e.fresh("tap")
    e.emit(f"{out} = fadd double {near}, {scaled}")
    return out


def _zero_of(graph, type_name: str):
    """A silent value of this type — `audioengine.zero`, borrowed.

    A `line` has no `init` to fall back on at the first instant the way a
    `scan` does, so the two engines have to agree about what silence *is*
    for its element type, and agreeing is cheapest when it is one function.
    """
    from .audioengine import zero

    return zero(graph, type_name)


def _fn(name: str) -> str:
    """A generated function's symbol, in its own namespace.

    Prefixed, and the reason is a bug worth keeping: `audio.ges` defines
    `floor`, which was emitted as `@floor` — and at `-O0` LLVM lowers
    `llvm.floor.f64` to a **call to libm's `floor`**, which then bound to
    the generated one.  `wrap` recursed half a million frames deep and
    segfaulted.  At `-O2` the intrinsic becomes an SSE instruction and the
    collision never happens, which is exactly why both optimisation levels
    are compared.  A synth may define `sin`, `pow` or `abs` too.
    """
    return _ident("gestate." + name)


def _double(x: float) -> str:
    """A `double` literal LLVM reads back exactly.

    Hexadecimal, not decimal: LLVM parses `0x…` as the exact bit pattern,
    and a decimal it has to round is precisely how a bit-identical
    comparison would fail for a reason nobody could see.
    """
    import struct

    bits = struct.unpack("<Q", struct.pack("<d", x))[0]
    return f"0x{bits:016X}"


def check_int_range(graph: Graph) -> None:
    """No check yet — the hazard, named where a reader will meet it.

    `Int` is unbounded in the language and `i64` here, so a computation the
    oracle carries exactly will wrap in the engine.  `drums.ges` reaches
    25.7% of the range in its LCG, so the examples are safe and nothing
    proves the next synth is.  The failure is silent in the sound and loud
    in the bit-identical comparison, which is where it will surface.
    """


# ── Building it, where a toolchain exists ───────────────────────────────────


#: Build counter — see `build`.
_BUILD = __import__("itertools").count()


#: Bump when what `build` produces changes for the same IR text — the
#: store's key is `(schema, sha256(IR), opt)`, and nothing else.
_SO_SCHEMA = 1


def _flags(opt: str) -> list:
    """What clang is asked, which is not only the optimisation level.

    **`-fno-slp-vectorize`, because the pass costs a second and buys
    nothing here.**  `-ftime-report` on `quartet.ges` put 56% of the
    optimiser inside `SLPVectorizerPass` — 1.0 s of 1.8 — and turning
    it off makes the object **bit-identical**, which is not luck: this
    emitter writes no fast-math flags, so nothing may reorder a
    floating-point sum, and superword parallelism across a graph of
    scalar step functions finds almost nothing it is allowed to take.
    Measured over `quartet` (2.7 s → 1.7), `chopin` (0.53 → 0.41),
    `strings2`, `lead` and `blip`: the saving scales with the file and
    the samples never move.  Render speed is unchanged within the noise
    of repeated runs — which is the claim, rather than the 8% one run
    showed.

    Named here rather than folded into `opt` so the store's key can be
    the whole command: an object built before this line was written has
    a different key and is simply not found, which is what a
    content-addressed cache is for.
    """
    return [opt, "-fno-slp-vectorize"]


def _so_store():
    """Where compiled objects are remembered, or `None` when off.

    The `.so` is a pure function of the IR text and the flags, so this is
    a content-addressed cache in the strict sense: nothing in it is
    authoritative, a miss costs one clang run, and `GESTATE_SO_CACHE=0`
    turns it off.  Reopening yesterday's synth stops paying for clang,
    which was measured at 3.5 s of a cold editor start.
    """
    import os
    from pathlib import Path

    if os.environ.get("GESTATE_SO_CACHE", "1") == "0":
        return None
    root = os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")
    return Path(root) / "gestate"


def build(graph: Graph, directory, opt: str = "-O2"):
    """Compile the graph to a shared object and return its path.

    `-O2` is safe for the comparison and worth stating why: LLVM will not
    reassociate floating-point arithmetic without fast-math flags on the
    instructions, and this emitter writes none.

    Answered from the store when the same IR was built before: the object
    is *copied* into `directory` rather than loaded from the store, so a
    cached build and a fresh one live identical lives — a fresh name in a
    caller-owned directory — and a cleared cache mid-session breaks
    nothing that is already mapped.
    """
    import shutil
    import subprocess
    from pathlib import Path

    # A fresh name per build.  Overwriting a shared object that is still
    # mapped corrupts the mapping and crashes the process rather than
    # failing — and rebuilding into one directory is exactly what testing
    # several block sizes does.
    directory = Path(directory)
    stem = f"synth{next(_BUILD)}"
    ll = directory / f"{stem}.ll"
    so = directory / f"{stem}.so"
    text = emit(graph)
    ll.write_text(text)

    store = _so_store()
    kept = None
    if store is not None:
        import hashlib

        sha = hashlib.sha256(
            (" ".join(_flags(opt)) + "\n" + text).encode()).hexdigest()[:32]
        kept = store / f"so-{_SO_SCHEMA}-{sha}.so"
        if kept.exists():
            try:
                shutil.copyfile(kept, so)
                return so
            except OSError:
                pass                     # a torn cache is only a slow one

    # `-lm` is not optional: `llvm.floor.f64` becomes an SSE instruction at
    # `-O2` and a call to libm's `floor` at `-O0`, so leaving it out builds
    # a shared object that loads cleanly and segfaults the first time a
    # phase is wrapped.  Optimised and unoptimised builds must both work,
    # because comparing them is how the no-fast-math claim is checked.
    #
    # Timed below the store, so `GESTATE_BUILD_TIME` shows the compiler
    # runs and not the copies — a hit is meant to cost nothing and a
    # phase reading 0.05 s would leave you wondering which it was.
    from .buildtime import phase

    with phase("clang"):
        subprocess.run(["clang", *_flags(opt), "-shared", "-fPIC", str(ll),
                        "-o", str(so), "-lm"],
                       check=True, capture_output=True)
    if kept is not None:
        try:
            kept.parent.mkdir(parents=True, exist_ok=True)
            tmp = kept.with_name(kept.name + f".tmp{stem}")
            shutil.copyfile(so, tmp)
            tmp.replace(kept)            # atomic — a reader sees whole files
        except OSError:
            pass
    return so


def load(so_path):
    """`(render_block, State)` — the generated code, callable from Python."""
    import ctypes

    lib = ctypes.CDLL(str(so_path))
    lib.render_block.restype = None
    lib.render_block.argtypes = [ctypes.c_void_p,
                                 ctypes.POINTER(ctypes.c_double),
                                 ctypes.c_int64, ctypes.c_int64]
    return lib


def native_blocks(graph: Graph, directory, samples: int,
                  block: int | None = None, control=None, opt: str = "-O2"):
    """Blocks of interleaved doubles, yielded as the generated code fills
    them.

    The loop behind `run_native`, split out so a long render can be
    *consumed as it goes*: a twenty-minute piece held whole as Python
    floats measured in the gigabytes, and the wav writer only ever
    needed one block of it.  Each yield is a fresh list of
    `want * channels` doubles, gone as soon as the caller lets go of it.
    """
    import ctypes

    lib = load(build(graph, directory, opt=opt))
    # Declared rather than inferred: the fourth argument is a *pointer* to
    # the control slots now, and ctypes left to guess turns a `c_void_p`
    # into "cannot be interpreted as an integer" at the call.
    lib.render_block.restype = None
    lib.render_block.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                 ctypes.c_int64, ctypes.c_void_p]
    size = block or samples
    # The state is `t` plus one slot per node; the widest field is 8 bytes
    # and everything is naturally aligned, so a zeroed buffer of 8-byte
    # slots is the layout.  Zero is right for `t`; every other field is
    # written before it is read, because `t == 0` selects the initial value.
    width = 8 * (1 + sum(_slots(graph, n) for n in graph.nodes))
    state = ctypes.create_string_buffer(width)
    # Interleaved, so a block of `size` frames is `size * channels` doubles.
    # `samples` stays a count of *frames* — it is the graph's instants, and
    # an instant is one frame however many channels it carries.
    channels = out_channels(graph)
    buf = (ctypes.c_double * (size * channels))()

    control = control or (lambda _node, t: t)
    sources = graph.control_sources()
    slots = (ctypes.c_int64 * max(1, len(sources)))()
    done = 0
    while done < samples:
        want = min(size, samples - done)
        pack_control(graph, slots, sources, control, done)
        lib.render_block(ctypes.cast(state, ctypes.c_void_p), buf, want,
                         ctypes.cast(slots, ctypes.c_void_p))
        yield buf[:want * channels]
        done += want


def run_native(graph: Graph, directory, samples: int, block: int | None = None,
               control=None, opt: str = "-O2") -> list:
    """Render through the generated code — the stage-4 comparison itself."""
    channels = out_channels(graph)
    out: list = []
    for got in native_blocks(graph, directory, samples, block=block,
                             control=control, opt=opt):
        # Floats for a mono graph and frame tuples for the rest, which is
        # what `audio.render`/`render_frames` and `parse_golden` hand back —
        # so the bit-identical comparison stays `native == want`.
        out += got if channels == 1 else [
            tuple(got[i:i + channels]) for i in range(0, len(got), channels)]
    return out


def pack_control(graph: Graph, slots, sources: list, control, t: int) -> None:
    """Fill the control buffer for one block, one slot per source.

    A `Float` parameter is **reinterpreted** into its slot rather than
    converted: the generated code bitcasts it back, so a knob at 0.5 must
    arrive as the bits of 0.5 and not as the integer 0.  Getting this
    backwards is silent — the sound is wrong and nothing raises — which is
    why it is one function with one caller per back end rather than two
    lines repeated.
    """
    import ctypes
    import struct

    for i, node in enumerate(sources):
        value = control(node.id, t)
        if node.type_ == "Float":
            slots[i] = struct.unpack("<q", struct.pack("<d", float(value)))[0]
        else:
            slots[i] = int(value)
    return ctypes.cast(slots, ctypes.c_void_p)


def _slots(graph: Graph, node) -> int:
    """How many 8-byte words a node's **state** occupies.

    A node's value and its state are the same thing everywhere except a
    `line`, whose value is one sample and whose state is `length` of them.
    Getting this wrong is not a wrong number: the host allocates `%State`
    from it, so a `line` counted as one word gives the generated code a
    buffer shorter than the struct it writes through — measured, a
    heap overflow and a segfault, with the ring reading uninitialised
    memory (`3.98e-310`) until it did.
    """
    words = _words(graph, node.type_)
    return (words * node.length
            if node.kind in ("line", "tap", "loop", "slide", "scope", "spectro")
            else words)


def _words(graph: Graph, type_name: str) -> int:
    """The size of a type, in 8-byte words — `Graph.words`.

    Moved onto the graph when the extractor and the control buffer both
    needed it: a layout is a property of the IR rather than of one back
    end.  Kept here as the name this module's readers already know.
    """
    return graph.words(type_name)


def state_size(graph: Graph) -> int:
    """Bytes in `%State`: the instant counter, then one slot per node."""
    return 8 * (1 + sum(_slots(graph, n) for n in graph.nodes))


def pack_state(graph: Graph, values: list, t: int, lines=None) -> bytes:
    """A Python state, as the bytes `%State` is.

    The two engines share one notion of what a state *is* — a value per
    node — and differ only in how they hold it.  Stage 5 migrates the
    shared one and packs the result, so migration has a single semantics
    and the Python engine's tests are tests of the live path too.

    `lines` is `State.lines` — the ring buffers, which are the one piece of
    state that is not one value per node.
    """
    import struct

    out = bytearray(struct.pack("<q", t))
    for node, value in zip(graph.nodes, values):
        if node.kind in ("line", "tap", "loop", "slide", "scope", "spectro"):
            # **A line's slot is its ring, not its sample.**  `values` is
            # one value per node and a line's is the sample downstream
            # read; the ring lives in `State.lines`, and what goes into the
            # struct here is the ring.  Silence when there is none, which
            # is a line that has not run yet or one a migration reset.
            start = (node.init if node.kind == "loop"
                     else _zero_of(graph, node.type_))
            ring = (lines or {}).get(node.id) or [
                start for _ in range(node.length)]
            for held in ring:
                out += _pack(graph, node.type_, held)
            continue
        out += _pack(graph, node.type_, value)
    return bytes(out)


def unpack_state(graph: Graph, data) -> tuple:
    """`(values, t, lines)` — the running engine's state, read back out."""
    import struct

    raw = bytes(data)[:state_size(graph)]
    t = struct.unpack_from("<q", raw, 0)[0]
    values, lines, at = [], {}, 8
    for node in graph.nodes:
        if node.kind in ("line", "tap", "loop", "slide", "scope", "spectro"):
            ring = []
            for _ in range(node.length):
                held, at = _unpack(graph, node.type_, raw, at)
                ring.append(held)
            lines[node.id] = ring
            # The *sample* a line last produced is the slot the cursor is
            # about to move off, which is where it was written.
            values.append(ring[(t - 1) % node.length] if t else
                          node.init if node.kind == "loop" else
                          _zero_of(graph, node.type_))
            continue
        value, at = _unpack(graph, node.type_, raw, at)
        values.append(value)
    return values, t, lines


def _pack(graph: Graph, type_name: str, value) -> bytes:
    import struct

    if type_name == "Float":
        return struct.pack("<d", value)
    if type_name == "Int":
        return struct.pack("<q", value)
    tag, fields = value
    out = bytearray(struct.pack("<q", tag))
    for name, field in zip(graph.layouts[type_name][0]["fields"], fields):
        out += _pack(graph, name, field)
    return bytes(out)


def _unpack(graph: Graph, type_name: str, raw: bytes, at: int) -> tuple:
    import struct

    if type_name == "Float":
        return struct.unpack_from("<d", raw, at)[0], at + 8
    if type_name == "Int":
        return struct.unpack_from("<q", raw, at)[0], at + 8
    tag = struct.unpack_from("<q", raw, at)[0]
    at += 8
    fields = []
    for name in graph.layouts[type_name][0]["fields"]:
        value, at = _unpack(graph, name, raw, at)
        fields.append(value)
    return (tag, tuple(fields)), at


# ── CLI ─────────────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    """Retired — the IR is a library call on the way to sound."""
    import sys

    print("gestate: the `gestate.audiollvm` CLI is retired — the IR is a "
          "library call (`audiollvm.emit`),\nand every render through "
          "`python -m gestate.audioperform -o` compiles it on the way to "
          "sound.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
