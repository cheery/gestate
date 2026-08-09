"""End-to-end pipeline: source → G-machine result."""

from __future__ import annotations

import threading as _threading
from collections import OrderedDict

from dataclasses import dataclass

from .syntax import parse
from .syntax.ast import VModule
from .prelude import merge as prelude_merge
from .declarations import classify
from .desugar import (
    desugar_program, lower_fields, strip_annotations, DesugarError,
)
from .lift import lift
from .gmachine import (GmState, compile_program, run, show_result,
                       add_primitives, MATH_FLOAT)
from .infer import infer_program, InferError
from .constraint import solve_constraints, ConstraintError
from .elaborate import (
    check_main_has_no_context, elaborate, resolve_static_methods,
)
from .specialise import specialise
from .envexpand import expand as expand_envelopes
from .kindcheck import build_kind_env, check_kind, KindError
from .helpers import generate_all_helpers, _type_suffix
from .seminaive import transform as seminaive_transform, make_semifix_helpers
from .bottoms import propagate_scs as propagate_bottoms
from .types import TApp, TCon, TFun, Type, TVar, free_vars, tuple_con
from .expr import EAnnot, EGlobal, ELambda, Expr, subexprs
from .exhaust import check_program, ExhaustError
from .monotone import check_scs as check_monotone
from .subgrammar import check_scs as check_subgrammars


class PipelineError(Exception):
    pass


class MonotoneError(Exception):
    """A box closed over a monotone variable (see `monotone.py`)."""


class SubgrammarError(Exception):
    """A type escaped its subgrammar (see `subgrammar.py`)."""


def _is_given(pred, givens) -> bool:
    """Is ``pred`` already granted by the enclosing SC's context?"""
    return any(g.class_name == pred.class_name and g.type_ == pred.type_
               for g in givens)


def _build_builtins() -> dict:
    return {
        "prim_eq_int": TFun(TCon("Int"), TFun(TCon("Int"), TCon("Bool"))),
        "prim_lt_int": TFun(TCon("Int"), TFun(TCon("Int"), TCon("Bool"))),
        "prim_mod_int": TFun(TCon("Int"), TFun(TCon("Int"), TCon("Int"))),
        "prim_add_int": TFun(TCon("Int"), TFun(TCon("Int"), TCon("Int"))),
        "prim_sub_int": TFun(TCon("Int"), TFun(TCon("Int"), TCon("Int"))),
        "prim_mul_int": TFun(TCon("Int"), TFun(TCon("Int"), TCon("Int"))),
        "prim_div_int": TFun(TCon("Int"), TFun(TCon("Int"), TCon("Int"))),
        "prim_eq_float": TFun(TCon("Float"), TFun(TCon("Float"), TCon("Bool"))),
        "prim_lt_float": TFun(TCon("Float"), TFun(TCon("Float"), TCon("Bool"))),
        "prim_add_float": TFun(TCon("Float"), TFun(TCon("Float"), TCon("Float"))),
        "prim_sub_float": TFun(TCon("Float"), TFun(TCon("Float"), TCon("Float"))),
        "prim_mul_float": TFun(TCon("Float"), TFun(TCon("Float"), TCon("Float"))),
        "prim_div_float": TFun(TCon("Float"), TFun(TCon("Float"), TCon("Float"))),
        "prim_mod_float": TFun(TCon("Float"), TFun(TCon("Float"), TCon("Float"))),
        "prim_to_float": TFun(TCon("Int"), TCon("Float")),
        "prim_floor_float": TFun(TCon("Float"), TCon("Int")),
        # The transcendentals, all `Float -> Float`.  `sqrt` is IEEE-exact
        # everywhere; the other four are libm's, and `spec/liveaudio.md`
        # open question 2 records what that costs and what checks it.
        **{f"prim_{fn}_float": TFun(TCon("Float"), TCon("Float"))
           for fn in MATH_FLOAT},
        # `Char` and `Int` share a representation but not a type; these
        # move a value between them, and are the identity at run time.
        "chr": TFun(TCon("Int"), TCon("Char")),
        "ord": TFun(TCon("Char"), TCon("Int")),
        # `empty? : □Prop → Bool`.  The plain arrow *is* `□A → B` — the
        # argument is discrete — which is exactly the restriction Datafun
        # puts on `empty?`, so it needs no `Box` in the signature to be
        # non-monotone.
        "empty?": TFun(TApp(TCon("Set"), tuple_con(0)), TCon("Bool")),
    }


def _kind_check_program(program, sigs, assume: dict | None = None):
    kind_env = build_kind_env(program.cons, program.kind_decls)
    if assume:
        for name, kind in assume.items():
            kind_env.setdefault(name, kind)
    for ci in program.cons.values():
        check_kind(ci.type_, kind_env)
    for _name, _arity, _lam, sig in sigs:
        if sig is not None and isinstance(sig, Type):
            check_kind(sig, kind_env)
    for _name, _arity, lam, _sig in sigs:
        _check_annotations(lam.body, kind_env)


