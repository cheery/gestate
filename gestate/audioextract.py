"""Graph extraction — `spec/liveaudio.md` stage 2.

A compiled `Sig Float` in, a flat `Graph` out.  Nothing here decides whether
a program *can* be extracted: `audiograph.check` does that, and extraction
refuses to start on a program it rejects, because every stage of this plan
begins after the previous one verifies.

Two things happen, and only two:

**The signal expression is flattened into nodes.**  `sound = gain 0.6
(lowpass 0.25 raw)` is not three definitions to the engine; it is two nodes,
and `gain`/`lowpass` disappear into them.  Inlining a signal definition is
sound because the fragment made its arguments flat constants — `0.25`
becomes a literal inside the filter's step function, exactly as a
partially-evaluated synth should.

**Step functions are translated into the small IR.**  Calls between scalar
definitions survive as `Call`, into a table of functions on the graph.
Inlining those as well would be legal — the fragment forbids recursion, so
it terminates — and is not done: `kitOut` calling `kickOut`, `snareOut` and
`hatOut` is the structure a reader and a code generator both want to keep.

    python -m gestate.audioextract examples/audio/blip.ges
"""

from __future__ import annotations

from .audio import AUDIO_CLOCK
from .audiograph import (FORMERS, PRIMITIVES, check_analysis, _arrow,
                         _signal_elem, let_inlined)
from .audioir import (SCOPE_LEN, Call, Case, Con, Const, Field, Func,
                      Graph, Let, Node,
                      Prim, Var)
from .expr import (EAnnot, EAp, ECase, EChr, ECon, EGlobal, ELambda, ELet,
                   ENum, EProj, ESigCons, ETuple, EVar, EWait)
from .gmachine import is_tuple_tag, tuple_tag
from .show import show_type
from .types import TCon, Type, free_vars


def _uses(e, name: str) -> bool:
    """Does `e` mention `Var(name)` free?

    The mirror of `_substitute`, and shadowed the same way: a `Let` or a
    `Case` alternative binding the name hides whatever is under it.
    """
    if isinstance(e, Var):
        return e.name == name
    if isinstance(e, (Prim, Call, Con)):
        return any(_uses(a, name) for a in e.args)
    if isinstance(e, Field):
        return _uses(e.base, name)
    if isinstance(e, Case):
        return _uses(e.scrut, name) or any(
            name not in binders and _uses(body, name)
            for _tag, binders, body in e.alts)
    if isinstance(e, Let):
        return _uses(e.value, name) or (e.name != name
                                        and _uses(e.body, name))
    return False


def _substitute(e, name: str, value):
    """`e` with every free `Var(name)` replaced by `value`.

    Binders shadow: a `Let` of the same name, or a `Case` alternative that
    binds it, hides the substitution inside its body.  Getting that wrong
    would fold a constant into a place where the name meant something else,
    which is the one way this pass could change a sound.
    """
    if isinstance(e, Var):
        return value if e.name == name else e
    if isinstance(e, Prim):
        return Prim(e.op, tuple(_substitute(a, name, value) for a in e.args))
    if isinstance(e, Call):
        return Call(e.fn, tuple(_substitute(a, name, value) for a in e.args))
    if isinstance(e, Con):
        return Con(e.tag, tuple(_substitute(a, name, value) for a in e.args))
    if isinstance(e, Field):
        return Field(_substitute(e.base, name, value), e.index)
    if isinstance(e, Case):
        return Case(_substitute(e.scrut, name, value), tuple(
            (tag, binders, body if name in binders
             else _substitute(body, name, value))
            for tag, binders, body in e.alts))
    if isinstance(e, Let):
        return Let(e.name, _substitute(e.value, name, value),
                   e.body if e.name == name
                   else _substitute(e.body, name, value))
    return e


class ExtractError(Exception):
    """The program is in the fragment and something else went wrong.

    Distinct from a fragment rejection on purpose: that is a statement
    about the *program*, and this is one about the extractor.
    """


def extract(source: str, *, rate: int = 22050, entry: str = "sound") -> Graph:
    """Extract the graph of a synth program."""
    from .audio import assemble
    from .pipeline import analyse

    return extract_analysis(analyse(assemble(source, rate)),
                            entry=entry, rate=rate)


def extract_analysis(analysis, *, entry: str = "sound",
                     rate: int = 0) -> Graph:
    report = check_analysis(analysis, entry=entry)
    if not report:
        # **The refusal explains the rule it is applying.**  "Not in
        # the static signal fragment" is the checker's own vocabulary;
        # the sentence a person needs is what the fragment *is* and
        # why being outside it stops the sound.  The itemized reasons
        # below it each name a definition, its position, and who
        # reached it (`audiograph._error` and the `via` provenance).
        raise ExtractError(
            "this program cannot be compiled for the sound card: the "
            "engine plays a fixed graph, so everything `sound` reaches "
            "must be either a signal or a per-sample value, decided "
            "once at compile time (the static signal fragment, "
            "`spec/liveaudio.md`).  What stopped it:\n" + report.message)
    return _Extract(analysis, entry, rate).run()


