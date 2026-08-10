"""Serialize a compiled program for `crust/` — and read both answers.

`crust` is the G-machine's pure core in Rust (`spec/crust.md`), and
`gmachine.py` is the reference it is held against.  This module is the
seam: `serialize` lowers the globals reachable from an entry point into
the flat text format the crate parses, refusing — by name, before
anything runs — any instruction outside the core.  A program that
crosses is one the mirror wholly understands, which is what makes a
disagreement a bug rather than a shrug.

`canonical` renders a forced value the way `crust` prints one —
`42`, `#tag(a b)` — so the parity test compares strings and the strings
mean the same thing.
"""

from __future__ import annotations

from . import gmachine as gm


class CrustError(Exception):
    pass


#: The pure core: what a score's forcing needs, and nothing reactive.
_SIMPLE = {gm.Unwind: "Unwind", gm.Mkap: "Mkap", gm.Eval: "Eval",
           gm.MatchFail: "MatchFail", gm.AddInt: "AddInt",
           gm.SubInt: "SubInt", gm.MulInt: "MulInt", gm.DivInt: "DivInt",
           gm.ModInt: "ModInt", gm.XorInt: "XorInt",
           gm.DivFloat: "DivFloat", gm.ModFloat: "ModFloat",
           gm.ToFloat: "ToFloat", gm.FloorFloat: "FloorFloat"}
_UNARY = {gm.Push: "Push", gm.PushArg: "PushArg",
          gm.Update: "Update", gm.Pop: "Pop", gm.Alloc: "Alloc",
          gm.Slide: "Slide", gm.Proj: "Proj"}


def _float_bits(value: float) -> int:
    """A float as its IEEE bits — the only spelling that survives two
    languages' decimal printers without a quiet last-ulp drift."""
    import struct

    return struct.unpack("<Q", struct.pack("<d", value))[0]


def serialize(state, entry: str = "main") -> str:
    """The program under `entry`, in crust's flat text format.

    Only what `entry` reaches crosses: a compiled program's globals
    include every library definition, reactive machinery and all, and a
    score-forcing core has no business refusing a program over a
    `NewChan` nothing will ever call.
    """
    blocks: list = []
    lines: list = ["crust 1"]

    def block_of(code) -> int:
        rows: list = []
        for instr in code:
            t = type(instr)
            if t in _SIMPLE:
                rows.append(f"I {_SIMPLE[t]}")
            elif t in _UNARY:
                field = next(iter(instr.__dataclass_fields__))
                rows.append(f"I {_UNARY[t]} {getattr(instr, field)}")
            elif t is gm.PushInt:
                # `PushInt` carries either kind of literal — the
                # compiler reuses it for floats under `NNum`'s duck
                # typing — so the split into two spellings is made
                # here, where the value's own type is visible.
                if isinstance(instr.n, float):
                    rows.append(f"I PushFloat {_float_bits(instr.n)}")
                else:
                    rows.append(f"I PushInt {instr.n}")
            elif t is gm.MathFloat:
                rows.append(f"I MathFloat {instr.fn}")
            elif t is gm.PushGlobal:
                rows.append(f"I PushGlobal {instr.name}")
            elif t is gm.Pack:
                rows.append(f"I Pack {instr.tag} {instr.arity}")
            elif t is gm.PackTuple:
                rows.append(f"I PackTuple {gm.tuple_tag(instr.arity)} "
                            f"{instr.arity}")
            elif t is gm.EqInt:
                rows.append(f"I EqInt {instr.tag_true} {instr.tag_false}")
            elif t is gm.LtInt:
                rows.append(f"I LtInt {instr.tag_true} {instr.tag_false}")
            elif t is gm.CaseJump:
                pairs = [(tag, block_of(body)) for tag, body in instr.table]
                rows.append("I CaseJump " + str(len(pairs)) + " "
                            + " ".join(f"{t} {b}" for t, b in pairs))
            else:
                raise CrustError(
                    f"`{t.__name__}` is outside crust's pure core — this "
                    f"program needs the reference machine")
        blocks.append(rows)
        return len(blocks) - 1

    done: dict = {}
    queue = [entry]
    globals_out = []
    while queue:
        name = queue.pop()
        if name in done:
            continue
        node = state.globals.get(name)
        if node is None:
            raise CrustError(f"unknown global `{name}`")
        done[name] = True
        for instr in _walk(node.code):
            if isinstance(instr, gm.PushGlobal):
                queue.append(instr.name)
        globals_out.append((name, node.arity, block_of(node.code)))

    for rows in blocks:
        lines.append("block")
        lines.extend(rows)
    for name, arity, block in globals_out:
        lines.append(f"global {name} {arity} {block}")
    lines.append(f"entry {entry}")
    return "\n".join(lines) + "\n"