def _check_annotations(expr: Expr, kind_env: dict) -> None:
    if isinstance(expr, EAnnot):
        ann_t = expr.type_
        if isinstance(ann_t, Type):
            check_kind(ann_t, kind_env)
        _check_annotations(expr.expr, kind_env)
        return
    from .expr import (EAp, EAppEx, EAppFa, EBox, ECase, EChan, EChr, ECon, EDelay,
                       EFix, EFor, EGFix, EGlobal, ELet, ENever, ENum, ESet,
                       ESigCons, ESigHead, ESync, ETail, ETuple, EUnbox, EVar,
                       EWait, EWatch)
    if isinstance(expr, (EVar, EGlobal, ENum, EChr, ENever, EChan)):
        return
    if isinstance(expr, EAp):
        _check_annotations(expr.fn, kind_env)
        _check_annotations(expr.arg, kind_env)
    elif isinstance(expr, ELambda):
        _check_annotations(expr.body, kind_env)
    elif isinstance(expr, ELet):
        for _n, d in expr.defs:
            _check_annotations(d, kind_env)
        _check_annotations(expr.body, kind_env)
    elif isinstance(expr, ECase):
        _check_annotations(expr.scrut, kind_env)
        for alt in expr.alts:
            _check_annotations(alt.body, kind_env)
    elif isinstance(expr, ECon):
        for a in expr.args:
            _check_annotations(a, kind_env)
    elif isinstance(expr, ETuple):
        for a in expr.args:
            _check_annotations(a, kind_env)
    elif isinstance(expr, ESigCons):
        _check_annotations(expr.value, kind_env)
        _check_annotations(expr.tail, kind_env)
    elif isinstance(expr, ESigHead):
        _check_annotations(expr.sig, kind_env)
    elif isinstance(expr, EDelay):
        _check_annotations(expr.body, kind_env)
    elif isinstance(expr, (EAppFa, EAppEx)):
        _check_annotations(expr.fn, kind_env)
        _check_annotations(expr.arg, kind_env)
    elif isinstance(expr, EWait):
        _check_annotations(expr.chan, kind_env)
    elif isinstance(expr, EWatch):
        _check_annotations(expr.sig, kind_env)
    elif isinstance(expr, ETail):
        _check_annotations(expr.sig, kind_env)
    elif isinstance(expr, ESync):
        _check_annotations(expr.left, kind_env)
        _check_annotations(expr.right, kind_env)
    elif isinstance(expr, EGFix):
        _check_annotations(expr.body, kind_env)
    elif isinstance(expr, EFix):
        _check_annotations(expr.body, kind_env)
    elif isinstance(expr, EFor):
        _check_annotations(expr.set_expr, kind_env)
        _check_annotations(expr.body, kind_env)
    elif isinstance(expr, EBox):
        _check_annotations(expr.body, kind_env)
    elif isinstance(expr, EUnbox):
        _check_annotations(expr.binding, kind_env)
        _check_annotations(expr.body, kind_env)
    elif isinstance(expr, ESet):
        for a in expr.items:
            _check_annotations(a, kind_env)


# ── Prelude ──────────────────────────────────────────────────────────────
#
# Loading, merging and shadowing live in `gestate/prelude.py`.

_merge_prelude = prelude_merge


# ---------------------------------------------------------------------------
# Stack depth  (`fixme.md` F66)
# ---------------------------------------------------------------------------
#
# Every stage that walks an expression is recursive — `infer`, `phi`/`delta`,
# `lift`, `compileC` — so the stack depth compilation needs is proportional to
# how deeply the *source* nests, measured at about six Python frames per
# level.  CPython's default limit of 1000 therefore stops at roughly 165
# nested applications.
#
# That was recorded as a wrong failure mode with "no evidence a real program
# reaches it".  There is now: a melody is one `++` chain, so a piece hits the
# ceiling at about 170 notes — well inside anything worth listening to, and
# the whole music half of the language was capped by it.
#
# Rewriting six walkers iteratively would be a large change to the stages
# most likely to be wrong.  Compilation instead runs on a thread with a stack
# big enough for the depth real programs need.  The limit stays *finite* so
# that genuine runaway recursion is still reported rather than segfaulting —
# it buys a bigger program, not an unbounded one.

#: ~50k frames at the ~1 KB per frame these walkers use, with room over.
_COMPILE_STACK_BYTES = 256 * 1024 * 1024
#: ~8,000 levels of source nesting, at six frames each.
_COMPILE_RECURSION_LIMIT = 50_000


#: **One front end at a time, whatever asks for it.**
#:
#: Inference is destructive by design — `types.unifying` swaps in a
#: `Unifier` for the duration — and it does so through a *module global*,
#: because metavariable ids restart with each `Fresh()` and two entry
#: points must not confuse their variables.  That is sound in one thread
#: and unsound in two, and it stopped being hypothetical when the editor
#: grew a rebuild worker and a sidebar that reads types while you type:
#: two analyses at once, one store, and an answer that came back `?`.
#:
#: Serialising here rather than at each caller, because the constraint
#: belongs to inference rather than to whoever happens to want it, and
#: because this is already the one door every front end goes through.
#: `sys.setrecursionlimit` and `threading.stack_size` below are
#: process-global for the same reason and were already relying on it.
_FRONT_END = _threading.Lock()


def _deep_stack(thunk):
    """Run ``thunk`` where deep recursion is survivable, and re-raise as-is.

    Held under `_FRONT_END`, so two threads never infer at once.
    """
    with _FRONT_END:
        return _deep_stack_alone(thunk)