class _Extract:
    def __init__(self, analysis, entry: str, rate: int):
        self.entry = entry
        self.cons = analysis.program.cons
        self.types = analysis.types
        self.by_name = {str(n): (a, lam, sig)
                        for n, a, lam, sig in analysis.scs}
        self.by_tag = {info.tag: info for info in self.cons.values()}
        self.graph = Graph(rate=rate)
        self.graph.true_tag = self.cons["True"].tag
        self.graph.false_tag = self.cons["False"].tag
        # Every comparison primitive produces one, so every graph needs it.
        self._layout(TCon("Bool"))
        #: Signal definitions already extracted, keyed by name and by the
        #: arguments they were given — the same call twice is one node.
        self.memo: dict = {}
        #: `path/former` → how many of that former the path has produced,
        #: which is what makes an origin unique without being positional.
        self.counter: dict = {}
        #: Clock name → its source node.  One node per clock, however many
        #: times the program writes `mkSig (wait c)`.
        self.sources: dict = {}

    def run(self) -> Graph:
        self.graph.out = self._signal(EGlobal(self.entry), {}, "", "")
        # Folding first: it orphans the `constSig` nodes it consumes, and
        # `_prune` is what drops the functions those nodes were the only
        # callers of.  The other order leaves dead code in the table.
        self._fold_constants()
        self._prune()
        return self.graph

    def _fold_constants(self) -> None:
        """Fold a lifted literal into the step that consumes it.

        **What this is for.**  `0.25 * tone` is not `gain 0.25 tone`:
        `(*)` at `Sig Float` is `mulSig`, which takes two *signals*, so the
        literal is lifted by `Floating (Sig Float)`'s `fromFloat x =
        constSig x` — and `constSig v = mapSig (n => v) ticks` is a node.
        A fixed filter cutoff written that way therefore recomputes `svfG`,
        and so `tan`, every single sample, where the same cutoff passed as
        a `Float` is folded into the step once.

        **Why it is safe, which is the whole question.**  A node's `origin`
        is its identity across a recompile and `migrate` carries state by
        matching them — so removing a node looks like it must lose state.
        It does not, for `map` and `zip`: `audioengine.render_block`
        computes both from `cur` alone, never from `prev`, and neither has
        an `init`.  Their slot in `State.values` is a write-only cache
        within the sample.  Only `scan` and `source` carry anything across
        an instant.

        So the rule this obeys, and it is the whole of it:

            fold into `map` and `zip` steps;
            never remove or re-kind a `scan` or a `source`.

        A `zip` with one constant operand becomes a `map` over the other,
        which is a re-kind of a stateless node and costs nothing;
        `migrate` then fails to match it and falls to `zero(...)`, which is
        overwritten before anything reads it.  The `scan`s keep their
        origins untouched, which is why an oscillator holds its phase and a
        filter its memory across the edit this pass changes the shape of.

        `test_audiolive.py` pins the values through all three engines and
        `test_liveupdate.py` pins the phases across an edit; both were
        written before this existed, which is the only way a test of a
        change is worth anything.
        """
        def constant_of(node) -> object | None:
            """The value this node always produces, if it always produces one.

            **The test is "the step ignores its input", not "the body is a
            literal".**  A step function's only way in is its parameters, so
            a body that never names them yields the same value at every
            instant whatever shape it has.  Checking for `Const` alone
            missed `constSig (Stereo x x)` — whose body is a `Con` of two
            literals — and that is precisely the lifted constant a stereo
            mix produces, so the narrow test folded mono and left stereo
            paying for a node per sample.
            """
            if node.kind != "map" or node.step is None:
                return None
            fn = self.graph.funcs.get(node.step)
            if fn is None or len(fn.params) != 1:
                return None
            return None if _uses(fn.body, fn.params[0]) else fn.body

        changed = True
        while changed:
            changed = False
            for node in self.graph.nodes:
                # `scan` and `source` are never touched — see above.  A
                # `map` is left alone too: folding its only input would
                # leave a node with no inputs, which no kind describes.
                if node.kind != "zip" or node.step is None:
                    continue
                fn = self.graph.funcs.get(node.step)
                if fn is None or len(fn.params) != 2 or len(node.inputs) != 2:
                    continue
                for i in (0, 1):
                    value = constant_of(self.graph.nodes[node.inputs[i]])
                    if value is None:
                        continue
                    # A *new* function rather than an edited one: a step
                    # named for a global definition is shared between every
                    # node that calls it, and narrowing that in place would
                    # fold this node's constant into somebody else's step.
                    name = f"{node.origin}/step#folded"
                    self.graph.funcs[name] = Func(
                        name, (fn.params[1 - i],),
                        _substitute(fn.body, fn.params[i], value))
                    node.kind = "map"
                    node.inputs = (node.inputs[1 - i],)
                    node.step = name
                    changed = True
                    break

        self._drop_unreachable()

    def _drop_unreachable(self) -> None:
        """Renumber, keeping only what the output depends on.

        Folding orphans the `constSig` nodes it consumed.  Ids are indices
        and must stay topological — inputs before consumers — so the kept
        nodes hold their relative order and everything referring to an id
        is rewritten: each node's `inputs`, and the graph's `out`.
        """
        # **Every `source` and every `scan` is a root, reachable or not.**
        # This is the other half of the rule the fold obeys, and leaving it
        # out was a real bug: a voice whose output happens to be constant
        # has its payload channels folded out of the computation, and
        # sweeping them away deleted the *channels a host writes to*.  A
        # control source is interface, not arithmetic — `chan` names the
        # slot a schedule and a knob address — so a bank went from six
        # control sources to one and `test_audiovoices.py` said so.
        #
        # `scan` is a root for the migration reason: dropping one loses
        # state that an edit restoring the reference would have kept.
        # Neither costs anything real — `_prune` still removes the
        # *functions* nothing calls.
        keep: set = set()
        stack = [self.graph.out]
        # A `line` is a root for the same reason a `scan` is, and more so:
        # its buffer is `length` samples of state, and dropping it because
        # nothing reads it *this* recompile loses all of it.
        stack += [n.id for n in self.graph.nodes
                  if n.kind in ("source", "scan", "line", "tap", "loop",
                                "slide", "scope", "spectro")]
        while stack:
            i = stack.pop()
            if i in keep:
                continue
            keep.add(i)
            stack.extend(self.graph.nodes[i].inputs)

        if len(keep) == len(self.graph.nodes):
            return
        renumber = {}
        kept = []
        for node in self.graph.nodes:
            if node.id in keep:
                renumber[node.id] = len(kept)
                kept.append(node)
        for node in kept:
            node.id = renumber[node.id]
            node.inputs = tuple(renumber[i] for i in node.inputs)
        self.graph.out = renumber[self.graph.out]
        self.graph.nodes = kept

    def _prune(self) -> None:
        """Drop functions no node can reach.

        Folding a nullary definition to a constant translates its body on
        the way past, and translating registers whatever that body called —
        so `sampleRate` and `toFloat` end up in the table with the constant
        `22050` already inlined at every use.  A graph carrying functions
        nothing calls would hand stage 4 dead code to generate, and would
        make two graphs differ over definitions neither of them uses, which
        is exactly what stage 5 compares.
        """
        live: set[str] = set()
        stack = [n.step for n in self.graph.nodes if n.step]
        while stack:
            name = stack.pop()
            if name in live or name not in self.graph.funcs:
                continue
            live.add(name)
            stack.extend(_calls(self.graph.funcs[name].body))
        self.graph.funcs = {k: v for k, v in self.graph.funcs.items()
                            if k in live}

    # -- signal expressions -> nodes ----------------------------------------

    def _signal(self, e, env: dict, path: str, elem: str) -> int:
        """`elem` is the element type of the signal being built.

        Threaded down rather than reconstructed: a `scan` knows its own
        state type from its initial value, but a `map` does not know what
        its step returns without the step's signature — and the definition
        it sits in (`gain : Float -> Sig Float -> Sig Float`) says so.
        """
        e = _strip(e)

        if isinstance(e, ESigCons):
            return self._source(e, env, path, elem)

        if isinstance(e, EVar):
            what = env.get(e.name)
            if what is None or what[0] != "sig":
                raise ExtractError(f"{path}: `{e.name}` is not a signal here")
            return what[1]

        if isinstance(e, EGlobal):
            return self._inline(str(e.name), [], env, path, elem)

        if isinstance(e, EAp):
            head, args = _spine(e)
            if isinstance(head, EGlobal):
                name = str(head.name)
                if name in FORMERS:
                    return self._former(name, args, env, path, elem)
                return self._inline(name, args, env, path, elem)

        if isinstance(e, ELet):
            # Substituted away, as the checker substituted it — a `let`
            # over signals is a name for a subexpression and nothing else.
            if e.is_rec:
                raise ExtractError(f"{path}: a recursive `let` reached "
                                   f"extraction at signal level")
            return self._signal(let_inlined(e), env, path, elem)

        raise ExtractError(f"{path}: not a signal expression: {e!r}")

    def _source(self, e, env: dict, path: str, elem: str) -> int:
        """`v ::: mkSig (wait c)` — the clock, and the value it holds at t=0.

        **Two clocks, partitioned by name.**  `audio.ges` declares `clock`
        and the renderer advances it once per sample; any *other* channel a
        program declares is control rate — updated once per block, held
        constant in between.  By name rather than by channel id, because
        ids are handed out in evaluation order and are not the order
        anything was written in (`fixme.md` F90, F91).

        A third clock has no rate to be run at, and the fragment refuses it
        before this point.
        """
        tail = _strip(e.tail)
        if not (isinstance(tail, EAp) and _is(tail.fn, "mkSig")
                and isinstance(_strip(tail.arg), EWait)):
            raise ExtractError(f"{path}: a signal built by hand reached "
                               f"extraction, which the check should have "
                               f"refused")
        chan = _strip(_strip(tail.arg).chan)
        clock = str(chan.name) if isinstance(chan, EGlobal) else path
        if clock in self.sources:
            return self.sources[clock]          # one node per clock
        rate = "audio" if clock == AUDIO_CLOCK else "control"
        if rate == "audio" and any(n.clock == "audio" for n in self.graph.nodes
                                   if n.kind == "source"):
            raise ExtractError(
                f"this graph has two audio-rate clocks, and the engine has "
                f"one: `{AUDIO_CLOCK}` advances every sample")

        init = self._constant(e.value, env, path)
        type_ = self._value_type(init)
        if rate == "control" and self.graph.words(type_) != 1:
            # A control value is one 8-byte slot of the control buffer, so a
            # channel carrying a constructor with fields has nowhere to go.
            # It used to extract and then die inside the engine as `case on
            # a non-constructor`, because the host supplied a scalar into a
            # slot the graph read as a `Voice`.
            #
            # Nothing is lost by refusing it: several parameters are several
            # *channels* now, which is better than one record anyway —
            # adding a field changes the type, and stage 5 migrates by
            # shape, so a fourth knob would reset the other three.
            raise ExtractError(
                f"the control channel `{clock}` carries `{type_}`, which is "
                f"not a scalar: a control value is one slot, and `{type_}` "
                f"is {self.graph.words(type_)}.  Several parameters are "
                f"several channels — each keeps its own value across an "
                f"edit, which fields of one record would not")
        node = self._add(Node(id=0, kind="source", init=init,
                              type_=type_, clock=rate, chan=clock),
                         path, "source")
        self.sources[clock] = node
        return node

    def _former(self, name: str, args: list, env: dict, path: str,
                elem: str) -> int:
        kind = FORMERS[name]
        if kind == "source":
            raise ExtractError(f"{path}: a bare `mkSig` is not a node")

        # **A step function's type says what its signal's elements are.**
        # `zipSig f l r` with `f : a -> b -> c` means `l : Sig a`,
        # `r : Sig b` and the node itself `Sig c` — so a former nested
        # directly inside another can be typed from the step rather than
        # from what the parent threads down, which is nothing
        # (`fixme.md` F94).
        # The step is the first argument of every former **except a
        # `line`**, whose length comes first — so ask the shape rather than
        # assuming a position.  Reading the length's arrow instead gave "the
        # element type could not be determined", which is a true sentence
        # about the wrong expression.
        # The step is the first argument of every former **except** a `line`,
        # whose length comes first, and a `tap`, which has none at all — so
        # ask the shape rather than assuming a position.
        params, result = ((None, None) if kind == "tap" else
                          self._step_arrow(
                              args[1 if kind in ("line", "loop", "slide")
                                   else 0]))

        def of(i: int) -> str:                                    # noqa: D401
            """The `i`th parameter's layout, when it has one.

            A step inside a *polymorphic* signal definition is checked at
            that definition's own type, variables and all — a step over
            `Both Gate a` has a variable in it — and a variable has no
            layout.  The
            use site settles it, so saying nothing here is right and asking
            for a layout was "no layout for a".
            """
            if params is None or i >= len(params) or free_vars(params[i]):
                return ""
            return self._layout(params[i])

        scope_label = None
        if kind == "map":
            step_e, sig_e = args
            inputs = [self._signal(sig_e, env, path, of(0))]
            init, type_ = None, elem
        elif kind == "scan":
            step_e, init_e, sig_e = args
            # `step : b -> a -> b`, so the *second* parameter is the input's
            # element type; the first is the state, which `init` gives.
            inputs = [self._signal(sig_e, env, path, of(1))]
            init = self._constant(init_e, env, path)
            # A `scan`'s element type *is* the type of its state, and its
            # initial value is that state — so this one needs nothing
            # threaded to it.
            type_ = self._value_type(init)
        elif kind == "tap":
            # `tap n pos s` — no step at all: the read is interpolation and
            # the write is the input, so there is nothing to name.  The
            # element type is the input's, which is the whole point of a
            # delay line.
            length_e, pos_e, sig_e = args
            length = self._length(length_e, env, path)
            inputs = [self._signal(sig_e, env, path, elem),
                      self._signal(pos_e, env, path, "Float")]
            init, type_ = None, elem or "Float"
        elif kind == "line":
            # `feedback n f s` — `step : b -> a -> b` as a `scan`'s is, so
            # the input's element type is the second parameter and the
            # node's own is the first.  What differs is the *length*, which
            # has to be a number before the program runs: the slot is that
            # many words wide and the engine has no allocator.
            length_e, step_e, sig_e = args
            inputs = [self._signal(sig_e, env, path, of(1))]
            length = self._length(length_e, env, path)
            init, type_ = None, of(0)
        elif kind == "loop":
            # `loop n f z s` — `step : b -> b -> a -> b`, so the input's
            # element type is the *third* parameter, both of the first two
            # being the state.  The node's own element type is that state,
            # and `init` gives it, exactly as a `scan`'s does — which is why
            # this reads the initial value rather than the step's arrow.
            length_e, step_e, init_e, sig_e = args
            length = self._length(length_e, env, path)
            inputs = [self._signal(sig_e, env, path, of(2))]
            init = self._constant(init_e, env, path)
            type_ = self._value_type(init)
        elif kind in ("scope", "spectro"):
            # `scope label s` — identity on the sound, a ring write on
            # the way past (`spec/scope.md`).  No step: there is
            # nothing to compute, only a window to keep.  The label is
            # an assembly-time fact like a `line`'s length, and the
            # length is the spec's fixed window.
            label_e, sig_e = args
            label = self._label_text(label_e, env, path)
            if not isinstance(label, str) or not label:
                raise ExtractError(
                    f"{path}: a scope's label has to be a piece of text "
                    f"it can be asked for by — `scope \"post\" s`")
            inputs = [self._signal(sig_e, env, path, "Float")]
            init, type_ = None, "Float"
            length = SCOPE_LEN
            scope_label = label
        elif kind == "slide":
            # `slide n f pos s` — the step folds the interpolated read with
            # the input, `step : Float -> a -> Float`, and the ring holds
            # the node's own output, so the element type is the step's
            # first parameter (always `Float` — interpolation is what the
            # node *is*, and only floats blend).
            length_e, step_e, pos_e, sig_e = args
            length = self._length(length_e, env, path)
            if length < 2:
                raise ExtractError(
                    f"{path}: a `slide` of {length} has no room to move — "
                    f"its position is clamped to 1 .. n-1, so the shortest "
                    f"line that means anything is 2")
            inputs = [self._signal(sig_e, env, path, of(1)),
                      self._signal(pos_e, env, path, "Float")]
            init, type_ = None, "Float"
        else:                                             # zip
            step_e, left_e, right_e = args
            inputs = [self._signal(left_e, env, path, of(0)),
                      self._signal(right_e, env, path, of(1))]
            init, type_ = None, elem

        if not type_ and result is not None and not free_vars(result):
            type_ = self._layout(result)
        if not type_:
            raise ExtractError(
                f"{path}: the element type of this `{name}` could not be "
                f"determined.  It is nested directly inside another "
                f"combinator and its step function is a lambda, so nothing "
                f"names the type — give the step a signature, or name the "
                f"inner signal with a definition of its own")

        want = 1 if kind == "map" else 3 if kind == "loop" else 2
        origin = self._origin(path, kind)
        step = (None if kind in ("tap", "scope", "spectro")
                else self._step(step_e, env, origin, want))
        return self._add(Node(id=0, kind=kind, inputs=tuple(inputs),
                              step=step, init=init, type_=type_,
                              length=(length if kind in ("line", "tap",
                                                         "loop", "slide",
                                                         "scope",
                                                         "spectro")
                                      else 0),
                              chan=(scope_label
                                    if kind in ("scope", "spectro")
                                    else None)),
                         path, kind, origin=origin)

    def _label_text(self, e, env: dict, where: str):
        """A `String` literal's text, read off the expression itself.

        **Not through `_constant`**: the small IR has no characters,
        because the engine never holds text — a scope's label is
        consumed here, before any IR exists, and lives on the node
        (`spec/scope.md`).  A string literal is a cons chain of
        `EChr`s; anything else refuses with the spelling to use.
        """
        out = []
        while True:
            while isinstance(e, EAnnot):
                e = e.expr
            if isinstance(e, ECon) and len(e.args) == 0:
                return "".join(out)
            if isinstance(e, ECon) and len(e.args) == 2:
                head, e = e.args
                while isinstance(head, EAnnot):
                    head = head.expr
                if isinstance(head, EChr):
                    out.append(chr(head.n))
                    continue
            return None

    def _length(self, e, env: dict, where: str) -> int:
        """A delay line's length, in samples — **a constant, or nothing.**

        `feedback (seconds 0.25) …` is fine: `seconds` folds to an integer
        before the graph exists.  A length that varies is not, and the
        refusal says why rather than failing later with a shape the engine
        cannot lay out.
        """
        value = self._constant(e, env, where)
        if not isinstance(value, int) or isinstance(value, bool):
            raise ExtractError(
                f"{where}: a delay line's length has to be a whole number "
                f"of samples known before the program runs, and this is "
                f"{value!r}")
        if value < 1:
            raise ExtractError(
                f"{where}: a delay line of {value} samples reaches back to "
                f"nothing; `feedback 1` is the shortest there is, and it "
                f"is what `scan` already does")
        return value

    def _step_arrow(self, step_e) -> tuple:
        """`(parameter types, result type)` of a step function, if known.

        Known when the step is a *named* definition, which is where its
        type is written down — and now also when it is a **lambda**, which
        carries the arrow it was checked against (`ELambda.type_`).

        The second used to be unknown, and it was not unknowable: inference
        had the type and dropped it.  What that cost was a rule authors had
        to learn and work around — a former nested directly inside another
        with a lambda step could not be typed, so the inner signal had to
        be given a name whose only purpose was to carry one.  Every such
        name is plumbing in code whose subject is a sound
        (`spec/frp_lesson.md`).
        """
        e = _strip(step_e)
        if isinstance(e, ELambda):
            t = e.type_
        elif isinstance(e, EGlobal):
            t = self._type_of(str(e.name))
        else:
            return ([], None)
        if not isinstance(t, Type):
            return ([], None)
        return _arrow(t)

    def _inline(self, name: str, args: list, env: dict, path: str,
                elem: str = "") -> int:
        """A signal definition disappears into the nodes it builds.

        **`elem` is what makes a polymorphic one work.**  A signal
        definition is inlined at every use, so its type variables are
        resolved by the time anything is built — `mkKnob : a -> Sig a` used
        as `level : Sig Float` produces a source of `Float`, and there is
        no `a` left anywhere in the graph.  What the extractor cannot do is
        read that off the *definition's* signature, which still says `a`;
        the caller knows, and `_signal` has threaded it down since
        `fixme.md` F94 taught the same lesson about nested formers.

        So a ground element type from the signature wins — it is the exact
        answer — and a polymorphic one falls back to what the use site
        says.
        """
        arity, lam, _sig = self.by_name.get(name, (None, None, None))
        if lam is None:
            raise ExtractError(f"{path}: `{name}` has no definition")

        t = self._type_of(name)
        params, _result = _arrow(t) if t is not None else ([], None)
        inner: dict = {}
        key: list = [name]
        for param_name, param_t, arg in zip(lam.params, params, args):
            param_elem = _signal_elem(param_t)
            if param_elem is not None:
                # **A polymorphic *parameter* is the caller's to settle,
                # exactly as a polymorphic result is.**  The signature of
                # `soften : Sig (Both Gate a) -> Sig a` says `Both Gate a`,
                # which has no layout and never will; the argument being
                # passed is a signal of some concrete thing, and building
                # it is what says which.  Asking for the signature's layout
                # here failed with "no layout for a" — the same lesson as
                # `inner_elem` below, one parameter to the left.
                hint = ("" if free_vars(param_elem)
                        else self._layout(param_elem))
                node = self._signal(arg, env, path, hint)
                inner[param_name] = ("sig", node)
                key.append(("sig", node))
            else:
                value = self._translate(arg, env, path)
                inner[param_name] = ("val", value)
                key.append(("val", repr(value)))

        memo_key = tuple(key)
        if memo_key in self.memo:
            return self.memo[memo_key]
        _params, result = _arrow(t) if t is not None else ([], None)
        inner_elem = _signal_elem(result) if result is not None else None
        if inner_elem is not None and free_vars(inner_elem):
            inner_elem = None               # polymorphic: the caller knows
        node = self._signal(lam.body, inner, _join(path, name),
                            self._layout(inner_elem) if inner_elem else elem)
        self.memo[memo_key] = node
        return node

    def _add(self, node: Node, path: str, kind: str, origin=None) -> int:
        node.id = len(self.graph.nodes)
        node.origin = origin or self._origin(path, kind)
        self.graph.nodes.append(node)
        return node.id

    def _origin(self, path: str, kind: str) -> str:
        """Stable identity: which definitions, which former, which one.

        Not a source position and not an index into the node list.  A
        position moves when a line is added above it and an index moves
        when a node is inserted anywhere earlier, and either would reset
        state on an edit that changed nothing about this node.
        """
        base = f"{path or self.entry}/{kind}"
        n = self.counter.get(base, 0)
        self.counter[base] = n + 1
        return f"{base}#{n}"

    def _value_type(self, v) -> str:
        """The type of a constant, named as the source names it.

        A constructor value carries its tag, and a tag names a constructor,
        and a constructor's own type names the data type — so `Voice 0.0 0`
        is reported as `Voice` rather than as "a tuple of two things".

        A tuple has no `ConInfo` to look up, so its name is built from its
        components — the same `(Float, Float)` `show_type` prints and
        `_layout` keys on, so the two agree without either asking.
        """
        if isinstance(v, tuple):
            info = self.by_tag.get(v[0])
            if info is not None:
                _fields, result = _arrow(info.type_)
                return self._layout(result)
            if is_tuple_tag(v[0]):
                return "(" + ", ".join(self._value_type(f)
                                       for f in v[1]) + ")"
            return f"#{v[0]}"
        return {int: "Int", float: "Float"}.get(type(v), type(v).__name__)

    # -- state layouts ------------------------------------------------------

    def _layout(self, t) -> str:
        """The type's name, recording what a value of it is made of.

        A name is enough to *read* a graph and not enough to emit a struct
        for one, which is what stage 4 discovered.  Recorded here because
        this is the only place that still has the compiler's types; by the
        time a code generator has the graph, `Voice` is a string.
        """
        from .gmachine import tuple_tag
        from .types import TCon, TVar, _apply_subst_map, _spine, tuple_parts

        name = show_type(t)
        if name in ("Int", "Float") or name in self.graph.layouts:
            return name

        # **A tuple is laid out exactly like a one-constructor record**, and
        # this is the whole of what `fixme.md` F95 was missing.  It has no
        # `ConInfo` — nobody declared it — but it needs none: its arity is
        # its type's, its tag is `tuple_tag`, and its fields are the
        # components.  `(Float, Float)` is the name, which is what
        # `show_type` already prints and what the generated struct is
        # called; the parentheses are safe because `audiollvm._ident`
        # quotes.
        parts = tuple_parts(t)
        if parts is not None:
            fields: list = []
            self.graph.layouts[name] = [
                {"tag": tuple_tag(len(parts)), "name": name, "fields": fields}]
            fields.extend(self._layout(p) for p in parts)
            return name

        head, args = _spine(t)
        if not isinstance(head, TCon):
            raise ExtractError(f"no layout for {name}")

        constructors: list = []
        self.graph.layouts[name] = constructors      # before recursing
        for info in self.cons.values():
            fields, result = _arrow(info.type_)
            rhead, params = _spine(result)
            if not (isinstance(rhead, TCon) and rhead.name == head.name):
                continue
            subst = {p.id: a for p, a in zip(params, args)
                     if isinstance(p, TVar)}
            constructors.append({
                "tag": info.tag, "name": info.name,
                "fields": [self._layout(_apply_subst_map(f, subst))
                           for f in fields],
            })
        constructors.sort(key=lambda c: c["tag"])
        if not constructors:
            del self.graph.layouts[name]
            raise ExtractError(f"`{name}` is not a data type gestate knows")
        return name

    # -- step functions -----------------------------------------------------

    def _step(self, e, env: dict, origin: str, want: int) -> str:
        """Translate a step function and put it in the graph's table."""
        e = _strip(e)
        if isinstance(e, EGlobal):
            return self._func(str(e.name))
        if isinstance(e, ELambda):
            if len(e.params) != want:
                raise ExtractError(
                    f"{origin}: its step function takes {len(e.params)} "
                    f"argument(s), and this node calls it with {want}")
            name = f"{origin}/step"
            inner = dict(env)
            for p in e.params:
                inner[p] = ("val", Var(p))
            self.graph.funcs[name] = Func(name, tuple(e.params), Const(None))
            self.graph.funcs[name] = Func(
                name, tuple(e.params), self._translate(e.body, inner, name))
            return name
        raise ExtractError(f"{origin}: a step function that is not a "
                           f"definition or a lambda reached extraction")

    def _func(self, name: str) -> str:
        """Translate a scalar definition once, and remember it."""
        if name in self.graph.funcs:
            return name
        arity, lam, _sig = self.by_name.get(name, (None, None, None))
        if lam is None:
            raise ExtractError(f"`{name}` has no definition")
        env = {p: ("val", Var(p)) for p in lam.params}
        # Registered before translating: the fragment forbids recursion, so
        # this cannot be needed — and if a cycle ever does appear, it
        # terminates with a wrong answer rather than a stack overflow, which
        # is worth the one line.
        self.graph.funcs[name] = Func(name, tuple(lam.params), Const(None))
        self.graph.funcs[name] = Func(name, tuple(lam.params),
                                      self._translate(lam.body, env, name))
        return name

    # -- scalar expressions -> IR -------------------------------------------

    def _translate(self, e, env: dict, where: str):
        e = _strip(e)

        if isinstance(e, ENum):
            return Const(e.n)

        if isinstance(e, EVar):
            what = env.get(e.name)
            if what is None:
                raise ExtractError(f"{where}: `{e.name}` is not in scope")
            if what[0] != "val":
                raise ExtractError(f"{where}: `{e.name}` is a signal, used "
                                   f"as a value")
            return what[1]

        if isinstance(e, EGlobal):
            return self._global(str(e.name), [], env, where)

        if isinstance(e, ECon):
            info = self.by_tag.get(e.tag)
            if info is not None:
                _fields, result = _arrow(info.type_)
                if not free_vars(result):
                    self._layout(result)
            return Con(e.tag, tuple(self._translate(a, env, where)
                                    for a in e.args))

        if isinstance(e, ETuple):
            # The same `Con` a record builds, which is the point: a tuple is
            # a constructor whose name nobody wrote, and the IR below here
            # cannot tell the two apart.
            return Con(tuple_tag(len(e.args)),
                       tuple(self._translate(a, env, where)
                             for a in e.args))

        if isinstance(e, ECase):
            scrut = self._translate(e.scrut, env, where)
            alts = []
            for alt in e.alts:
                inner = dict(env)
                for n in alt.names:
                    inner[n] = ("val", Var(n))
                alts.append((alt.tag, tuple(alt.names),
                             self._translate(alt.body, inner, where)))
            return Case(scrut, tuple(alts))

        if isinstance(e, ELet):
            if e.is_rec:
                raise ExtractError(f"{where}: a recursive `let` reached "
                                   f"extraction")
            inner = dict(env)
            body_of = []
            for name, value in e.defs:
                body_of.append((name, self._translate(value, inner, where)))
                inner[name] = ("val", Var(name))
            out = self._translate(e.body, inner, where)
            for name, value in reversed(body_of):
                out = Let(name, value, out)
            return out

        if isinstance(e, EAp):
            head, args = _spine(e)
            if isinstance(head, EGlobal):
                return self._global(str(head.name), args, env, where)
            if isinstance(head, EProj) and len(args) == 1:
                return Field(self._translate(args[0], env, where), head.i)
            raise ExtractError(f"{where}: cannot apply {head!r}")

        raise ExtractError(f"{where}: no IR for {type(e).__name__}")

    def _global(self, name: str, args: list, env: dict, where: str):
        ir_args = tuple(self._translate(a, env, where) for a in args)

        if name in PRIMITIVES:
            return Prim(name, ir_args)

        arity, lam, _sig = self.by_name.get(name, (None, None, None))
        if lam is None:
            raise ExtractError(f"{where}: `{name}` has no definition")

        if arity == 0 and not args:
            # A nullary definition is a constant of the program — the sample
            # rate, a tempo, a table of note numbers.  Folded here, so the
            # graph does not depend on the prelude that produced it.
            return Const(self._value(self._func_body(name), where))

        if len(ir_args) != arity:
            raise ExtractError(
                f"{where}: `{name}` takes {arity} argument(s) and is applied "
                f"to {len(ir_args)} — a partial application is a closure, "
                f"which the fragment does not admit")
        return Call(self._func(name), ir_args)

    def _func_body(self, name: str):
        self._func(name)
        return self.graph.funcs[name].body

    # -- constants ----------------------------------------------------------

    def _constant(self, e, env: dict, where: str):
        """A `scan`'s initial state, evaluated now rather than per sample."""
        return self._value(self._translate(e, env, where), where)

    def _value(self, ir, where: str):
        from .audioengine import evaluate

        try:
            return evaluate(ir, {}, self.graph)
        except Exception as exc:                        # noqa: BLE001
            raise ExtractError(
                f"{where}: this should be a constant and is not: {exc}"
            ) from exc

    def _type_of(self, name: str):
        _arity, _lam, sig = self.by_name.get(name, (0, None, None))
        if isinstance(sig, Type):
            return sig
        t = self.types.get(name)
        return t if isinstance(t, Type) else None