def _walk(code):
    for instr in code:
        yield instr
        if isinstance(instr, gm.CaseJump):
            for _tag, body in instr.table:
                yield from _walk(body)


# ── In-process: the cdylib over ctypes ──────────────────────────────────
#
# `crust/` builds a `libcrust.so` beside its binary, and this is the
# house way of using it: ctypes over a hand-declared five-function
# surface, the same pattern `audiollvm` and `audiohost` already live
# by.  No PyO3, no packaging tool, no CPython-version coupling — the
# dependency cost of the seam is zero on both sides, which is what
# `requirements.txt` and `crust/Cargo.toml` each promise.

_CRUST_DIR = None
_LIB = None


def _stream_abi(lib):
    """Declare the stream half of the surface, once."""
    import ctypes

    lib.crust_stream_open.argtypes = [
        ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int64, ctypes.c_int64,
        ctypes.c_int64, ctypes.c_int64, ctypes.c_int64, ctypes.c_int64]
    lib.crust_stream_open.restype = ctypes.c_void_p
    lib.crust_stream_pull.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int64, ctypes.c_int64,
        ctypes.c_int64]
    lib.crust_stream_pull.restype = ctypes.POINTER(ctypes.c_int64)
    lib.crust_stream_stat.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_int64)]
    lib.crust_stream_stat.restype = None
    lib.crust_stream_free.argtypes = [ctypes.c_void_p]
    lib.crust_stream_free.restype = None
    lib.crust_stream_open_live.argtypes = [
        ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int64, ctypes.c_int64,
        ctypes.c_int64, ctypes.c_int64, ctypes.c_int64, ctypes.c_int64,
        ctypes.c_int64]
    lib.crust_stream_open_live.restype = ctypes.c_void_p
    lib.crust_stream_ask.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(ctypes.c_int64)]
    lib.crust_stream_ask.restype = ctypes.c_int64
    lib.crust_stream_answer.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_int64), ctypes.c_int64]
    lib.crust_stream_answer.restype = ctypes.c_int64


def _library():
    """The cdylib, built at need and loaded once per process."""
    global _CRUST_DIR, _LIB
    if _LIB is not None:
        return _LIB
    import ctypes
    import shutil
    import subprocess
    from pathlib import Path

    _CRUST_DIR = Path(__file__).resolve().parent.parent / "crust"
    so = _CRUST_DIR / "target" / "release" / "libcrust.so"
    if not so.exists():
        if shutil.which("cargo") is None:
            raise CrustError(
                "no libcrust.so and no cargo to build it — "
                "`cargo build --release` in `crust/` makes one")
        subprocess.run(["cargo", "build", "--release", "--quiet",
                        "--target-dir", str(_CRUST_DIR / "target")],
                       cwd=_CRUST_DIR, check=True)
    lib = ctypes.CDLL(str(so))
    lib.crust_load.argtypes = [ctypes.c_char_p]
    lib.crust_load.restype = ctypes.c_void_p
    # `c_void_p`, not `c_char_p`: ctypes converts a `c_char_p` result
    # to bytes and drops the pointer, and the pointer is what
    # `crust_free_str` needs back.
    lib.crust_force.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    lib.crust_force.restype = ctypes.c_void_p
    lib.crust_error.argtypes = []
    lib.crust_error.restype = ctypes.c_char_p
    lib.crust_free_str.argtypes = [ctypes.c_void_p]
    lib.crust_free_str.restype = None
    lib.crust_free.argtypes = [ctypes.c_void_p]
    lib.crust_free.restype = None
    _stream_abi(lib)
    _LIB = lib
    return lib