def _deep_stack_alone(thunk):
    import sys
    import threading

    box: dict[str, object] = {}

    def worker():
        try:
            box["value"] = thunk()
        except BaseException as exc:      # re-raised on the calling thread
            box["error"] = exc

    old_limit = sys.getrecursionlimit()
    try:
        old_size = threading.stack_size(_COMPILE_STACK_BYTES)
    except (ValueError, RuntimeError):
        # The platform refused the size; the default stack is all there is,
        # so run inline rather than pretending otherwise.
        return thunk()
    try:
        sys.setrecursionlimit(_COMPILE_RECURSION_LIMIT)
        t = threading.Thread(target=worker)
        t.start()
        t.join()
    finally:
        sys.setrecursionlimit(old_limit)
        threading.stack_size(old_size)

    if "error" in box:
        err = box["error"]
        if isinstance(err, RecursionError):
            raise PipelineError(
                "the program nests too deeply to compile (over "
                f"{_COMPILE_RECURSION_LIMIT // 6:,} levels).  This is a limit "
                "of the compiler, not of the language: every stage walks an "
                "expression recursively.  Break the expression up — a long "
                "chain of one operator can be split across definitions"
            ) from err
        raise err
    return box["value"]


def compile(source: str, *, typecheck: bool = True,
            prelude: bool = True) -> GmState:
    """Compile ``source``, on a stack deep enough for real programs."""
    return _deep_stack(
        lambda: _compile(source, typecheck=typecheck, prelude=prelude))


@dataclass
class Analysis:
    """The program as the front half leaves it: typed, elaborated, unlifted.

    This is the one point where a *whole program* is visible with its types
    still attached, its class methods already resolved to direct calls, and
    its definitions still under the names the author wrote — so it is where
    a check about the shape of user code belongs.  `gestate/audiograph.py`
    is the caller that made it worth naming (`spec/liveaudio.md` stage 1);
    `compile` uses it for everything downstream.

    Before elaboration would be too early — a class method is still a
    projection out of a dictionary, so all arithmetic looks higher-order.
    After lifting would be too late — a local lambda has become a
    supercombinator with a generated integer name, and an error message
    cannot say which definition it came from.
    """
    #: `(name, arity, ELambda, sig)`, as every pass here takes them.
    scs: list
    #: The classified module: constructors, classes, instances, kinds.
    program: object
    #: Supercombinator name → inferred type.  Empty when `typecheck=False`.
    types: dict
    #: Instance methods now called by name, which the ϕ/δ gate must treat
    #: as ordinary supercombinators.
    method_scs: set
    main_type: object = None


#: How many recent analyses to keep, and why keeping any is right.
#:
#: **One text is analysed several times within a second**, by readers with
#: no way to know about each other.  Starting `examples/audio/quartet.ges`
#: ran four front ends over the same program — `audioperform.graph_of` for
#: the engine's graph, `audiospans.located` for where the knobs go,
#: `_load_from_midi` for the instances, `audioscore.perform_voices` for the
#: piece — and the editor's sidebar, `?` and `Tab` each add another while
#: you look at it.  That was twenty-eight seconds before its window opened,
#: nine and a half of them spent discovering that quartet has no knobs.
#:
#: An `Analysis` is a pure function of its source and stays usable: a later
#: front end does not disturb one, and `compile` reads rather than rewrites
#: it — the transforms downstream build new lists.  `test/test_pipeline.py`
#: holds both of those as tests, because the whole cache rests on them.
#:
#: Four, because an editor has three assemblies of one file live at once —
#: the sound's, the score's and the canvas's, which differ in their entry
#: points — and the fourth slot is what survives a keystroke.
_KEEP_ANALYSED = 4

_analysed: "OrderedDict[tuple, Analysis]" = OrderedDict()
_analysed_lock = _threading.Lock()


def analyse(source: str, *, typecheck: bool = True,
            prelude: bool = True) -> Analysis:
    """Run the front half only, on a stack deep enough for real programs.

    Answered from `_KEEP_ANALYSED` recent ones when the *exact* text has
    been analysed before.  The lookup happens **before** `_FRONT_END` is
    taken, so a question about a text already analysed — which is what the
    sidebar, `?` and `Tab` ask — does not queue behind a rebuild.
    """
    key = (source, typecheck, prelude)
    got = _recall(key)
    if got is not None:
        return got
    return _deep_stack(lambda: _analysed_or_new(key))


def _analysed_or_new(key: tuple) -> Analysis:
    """The cache, for a caller already on the deep stack.

    `_FRONT_END` is not reentrant, so `compile` cannot reach the analysis
    through `analyse` — it is *inside* the lock by then.  One function both
    can use, and the lock is taken by whoever is outside it.
    """
    got = _recall(key)
    if got is not None:
        return got
    source, typecheck, prelude = key
    found = _analyse(source, typecheck=typecheck, prelude=prelude)
    with _analysed_lock:
        _analysed[key] = found
        _analysed.move_to_end(key)
        while len(_analysed) > _KEEP_ANALYSED:
            _analysed.popitem(last=False)
    return found


def _recall(key: tuple):
    with _analysed_lock:
        got = _analysed.get(key)
        if got is not None:
            _analysed.move_to_end(key)
        return got


def forget_analyses() -> None:
    """Drop what has been kept.

    For a caller that means to *measure* a front end, and for a test that
    means to run one — there is nothing to invalidate otherwise, since the
    key is the whole text.  The in-memory stack fronts go with it; the
    disk store stays, because a measurement that must not see it says
    `GESTATE_STACK_CACHE=0` instead.
    """
    with _analysed_lock:
        _analysed.clear()
    _STACK_FRONTS.clear()


# ── The stack front: the libraries' analysis, remembered ────────────────────

#: Bump whenever the shape of what `StackFront` pickles changes — a store
#: with another schema in its name is simply not found, and rebuilt.
#: 2: constraint sites are stamps on the nodes rather than `id()`s.
#: 3: `Nil`/`Cons`/`False`/`True` are pinned tags, baked into cached SCs.
_STACK_SCHEMA = 3


