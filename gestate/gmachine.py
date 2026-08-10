"""G-machine: compiler and evaluator for the supercombinator language.

Implements ``spec/supercomb.md``.  The input is the output of the
lambda lifter (``gestate.lift``): a list of
``(Name, Arity, ELambda(params, body))`` containing no nested
``ELambda`` -- each SC's outer ``ELambda`` carries its frame parameters.
``compile_program`` unwraps that ``ELambda`` and compiles the body.

The heap is the live graph of Python ``Node`` objects -- there is no
separate address space, no integer ``Addr`` and no dict/array table.
Nodes reference each other directly; allocation is just constructing a
node, and ``Update`` morphs an existing node in place into an ``NInd``.

Two stack-reference modes are distinguished at compile time because the
stack at supercombinator entry carries the spine of ``NAp`` nodes
(below the ``NGlobal``), so a parameter must be fetched by navigating
its ``NAp`` whereas a ``let``/``case`` binder is a standalone cell:

  * ``Push n``     -- push ``stack !! n`` directly (let/case binders).
  * ``PushArg n``  -- push the ``.arg`` of the ``NAp`` at ``stack !! (n+1)``
                     (a supercombinator parameter).

The compile-time ``Env`` is keyed by binder name (a ``dict[Name,
StackRef]``).  ``Arg n`` corresponds to the n-th SC parameter (in
source order: ``params[i] -> Arg i`` because the caller applies
``params`` left-to-right, which puts ``params[0]``'s value behind the
innermost ``NAp`` = reachable via ``PushArg 0``).  ``Local n``
corresponds to the n-th stack slot from the top (``Local 0`` ==
topmost).  ``let``/``case`` binders are ``Local`` references:

  * ``let``/``letrec``: defs are pushed left-to-right; in the body the
    i-th pair's binder is at offset ``n-1-i`` (last-pushed is topmost),
    so ``compile_let`` assigns ``defs[i].name -> Local (n-1-i)``.
  * ``case`` alt: the ``CaseJump`` reverses the ``NCon`` args when
    pushing them onto the stack (so the LAST source field is topmost),
    and ``compile_case`` assigns ``alt.names[i] -> Local (a-1-i)``.
    (This fixes a previously-latent bug in the DeBruijn implementation
    where ``<t> x y -> x`` returned the SECOND arg.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .expr import (
    Alter,
    EAnnot,
    EAp,
    EAppEx,
    EAppFa,
    EBox,
    ECase,
    EChan,
    ECon,
    EDelay,
    EFix,
    EFor,
    EGFix,
    EGlobal,
    EHole,
    ELambda,
    ELet,
    ENever,
    EChr,
    ENum,
    EProj,
    ESet,
    ESigCons,
    ESigHead,
    ESync,
    ETail,
    ETuple,
    EUnbox,
    EVar,
    EWait,
    EWatch,
    Name,
)
from .match import MATCH_FAIL

__all__ = [
    "Unwind", "PushGlobal", "PushInt", "Push", "PushArg", "Mkap",
    "Update", "Pop", "Alloc", "Slide", "Eval",
    "Pack", "PackTuple", "Proj", "CaseJump",
    "SigCons", "SigHead", "NewChan", "MkDelayAp",
    "EqInt", "LtInt", "ModInt", "DivInt", "ModFloat", "MatchFail", "Hole",
    "Node", "NNum", "NAp", "NGlobal", "NInd", "NCon",
    "NSig", "NChan",
    "TAG_WAIT", "TAG_WATCH", "TAG_SYNC", "TAG_NEVER",
    "TAG_TAIL", "TAG_EXISTS5", "TAG_DELAY",
    "TAG_NOTHING", "TAG_JUST", "TAG_SYNC_L", "TAG_SYNC_R", "TAG_SYNC_BOTH",
    "TAG_NIL", "TAG_CONS", "TAG_FALSE", "TAG_TRUE",
    "TAG_TUPLE_BASE", "tuple_tag", "is_tuple_tag", "tuple_arity", "is_tuple",
    "StackRef", "Arg", "Local",
    "GmState", "compile_program", "run", "step", "show_result",
    "GmError",
]


class GmError(Exception):
    pass


class StepLimit(GmError):
    """`run` spent its whole budget without finishing.

    A subclass rather than a message, because the two mean opposite
    things to a caller with a budget: a `GmError` is the *program's*
    fault and final; a `StepLimit` is the caller's allowance running out,
    and the state it interrupts is left mid-flight and **resumable** —
    call `run` again and evaluation continues where it stopped.  The
    dynamic score's stall rule (`spec/dynamicscore.md`) is built on that
    difference.
    """


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Unwind:
    __slots__ = ()


@dataclass(frozen=True)
class PushGlobal:
    name: Name


@dataclass(frozen=True)
class PushInt:
    n: int


@dataclass(frozen=True)
class Push:
    n: int


@dataclass(frozen=True)
class PushArg:
    n: int


@dataclass(frozen=True)
class Mkap:
    __slots__ = ()


@dataclass(frozen=True)
class Update:
    n: int


@dataclass(frozen=True)
class Pop:
    n: int


@dataclass(frozen=True)
class Alloc:
    n: int


@dataclass(frozen=True)
class Slide:
    n: int


@dataclass(frozen=True)
class Eval:
    __slots__ = ()


@dataclass(frozen=True)
class Pack:
    tag: int
    arity: int


@dataclass(frozen=True)
class PackTuple:
    """Pack the top ``arity`` cells into the ``NCon`` a tuple is.

    The tag is ``tuple_tag(arity)``; see ``TAG_TUPLE_BASE``.
    """
    arity: int


@dataclass(frozen=True)
class Proj:
    """Select the i-th (0-based, source order) field of the ``NCon``
    on top of the stack.  The caller must have ``Eval``-uated the scrut
    to WHNF before emitting this.

    Direct selection rather than a ``CaseJump`` with one alternative, which
    is what a record field lowers to.  Both read the same ``NCon``; this is
    the cheaper path and is why ``EProj`` survives a tuple being tagged.
    """
    i: int


@dataclass(frozen=True)
class CaseJump:
    table: tuple            # tuple of (tag, tuple-of-instructions)


# ---------------------------------------------------------------------------
# FRP / Rizzo instructions (increment 9c)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SigCons:
    """Signal cons: pop tail and value from stack, allocate NSig."""
    __slots__ = ()


@dataclass(frozen=True)
class SigHead:
    """Signal head: project the current value from an NSig on top of stack."""
    __slots__ = ()


@dataclass(frozen=True)
class NewChan:
    """Channel: allocate a fresh NChan, push its address.

    ``elem_type`` is the rendered ``A`` of this occurrence's ``Chan A``,
    carried from inference so the driver can record a channel context.
    """
    elem_type: Optional[str] = None


@dataclass(frozen=True)
class MkDelayAp:
    """Combine two NCon tagDelay nodes on stack into NAp wrapped in NCon tagDelay."""
    __slots__ = ()


# ---------------------------------------------------------------------------
# Primitive integer comparison (increment 10b)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EqInt:
    """Pop two NNum from stack, push NCon(true_tag, ()) if equal else false_tag."""
    tag_true: int
    tag_false: int


@dataclass(frozen=True)
class LtInt:
    """Pop two NNum, push True if stack[0] < stack[1] (top < second)."""
    tag_true: int
    tag_false: int


@dataclass(frozen=True)
class ModInt:
    """Pop two NNum (a % b), push NNum result."""
    __slots__ = ()


@dataclass(frozen=True)
class DivInt:
    """Pop two NNum (a // b), push NNum result."""
    __slots__ = ()


@dataclass(frozen=True)
class MatchFail:
    """Abort: a pattern match fell through every alternative.

    `gestate/exhaust.py` rejects a match that is not exhaustive, so this is
    unreachable in checked code — *except* under guards, where exhaustiveness
    is not decidable and the fall-through is genuine.
    """
    __slots__ = ()


@dataclass(frozen=True)
class Hole:
    """Abort: a `_` was reached.

    The runtime half of `EHole`.  A hole is a question the type checker
    answers and the evaluator cannot, and this is where that is said — at
    the moment the code around it runs, rather than when it is compiled, so
    that a program with an unfinished definition still runs everything
    that does not depend on it.

    The position is carried rather than looked up, because by the time this
    raises there is no expression left to ask — and it is carried in the
    compiler's own 0-based coordinates, so that the `(at line:col)` form
    `audiospans.in_source` already rewrites puts it back in the author's
    file.  A hole is the one error a person is *expecting*, and telling
    them about line 1544 of an assembly they did not write would be the
    least useful moment to start counting preludes.
    """
    line: int = 0
    col: int = 0


@dataclass(frozen=True)
class ModFloat:
    """Pop two NNum (a % b) at `Float`, push NNum result.

    Its own instruction for the reason `DivFloat` is: `ModInt` and this
    disagree, and the disagreement is the point.  Python's `%` takes the
    sign of the divisor at both types, so the *values* agree — what does
    not is the native backend, where the integer form is `srem` and this
    is `frem`, and emitting one for the other is a type error in the IR
    rather than a wrong answer.

    It exists because `Div Float` promises it.  A phase is a number of
    turns in 0..1 and every oscillator in `synth.ges` wraps one by hand;
    `x % 1.0` is what that sentence should have said.
    """
    __slots__ = ()


@dataclass(frozen=True)
class DivFloat:
    """Pop two NNum (a / b), push NNum result.

    The one arithmetic instruction floats genuinely need of their own:
    `DivInt` floors, and `1.0 / 2.0` must be `0.5`.  Addition, subtraction,
    multiplication and the comparisons are shared, because Python's
    operators already do the right thing on either kind of number — the
    `prim_*_float` names exist so generated code says which type it meant.
    """
    __slots__ = ()


@dataclass(frozen=True)
class ToFloat:
    """Pop one NNum, push it as a float.  `Num Float`'s `fromInteger`."""
    __slots__ = ()


@dataclass(frozen=True)
class FloorFloat:
    """Pop one NNum, push the greatest integer not above it."""
    __slots__ = ()


@dataclass(frozen=True)
class MathFloat:
    """Pop one NNum, push `math.<fn>` of it — `sin`, `cos`, `exp`, `log`,
    `sqrt`.

    One instruction rather than five identically-shaped ones, which is
    where generalising earns its place.  `fn` names a function in Python's
    `math`, and the *same* name is what `audiollvm.py` turns into
    `llvm.<fn>.f64`; the two agreeing is not a coincidence to be relied on
    but a fact that is measured — see `test_transcendental.py`.
    """
    fn: str
    __slots__ = ("fn",)


#: The five, and the single place they are listed.  A name here becomes a
#: `prim_<fn>_float` global, a `Float -> Float` signature in `pipeline.py`,
#: a member of the audio fragment, and an `llvm.<fn>.f64` call — so adding
#: one is adding a name here and a prelude line, and forgetting a step is a
#: test failure rather than a silent omission.
MATH_FLOAT = ("sin", "cos", "exp", "log", "sqrt")


@dataclass(frozen=True)
class AddInt:
    """Pop two NNum (a + b), push NNum result."""
    __slots__ = ()


@dataclass(frozen=True)
class SubInt:
    """Pop two NNum (a - b), push NNum result."""
    __slots__ = ()


@dataclass(frozen=True)
class MulInt:
    """Pop two NNum (a * b), push NNum result."""
    __slots__ = ()


# ---------------------------------------------------------------------------
# Nodes -- the heap is the graph of these objects.
# ---------------------------------------------------------------------------

class Node:
    __slots__ = ()


@dataclass
class NNum(Node):
    n: int


@dataclass
class NAp(Node):
    fn: Node
    arg: Node


@dataclass
class NGlobal(Node):
    arity: int
    code: tuple             # tuple of Instruction


@dataclass
class NInd(Node):
    target: Optional[Node]  # None == null indirection (placeholder)


@dataclass
class NCon(Node):
    """A saturated constructor value, and a tuple is one of these.

    ``args`` is in source order: ``args[0]`` is the first field.  A tuple
    carries ``tuple_tag(n)`` — see ``TAG_TUPLE_BASE`` for why it carries a
    tag at all — and is the one kind that ``Proj`` reads directly instead
    of going through ``CaseJump``.  That is an access path, not a second
    representation: the value is the same shape either way.
    """
    tag: int
    args: tuple             # tuple of Node, source-order: args[0]=first arg


# ---------------------------------------------------------------------------
# FRP / Rizzo heap nodes (increment 9b)
# ---------------------------------------------------------------------------

@dataclass(eq=False)
class NSig(Node):
    """A live signal cell — mutated in place by the reactive driver.

    ``value`` is the current (most recent) value of the signal.
    ``tail`` is a delayed ⃝∃ computation that produces the next value.
    ``ticked`` is ``True`` when the signal was updated in the current step.
    ``current`` is the ✓ frontier of the paper's ``η_N ✓ η_E`` heap split
    (§4.1): ``True`` while the cell is on the *now* heap, ``False`` while
    it is still on the earlier heap awaiting this step's sweep.  There is
    deliberately no rule for ``head`` on an earlier-heap signal — such a
    program is stuck (§4.6.3), and running one heap with in-place update
    turns that stuck state into a silently stale read unless the mark is
    checked.

    ``eq=False``: a signal is a mutable heap cell, so it is its own
    identity.  Two distinct cells that happen to hold the same value are
    not the same signal, and the driver keys clocks by cell.
    """
    value: "Node"
    tail: "Node"
    ticked: bool
    current: bool = True


@dataclass
class NChan(Node):
    """A channel identity — integers serve as globally unique channel ids."""
    chan_id: int


# Reserved constructor tags for the six ⃝∃ forms (Rizzo fig. 10).
# These use the existing ``NCon`` node type; the tags let the
# reactive driver's ``ticked``/``advance`` dispatch on them.
TAG_WAIT   = 90
TAG_WATCH  = 91
TAG_SYNC   = 92
TAG_NEVER  = 93
TAG_TAIL   = 94
TAG_EXISTS5 = 95
TAG_DELAY   = 96

# Reserved constructor tags for the two data types the FRP interface names
# in its own signatures: ``Maybe`` (the payload ``watch`` observes) and
# ``Sync`` (what ``sync`` returns).  Unlike the tags above these are
# *ordinary* constructors — user code pattern-matches them — but the
# reactive driver has to recognise them without a constructor table, so
# ``declarations.py`` pins them here rather than handing out fresh tags.
TAG_NOTHING   = 80
TAG_JUST      = 81
TAG_SYNC_L    = 82
TAG_SYNC_R    = 83
TAG_SYNC_BOTH = 84

# `List` and `Bool`, pinned for a third reason: the staged front end
# (`pipeline._stack_front`) numbers the library stack's constructors once
# and a program's after them, so a tag handed out *after* the module's own
# declarations would land at a different number depending on how many
# types the program declares — and a cached `case` over `Bool` would then
# meet a `True` built under the other numbering.  A pinned tag is the same
# in every numbering.  Pinned at the *front* — declared constructors start
# at 4 — because that is where a program with no declarations always put
# them anyway.
TAG_NIL   = 0
TAG_CONS  = 1
TAG_FALSE = 2
TAG_TRUE  = 3

#: Tuple tags — `TAG_TUPLE_BASE + n` is the tag of an `n`-tuple.
#:
#: **A tuple is a one-constructor data type now**, and this is what makes
#: it one.  It used to be an `NTuple` with no tag at all, on the reasoning
#: that a tuple is never matched by `CaseJump` and so needs none — which
#: was true of the evaluator and false of everything downstream: the audio
#: IR lays every flat value out as a tagged `NCon`, so `Sig (Float, Float)`
#: passed the fragment check and then had no layout to be given
#: (`fixme.md` F95).  A tuple that carries its tag is a record whose name
#: nobody wrote, which is what a tuple should have been.
#:
#: Well clear of the range `declarations.fresh_tag` hands out — that counts
#: from 0 and the prelude reaches 3 — and clear of the reserved block
#: above.  Arity is unbounded, so the *base* is a floor rather than a
#: block: a 300-field tuple would be tag 500, and nothing else is up there.
TAG_TUPLE_BASE = 200


def tuple_tag(arity: int) -> int:
    """The tag an `arity`-tuple carries."""
    return TAG_TUPLE_BASE + arity


def is_tuple_tag(tag: int) -> bool:
    """Is this the tag of a tuple rather than of a declared constructor?"""
    return tag > TAG_TUPLE_BASE


def tuple_arity(tag: int) -> int:
    """How wide a tuple this tag belongs to.  Ask `is_tuple_tag` first."""
    return tag - TAG_TUPLE_BASE


def is_tuple(node, arity: int | None = None) -> bool:
    """Is this value a tuple — of `arity` fields, if one is given?

    What `isinstance(node, NTuple)` used to be, and it has to be a function
    now because the *tag* is what separates a tuple from a record with the
    same fields.  A backend reading a `(bpm, events)` out of an entry point
    wants both halves of the question answered at once, and asking them
    separately is how the arity check gets forgotten.
    """
    return (isinstance(node, NCon) and is_tuple_tag(node.tag)
            and (arity is None or tuple_arity(node.tag) == arity))


def _overwrite(node: Node, target: Node) -> None:
    """Turn ``node`` into an ``NInd`` pointing at ``target``."""
    node.__class__ = NInd
    node.target = target


def _update_sig(sig: NSig, value: Node, tail: Node, ticked: bool) -> None:
    """Mutate an ``NSig`` in place — the reactive driver's analogue of ``_overwrite``.

    Updating a cell moves it across the ✓ frontier onto the now heap.
    """
    sig.value = value
    sig.tail = tail
    sig.ticked = ticked
    sig.current = True


# ---------------------------------------------------------------------------
# Stack references -- the compile-time env distinguishes SC parameters
# (which live inside `NAp` nodes on the stack and need `PushArg`) from
# `let`/`case` binders (which are standalone cells and need `Push`).
# ---------------------------------------------------------------------------

class StackRef:
    __slots__ = ()


@dataclass(frozen=True)
class Arg(StackRef):
    n: int


@dataclass(frozen=True)
class Local(StackRef):
    n: int


def _bump(r: StackRef) -> StackRef:
    if isinstance(r, Arg):
        return Arg(r.n + 1)
    return Local(r.n + 1)


def _push_ref(r: StackRef):
    if isinstance(r, Arg):
        return [PushArg(r.n)]
    return [Push(r.n)]


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class GmState:
    """Mutable G-machine state.

    ``code`` and ``stack`` are as in the standard G-machine.
    ``globals`` maps ``Name`` to ``NGlobal`` node addresses.
    ``dump`` holds saved ``(code, stack)`` frames for ``Eval``.
    ``now`` accumulates ``NSig`` addresses in allocation order
    (used by the reactive driver, increment 9d).
    ``chanCounter`` provides fresh channel ids for ``NewChan``, and
    ``chans`` is the channel context Δ: id -> rendered element type.
    ``result_type`` is the inferred type of ``main``, recorded so the
    result can be rendered as what it *is* — a `String` is a cons list of
    code points and would otherwise print as its `Pack` spine.
    """

    __slots__ = ("_code", "_pc", "stack", "globals", "dump", "now",
                 "chanCounter", "chans", "result_type", "cons")

    def __init__(self, code, stack, globals_, dump,
                 now=None, chanCounter=0, chans=None, result_type=None,
                 cons=None):
        self.code = code
        self.stack = stack
        self.globals = globals_
        self.dump = dump
        self.result_type = result_type
        #: The program's constructor table, so a backend reading a
        #: result out of the heap can name a tag instead of guessing
        #: one — user constructors are numbered first (`fixme.md` F68).
        self.cons = cons or {}
        self.now = now if now is not None else []
        self.chanCounter = chanCounter
        self.chans = chans if chans is not None else {}

    #: The instruction stream, and how far into it execution has got.
    #:
    #: `step` used to advance with `instr, s.code = s.code[0], s.code[1:]`,
    #: which allocated a fresh list *per instruction* — 1.5M of them for
    #: `fib 20`.  An index costs nothing and the code list is never mutated,
    #: only rebound, so nothing else has to change: `code` is still a
    #: property, and assigning to it rewinds the counter as before.

    @property
    def code(self) -> list:
        """What is left to execute."""
        return self._code[self._pc:] if self._pc else self._code

    @code.setter
    def code(self, value) -> None:
        self._code = value
        self._pc = 0

    @property
    def isFinal(self) -> bool:
        return self._pc >= len(self._code) and not self.dump

    def __repr__(self):
        return (f"GmState(code={self.code}, stack={self.stack}, "
                f"globals={self.globals}, dump={self.dump})")


# ---------------------------------------------------------------------------
# Compiler
# ---------------------------------------------------------------------------

def compile_program(program, _unused=None):
    """Build the initial ``GmState`` for ``program``.

    ``program`` is the lifter's output: a list of
    ``(Name, Arity, ELambda(params, body))`` triples with no nested
    ``ELambda``.  The wrapping ``ELambda`` supplies the SC's frame
    parameter names.
    """
    globals_ = {}
    for (name, arity, wrapped) in program:
        if not isinstance(wrapped, ELambda) or len(wrapped.params) != arity:
            raise GmError(
                f"compile_program: SC {name!r} expected an ELambda with "
                f"{arity} params, got {wrapped!r}")
        params = list(wrapped.params)
        code = tuple(compile_sc(wrapped.body, params))
        globals_[name] = NGlobal(arity, code)
    initial_code = [PushGlobal("main"), Unwind()]
    return GmState(initial_code, [], globals_, [])


def _prim_unop_code(op) -> tuple:
    """Strict unary primitive: evaluate the argument, then apply ``op``."""
    return (PushArg(0), Eval(), op, Update(1), Pop(1), Unwind())


def _prim_binop_code(op) -> tuple:
    """Strict binary primitive: evaluate both arguments, then apply ``op``.

    At entry the stack is ``[NGlobal, NAp₁, NAp₂, …]``, so ``PushArg 1``
    fetches the second argument (behind ``NAp₂``).  ``Eval`` reduces it to
    WHNF and leaves the value on top, which shifts the spine down by one —
    hence the second ``PushArg 1``, which now reaches ``NAp₁`` and yields
    the *first* argument.  The op then sees ``[x, y, NGlobal, NAp₁, NAp₂, …]``
    and replaces the two values with its result.  ``Update 2`` overwrites
    the redex root ``NAp₂`` so the work is shared.
    """
    return (PushArg(1), Eval(), PushArg(1), Eval(), op,
            Update(2), Pop(2), Unwind())


def add_primitives(state: GmState, true_tag: int, false_tag: int,
                   nil_tag: int = 0, cons_tag: int = 1) -> GmState:
    """Register ``prim_eq_int``, ``prim_lt_int``, and arithmetic primitives."""
    state.globals["prim_eq_int"] = NGlobal(
        2, _prim_binop_code(EqInt(true_tag, false_tag)))
    state.globals["prim_lt_int"] = NGlobal(
        2, _prim_binop_code(LtInt(true_tag, false_tag)))
    state.globals["prim_mod_int"] = NGlobal(2, _prim_binop_code(ModInt()))
    state.globals["prim_add_int"] = NGlobal(2, _prim_binop_code(AddInt()))
    state.globals["prim_sub_int"] = NGlobal(2, _prim_binop_code(SubInt()))
    state.globals["prim_mul_int"] = NGlobal(2, _prim_binop_code(MulInt()))
    state.globals["prim_div_int"] = NGlobal(2, _prim_binop_code(DivInt()))
    # Floats.  Only division and the two coercions are their own
    # instructions; the rest share the integer ones because Python's
    # operators are already correct on either kind of number.  The separate
    # names keep generated code honest about which type it meant.
    state.globals["prim_add_float"] = NGlobal(2, _prim_binop_code(AddInt()))
    state.globals["prim_sub_float"] = NGlobal(2, _prim_binop_code(SubInt()))
    state.globals["prim_mul_float"] = NGlobal(2, _prim_binop_code(MulInt()))
    state.globals["prim_div_float"] = NGlobal(2, _prim_binop_code(DivFloat()))
    state.globals["prim_mod_float"] = NGlobal(2, _prim_binop_code(ModFloat()))
    state.globals["prim_eq_float"] = NGlobal(
        2, _prim_binop_code(EqInt(true_tag, false_tag)))
    state.globals["prim_lt_float"] = NGlobal(
        2, _prim_binop_code(LtInt(true_tag, false_tag)))
    state.globals["prim_to_float"] = NGlobal(1, _prim_unop_code(ToFloat()))
    state.globals["prim_floor_float"] = NGlobal(
        1, _prim_unop_code(FloorFloat()))
    # The transcendentals.  Each is `Float -> Float` and each is exactly the
    # libm function of the same name — `spec/liveaudio.md` open question 2
    # is the argument for why that identity, rather than accuracy, is what
    # matters here.
    for _fn in MATH_FLOAT:
        state.globals[f"prim_{_fn}_float"] = NGlobal(
            1, _prim_unop_code(MathFloat(_fn)))
    # `Char` is represented as its code point, so both coercions are the
    # identity — they exist to move a value between the two *types*.
    ident = (PushArg(0), Update(1), Pop(1), Unwind())
    state.globals["chr"] = NGlobal(1, ident)
    state.globals["ord"] = NGlobal(1, ident)
    # `empty?` — Datafun's boolean eliminator (fig. 2.1), and necessarily a
    # primitive: it is the *non-monotone* observation of a `Prop`, and `for`
    # eliminates only into a semilattice, so nothing in the language can
    # define it.  A set is a cons-list at run time, so this is a tag test:
    # tag 0 is the empty set, tag 1 a cons cell with two fields to drop.
    # The set's cons-list tags are **not** 0 and 1 in general: user
    # constructors are numbered first, so a program declaring three of them
    # pushes `Nil`/`Cons` to 3/4.  Hardcoding them here meant `empty?` —
    # and so `holds`, and so every comprehension guard — died as
    # `CaseJump: no alt for tag 4` in any program with a data type in it.
    state.globals["empty?"] = NGlobal(1, (
        PushArg(0), Eval(),
        CaseJump((
            (nil_tag, (Pack(true_tag, 0), Slide(0))),
            (cons_tag, (Pack(false_tag, 0), Slide(2))),
        )),
        Update(1), Pop(1), Unwind(),
    ))
    state.globals[MATCH_FAIL] = NGlobal(0, (MatchFail(),))
    return state


def compile_sc(body, params):
    """Compile an SC body against its frame parameters.

    ``params`` is the frame parameter list in Arg-index order:
    ``params[i]`` corresponds to ``Arg i`` because the caller applies
    the SC's parameters left-to-right, putting ``params[0]``'s value
    in the innermost ``NAp`` (reachable via ``PushArg 0``).
    """
    env = {p: Arg(i) for i, p in enumerate(params)}
    return compile_r(body, env, len(params))


def compile_r(e, env, arity):
    return compile_c(e, env) + [Update(arity), Pop(arity), Unwind()]


def _bump_env(env):
    """Return a new env with every StackRef bumped by one (one cell
    pushed on top of the stack, shifting all existing references down).
    """
    return {name: _bump(r) for name, r in env.items()}


def _apply_n_bump_env(i, env):
    """Apply `_bump_env` to `env`, `i` times."""
    for _ in range(i):
        env = _bump_env(env)
    return env


def compile_c(e, env):
    if isinstance(e, EGlobal):
        return [PushGlobal(e.name)]
    if isinstance(e, EVar):
        if e.name not in env:
            raise GmError(f"compileC: unbound variable {e.name!r}")
        return _push_ref(env[e.name])
    if isinstance(e, EChr):
        # A `Char` is its code point; nothing at run time distinguishes it
        # from an `Int`, which is what lets the integer primitives serve
        # `Eq Char` and `Ord Char`.
        return [PushInt(e.n)]
    if isinstance(e, ENum):
        return [PushInt(e.n)]
    if isinstance(e, ECon):
        out = []
        for i, a in enumerate(e.args):
            out += compile_c(a, _apply_n_bump_env(i, env))
        out.append(Pack(e.tag, len(e.args)))
        return out
    if isinstance(e, ETuple):
        out = []
        for i, a in enumerate(e.args):
            out += compile_c(a, _apply_n_bump_env(i, env))
        out.append(PackTuple(len(e.args)))
        return out
    if isinstance(e, EAp) and isinstance(e.fn, EProj):
        # `EAp (EProj i) tup`: force the tuple and select field `i`.
        # This case MUST precede the generic `EAp` rule so projection
        # is not wrapped into an `NAp` node.
        out = compile_c(e.arg, env)
        out.append(Eval())
        out.append(Proj(e.fn.i))
        return out
    if isinstance(e, EAp):
        return (compile_c(e.arg, env)
                + compile_c(e.fn, _bump_env(env))
                + [Mkap()])
    if isinstance(e, ELet):
        if e.is_rec:
            return compile_letrec(e.defs, e.body, env)
        return compile_let(e.defs, e.body, env)
    if isinstance(e, ECase):
        return compile_case(e, env)
    if isinstance(e, ELambda):
        raise GmError("ELambda reached the G-machine compiler; "
                      "lambda lifting did not run")
    if isinstance(e, EHole):
        # A hole type-checks and has no value — but that is a fact about
        # *running* it, and this used to be a fact about compiling anything
        # near it.  One unfinished definition therefore took the whole
        # program down: `substrate = _` in a file that also plays a score
        # stopped the score being read, so the synth came up silent and the
        # message named a line in a prelude nobody had written.
        #
        # Compiled to an instruction that aborts when the code around it
        # actually runs, the way `MatchFail` does.  A program with a hole
        # in a definition nothing reaches now runs — which is the state
        # every editor session passes through, and the state `--fits` and
        # `Tab` exist to help you out of.
        if e.span is None:
            return [Hole()]
        return [Hole(e.span.start.line, e.span.start.col)]
    if isinstance(e, EAnnot):
        return compile_c(e.expr, env)
    # -- FRP nodes (increment 9c) --

    if isinstance(e, ESigCons):
        return (compile_c(e.value, env) + [Eval()]
                + compile_c(e.tail, _bump_env(env)) + [Eval()]
                + [SigCons()])

    if isinstance(e, ESigHead):
        return compile_c(e.sig, env) + [Eval(), SigHead()]

    if isinstance(e, EDelay):
        return compile_c(e.body, env) + [Pack(TAG_DELAY, 1)]

    if isinstance(e, EAppFa):
        # s ⊛ t : ⃝∀B.  Both sides are ⃝∀, so no clock is consulted and
        # the application can be built now: `delay f ⊛ delay x` becomes
        # `delay (f x)`.  Both operands must be forced to reach the
        # ``tagDelay`` node ``MkDelayAp`` unwraps.
        return (compile_c(e.fn, env) + [Eval()]
                + compile_c(e.arg, _bump_env(env)) + [Eval()]
                + [MkDelayAp()])

    if isinstance(e, EAppEx):
        # s 5 t : ⃝∃B.  The result inherits t's clock, so the application
        # cannot happen until t fires — it is stored unevaluated and the
        # reactive driver's ``advance`` performs it.
        return (compile_c(e.fn, env) + [Eval()]
                + compile_c(e.arg, _bump_env(env)) + [Eval()]
                + [Pack(TAG_EXISTS5, 2)])

    if isinstance(e, EWait):
        return compile_c(e.chan, env) + [Eval(), Pack(TAG_WAIT, 1)]

    if isinstance(e, EWatch):
        return compile_c(e.sig, env) + [Eval(), Pack(TAG_WATCH, 1)]

    if isinstance(e, ESync):
        return (compile_c(e.left, env) + [Eval()]
                + compile_c(e.right, _bump_env(env)) + [Eval()]
                + [Pack(TAG_SYNC, 2)])

    if isinstance(e, ENever):
        return [Pack(TAG_NEVER, 0)]

    if isinstance(e, ETail):
        return compile_c(e.sig, env) + [Eval(), Pack(TAG_TAIL, 1)]

    if isinstance(e, EChan):
        return [NewChan(_type_name(e.elem_type))]

    if isinstance(e, EGFix):
        # `gfix x. t ⟶ t[delay (gfix x. t) / x]`, i.e. the letrec
        #
        #     letrec x = delay v ; v = t in v
        #
        # `x` must be bound to `delay v` — a ⃝∀ wrapper around the *value*
        # of the whole fixed point — not to a self-referential delay node,
        # or advancing `x` would yield another delay instead of unrolling
        # the recursion.  `v`'s letrec cell is still a hole when `delay v`
        # captures it and `Update` fills that same node in place, so the
        # two share; `x` is defined first so that `t` never forces a hole.
        v = "_gfix"
        return compile_letrec([(e.var, EDelay(EVar(v))), (v, e.body)],
                              EVar(v), env)

    # -- Datafun stubs (increment 10a, codegen in 10c) --

    if isinstance(e, (EFix, EFor, EBox, EUnbox, ESet)):
        raise GmError(
            f"Datafun primitive {type(e).__name__} not yet implemented "
            f"(increment 10c)"
        )

    if isinstance(e, EProj):
        # A bare `EProj i` not wrapped by `EAp (EProj i) tup` -- it
        # is not a first-class value, mirroring `Pack`.
        raise GmError("EProj must be applied to a tuple; "
                      "bare EProj is not a first-class value")
    raise GmError(f"compileC: unknown expr {e!r}")


def _local_env(def_names, env):
    """Binders visible from the body once all `n` defs sit on the stack.

    The last-pushed def is topmost (``Local 0``); the first-pushed (the
    0th source pair) is deepest (``Local n-1``).  Therefore
    ``def_names[i] -> Local (n-1-i)``.  The outer env's references are
    all bumped by ``n`` (the n cells pushed on top of them).
    """
    n = len(def_names)
    out = _apply_n_bump_env(n, env)
    for i, nm in enumerate(def_names):
        out[nm] = Local(n - 1 - i)
    return out


def compile_let(defs, body, env):
    n = len(defs)
    out = []
    for i, (nm, d) in enumerate(defs):
        # While compiling def i the cells of defs 0..i-1 are already on
        # the stack, so a later binding may read an earlier one — the
        # sequential scope `ELet`'s contract states, which the desugarer
        # now threads.  `_local_env` over the first `i` names is exactly
        # that stack: def j's cell at depth i-1-j, the outer references
        # bumped by the i cells pushed over them.
        out += compile_c(d, _local_env([nm2 for nm2, _ in defs[:i]], env))
    out += compile_c(body, _local_env([nm for (nm, _) in defs], env))
    out.append(Slide(n))
    return out


def compile_letrec(defs, body, env):
    n = len(defs)
    env_local = _local_env([nm for (nm, _) in defs], env)
    out = [Alloc(n)]
    for i, (nm, d) in enumerate(defs):
        out += compile_c(d, env_local)
        out.append(Update(n - 1 - i))
    out += compile_c(body, env_local)
    out.append(Slide(n))
    return out


def compile_case(e, env):
    out = compile_c(e.scrut, env)
    table = []
    for alt in e.alts:
        a = len(alt.names)
        env_local = _local_env(list(alt.names), env)
        body_code = compile_c(alt.body, env_local) + [Slide(a)]
        table.append((alt.tag, tuple(body_code)))
    out.append(Eval())
    out.append(CaseJump(tuple(table)))
    return out


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

def step(s: GmState):
    """Execute a single instruction (or dump-restore) on ``s``.

    When the code runs out with a non-empty dump, an `Eval`-driven
    `Unwind` has just reached WHNF: the result sits on top of the
    current (mini) stack, and the saved frame holds the caller's stack
    sans that expr.  Restore by prepending the result to the saved
    stack -- mirroring `Unwind`-on-WHNF in the spec.
    """
    if s._pc >= len(s._code):
        if not s.dump:
            return
        c, pc, st = s.dump.pop()
        s._code, s._pc = c, pc
        s.stack = ([s.stack[0]] + st) if s.stack else st
        return
    instr = s._code[s._pc]
    s._pc += 1
    _DISPATCH[type(instr)](instr, s)


#: `Unwind` carries no operand, so every `[Unwind()]` in here is the same
#: program.  Sharing one is safe because a code list is only ever rebound,
#: never mutated in place — `step` walks it with an index.
_UNWIND: list = [Unwind()]


#: The node kinds that are already in weak head normal form.  A set keyed
#: by exact type: every node class is a leaf, so `type(x) is C` decides it,
#: and that is a pointer comparison where `isinstance` against a five-tuple
#: is a loop.  `_unwind` runs on a third of all instructions.
_WHNF = frozenset((NNum, NCon, NSig, NChan))


#: An exhausted code sequence.  Shared, like `_UNWIND`, and for the same
#: reason: code lists are rebound, never mutated.
_EMPTY: list = []


def _unwind(_: Unwind, s: GmState):
    """Unwind the spine — all of it, in one instruction.

    The rule is stated one link at a time: push the function, set the code
    to `[Unwind]`, and go round again.  Following it literally re-entered
    the dispatch loop for every link, and *a third of all instructions the
    machine executed were this* — 507,000 of `fib 19`'s 1,461,000.  Every
    one of them did the same two things.

    The loop below is the same rule applied until it stops applying, which
    leaves the machine in the state the one-at-a-time version would have
    reached.  `walked` is why: on reaching weak head normal form the code
    the original had left behind is the `[Unwind]` it just consumed, so an
    unwind that moved has to end with the code exhausted.
    """
    stack = s.stack
    node = stack[0]
    walked = False
    while True:
        t = type(node)
        if t is NAp:
            stack.insert(0, node.fn)
            node = node.fn
        elif t is NInd:
            if node.target is None:
                raise GmError("Unwind on null indirection")
            node = node.target
            stack[0] = node
        else:
            break
        walked = True

    if t in _WHNF:
        if walked:
            s.code = _EMPTY
        return
    if t is NGlobal:
        if len(stack) < node.arity + 1:
            raise GmError("Unwinding global with too few args")
        # No copy: a code list is only ever rebound, never mutated.
        s.code = node.code
        return
    raise GmError(f"unwind: bad node {node!r}")


def _pushglobal(i: PushGlobal, s: GmState):
    g = s.globals.get(i.name)
    if g is None:
        raise GmError(f"unknown global {i.name!r}")
    s.stack.insert(0, g)


def _pushint(i: PushInt, s: GmState):
    s.stack.insert(0, NNum(i.n))


def _push(i: Push, s: GmState):
    s.stack.insert(0, s.stack[i.n])


def _pusharg(i: PushArg, s: GmState):
    ap = s.stack[i.n + 1]
    if not isinstance(ap, NAp):
        raise GmError("PushArg: stack slot is not an NAp")
    s.stack.insert(0, ap.arg)


def _mkap(_: Mkap, s: GmState):
    fn = s.stack[0]
    arg = s.stack[1]
    s.stack[:2] = [NAp(fn, arg)]


def _update(i: Update, s: GmState):
    result = s.stack[0]
    rest = s.stack[1:]
    _overwrite(rest[i.n], result)
    s.stack = rest


def _pop(i: Pop, s: GmState):
    s.stack = s.stack[i.n:]


def _slide(i: Slide, s: GmState):
    top = s.stack[0]
    s.stack = [top] + s.stack[1 + i.n:]


def _alloc(i: Alloc, s: GmState):
    for _ in range(i.n):
        s.stack.insert(0, NInd(None))


def _eval(_: Eval, s: GmState):
    a = s.stack[0]
    s.dump.append((s._code, s._pc, s.stack[1:]))
    s.code = _UNWIND
    s.stack = [a]


def _pack(i: Pack, s: GmState):
    args = s.stack[:i.arity]
    rest = s.stack[i.arity:]
    # args[0] (topmost) is the LAST source arg; store args in source
    # order: args[0] of the NCon corresponds to the FIRST source arg.
    s.stack = [NCon(i.tag, tuple(reversed(args)))] + rest


def _packtuple(i: PackTuple, s: GmState):
    args = s.stack[:i.arity]
    rest = s.stack[i.arity:]
    # Same convention as `_pack`: topmost cell is the LAST source
    # field; reverse so the resulting tuple's args[0] is the FIRST
    # source field, matching `Proj i` (0-based source-order indexing).
    s.stack = [NCon(tuple_tag(i.arity), tuple(reversed(args)))] + rest


def _proj(i: Proj, s: GmState):
    node = s.stack[0]
    if not isinstance(node, NCon):
        raise GmError("Proj on a value that is not a constructor")
    if not 0 <= i.i < len(node.args):
        raise GmError(f"Proj: index {i.i} out of range "
                      f"(arity {len(node.args)})")
    s.stack = [node.args[i.i]] + s.stack[1:]


def _casejump(i: CaseJump, s: GmState):
    node = s.stack[0]
    if not isinstance(node, NCon):
        raise GmError("CaseJump on non-constructor")
    for (t, body_code) in i.table:
        if t == node.tag:
            s.stack = list(reversed(node.args)) + s.stack[1:]
            # Splice the alternative in front of whatever is left, which
            # the counter — not a slice of `s.code` — says where to find.
            # `body_code` comes from the compiler and may be a tuple.
            rest = s._code[s._pc:]
            s.code = list(body_code) + list(rest) if rest else list(body_code)
            return
    raise GmError(f"CaseJump: no alt for tag {node.tag}")


# ---------------------------------------------------------------------------
# FRP instruction semantics (increment 9c)
# ---------------------------------------------------------------------------

def _sigcons(_: SigCons, s: GmState):
    """Pop tail and value from stack, allocate NSig, push addr, register."""
    tail = s.stack[0]
    value = s.stack[1]
    sig = NSig(value, tail, False)
    s.stack[:2] = [sig]
    s.now.append(sig)


def _sighead(_: SigHead, s: GmState):
    """Project the value field from an NSig on top of stack.

    `head` is defined only on the *now* heap (Rizzo §4.1): reading a
    signal the current sweep has not reached yet is a stuck state, and
    Theorem 4.1 rules it out for well-typed programs.  Because signals
    are updated in place there is no second heap to make the read fail
    on its own, so the ✓ mark is checked here — otherwise a
    scheduler-ordering bug quietly returns last step's value.
    """
    node = _deref(s.stack[0])
    if not isinstance(node, NSig):
        raise GmError("SigHead on non-NSig")
    if not node.current:
        raise GmError(
            "head of a signal on the earlier heap: it has not been updated "
            "yet this step.  A signal may only read signals allocated "
            "before it (Rizzo §4.1, the now ✓ earlier frontier)"
        )
    s.stack[0] = node.value


def _newchan(i: NewChan, s: GmState):
    """Allocate a fresh NChan, push its address, extend the channel context.

    `⟨chan_A; σ/Δ⟩ ⇓ ⟨κ; σ/Δ, κ:Chan A⟩` — allocation grows Δ, and it can
    happen at any time, including inside a sub-evaluation the reactive
    driver runs (the paper's GUI example mints one channel per widget).
    """
    cid = s.chanCounter
    s.chanCounter = cid + 1
    s.chans[cid] = i.elem_type
    s.stack.insert(0, NChan(cid))


def _mkdelayap(_: MkDelayAp, s: GmState):
    """Combine two NCon tagDelay nodes into NAp(f, x) wrapped in tagDelay NCon."""
    # ``Eval`` leaves WHNF but a ``gfix`` binder reaches here as an
    # indirection into the letrec cell it shares, so chase those first.
    b = _deref(s.stack[0])
    a = _deref(s.stack[1])
    if not isinstance(a, NCon) or a.tag != TAG_DELAY or len(a.args) != 1:
        raise GmError("MkDelayAp: left operand must be NCon tagDelay [f]")
    if not isinstance(b, NCon) or b.tag != TAG_DELAY or len(b.args) != 1:
        raise GmError("MkDelayAp: right operand must be NCon tagDelay [x]")
    f = a.args[0]
    x = b.args[0]
    ap = NAp(f, x)
    delay_ap = NCon(TAG_DELAY, (ap,))
    s.stack[:2] = [delay_ap]


def _type_name(t) -> Optional[str]:
    """Render a channel's element type for the runtime channel context.

    The heap is untyped, so this is a label the driver reports and checks
    input shape against — not a type the machine reasons with.
    """
    if t is None:
        return None
    from .show import show_type
    from .types import Type

    return show_type(t) if isinstance(t, Type) else str(t)


def _prim_operands(s: GmState, name: str) -> tuple[NNum, NNum]:
    """The two evaluated operands a strict primitive left on the stack.

    ``_prim_binop_code`` arranges for the first argument to be on top and
    the second below it; both are already in WHNF.
    """
    if len(s.stack) < 2:
        raise GmError(f"{name}: missing operands")
    a, b = _deref(s.stack[0]), _deref(s.stack[1])
    if not isinstance(a, NNum) or not isinstance(b, NNum):
        raise GmError(f"{name}: operands must be integers, got "
                      f"{type(a).__name__} and {type(b).__name__}")
    return a, b


def _prim_result(s: GmState, node: Node) -> None:
    """Replace the two consumed operands with the primitive's result."""
    s.stack[:2] = [node]


def _prim_operand(s: GmState, name: str) -> NNum:
    """The single evaluated operand a strict unary primitive left on top."""
    if not s.stack:
        raise GmError(f"{name}: missing operand")
    a = _deref(s.stack[0])
    if not isinstance(a, NNum):
        raise GmError(f"{name}: operand must be a number, got "
                      f"{type(a).__name__}")
    return a


def _prim_result1(s: GmState, node: Node) -> None:
    """Replace the one consumed operand with the primitive's result."""
    s.stack[:1] = [node]


def _deref(node: Node) -> Node:
    while isinstance(node, NInd):
        if node.target is None:
            raise GmError("dereferenced a null indirection")
        node = node.target
    return node


def _matchfail(_: MatchFail, s: GmState):
    raise GmError("pattern match failure: no alternative matched")


def _hole(i: Hole, s: GmState):
    """Said by name, because the author knows exactly what is missing."""
    where = f" (at {i.line}:{i.col})" if (i.line or i.col) else ""
    raise GmError(f"a hole (`_`){where} has no value: it is a question "
                  f"the type checker answers and the evaluator cannot")


def _eqint(i: EqInt, s: GmState):
    a, b = _prim_operands(s, "EqInt")
    _prim_result(s, NCon(i.tag_true if a.n == b.n else i.tag_false, ()))


def _ltint(i: LtInt, s: GmState):
    a, b = _prim_operands(s, "LtInt")
    _prim_result(s, NCon(i.tag_true if a.n < b.n else i.tag_false, ()))


def _divint(_: DivInt, s: GmState):
    a, b = _prim_operands(s, "DivInt")
    if b.n == 0:
        raise GmError("DivInt: division by zero")
    _prim_result(s, NNum(a.n // b.n))


def _modint(_: ModInt, s: GmState):
    a, b = _prim_operands(s, "ModInt")
    if b.n == 0:
        raise GmError("ModInt: division by zero")
    _prim_result(s, NNum(a.n % b.n))


def _divfloat(_: DivFloat, s: GmState):
    a, b = _prim_operands(s, "DivFloat")
    if b.n == 0:
        raise GmError("DivFloat: division by zero")
    _prim_result(s, NNum(a.n / b.n))


def _modfloat(_: ModFloat, s: GmState):
    a, b = _prim_operands(s, "ModFloat")
    if b.n == 0:
        raise GmError("ModFloat: division by zero")
    _prim_result(s, NNum(a.n % b.n))


def _tofloat(_: ToFloat, s: GmState):
    a = _prim_operand(s, "ToFloat")
    _prim_result1(s, NNum(float(a.n)))


def _floorfloat(_: FloorFloat, s: GmState):
    import math
    a = _prim_operand(s, "FloorFloat")
    _prim_result1(s, NNum(math.floor(a.n)))


def _mathfloat(op: MathFloat, s: GmState):
    import math
    a = _prim_operand(s, "MathFloat")
    try:
        # `float(...)` because `sqrt 4` at an `Int`-typed literal would give
        # `2.0` from `math` anyway, but `exp 0` gives `1.0` and `log` of an
        # int likewise — the result type is `Float` in every case, and the
        # generated code returns a double unconditionally.
        _prim_result1(s, NNum(float(getattr(math, op.fn)(a.n))))
    except ValueError as exc:
        # `log` of a negative, `sqrt` of a negative.  Python raises where C
        # returns NaN, so the two would diverge here rather than agree on a
        # value; saying so is better than either.
        raise GmError(f"{op.fn} is undefined at {a.n!r}: {exc}") from None
    except OverflowError:
        raise GmError(
            f"{op.fn} overflowed at {a.n!r}: the result is larger than a "
            f"double can hold") from None


def _addint(_: AddInt, s: GmState):
    a, b = _prim_operands(s, "AddInt")
    _prim_result(s, NNum(a.n + b.n))


def _subint(_: SubInt, s: GmState):
    a, b = _prim_operands(s, "SubInt")
    _prim_result(s, NNum(a.n - b.n))


def _mulint(_: MulInt, s: GmState):
    a, b = _prim_operands(s, "MulInt")
    _prim_result(s, NNum(a.n * b.n))


_DISPATCH = {
    Unwind:     _unwind,
    PushGlobal: _pushglobal,
    PushInt:    _pushint,
    Push:       _push,
    PushArg:    _pusharg,
    Mkap:       _mkap,
    Update:     _update,
    Pop:        _pop,
    Alloc:      _alloc,
    Slide:      _slide,
    Eval:       _eval,
    Pack:       _pack,
    PackTuple:  _packtuple,
    Proj:       _proj,
    CaseJump:   _casejump,
    SigCons:    _sigcons,
    SigHead:    _sighead,
    NewChan:    _newchan,
    MkDelayAp:  _mkdelayap,
    EqInt:      _eqint,
    MatchFail:  _matchfail,
    Hole:       _hole,
    DivInt:     _divint,
    LtInt:      _ltint,
    ModInt:     _modint,
    DivFloat:   _divfloat,
    ModFloat:   _modfloat,
    ToFloat:    _tofloat,
    FloorFloat: _floorfloat,
    MathFloat:  _mathfloat,
    AddInt:     _addint,
    SubInt:     _subint,
    MulInt:     _mulint,
}


def run(s: GmState, max_steps=10_000_000) -> GmState:
    """Drive ``s`` to a final state (or raise after ``max_steps``).

    `step`'s body is written out here rather than called.  The two were a
    third of the machine's time between them and neither was doing any
    work: a Python call per instruction, and `isFinal` — a *property* —
    evaluated once per instruction to ask a question the loop already has
    the answer to.  `step` remains, unchanged, for single-stepping in
    tests and in the reactive driver.
    """
    dispatch = _DISPATCH
    n = 0
    while True:
        code = s._code
        pc = s._pc
        if pc >= len(code):
            if not s.dump:
                return s
            # An `Eval`-driven `Unwind` has reached WHNF: the result is on
            # top of the current (mini) stack and the saved frame holds the
            # caller's stack without it.
            c, p, st = s.dump.pop()
            s._code, s._pc = c, p
            s.stack = ([s.stack[0]] + st) if s.stack else st
        else:
            instr = code[pc]
            s._pc = pc + 1
            dispatch[type(instr)](instr, s)
        n += 1
        if n > max_steps:
            raise StepLimit("run: step limit exceeded (possible infinite loop)")


# ---------------------------------------------------------------------------
# Result helpers
# ---------------------------------------------------------------------------

def show_result(s: GmState) -> str:
    """Render the WHNF on top of the stack as a flat Core-like string."""
    if not s.stack:
        return "<empty stack>"
    if _is_string_type(s.result_type):
        text = _decode_string(s.stack[0], s)
        if text is not None:
            return text
    return _show_node(s.stack[0], 0)


def _is_string_type(t) -> bool:
    """Is ``t`` the expanded form of `String`, i.e. `List Char`?"""
    from .types import TApp, TCon

    return (isinstance(t, TApp) and isinstance(t.fn, TCon)
            and t.fn.name == "List" and isinstance(t.arg, TCon)
            and t.arg.name == "Char")


def _force(node: Node, s: GmState) -> Node:
    """Reduce ``node`` to WHNF on a scratch machine sharing ``s``'s heap.

    ``run`` stops at the result's own WHNF, so a computed list is a cons
    cell whose tail is still a thunk.  Rendering the spine means forcing
    it cell by cell — on a scratch state rather than by splicing frames
    into the finished one, the same way the reactive driver re-enters the
    evaluator (`fixme.md` F20).
    """
    scratch = GmState([Eval()], [node], s.globals, [])
    run(scratch, max_steps=1_000_000)
    return scratch.stack[0] if scratch.stack else node


def _decode_string(node: Node, s: GmState, limit: int = 100_000) -> str | None:
    """Read a `List Char` off the heap, or ``None`` if it is not one."""
    out: list[str] = []
    for _ in range(limit):
        node = _force(node, s)
        while isinstance(node, NInd):
            if node.target is None:
                return None
            node = node.target
        if not isinstance(node, NCon):
            return None
        if not node.args:
            return "".join(out)
        if len(node.args) != 2:
            return None
        ch = _force(node.args[0], s)
        while isinstance(ch, NInd) and ch.target is not None:
            ch = ch.target
        if not isinstance(ch, NNum):
            return None
        out.append(chr(ch.n))
        node = node.args[1]
    return None


#: Depth at which structural rendering gives up.  It is a guard against a
#: cyclic graph — a signal refers to itself — not a display preference, so
#: it has to be well clear of the sizes real results reach: a set is a cons
#: list, and every element costs one level of depth.
_SHOW_DEPTH_CAP = 400


def _show_node(node: Node, depth: int) -> str:
    if depth > _SHOW_DEPTH_CAP:
        return "..."
    if isinstance(node, NNum):
        return str(node.n)
    if isinstance(node, NCon):
        if is_tuple_tag(node.tag):
            inner = ", ".join(_show_node(a, depth + 1) for a in node.args)
            return f"({inner})"
        if not node.args:
            return f"Pack{{{node.tag},0}}"
        inner = " ".join(_show_node(a, depth + 1) for a in node.args)
        return f"Pack{{{node.tag},{len(node.args)}}} {inner}"
    if isinstance(node, NInd):
        if node.target is None:
            return "<null>"
        return _show_node(node.target, depth + 1)
    if isinstance(node, NAp):
        return f"({_show_node(node.fn, depth+1)} {_show_node(node.arg, depth+1)})"
    if isinstance(node, NGlobal):
        return f"<global arity={node.arity}>"
    if isinstance(node, NSig):
        v = _show_node(node.value, depth + 1)
        t = _show_node(node.tail, depth + 1)
        tk = "✓" if node.ticked else "✗"
        return f"NSig({v}, {t}, {tk})"
    if isinstance(node, NChan):
        return f"NChan({node.chan_id})"
    return f"<?{node!r}>"