class Native:
    """A crust machine held in-process — `serialize`'s output loaded
    once, forced by entry name as often as wanted, the heap persisting
    between calls so a shared thunk forced once is forced.

    A refusal raises `CrustError` with the machine's own message and
    the process lives on; after a failed force, values already
    computed are intact, but the interrupted redex may be left
    black-holed, so a later force through it refuses rather than
    answers — a refusal, never corruption.
    """

    def __init__(self, program: str):
        self._m = None
        self._lib = _library()
        self._m = self._lib.crust_load(program.encode())
        if not self._m:
            raise CrustError(self._lib.crust_error().decode())

    def force(self, entry: str = "main") -> str:
        """The canonical spelling of `entry`, forced on the machine."""
        import ctypes

        if self._m is None:
            raise CrustError("force on a closed machine")
        out = self._lib.crust_force(self._m, entry.encode())
        if not out:
            raise CrustError(self._lib.crust_error().decode())
        try:
            return ctypes.string_at(out).decode()
        finally:
            self._lib.crust_free_str(out)

    def close(self):
        if self._m is not None:
            self._lib.crust_free(self._m)
            self._m = None

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()

    def __del__(self):
        self.close()


class NativeStream:
    """`audiodynamic.ScoreStream`'s twin, forced by crust in-process.

    Same protocol, same facts across calls — `pull(horizon)` yields
    `(onset, offset, bank, payload)` events below the horizon as far
    as the fuel allowed; `frontier` is the tick below which the stream
    is complete; `stalled` says the last pull ran out of budget
    mid-thought and the parked forcing resumes on the next call.
    Payloads keep their nesting — the wire carries constructor
    structure, so an event here *is* the reference's event, and code
    that indexes into `history` cannot tell the machines apart.
    Patience — the wall clock — stays with the caller, where the wall
    clock lives.
    """

    def __init__(self, native: Native, entry: str, seed: int, *,
                 tick: int = 0, cons_tag: int, nil_tag: int,
                 tuple3_tag: int = 0, by_tag: dict,
                 live_tags: tuple | None = None,
                 fuel: int = 200_000, burst: int = 4096):
        self._native = native
        self._lib = native._lib
        self.by_tag = by_tag
        self.fuel = fuel
        self.burst = burst
        if live_tags is not None:
            # A `liveMain` stream: cue cells, and the tick always
            # applies — resume-aware by its own second argument.
            ev, askt, endt = live_tags
            self._s = self._lib.crust_stream_open_live(
                native._m, entry.encode(), seed, tick,
                cons_tag, nil_tag, ev, askt, endt)
        else:
            self._s = self._lib.crust_stream_open(
                native._m, entry.encode(), seed, tick,
                1 if tick > 0 else 0, cons_tag, nil_tag, tuple3_tag)
        if not self._s:
            raise CrustError(self._lib.crust_error().decode())
        self.done = False
        self.stalled = False
        self.frontier = 0

    @property
    def ask(self):
        """`(tick, port, key)` when a question is owed, else `None` —
        what `LazyPerformer` duck-types for.  The key is the
        question's stamped position (`spec/ariadne.md`)."""
        import ctypes

        if self._s is None:
            return None
        out = (ctypes.c_int64 * 3)()
        if self._lib.crust_stream_ask(self._s, out):
            return (out[0], out[1], out[2])
        return None

    def answer(self, reading) -> None:
        """The port's reading, in: the performance continues into what
        the question's continuation returns."""
        import ctypes

        values = [int(x) for x in reading]
        arr = (ctypes.c_int64 * len(values))(*values) if values else None
        if self._lib.crust_stream_answer(self._s, self._native._m,
                                         arr, len(values)) != 0:
            raise CrustError(self._lib.crust_error().decode())

    def _stat(self):
        import ctypes

        out = (ctypes.c_int64 * 4)()
        self._lib.crust_stream_stat(self._s, self._native._m, out)
        self.done = bool(out[0])
        self.stalled = bool(out[1])
        self.frontier = out[2]
        return out[3]

    @property
    def heap_words(self) -> int:
        """The machine's heap size in nodes — what the collector holds
        down; a number for a test to watch, not a knob."""
        return self._stat()

    def _item(self, buf, at):
        """One payload item off the wire — kind 0 an integer, kind 1
        a float as its bits, kind 2 a constructor whose children
        follow — back into the nested tuple `ScoreStream._flat`
        yields, because `history` is an interface the editor indexes
        into."""
        import struct

        kind = buf[at]
        if kind == 2:
            n = buf[at + 1]
            at += 2
            items = []
            for _ in range(n):
                value, at = self._item(buf, at)
                items.append(value)
            return tuple(items), at
        value = buf[at + 1]
        if kind == 1:
            value = struct.unpack("<d", struct.pack("<q", value))[0]
        return value, at + 2

    def pull(self, horizon: int) -> list:
        """Every event with onset below `horizon` ticks, budget
        permitting — decoded off the wire: `[count, events…]`, each
        event `[on, off, tag, words, payload…]`."""
        if self._s is None:
            raise CrustError("pull on a closed stream")
        buf = self._lib.crust_stream_pull(self._s, self._native._m,
                                          horizon, self.fuel, self.burst)
        if not buf:
            raise CrustError(self._lib.crust_error().decode())
        out = []
        count = buf[0]
        at = 1
        for _ in range(count):
            on, off, tag, words = buf[at], buf[at + 1], buf[at + 2], \
                buf[at + 3]
            at += 4
            stop = at + words
            fields = []
            while at < stop:
                value, at = self._item(buf, at)
                fields.append(value)
            bank = self.by_tag.get(tag)
            if bank is None:
                raise CrustError(
                    f"a note assigned to a voice bank this program does "
                    f"not declare (constructor tag {tag})")
            out.append((on, off, bank, tuple(fields)))
        self._stat()
        return out

    def close(self):
        if self._s is not None:
            self._lib.crust_stream_free(self._s)
            self._s = None

    def __del__(self):
        self.close()