@dataclass
class StackFront:
    """The library stack's front half, stopped just after inference.

    Everything after this point — constraint solving, elaboration,
    specialisation — runs *whole-program*, because a program's call sites
    reach into library bodies (a constant dictionary specialises a library
    function).  Everything before it is closed over the stack alone: the
    libraries never name a program definition, and a program-side instance
    cannot change how a library body elaborates, because a constrained
    library SC keeps its dictionary parameter until `specialise` anyway.

    The one thing a program *can* do to the stack is shadow a name, and
    then this whole object is wrong for it — `_analyse_staged` detects
    that and falls back to the whole-text path, which renames.  A program
    shadowing an *audio-library* name never reaches that fallback:
    `shadow_libraries` renames the library text before the seam is cut,
    so the head is simply a different text with its own entry here.
    """
    #: The stack's declarations, parsed and fixity-resolved — reused as
    #: the head of every program's module, never mutated by later passes.
    items: list
    #: Desugared, inferred, field-lowered SCs — annotated trees, shared.
    scs: list
    results: dict
    per_sc_constraints: list
    per_sc_givens: list
    #: name → `Scheme` — what program inference imports.
    imports: dict
    #: Where the stack's `Fresh` stopped, so a program starts above it.
    fresh_end: int
    #: Every value name the stack defines — the shadowing check.
    defined: frozenset


_STACK_FRONTS: OrderedDict = OrderedDict()
_KEEP_STACK_FRONTS = 4


def _stack_store():
    """The directory pickled stack fronts live in, or `None` when off.

    A *cache*, in the strict sense: nothing in it is authoritative, a
    missing or corrupt file costs one rebuild, and `GESTATE_STACK_CACHE=0`
    turns the disk half off entirely (the in-memory half has no reason to
    be optional)."""
    import os
    from pathlib import Path

    if os.environ.get("GESTATE_STACK_CACHE", "1") == "0":
        return None
    root = os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")
    return Path(root) / "gestate"


def _stack_front(head: str) -> StackFront:
    got = _STACK_FRONTS.get(head)
    if got is not None:
        _STACK_FRONTS.move_to_end(head)
        return got
    import hashlib
    import pickle

    store = _stack_store()
    path = None
    if store is not None:
        sha = hashlib.sha256(head.encode()).hexdigest()[:32]
        path = store / f"stack-{_STACK_SCHEMA}-{sha}.pickle"
    front = None
    if path is not None and path.exists():
        try:
            with open(path, "rb") as f:
                front = pickle.load(f)
        except Exception:                               # noqa: BLE001
            front = None
    if front is None:
        front = _build_stack_front(head)
        if path is not None:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp = path.with_name(path.name + ".tmp")
                with open(tmp, "wb") as f:
                    pickle.dump(front, f, protocol=pickle.HIGHEST_PROTOCOL)
                tmp.replace(path)   # atomic — a reader sees whole files
            except Exception:                           # noqa: BLE001
                pass                # a cache that cannot write is only slow
    _STACK_FRONTS[head] = front
    while len(_STACK_FRONTS) > _KEEP_STACK_FRONTS:
        _STACK_FRONTS.popitem(last=False)
    return front


def _build_stack_front(head: str) -> StackFront:
    """The front half, run over the stack text alone."""
    from .infer import Fresh

    module = _merge_prelude(head)
    program = classify(module)
    exhaust_errors = check_program(program)
    if exhaust_errors:
        raise ExhaustError('\n'.join(exhaust_errors))
    scs = desugar_program(program)
    from .kindcheck import KType

    # `Voice` is generated per program from its `voices` banks (a stub,
    # for a MIDI piece), so the stack that mentions it in `layVoices`'s
    # signature is checked assuming it is a type — the type-level mirror
    # of assuming `sampleRate` below.
    _kind_check_program(program, scs, assume={"Voice": KType()})
    sc_contexts = {sc.name: sc.sig_constraints for sc in program.scs
                   if sc.sig_constraints}
    fresh = Fresh()
    imports: dict = {}
    # The renderer-supplied names (`doc/ref/index.md` § "Names no page
    # lists").  They are *defined* in the tail, program-side, but the
    # libraries reference them — `seconds` reads `sampleRate`, `!x`
    # desugars to `constSig x` — so the stack alone assumes exactly the
    # types the tail always defines them at.
    from .infer import Scheme

    supplied = {"constSig": Scheme(frozenset({0}),
                                   TFun(TVar(0),
                                        TApp(TCon("Sig"), TVar(0))))}
    results, per_c, per_g = infer_program(
        scs, _build_builtins() | {"sampleRate": TCon("Float")},
        program.cons, program.classes, sc_contexts,
        imports=supplied, fresh=fresh, export=imports)
    scs = lower_fields(scs)
    mono_errors = check_monotone(scs)
    if mono_errors:
        raise MonotoneError('\n'.join(mono_errors))
    grammar_errors = check_subgrammars(scs, program.cons)
    if grammar_errors:
        raise SubgrammarError('\n'.join(grammar_errors))
    return StackFront(list(module.items), scs, results, per_c, per_g,
                      imports, fresh._n, frozenset(results))


