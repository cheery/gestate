"""The static signal fragment — `spec/liveaudio.md` stage 1.

A flat graph can only be extracted from a graph that is **static**: known at
compile time and unchanging while it runs.  Nothing in `blip.ges` or
`drums.ges` needs otherwise, but the *language* allows more — `chan`,
higher-order signals, `sync` between arbitrary clocks — so the audio
compiler accepts a **sublanguage**, and this is the check that says whether
a program is in it.

The third time this project draws such a boundary, after the monomorphic
Datafun sublanguage (`errata.md` D9) and `[: Void :]` as the scores the MIDI
backend accepts.  It is written to the same standard as `subgrammar.py`: it
reports *why* a definition leaves the fragment, and names the definition,
because a checker whose message is "not supported" moves the work of
finding the cause onto the reader.

What it does **not** do is decide anything about running the program.
`render()` will happily run a program this rejects, and that is the point:
the fragment is what the *engine* can compile, not what the language means.

    python -m gestate.audiograph examples/audio/drums.ges
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .expr import (EAnnot, EAp, EBox, ECase, EChan, ECon, EDelay, EFix, EFor,
                   EGFix, EGlobal, EJoin, ELambda, ELet, ENever, EProj, ESet,
                   ESigCons, ESigHead, ESync, ETail, EUnbox, EVar,
                   EWait, EWatch, subexprs)
from .gmachine import MATH_FLOAT
from .show import show_type
from .types import (TApp, TCon, TFun, TVar, Type, is_flat,
                    why_not_flat)

#: The signal formers the fragment is built from.  They are *primitives* of
#: the fragment rather than definitions in it: their own bodies are `gfix`
#: over `delay`/`<*>`, which is the guarded-recursion machinery that makes a
#: signal productive and is exactly what the engine replaces.  Each maps to
#: the node kind stage 2 will emit.
FORMERS = {
    "mkSig": "source",
    "mapSig": "map",
    "scan": "scan",
    "zipSig": "zip",
    # `map` at `Sig`, as `elaborate.resolve_static_methods` leaves it.
    # `signal.ges` writes `instance Functor Sig where map f s = mapSig f s`
    # and keeps `mapSig` internal, so `map` is the name a program says and
    # this is the name the program *has* by the time the fragment reads it.
    #
    # A former rather than a definition, even though the instance really
    # does define one.  The body is the alias it looks like, but its type
    # is `(a -> b) -> Sig a -> Sig b`: two variables, and the fragment is
    # monomorphic, so checking it as a definition asked for the layout of
    # `a -> b` and got "a function has no layout in a state struct".  The
    # use site is where the types are settled, which is exactly the reason
    # `mapSig` was a former and not a definition either.
    "__Functor_Sig_map__": "map",
    # `zip` at `Sig`, the same arrangement: `signal.ges` writes
    # `instance Zip Sig where zip f s t = zipSig f s t` and keeps `zipSig`
    # internal, so `zip` is the name a program says and this is the name
    # the program *has* by the time the fragment reads it.
    "__Zip_Sig_zip__": "zip",
    #: A delay line with a fold around it — `spec/delaylines.md`.  A `scan`
    #: with a longer arm, and it needs no relaxation of the graph's
    #: acyclicity because the loop is *inside* the node exactly as a
    #: `scan`'s is.
    "feedback": "line",
    #: A delay line read at a moving position.  **The one node whose output
    #: is a function of its state alone** — its input is consumed at the
    #: end of the instant — which is what lets a cycle close through it.
    "tap": "tap",
    #: A delay line with a filter in it — a `line` whose ring holds whole
    #: states rather than samples, so the step reaches both the far end and
    #: the near one.  Still no cycle: the loop is inside the node.
    "loop": "loop",
    #: A delay line that bends: `tap`'s interpolated moving read closed
    #: into `feedback`'s loop, so the *length* of a feedback path may be a
    #: signal.  Still no cycle in the graph — the loop is inside the node —
    #: and the read is clamped a sample back, so it cannot close empty.
    "slide": "slide",
}

#: What each former takes, by the *node kind* rather than by the name — two
#: names can emit the same node, and what a `map` node needs is a property
#: of the node.
SHAPES = {
    "source": ("value",),
    "map": ("step", "signal"),
    "scan": ("step", "value", "signal"),
    "zip": ("step", "signal", "signal"),
    # `feedback n f s` — the length first, because it is the thing that has
    # to be constant and reads better said first.
    "line": ("value", "step", "signal"),
    # `tap n pos s` — the length first, because it is the one that has to
    # be constant.
    "tap": ("value", "signal", "signal"),
    # `loop n f z s` — the length first as a `line`'s is, then the step,
    # then the initial state, which is where a `scan` keeps it too.
    "loop": ("value", "step", "value", "signal"),
    # `slide n f pos s` — the length first as its siblings', the step, and
    # then two signals: the position and the input.
    "slide": ("value", "step", "signal", "signal"),
}

#: Machine primitives over flat types.  `chr`/`ord` move between `Int` and
#: `Char` and are the identity at run time; `empty?` is Datafun's and is
#: deliberately absent.
PRIMITIVES = frozenset({
    "prim_eq_int", "prim_lt_int", "prim_mod_int", "prim_add_int",
    "prim_sub_int", "prim_mul_int", "prim_div_int",
    "prim_eq_float", "prim_lt_float", "prim_add_float", "prim_sub_float",
    "prim_mul_float", "prim_div_float", "prim_mod_float",
    "prim_to_float", "prim_floor_float",
    # The transcendentals.  In the fragment because they are first-order,
    # non-allocating and flat — the same three properties every primitive
    # here has — and because the generated code calls the same libm the
    # oracle does (`spec/liveaudio.md` open question 2).
    *(f"prim_{fn}_float" for fn in MATH_FLOAT),
    "chr", "ord",
})

#: Primitives that exist and are outside the fragment anyway — worth
#: naming, so the message says *why* rather than "unknown".
_DATAFUN_PRIMITIVES = frozenset({"empty?"})

#: Instance types a statically-resolved class method may be at.  A method
#: that survives `resolve_static_methods` as `__Num_Float_+__` is a direct
#: call to machine arithmetic and is first-order; one still reached through
#: a dictionary is not, and is caught as a dictionary instead.
_FLAT_INSTANCE_HEADS = frozenset({"Int", "Float", "Bool", "Char"})


@dataclass
class Report:
    """What the check found, whether or not it passed.

    The classification is not a by-product — stage 2 extracts its graph from
    exactly these sets, so producing them *is* half of the extractor's
    input, and having them here keeps the two from disagreeing about what a
    node is.
    """
    errors: list[str] = field(default_factory=list)
    #: Definitions whose value is a signal: the nodes of the graph.
    signals: list[str] = field(default_factory=list)
    #: Definitions used as step functions or called from one.
    scalars: list[str] = field(default_factory=list)
    #: Definitions whose body is `chan` — one clock each.
    clocks: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return not self.errors

    @property
    def message(self) -> str:
        return "\n".join(self.errors)


# ── Entry points ────────────────────────────────────────────────────────────


def check(source: str, *, rate: int = 22050, entry: str = "sound") -> Report:
    """Is this synth program in the fragment?  Compiles it to find out."""
    from .audio import assemble
    from .pipeline import analyse

    return check_analysis(analyse(assemble(source, rate)), entry=entry)


def check_analysis(analysis, *, entry: str = "sound") -> Report:
    return _Check(analysis, entry).run()


# ── The check ───────────────────────────────────────────────────────────────


class _Check:
    def __init__(self, analysis, entry: str):
        self.entry = entry
        self.cons = analysis.program.cons
        self.types = analysis.types
        self.by_name = {str(n): (a, lam, sig)
                        for n, a, lam, sig in analysis.scs}
        #: tag → the constructor's own type, for judging an `ECon`.
        self.by_tag = {info.tag: info for info in self.cons.values()}
        self.report = Report()
        #: name → "signal" | "scalar", as each is reached.
        self.seen: dict[str, str] = {}
        #: Calls between scalar definitions, for the recursion check.
        self.calls: dict[str, set[str]] = {}
        self.here = ""

    # -- driving ------------------------------------------------------------

    def run(self) -> Report:
        if self.entry not in self.by_name:
            return self._fail(f"there is no `{self.entry}` to check")
        t = self._type_of(self.entry)
        if t is not None and _signal_elem(t) is None:
            return self._fail(
                f"`{self.entry}` must be a `Sig Float` and is "
                f"{show_type(t)}")

        # Breadth-first from `sound`, so the messages come out in the order
        # a reader would reach them from the definition they started at.
        from collections import deque
        self.pending: deque = deque([(self.entry, "signal")])
        while self.pending:
            name, kind = self.pending.popleft()
            if self.seen.get(name) == kind:
                continue
            if name in self.seen and self.seen[name] != kind:
                self._error(name, "is used both as a signal and as an "
                                  "ordinary value")
                continue
            self.seen[name] = kind
            self._definition(name, kind)

        self._check_recursion()
        self._check_clocks()
        self.report.signals = sorted(n for n, k in self.seen.items()
                                     if k == "signal")
        self.report.scalars = sorted(n for n, k in self.seen.items()
                                     if k == "scalar")
        self.report.errors = _dedup(self.report.errors)
        return self.report

    def _need(self, name: str, kind: str) -> None:
        self.pending.append((name, kind))

    # -- one definition -----------------------------------------------------

    def _definition(self, name: str, kind: str) -> None:
        arity, lam, _sig = self.by_name[name]
        self.here = name
        t = self._type_of(name)

        if isinstance(lam.body, EChan):
            self.report.clocks.append(name)
            return

        if t is not None:
            args, result = _arrow(t)
            if arity > len(args):
                # `elaborate` prepends one parameter per constraint, so a
                # supercombinator wider than its own type is one that takes
                # a class dictionary — which is a record of functions, and
                # the most precise possible statement of "not monomorphic".
                self._error(name, "is polymorphic: it takes a class "
                                  "dictionary, which is a record of "
                                  "functions the engine cannot lay out")
                return
            before = len(self.report.errors)
            self._check_signature(name, args, result, kind)
            if len(self.report.errors) > before:
                # Its type is already the answer.  Walking the body as well
                # reports the same fact a second time, in terms of the
                # internal type of a `Cons` — which is true, unreadable and
                # not what the reader needs.
                return

        if kind == "signal":
            self._signal(lam.body)
        else:
            self._scalar(lam.body)

    def _check_signature(self, name, args, result, kind) -> None:
        # **A signal definition may be polymorphic, and a scalar one may
        # not.**  The difference is inlining: a signal definition
        # *disappears* into the nodes it builds, at every use and at that
        # use's own type, so `mkKnob : a -> Sig a` has no `a` left anywhere
        # in the graph — the source it produces is a `Float` one or an
        # `Int` one according to the value it was given.  A step function
        # survives into the IR as a function, and a function of unknown
        # size has nothing to be generated as.
        #
        # Refusing both was `fixme.md` F96's mistake in a second place:
        # judging a definition by its declared type rather than by what
        # becomes of it, and so rejecting programs the fragment admits.
        # `audioextract._inline` takes the element type from the use site
        # when the signature's own is a variable, which is what makes the
        # allowance real rather than a hole.
        # **And it may be polymorphic in what it takes, not only in what it
        # returns.**  The line used to be drawn between the two, on the
        # grounds that a definition does not know the element type of a
        # signal it was handed — which is true of the *definition* and not
        # of the program: a signal argument is itself a definition with a
        # type of its own, checked on its own terms, and inlining is what
        # brings the two together.
        #
        # Keeping the line there is what stopped the prelude from holding
        # anything that works on a note.  A bank hands a voice a
        # `Sig <payload>` of its own, so `payloadOf : Sig (Both Gate a) ->
        # Sig a` and everything else that works on a note could not be
        # written *once*, and every polyphonic example in this repository
        # re-implemented it against its own payload type.  That
        # is the ceremony `spec/frp_lesson.md` is about, and it was one
        # word of this function.
        #
        # `_settled` is what makes it sound rather than merely permissive:
        # a variable stands for whatever the inline site supplies, so the
        # type is judged as if it were already flat.  A parameter that is
        # *not* flat for any substitution — a function, a list — is refused
        # here exactly as before.
        free = kind == "signal"
        for i, a in enumerate(args):
            elem = _signal_elem(a)
            if elem is not None:
                if not is_flat(_settled(elem) if free else elem, self.cons):
                    self._error(name, f"takes a `{show_type(a)}`, whose "
                                      f"samples are {why_not_flat(elem, self.cons)}")
                continue
            if not is_flat(_settled(a) if free else a, self.cons):
                self._error(name, f"takes a parameter of type "
                                  f"{show_type(a)}, which is "
                                  f"{why_not_flat(a, self.cons)}"
                                  + self._table_hint(a))
        want = _signal_elem(result) if kind == "signal" else result
        if kind == "signal" and want is None:
            self._error(name, f"is used as a signal but yields "
                              f"{show_type(result)}")
            return
        if want is not None and not is_flat(_settled(want) if free else want,
                                            self.cons):
            self._error(name, f"yields {show_type(want)}, which is "
                              f"{why_not_flat(want, self.cons)}"
                              + self._table_hint(want))

    def _table_hint(self, t: Type) -> str:
        """The one transformation `spec/liveaudio.md` predicted."""
        head = t.fn if isinstance(t, TApp) else t
        if isinstance(head, TCon) and head.name == "List":
            return (".  A constant list read per sample is a **lookup "
                    "table**: the extractor lifts it to a constant array "
                    "and indexes it, but only once it is written as one "
                    "(`spec/liveaudio.md`, \"the transformation the "
                    "fragment forces\")")
        return ""

    # -- signal expressions -------------------------------------------------

    def _signal(self, e) -> None:
        """`S ::= source | map f S | scan f z S | zip f S S | g A… | x`."""
        if isinstance(e, EAnnot):
            return self._signal(e.expr)

        if isinstance(e, ESigCons):
            # `v ::: mkSig (wait c)` — the one source form.  Anything else
            # under `:::` is a signal built by hand, which is precisely the
            # thing the fragment exists to keep out.
            tail = _strip(e.tail)
            if (isinstance(tail, EAp) and _is(tail.fn, "mkSig")
                    and isinstance(_strip(tail.arg), EWait)):
                self._scalar(e.value)
                chan = _strip(_strip(tail.arg).chan)
                if isinstance(chan, EGlobal):
                    self._need(str(chan.name), "scalar")
                return
            self._error(self.here, "builds a signal with `:::` directly.  "
                                   "An audio-rate signal comes from `ticks` "
                                   "and the combinators over it, so that "
                                   "the graph is known before it runs")
            return

        if isinstance(e, EVar):
            return                       # a signal parameter, e.g. `lowpass`'s

        if isinstance(e, EGlobal):
            return self._reference(str(e.name), "signal")

        if isinstance(e, EAp):
            head, args = _spine_ap(e)
            if isinstance(head, EGlobal) and str(head.name) in FORMERS:
                return self._former(str(head.name), args)
            if isinstance(head, EGlobal):
                return self._call(str(head.name), args)

        self._error(self.here, f"is not a signal expression: "
                               f"{_describe(e)}")

    def _former(self, name: str, args: list) -> None:
        shape = SHAPES[FORMERS[name]]
        if len(args) != len(shape):
            self._error(self.here,
                        f"applies `{name}` to {len(args)} argument(s) "
                        f"where the fragment needs {len(shape)}.  A "
                        f"partially applied combinator is a signal the "
                        f"graph cannot name")
            return
        for kind, arg in zip(shape, args):
            if kind == "signal":
                self._signal(arg)
            elif kind == "value":
                self._scalar(arg)
            else:
                self._step(name, arg)

    def _call(self, name: str, args: list) -> None:
        """A user definition that yields a signal — `gain 0.6 (lowpass …)`."""
        t = self._type_of(name)
        if t is None:
            self._error(self.here, f"calls `{name}`, whose type is not known")
            return
        params, _result = _arrow(t)
        for param, arg in zip(params, args):
            if _signal_elem(param) is not None:
                self._signal(arg)
            elif isinstance(param, TFun):
                self._step(name, arg)
            else:
                self._scalar(arg)
        self._reference(name, "signal")

    def _step(self, former: str, e) -> None:
        """A step function: a definition, or a lambda written at the call."""
        e = _strip(e)
        if isinstance(e, EGlobal):
            return self._reference(str(e.name), "scalar")
        if isinstance(e, ELambda):
            return self._scalar(e.body)
        self._error(self.here,
                    f"gives `{former}` a step function that is "
                    f"{_describe(e)}.  It has to be a definition or a "
                    f"lambda written here: anything else is a closure "
                    f"built while the program runs, and the graph is "
                    f"fixed before it does")

    # -- scalar (audio-rate) code -------------------------------------------

    def _scalar(self, e) -> None:
        """Straight-line arithmetic over flat values, and nothing else."""
        if isinstance(e, EAnnot):
            return self._scalar(e.expr)

        if isinstance(e, (ESet, EFix, EFor, EJoin, EBox, EUnbox)):
            self._error(self.here, f"uses {_describe(e)} in audio-rate "
                                   f"code.  Datafun's forms build sets, "
                                   f"which allocate")
            return
        if isinstance(e, (ESigCons, ESigHead, ETail, EDelay, EWait, EWatch,
                          ESync, EGFix, ENever, EChan)):
            self._error(self.here, f"uses {_describe(e)} inside a step "
                                   f"function.  A step function is called "
                                   f"once per sample and computes a value; "
                                   f"the signal structure around it is the "
                                   f"graph, and is fixed")
            return
        if isinstance(e, ELambda):
            self._error(self.here, "builds a function value in audio-rate "
                                   "code.  The fragment is first-order: a "
                                   "closure has no layout in a state struct")
            return
        if isinstance(e, ELet) and e.is_rec:
            self._error(self.here, "uses a recursive `let` in audio-rate "
                                   "code, which need not terminate")
            return

        if isinstance(e, EVar):
            t = getattr(e, "type_", None)
            if isinstance(t, TFun):
                self._error(self.here, f"applies `{e.name}`, a function it "
                                       f"was given as a value.  The "
                                       f"fragment is first-order")
            return

        if isinstance(e, EGlobal):
            return self._reference(str(e.name), "scalar")

        if isinstance(e, ECon):
            info = self.by_tag.get(e.tag)
            if info is not None:
                _fields, result = _arrow(info.type_)
                # **A constructor's own parameters are not the question.**
                # This reads the *declared* result type, so `Both Gate a` used
                # to be refused for having an `a` in it — while `is_flat`
                # says `Both Gate Custom` is perfectly flat, and the extractor
                # substitutes and lays it out.  The check was rejecting a
                # whole class of program the fragment admits (`fixme.md`
                # F96).
                #
                # The expression's own type is not available here — an
                # `ECon` carries a tag and its arguments, not an inferred
                # type — so a parameter stands in as something known-flat
                # and the *shape* is judged: a list is still refused,
                # because `List` is recursive whatever its element is, and
                # that is the property this check exists for.
                ground = _monomorphise(result)
                if not is_flat(ground, self.cons):
                    # Named by its constructor rather than its type: at this
                    # point a literal list's `Cons` still has a type like
                    # `List a-57`, and an internal variable id in a message
                    # is noise the reader cannot act on.
                    self._error(self.here,
                                f"builds a `{info.name}`, which is "
                                f"{why_not_flat(ground, self.cons)}")
                    return

        if isinstance(e, EAp):
            head, args = _spine_ap(e)
            if isinstance(head, EGlobal) and str(head.name) in FORMERS:
                self._error(self.here,
                            f"calls `{head.name}` inside a step function.  "
                            f"A signal combinator builds graph structure, "
                            f"and the graph is fixed before it runs")
                return
            for arg in args:
                if self._is_function_value(arg):
                    self._error(self.here,
                                f"passes a function to `{_name_of(head)}`.  "
                                f"The fragment is first-order: a function "
                                f"argument would have to be a pointer the "
                                f"engine dereferences per sample")
                    return

        for child in subexprs(e):
            self._scalar(child)

    def _is_function_value(self, e) -> bool:
        e = _strip(e)
        if isinstance(e, ELambda):
            return True
        if isinstance(e, EGlobal):
            info = self.by_name.get(str(e.name))
            return info is not None and info[0] > 0
        return False

    # -- references ---------------------------------------------------------

    def _reference(self, name: str, kind: str) -> None:
        if name in FORMERS:
            return
        if name in PRIMITIVES:
            return
        if name in _DATAFUN_PRIMITIVES:
            self._error(self.here, f"calls `{name}`, which is Datafun's and "
                                   f"eliminates a set.  Audio-rate code has "
                                   f"no sets in it")
            return
        if name.startswith("__dict_"):
            self._error(self.here, f"needs the dictionary `{name}`, so it "
                                   f"is polymorphic.  The fragment is "
                                   f"monomorphic: a dictionary is a record "
                                   f"of functions")
            return
        head = _instance_head(name)
        if head is not None and head not in _FLAT_INSTANCE_HEADS:
            # **Checked as a definition when it has a type to be checked
            # against.**  A method at a flat head is machine arithmetic and
            # needs no more than its name to be judged.  One at any other
            # head is an ordinary user definition wearing a generated name
            # — `instance Num (Sig Float)` is `zipSig (x y => x * y)`, the
            # same body `addSig` has — so judging it by its head refused a
            # program for the spelling of its plumbing.  `elaborate` now
            # states such a method's type whenever it is monomorphic, and
            # what is left is to check the body like any other.
            #
            # A method with *no* stated type is one taking a class
            # dictionary or standing at a head with variables in it, which
            # is polymorphism the fragment cannot lay out — so the old
            # message is what it gets, and it is now true rather than
            # merely conservative.
            if self._type_of(name) is None:
                self._error(self.here, f"uses a class method at `{head}`, "
                                       f"which is polymorphic: it takes a "
                                       f"dictionary, or its instance head "
                                       f"has a type variable in it")
                return
        if name not in self.by_name:
            self._error(self.here, f"calls `{name}`, which the audio "
                                   f"backend does not know")
            return
        if kind == "scalar":
            self.calls.setdefault(self.here, set()).add(name)
        self._need(name, kind)

    # -- whole-program conditions -------------------------------------------

    def _check_recursion(self) -> None:
        """No recursion in audio-rate code.

        A step function runs once per sample inside a callback with a
        deadline, so it has to finish in a bounded number of steps that the
        compiler can see.  Structural recursion over a *flat* type would be
        admissible — it unrolls, since a flat type is not recursive — but
        nothing has wanted it, and admitting it means proving the unrolling
        terminates rather than assuming it.
        """
        for name in sorted(self.calls):
            if self.seen.get(name) != "scalar":
                continue
            seen, stack = set(), [name]
            while stack:
                n = stack.pop()
                for m in self.calls.get(n, ()):
                    if m == name:
                        self._error(name, "is recursive, and audio-rate "
                                          "code must finish in a bounded "
                                          "number of steps.  A fold over a "
                                          "list per sample is the usual "
                                          "cause; lift the list to a "
                                          "constant table and index it")
                        stack = []
                        break
                    if m not in seen:
                        seen.add(m)
                        stack.append(m)

    def _check_clocks(self) -> None:
        """Exactly two *rates*, and any number of control channels.

        `sync` lets a graph hold nodes on different clocks, and in an engine
        that is not an obstacle but the **control rate versus audio rate**
        distinction — SuperCollider's `.kr` and `.ar`, arrived at here from
        the other end.

        **Two rates is the ceiling; two channels was never the point.**
        This used to reject a third *clock*, which conflated the two: N
        control channels all tick at the same rate, at the same block
        boundary, and a synth with three knobs needs no third rate.  The
        conflation cost a synth its knobs — one parameter each, or a record
        on one channel, which stage 5 then reset in full whenever a field
        was added.  There is exactly one audio clock (`audio.ges` declares
        it and a program cannot make another), so what is left to check
        here is nothing, and the check that matters is the extractor's: a
        control value must be a scalar.
        """
        self.report.clocks = sorted(set(self.report.clocks))

    # -- reporting ----------------------------------------------------------

    def _error(self, where: str, what: str) -> None:
        self.report.errors.append(f"{where}: {what}")

    def _fail(self, message: str) -> Report:
        self.report.errors.append(message)
        return self.report

    def _type_of(self, name: str):
        _arity, _lam, sig = self.by_name.get(name, (0, None, None))
        if isinstance(sig, Type):
            return sig
        t = self.types.get(name)
        return t if isinstance(t, Type) else None


# ── Small helpers ───────────────────────────────────────────────────────────


def _arrow(t: Type) -> tuple[list, Type]:
    """`A -> B -> C` as `([A, B], C)`."""
    args = []
    while isinstance(t, TFun):
        args.append(t.arg)
        t = t.ret
    return args, t


def _settled(t: Type) -> Type:
    """`t` with its variables standing for whatever the use site supplies.

    A signal definition is inlined at every use, at that use's own type, so
    a variable in its signature is not a hole in the check — it is a name
    for something the caller will name.  Judging such a type means asking
    "flat once it is settled", and `Float` is as good a witness as any: a
    variable can only be settled to a flat type, because the thing that
    settles it is an argument the checker has judged flat on its own terms.

    `Both Gate a` therefore reads as `Both Gate Float` here — flat — and
    `a -> b` reads as `Float -> Float`, which is a function and is not.
    """
    if isinstance(t, TVar):
        return TCon("Float")
    if isinstance(t, TFun):
        return TFun(_settled(t.arg), _settled(t.ret))
    if isinstance(t, TApp):
        return TApp(_settled(t.fn), _settled(t.arg))
    return t


def _signal_elem(t) -> Type | None:
    """`A` where `t` is `Sig A`, else `None`."""
    if (isinstance(t, TApp) and isinstance(t.fn, TCon)
            and t.fn.name == "Sig"):
        return t.arg
    return None


def _monomorphise(t: Type) -> Type:
    """`t` with every type variable replaced by a known-flat stand-in.

    Used to ask "is this constructor's *shape* flat" without knowing what
    its parameters will be.  `Int` is the stand-in because it is the
    simplest flat thing there is; nothing about the answer depends on which
    flat type it is, since a recursive or function-valued field is
    disqualified by its own structure rather than by its arguments.

    What this deliberately does **not** decide is whether the argument at a
    use site is itself flat — `Both Gate (List Int)` looks flat here.  Nothing
    is lost: building that list is refused by this same check, one
    constructor down.
    """
    if isinstance(t, TVar):
        return TCon("Int")
    if isinstance(t, TApp):
        return TApp(_monomorphise(t.fn), _monomorphise(t.arg))
    if isinstance(t, TFun):
        return TFun(_monomorphise(t.arg), _monomorphise(t.ret),
                    None, getattr(t, "mono", False))
    return t


def _spine_ap(e) -> tuple:
    args = []
    while isinstance(e, (EAp, EAnnot)):
        if isinstance(e, EAnnot):
            e = e.expr
            continue
        args.append(e.arg)
        e = e.fn
    args.reverse()
    return e, args


def _strip(e):
    while isinstance(e, EAnnot):
        e = e.expr
    return e


def _is(e, name: str) -> bool:
    e = _strip(e)
    return isinstance(e, EGlobal) and str(e.name) == name


def _name_of(e) -> str:
    e = _strip(e)
    return str(e.name) if isinstance(e, (EGlobal, EVar)) else "a function"


def _instance_head(name: str) -> str | None:
    """`__Num_Float_+__` → `Float`; anything else → `None`."""
    if not (name.startswith("__") and name.endswith("__")):
        return None
    parts = name[2:-2].split("_")
    return parts[1] if len(parts) >= 3 else None


def _describe(e) -> str:
    return {
        ESet: "a set literal", EFix: "`fix`", EFor: "`for`",
        EJoin: "`\\/`", EBox: "a box", EUnbox: "`unbox`",
        ESigCons: "`:::`", ESigHead: "`head`", ETail: "`tail`",
        EDelay: "`delay`", EWait: "`wait`", EWatch: "`watch`",
        ESync: "`sync`", EGFix: "`gfix`", ENever: "`never`",
        EChan: "`chan`", ELambda: "a lambda", ELet: "a `let`",
        ECase: "a `case`", EProj: "a projection",
    }.get(type(e), type(e).__name__)


def _dedup(messages: list[str]) -> list[str]:
    out, seen = [], set()
    for m in messages:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


# ── CLI ─────────────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    import argparse
    from pathlib import Path

    ap = argparse.ArgumentParser(
        prog="python -m gestate.audiograph",
        description="Is this synth in the static signal fragment?")
    ap.add_argument("file")
    args = ap.parse_args(argv)

    report = check(Path(args.file).read_text())
    if report:
        print(f"{args.file}: in the fragment — "
              f"{len(report.signals)} signal node(s), "
              f"{len(report.scalars)} step definition(s), "
              f"{len(report.clocks)} clock(s)")
        return 0
    print(f"{args.file} is not in the static signal fragment:")
    for line in report.errors:
        print(f"  {line}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