def live_native(state, by_tag: dict, seed: int, tick: int = 0,
                fuel: int = 200_000):
    """The live twin over an *already-compiled* state, or `None` where
    the program cannot cross — the caller's cue to use the reference
    machine, which is never wrong, only slower.

    The one routing decision, spelled once: `audioperform.dynamic` and
    the editor's performer branch both call this rather than each
    holding its own try/except.  Costs a serialization and a ~3 ms
    load on top of the compile the caller already paid; `fuel` is the
    per-pull budget, patience's respelling in steps.
    """
    import subprocess

    try:
        native = Native(serialize(state, "liveMain"))
        return NativeStream(
            native, "liveMain", seed, tick=tick,
            cons_tag=state.cons["Cons"].tag,
            nil_tag=state.cons["Nil"].tag,
            by_tag=by_tag,
            live_tags=(state.cons["CueEv"].tag,
                       state.cons["CueAsk"].tag,
                       state.cons["CueEnd"].tag),
            fuel=fuel)
    except (CrustError, OSError, subprocess.CalledProcessError):
        return None


def native_stream(synth: str, piece: str = "", rate: int = 22050,
                  seed: int = 0, tick: int = 0, live: bool = False,
                  **budgets) -> tuple:
    """`(tempo, native, stream, by_tag)` — `stream_root`'s twin, the
    forcing crossing the seam.

    Compiles once (through `stream_root`, which also answers the
    tempo and the tag table), serializes the reachable pure core, and
    opens the same root crust-side: `streamMain seed`,
    `resumeMain seed tick` when resuming, or `liveMain seed tick` for
    the listening reading.  Keep `native` alive as long as `stream` —
    the stream's indices live in its heap.  Raises `CrustError` where
    the program cannot cross (an instruction outside the pure core),
    which is a caller's cue to fall back to the reference machine.
    """
    from .audioscore import stream_root
    from .gmachine import tuple_tag

    tempo, state, _root, by_tag = stream_root(synth, piece, rate,
                                              seed, tick, live=live)
    if live:
        entry = "liveMain"
        live_tags = (state.cons["CueEv"].tag, state.cons["CueAsk"].tag,
                     state.cons["CueEnd"].tag)
    else:
        entry = "resumeMain" if tick > 0 else "streamMain"
        live_tags = None
    native = Native(serialize(state, entry))
    stream = NativeStream(
        native, entry, seed, tick=tick,
        cons_tag=state.cons["Cons"].tag, nil_tag=state.cons["Nil"].tag,
        tuple3_tag=tuple_tag(3), by_tag=by_tag, live_tags=live_tags,
        **budgets)
    return tempo, native, stream, by_tag


def canonical(node, state) -> str:
    """The value, spelled the way `crust` spells it."""
    from .midi import _force

    node = _force(node, state)
    while isinstance(node, gm.NInd) and node.target is not None:
        node = node.target
    if isinstance(node, gm.NNum):
        if isinstance(node.n, float):
            # Bits, not decimals: float parity is bit parity, and the
            # two languages' printers disagree about exponent notation
            # long before the numbers disagree about anything.
            return f"f{_float_bits(node.n):016x}"
        return str(node.n)
    if isinstance(node, gm.NCon):
        inner = " ".join(canonical(a, state) for a in node.args)
        return f"#{node.tag}({inner})"
    raise CrustError(f"canonical: unexpected node {type(node).__name__}")