def _analyse_staged(source: str):
    """`_analyse`, with the library stack answered from `_stack_front`.

    Only for a text whose assembler registered a seam, and only when the
    program shadows nothing the stack defines — otherwise `None`, and the
    whole-text path does what it always did.  The program's items are
    parsed at their assembled line offset (the same shifted tokens
    `syntax.parse` uses for a seam), so every position and error message
    comes out identical to the unstaged path's.
    """
    from . import syntax as _syn

    cut = _syn._SEAMS.get(source)
    if cut is None:
        return None
    from .infer import Fresh
    from .syntax import _shifted, parse_module, tokenize
    from .syntax.descend import _build_fixity_table, _descend_val

    head, rest = source[:cut], source[cut:]
    sf = _stack_front(head)
    dn = head.count("\n")
    rest_mod = parse_module([_shifted(t, dn) for t in tokenize(rest)])
    mine = {str(i.name) for i in rest_mod.items if hasattr(i, "name")}
    if mine & sf.defined:
        # The program shadows a stack name.  The whole-text path renames
        # the stack's binding out of the way; this one cannot, because the
        # renaming would have to reach inside the cached analysis.
        return None
    table = _build_fixity_table(VModule(list(sf.items) + list(rest_mod.items)))
    rest_items = [_descend_val(i, table) for i in rest_mod.items]
    module = VModule(list(sf.items) + rest_items)
    program = classify(module)
    exhaust_errors = check_program(program)
    if exhaust_errors:
        raise ExhaustError('\n'.join(exhaust_errors))
    scs_all = desugar_program(program)
    scs_prog = scs_all[len(sf.scs):]
    _kind_check_program(program, scs_all)
    sc_contexts = {sc.name: sc.sig_constraints for sc in program.scs
                   if sc.sig_constraints}
    results_p, per_c_p, per_g_p = infer_program(
        scs_prog, _build_builtins(), program.cons, program.classes,
        sc_contexts, imports=sf.imports, fresh=Fresh(sf.fresh_end))
    main_type = results_p.get("main")
    scs_prog = lower_fields(scs_prog)
    mono_errors = check_monotone(scs_prog)
    if mono_errors:
        raise MonotoneError('\n'.join(mono_errors))
    grammar_errors = check_subgrammars(scs_prog, program.cons)
    if grammar_errors:
        raise SubgrammarError('\n'.join(grammar_errors))
    scs = list(sf.scs) + list(scs_prog)
    results = {**sf.results, **results_p}
    scs = _discharge(scs, program, results,
                     list(sf.per_sc_constraints) + per_c_p,
                     list(sf.per_sc_givens) + per_g_p)
    scs, method_scs = resolve_static_methods(scs)
    scs = expand_envelopes(scs, program.cons)
    return Analysis(scs, program, results, method_scs, main_type)


def _discharge(scs, program, results, per_sc_constraints, per_sc_givens):
    """Solve the program's constraints and rewrite the SCs they touch.

    The half of the front end after inference: contexts checked, instances
    solved, dictionaries inserted (`elaborate`) and constant ones folded
    away (`specialise`).  One function because the staged path and the
    whole-text path both end here, on the *combined* SC list, so the two
    cannot drift.
    """
    check_main_has_no_context(
        {name: 1 for (name, _a, _l, _s), givens
         in zip(scs, per_sc_givens) if givens})
    # A constraint the SC's own context already grants is discharged by
    # a dictionary parameter, not by an instance.
    all_constraints = [
        p
        for preds, givens in zip(per_sc_constraints, per_sc_givens)
        for p in preds
        if not _is_given(p, givens)
    ]
    if all_constraints or any(per_sc_givens):
        resolved = solve_constraints(all_constraints, program.instances)
        givens_by_name = {str(name): givens
                          for (name, _a, _l, _s), givens
                          in zip(scs, per_sc_givens) if givens}
        scs = elaborate(scs, per_sc_constraints, resolved, program,
                        results, per_sc_givens)
        # A constrained definition called with constant dictionaries
        # gets a copy with them substituted in, which is what lets one
        # be written at all in a synth: the fragment is monomorphic and
        # refuses anything that so much as mentions a dictionary.
        # `resolved` as well as `program.instances`: a `Num Float` is
        # *manufactured* while constraints are solved (`constraint.
        # _num_instance`) and appears in no declaration, so the
        # instance list alone does not know what `__dict_Num_Float__`
        # stands for.
        scs = specialise(scs, givens_by_name,
                         list(program.instances) + list(resolved.values()))
    return scs