# ── Helpers ─────────────────────────────────────────────────────────────────


def _calls(ir) -> list:
    """Every function an IR expression calls, at any depth."""
    out, stack = [], [ir]
    while stack:
        e = stack.pop()
        if isinstance(e, Call):
            out.append(e.fn)
            stack.extend(e.args)
        elif isinstance(e, (Prim, Con)):
            stack.extend(e.args)
        elif isinstance(e, Field):
            stack.append(e.base)
        elif isinstance(e, Let):
            stack.extend((e.value, e.body))
        elif isinstance(e, Case):
            stack.append(e.scrut)
            stack.extend(body for _t, _b, body in e.alts)
    return out


def _strip(e):
    while isinstance(e, EAnnot):
        e = e.expr
    return e


def _spine(e) -> tuple:
    args = []
    while True:
        e = _strip(e)
        if not isinstance(e, EAp):
            break
        args.append(e.arg)
        e = e.fn
    args.reverse()
    return _strip(e), args


def _is(e, name: str) -> bool:
    e = _strip(e)
    return isinstance(e, EGlobal) and str(e.name) == name


def _join(path: str, name: str) -> str:
    return f"{path}/{name}" if path else name


# ── CLI ─────────────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    """Retired — a stage-7 debugging window the tools outgrew."""
    import sys

    print("gestate: the `gestate.audioextract` CLI is retired — "
          "`python -m gestate.typecheck <file> --audio` answers what is "
          "in scope,\nand the graph itself is a library call "
          "(`audioextract.extract`).", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