def _analyse(source: str, *, typecheck: bool = True,
             prelude: bool = True) -> Analysis:
    main_type = None
    results: dict = {}
    if typecheck and prelude:
        staged = _analyse_staged(source)
        if staged is not None:
            return staged
    if prelude:
        module = _merge_prelude(source)
    else:
        module = parse(source)
    program = classify(module)

    # Exhaustiveness runs on the surface patterns, before desugaring: the
    # match compiler writes out an alternative for every constructor, so a
    # core `ECase` is always complete by construction.
    exhaust_errors = check_program(program)
    if exhaust_errors:
        raise ExhaustError('\n'.join(exhaust_errors))

    scs = desugar_program(program)

    if typecheck:
        _kind_check_program(program, scs)
        builtins = _build_builtins()
        typed = [(name, arity, lam, sig) for (name, arity, lam, sig) in scs]
        sc_contexts = {sc.name: sc.sig_constraints for sc in program.scs
                       if sc.sig_constraints}
        results, per_sc_constraints, per_sc_givens = infer_program(
            typed, builtins, program.cons, program.classes, sc_contexts)
        main_type = results.get("main")

        # `e.N` is resolved from its base's type and lowered here, before
        # any later pass has to know the node exists (`fixme.md` F28).
        scs = lower_fields(scs)

        # Datafun's monotone/discrete discipline.  It runs here, on the
        # tree inference just annotated: elaboration rebuilds the lambdas
        # to insert dictionary parameters and the binder flavours would
        # not survive that.
        mono_errors = check_monotone(scs)
        if mono_errors:
            raise MonotoneError('\n'.join(mono_errors))

        # Datafun's four type subgrammars — what keeps `Sig`/`Chan`/`⃝`
        # out of sets, joins and fixed points (`spec/data.md` §II.1).
        grammar_errors = check_subgrammars(scs, program.cons)
        if grammar_errors:
            raise SubgrammarError('\n'.join(grammar_errors))
        scs = _discharge(scs, program, results,
                         per_sc_constraints, per_sc_givens)

    # Resolve `πᵢ __dict_C_T__` to the method it selects, before ϕ/δ can
    # meet a projection out of a discrete value.  `method_scs` is the set
    # of instance methods now called by name, which the ϕ/δ gate must
    # therefore treat as ordinary supercombinators.
    scs, method_scs = resolve_static_methods(scs)

    # `on <points> x` into a balanced tree of comparisons, so that an
    # envelope can be read at audio rate — `envexpand.py`.
    #
    # **After `resolve_static_methods`, and that is not a preference.**
    # What it has to recognise is a `Float` literal, which at this point in
    # the pipeline is a call to `Floating`'s `fromFloat` — but only *after*
    # this line, because until it runs the same thing is a projection out
    # of a dictionary.  Placed one line earlier the pass matched nothing at
    # all and silently changed no program, which is the failure mode a
    # rewrite that declines to fire always has.
    scs = expand_envelopes(scs, program.cons)
    return Analysis(scs, program, results, method_scs, main_type)


def _compile(source: str, *, typecheck: bool = True,
             prelude: bool = True) -> GmState:
    # Through the cache, like every other reader: compiling a text the
    # engine has already analysed — which is what loading a program's
    # `FromMIDI` instances does, right after building its graph — used to
    # pay for the front end twice.
    analysis = _analysed_or_new((source, typecheck, prelude))
    scs = analysis.scs
    program = analysis.program
    method_scs = analysis.method_scs
    main_type = analysis.main_type

    # Generate Datafun helpers and desugar Datafun nodes.  This is scoped
    # to programs that actually use Datafun: `spec/data.md` §0 applies ϕ/δ
    # to Datafun-typed subterms, and running it over a program with no set
    # anywhere doubles the SC count while giving every FRP combinator a
    # nonsensical `f_delta` (δ has no case for `head`/`:::`, so the change
    # it emits is the original expression).
    if _uses_datafun(scs):
        set_types = _collect_set_types(scs)
        if not set_types:
            # The set type is used only inside a body, where
            # `_collect_set_types` cannot see it yet (see
            # `implementation_order.md` §17).
            from .types import TApp
            set_types = [TApp(TCon("Set"), TCon("Int"))]
        helpers = generate_all_helpers(set_types, program.cons)
        semifix_helpers = [
            h
            for st in set_types
            for h in make_semifix_helpers(
                program.cons["Nil"].tag, program.cons["Cons"].tag,
                program.cons["True"].tag, program.cons["False"].tag,
                _type_suffix(st),
            )
        ]
        helper_names = {name for name, _, _ in helpers}
        helper_names.update({name for name, _, _ in semifix_helpers})

        # Seminaïve ϕ/δ transform — runs BEFORE Datafun desugaring
        scs, changes = seminaive_transform(scs, helper_names, program.cons,
                                          method_scs)
        # δ's zero changes are built at their own type, and which types
        # those are is not known until it has run: a `dummy` at a sum type
        # is a generated function, and a `⊥` may be at a set type no
        # annotated node mentions.  Both are emitted here (`spec/data.md`
        # §I.4.3 lists `dummyA` among the per-program helpers).
        def _add(new: list) -> None:
            for h in new:
                if h[0] not in helper_names:
                    helper_names.add(h[0])
                    helpers.append(h)

        # Generating a `dummy` can ask for a `⊥`, and a `⊥` at a set type
        # nothing else mentions pulls in that type's whole helper family,
        # so this runs to a fixed point.
        while True:
            _add(changes.generate())
            missing = [st for suffix, st in changes.sets.items()
                       if f"bottom_{suffix}" not in helper_names]
            if not missing:
                break
            for st in missing:
                _add(generate_all_helpers([st], program.cons))
        # ⊥-propagation — between the two, while `EJoin`/`EFor` are still
        # nodes.  Without it ϕ/δ buys a constant factor and no asymptotics
        # (`spec/errata.md` D3).
        scs = propagate_bottoms(scs)
        # Datafun desugaring — runs AFTER ϕ/δ
        scs = _desugar_datafun(scs, set_types, program.cons)
        scs = scs + [(name, arity, lam, None) for name, arity, lam in helpers]
        scs = scs + [(name, arity, lam, None) for name, arity, lam in semifix_helpers]
        _check_helpers_exist(scs)

    stripped = []
    for name, arity, lam, _sig in scs:
        stripped.append((name, arity, strip_annotations(lam)))  # type: ignore[arg-type]

    lifted = lift(stripped)
    state = compile_program(lifted)
    state.result_type = main_type
    # A backend reading a result out of the heap needs to know which
    # tag is which — user constructors are numbered first, so no tag
    # is a constant (`fixme.md` F68).
    state.cons = program.cons
    if "True" in program.cons and "False" in program.cons:
        state = add_primitives(state,
                               program.cons["True"].tag,
                               program.cons["False"].tag,
                               program.cons["Nil"].tag,
                               program.cons["Cons"].tag)
    return state


def _desugar_datafun(
    scs: list, set_types: list, cons: dict,
) -> list:
    """Replace Datafun nodes with calls to generated helper SCs."""
    from .helpers import _type_suffix
    from .expr import (
        EAnnot, EAp, EAppEx, EAppFa, EBox, ECase, EChan, ECon, EDelay, EFix,
        EJoin,
        EFor, EGFix, EGlobal, ELambda, ELet, ENever, ENum, EChr, EProj, ESet,
        ESigCons, ESigHead, ESync, ETail, ETuple, EUnbox, EVar, EWait, EWatch,
        Alter, Expr,
    )

    def suffix_for(t, what: str) -> str:
        if not isinstance(t, Type):
            raise PipelineError(
                f"the type of this {what} did not reach code generation; "
                f"it should have been annotated during inference"
            )
        return _type_suffix(t)

    def desugar(expr):
        if isinstance(expr, EFix):
            # fix e → fix_X e, X from the fixed point's own type.
            suffix = suffix_for(expr.set_type, "`fix`")
            return EAp(EGlobal(f"fix_{suffix}"), desugar(expr.body))
        if isinstance(expr, EFor):
            # for (x in set) body → for_L set (λx. body).  The helper is
            # indexed by the *result* semilattice — that is where ⊥ and ∨
            # come from — and folds over any set, since the cons-list
            # constructors are shared.
            suffix = suffix_for(expr.result_type, "`for`")
            return EAp(EAp(EGlobal(f"for_{suffix}"),
                           desugar(expr.set_expr)),
                       ELambda([expr.var], desugar(expr.body)))
        if isinstance(expr, EJoin):
            suffix = suffix_for(expr.set_type, "`\\/`")
            return EAp(EAp(EGlobal(f"join_{suffix}"), desugar(expr.left)),
                       desugar(expr.right))
        if isinstance(expr, ESet):
            # {e1, …, en} → union {e1} (union {e2} … ⊥)
            #
            # Not a bare cons chain: a set *is* a sorted, duplicate-free
            # list, and every operation on one (`union`, `diff`, `eq`,
            # `subset`) is a merge that assumes it.  Building the literal
            # with `union` establishes the invariant instead of trusting
            # the author to have written the elements in order —
            # `{(1,2), (0,1)}` is a perfectly ordinary thing to write.
            nil_tag = cons["Nil"].tag
            cons_tag = cons["Cons"].tag
            if not expr.items:
                return ECon(nil_tag, [])
            suffix = suffix_for(expr.set_type, "set literal")
            union = EGlobal(f"union_{suffix}")
            acc: Expr = ECon(nil_tag, [])
            for item in reversed(expr.items):
                single = ECon(cons_tag, [desugar(item), ECon(nil_tag, [])])
                acc = EAp(EAp(union, single), acc)
            return acc
        if isinstance(expr, EBox):
            # A box is the pair `(base, change)` at runtime.  ϕ/δ needs the
            # second half; code outside the transform has no change to
            # offer, so it packs a zero one.  One representation matters:
            # a box built here can be consumed by ϕ/δ-generated code and
            # vice versa (§17).
            return ETuple([desugar(expr.body), EGlobal("bottom_Set_Int")])
        if isinstance(expr, EUnbox):
            # unbox x = e in f → let (x, dx) = e in f
            tmp = f"_box_{expr.var}"
            return ELet(False, [(tmp, desugar(expr.binding))],
                        ELet(False, [
                            (expr.var, EAp(EProj(0), EVar(tmp))),
                            ("d" + expr.var, EAp(EProj(1), EVar(tmp))),
                        ], desugar(expr.body)))
        # Recursive walk
        if isinstance(expr, EAp):
            return EAp(desugar(expr.fn), desugar(expr.arg))
        if isinstance(expr, ELambda):
            return ELambda(list(expr.params), desugar(expr.body))
        if isinstance(expr, ELet):
            defs = [(n, desugar(d)) for n, d in expr.defs]
            return ELet(expr.is_rec, defs, desugar(expr.body))
        if isinstance(expr, ECase):
            alts = [Alter(a.tag, list(a.names), desugar(a.body)) for a in expr.alts]
            return ECase(desugar(expr.scrut), alts)
        if isinstance(expr, (EVar, ENum, EChr, EGlobal, EProj, ENever, EChan)):
            return expr
        if isinstance(expr, EAnnot):
            return EAnnot(desugar(expr.expr), expr.type_)
        if isinstance(expr, ECon):
            return ECon(expr.tag, [desugar(a) for a in expr.args])
        if isinstance(expr, ETuple):
            return ETuple([desugar(a) for a in expr.args])
        # FRP nodes: the node itself is handled by compileC, but its
        # subterms are ordinary user code and may contain Datafun forms.
        if isinstance(expr, ESigCons):
            return ESigCons(desugar(expr.value), desugar(expr.tail))
        if isinstance(expr, ESigHead):
            return ESigHead(desugar(expr.sig))
        if isinstance(expr, EDelay):
            return EDelay(desugar(expr.body))
        if isinstance(expr, EAppFa):
            return EAppFa(desugar(expr.fn), desugar(expr.arg))
        if isinstance(expr, EAppEx):
            return EAppEx(desugar(expr.fn), desugar(expr.arg))
        if isinstance(expr, EWait):
            return EWait(desugar(expr.chan))
        if isinstance(expr, EWatch):
            return EWatch(desugar(expr.sig))
        if isinstance(expr, ETail):
            return ETail(desugar(expr.sig))
        if isinstance(expr, ESync):
            return ESync(desugar(expr.left), desugar(expr.right))
        if isinstance(expr, EGFix):
            return EGFix(expr.var, desugar(expr.body))
        return expr

    result = []
    for name, arity, lam, sig in scs:
        body = desugar(lam.body)
        result.append((name, arity, ELambda(list(lam.params), body), sig))
    return result


def _uses_datafun(scs: list) -> bool:
    """Does any SC body contain a Datafun form?

    ``EBox``/``EUnbox`` count: ϕ compiles a box to a ``(base, change)``
    pair, so a program using them needs the transform even with no set
    literal in sight.
    """
    from .expr import EBox, EFix, EFor, EJoin, ESet, EUnbox

    stack = [lam.body for _n, _a, lam, _s in scs]
    while stack:
        e = stack.pop()
        if isinstance(e, (ESet, EFix, EFor, EJoin, EBox, EUnbox)):
            return True
        stack.extend(subexprs(e))
    return False


class MonomorphizationError(Exception):
    """A Datafun operation landed at a type helpers were not generated for."""


def _check_helpers_exist(scs: list) -> None:
    """Every generated helper a supercombinator calls must actually exist.

    Datafun helpers are generated per *concrete* set type (`errata.md` D9),
    so an operation at a type that is still a variable has nothing to call.
    `_collect_set_types` drops such a type silently — it has to, because the
    polymorphic prelude's dead branches legitimately mention them — and the
    program then compiled and died at run time as
    `unknown global 'for_Set_a-43'`, a G-machine error naming an internal
    symbol and pointing nowhere near the cause (`fixme.md` F64).

    Checking *references* rather than types is what makes this precise: a
    non-ground type nothing reaches is harmless and stays harmless, and only
    a helper some body actually calls is required to exist.  Nothing is
    guessed from a name.
    """
    from .seminaive import _HELPER_PREFIXES

    defined = {str(name) for name, _a, _l, _s in scs}
    missing: dict[str, str] = {}
    for name, _arity, lam, _sig in scs:
        for node in _all_nodes(lam):
            if not isinstance(node, EGlobal) or not isinstance(node.name, str):
                continue
            if not node.name.startswith(_HELPER_PREFIXES):
                continue
            if node.name not in defined:
                missing.setdefault(node.name, str(name))
    if not missing:
        return

    import re

    def _readable(sc: str) -> str:
        # ϕ/δ renames a transformed supercombinator; the user wrote the
        # name without the suffix and should be told that one.
        for half in ("_phi", "_delta"):
            if sc.endswith(half):
                return sc[: -len(half)]
        return sc

    lines = []
    for helper, where in sorted(missing.items()):
        op, _, suffix = helper.partition("_")
        # `Set_a-43` is a generated suffix carrying an internal variable id.
        shown = re.sub(r"\ba-?\d+\b", "a", suffix.replace("_", " "))
        lines.append(
            f"  '{_readable(where)}' needs {op} at `{shown}`, "
            f"whose element type is not concrete"
        )
    raise MonomorphizationError(
        "Datafun operations are compiled per concrete type, so a set type "
        "has to be known here:\n" + "\n".join(lines) +
        "\n\nA signature polymorphic in a set's element type — `f : {a} ~> "
        "{a}` — is outside the Datafun sublanguage (`spec/errata.md` D9).  "
        "Give the element a concrete type, or drop the signature and let the "
        "use site determine it."
    )


def _collect_set_types(scs: list) -> list[Type]:
    """Every concrete set type the program needs helpers for.

    Read off the annotations inference left on `ESet`/`EFix`/`EFor` rather
    than guessed from signatures, so a set type that appears only inside a
    body is found too (`implementation_order.md` §17).  `Set Int` is always
    included: it is where a zero change lands when the tree records no
    type at all, which is now only an `EVar` inference never visited.  A
    set type ϕ/δ discovers for itself is added afterwards, from the
    `Changes` builder.
    """
    from .expr import EFix, EFor, EJoin, ESet

    types: list[Type] = []
    seen: set[str] = set()

    def add(t) -> None:
        if isinstance(t, Type) and not free_vars(t):
            key = str(t)
            if key not in seen:
                seen.add(key)
                types.append(t)

    add(TApp(TCon("Set"), TCon("Int")))
    for _name, _arity, lam, sig in scs:
        if isinstance(sig, Type):
            _scan_set_type(sig, types, seen)
        for node in _all_nodes(lam):
            if isinstance(node, (ESet, EFix, EJoin)):
                add(node.set_type)
            elif isinstance(node, EFor):
                add(node.result_type)
    return types


def _all_nodes(root: Expr):
    stack = [root]
    while stack:
        e = stack.pop()
        yield e
        stack.extend(subexprs(e))


def _scan_set_type(t: Type, types: list[Type], seen: set[str]) -> None:
    """Collect concrete set types from type annotations."""
    if isinstance(t, TApp) and isinstance(t.fn, TCon) and t.fn.name == "Set":
        suffix = str(t)
        if suffix not in seen:
            seen.add(suffix)
            types.append(t)
    elif isinstance(t, TApp):
        _scan_set_type(t.fn, types, seen)
        _scan_set_type(t.arg, types, seen)


def evaluate(source: str, max_steps: int = 10_000_000, *,
             typecheck: bool = True, prelude: bool = True) -> str:
    state = compile(source, typecheck=typecheck, prelude=prelude)
    run(state, max_steps=max_steps)
    return show_result(state)
