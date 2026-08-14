"""The read-only score box — `spec/scorebox.md`.

A `notes <expr>` line asks for a roll of the score expression beside
it.  This module is the box's whole mind: the *descent* walks the
expression's own parse tree and rebuilds it with every leaf tagged —
`leaf` becomes `(leaf >>= (x => '((k, x))))`, a pure bind that moves
no seeds — so one `spreadTo` of the sown rebuild yields every event
carrying the id of the source span it came from.  The picture is then
a generated substrate program the window walks like any canvas box,
with one touch region per leaf whose channel name the editor maps
back to a line.

Nothing here threads through the engines: provenance lives in the
view, and the events the instrument plays come from the same library
walk (`sowScore`, the score algebra) the performer uses.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

__all__ = ["asks", "build_roll", "roll_program", "Roll", "RollError"]


class RollError(Exception):
    """The box could not be built, in a sentence for the margin."""


#: The ask, `_sinks`'s manners: top level, a trailing comment is not
#: an expression.  `audiovoices._sinks` rewrites the line to a comment
#: with the same scan, and the two must agree ask for ask.
_ASK = re.compile(r"^notes\s+(\S.*)$")

#: The walk's patience — the sauna lesson (`spec/scorebox.md` §"The
#: hazards, named now"): a zero-width `cycle` runs out of fuel, not
#: time, and the box draws its complaint instead of hanging a window.
FUEL = 200_000

#: How much score the box shows, in beats: enough for every finite
#: piece in the tree, and the cut that makes an endless one welcome.
WINDOW_BEATS = 256

#: Leaves beyond this are collapsed into the last one: a descent that
#: found a hundred spans is drawing a picture nobody can click — and
#: each one is a nested `Over` in the generated picture, which is a
#: parenthesis the parser has to hold open.
MAX_LEAVES = 48

TICKS_PER_BEAT = 96

#: The chancy sniff — `audioperform`'s own precedent for deciding
#: whether a take needs a seed said.
_CHANCY = re.compile(r"\b(draw|hear|chance|roll|sow)\b")

#: A `>>=` right-hand side that only assigns — dropped by the descent,
#: read for the bank's name (`spec/scorebox.md` §"Provenance").  The
#: descent reads the *expanded* text, where `voices.piano` has already
#: been mangled to `voicesPiano` — the second alternative.
_ASSIGN = re.compile(r"^(?:voices\.(\w+)|voices([A-Z]\w*)"
                     r"|prog\s+\S+|percussion)$")


def _bank_of(m) -> str | None:
    name = m.group(1) or m.group(2)
    return (name[0].lower() + name[1:]) if name else None


#: An `=` that is not `=>`, `==`, `>=`, `<=`, `/=` or `!=` — which is
#: to say, the one that makes a line a *declaration*.
_DECLARES = re.compile(r"(?<![=/<>!])=(?![>=])")


def ask_of(line: str) -> str | None:
    """The expression a `notes` line asks for, or `None`.

    **A program is entitled to its own `notes`**, and one did:
    `test_audioeditor.py`'s fixture declares `notes = …` and the
    first rewrite ate it, taking a global the program went on to use.
    So an ask is a `notes` line that is not a declaration — no
    top-level `=`, no signature's `:` — nor a comment.  The one rule,
    read by the scan here and by the rewrite in `audiovoices._sinks`,
    because two spellings of "what is an ask" is how they drift.
    """
    m = _ASK.match(line)
    if m is None:
        return None
    rest = m.group(1)
    if rest.startswith("#") or rest.startswith(":") \
            or _DECLARES.search(rest):
        return None
    return rest


def asks(text: str) -> list:
    """Every `notes <expr>` ask: `(line_1based, expr_text)`."""
    out = []
    for i, line in enumerate(text.splitlines(), start=1):
        expr = ask_of(line)
        if expr is not None:
            out.append((i, expr))
    return out


@dataclass
class Leaf:
    """One provenance region: the finest span written in the text."""
    line: int                     # 1-based line of the span's start
    bank: str | None
    chancy: bool


@dataclass
class Roll:
    """A built take: events tagged with the leaf that wrote them."""
    events: list                  # (onset, offset, leaf, key, vel) in ticks
    leaves: list                  # Leaf per id
    cut: bool                     # the fuel ran out — say so, don't lie
    chancy: bool                  # any take ink: the label owes a seed
    seed: int


# ── The descent ─────────────────────────────────────────────────────────────


class _Descent:
    """Syntactic descent with a tagged rebuild (`spec/scorebox.md`).

    Descends only what is *literally* score syntax — `++`, `||`, `|*`,
    `|/`, `long`, `at`, `cycle`, `sow`, and a `>>=` whose right side
    only assigns — plus a bare name declared in the file, which is its
    definition worn openly.  Everything else is opaque: laid out whole
    by the library, all of its events wearing its span.
    """

    def __init__(self, decls: dict, copies: frozenset = frozenset()):
        #: Declarations that assign to a bank, and so are reached
        #: through an unassigned twin instead.
        self.copies = copies
        #: Twin → the bank its assignment named, so a leaf that only
        #: *calls* the twin still knows whose colour it is.
        self.twin_banks: dict = {}
        #: How the lines being walked map to the author's file.  The
        #: ask's expression parses inside a one-line wrapper, so while
        #: its nodes are walked every leaf wears the ask's own line;
        #: entering a named definition switches back to the file's.
        self._bias = 0
        self._decls = decls           # name -> VSCEqn (single, param-less)
        self._visiting: set = set()
        self._defs: dict = {}         # name -> rebuilt hidden text
        self.leaves: list = []

    def rebuild_ask(self, body, ask_line: int) -> str:
        self._bias = ask_line - 1
        try:
            return self.rebuild(body)
        finally:
            self._bias = 0

    def _src(self, v) -> str:
        """The node, printed back — **not sliced out of the source.**

        Slicing looked obvious and is a trap: a `VPrefix` carries a
        defaulted span, so `'(H 60 100)` sliced from column zero and
        swallowed the file down to itself.  The formatter is the one
        thing here that already knows how to turn a parsed node into
        text, and it is idempotent, so what it prints re-parses to
        the same tree — which is all a rebuild needs.
        """
        from .fmt.format import Formatter

        return Formatter()._fmt_val(v)

    def _line(self, v) -> int:
        """Where a node was written, by its **atoms**.

        Only `VWord`, `VConId`, `VNum` and `VStr` carry positions that
        survive fixity resolution; a phrase's own span may be
        defaulted.  The first line any of its atoms sits on is where
        a reader would say the thing is written, and is what a jump
        should land on.
        """
        from .syntax import VConId, VNum, VStr, VWord

        best = []

        def visit(node, depth=0):
            if depth > 64:
                return
            if isinstance(node, (VWord, VConId, VNum, VStr)):
                span = getattr(node, "span", None)
                if span is not None:
                    best.append(span.start.line)
            for field in ("left", "right", "fn", "arg", "body", "scrut",
                          "atoms", "alts", "params", "bindings"):
                child = getattr(node, field, None)
                if isinstance(child, list):
                    for item in child:
                        if hasattr(item, "span"):
                            visit(item, depth + 1)
                elif child is not None and hasattr(child, "span"):
                    visit(child, depth + 1)

        visit(v)
        return (min(best) if best else 0) + 1 + self._bias

    def _leaf(self, v, bank) -> str:
        # An assignment buried inside the leaf is undone here, and the
        # bank it named is the leaf's own when the descent above never
        # met one.
        inner: list = []
        v = _unassign(v, inner, self.copies)
        text = self._src(v)
        if inner:
            bank = inner[0]
        elif bank is None:
            # The assignment may sit inside a twin this leaf calls —
            # undertow's chimes are `barOf`'s, two calls down.
            for name in re.findall(r"__nbf_(\w+?)__", text):
                said = self.twin_banks.get(name)
                if said:
                    bank = said
                    break
        k = len(self.leaves)
        if k >= MAX_LEAVES:
            # Collapsed into the last region rather than dropped: the
            # note still draws and still jumps somewhere true, just
            # not as finely as a smaller piece would.
            k = MAX_LEAVES - 1
            return f"(tagAll {k} ({text}))"
        self.leaves.append(Leaf(line=self._line(v), bank=bank,
                                chancy=bool(_CHANCY.search(text))))
        return f"(tagAll {k} ({text}))"

    def rebuild(self, v, bank=None) -> str:
        from .syntax import VApp, VInfix, VPrefix, VWord

        if isinstance(v, VInfix):
            if v.op in ("++", "||"):
                return (f"({self.rebuild(v.left, bank)} {v.op} "
                        f"{self.rebuild(v.right, bank)})")
            if v.op in ("|*", "|/"):
                return (f"({self.rebuild(v.left, bank)} {v.op} "
                        f"({self._src(v.right)}))")
            if v.op == ">>=":
                right = self._src(v.right).strip()
                m = _ASSIGN.match(right)
                if m:
                    return self.rebuild(v.left, _bank_of(m) or bank)
                return self._leaf(v, bank)
            return self._leaf(v, bank)
        if isinstance(v, VApp):
            head, args = v, []
            while isinstance(head, VApp):
                args.insert(0, head.arg)
                head = head.fn
            if isinstance(head, VWord) and head.value in ("long", "at",
                                                          "sow") \
                    and len(args) == 2:
                return (f"({head.value} ({self._src(args[0])}) "
                        f"{self.rebuild(args[1], bank)})")
            if isinstance(head, VWord) and head.value == "cycle" \
                    and len(args) == 1:
                return f"(cycle {self.rebuild(args[0], bank)})"
            return self._leaf(v, bank)
        if isinstance(v, VWord):
            name = v.value
            eqn = self._decls.get(name)
            if eqn is None or name in self._visiting:
                # A library name, a parameter, or a recursive mention:
                # opaque, wearing the reference's own span.
                return self._leaf(v, bank)
            if name not in self._defs:
                self._visiting.add(name)
                self._defs[name] = "PENDING"
                # A definition's own lines are the file's, whatever
                # text the reference to it was found in.
                saved = self._bias
                self._bias = 0
                try:
                    self._defs[name] = self.rebuild(eqn.body, bank)
                finally:
                    self._bias = saved
                self._visiting.discard(name)
            return f"__nbd_{name}__"
        return self._leaf(v, bank)

    def twin_defs(self, assigning: dict) -> str:
        """The unassigned twin of every declaration that assigns.

        `voices.chimes (Key k 88)` becomes `' (Key k 88)` — the same
        music one step before it was committed to a bank — and a
        mention of another twin names the twin.  `at 0` anchors the
        param-less ones for the reason `hidden_defs` gives.
        """
        from .fmt.format import Formatter

        out, bodies = [], {}
        for name, eqn in assigning.items():
            found: list = []
            body = self._src(_unassign(eqn.body, found, self.copies))
            bodies[name] = body
            if found:
                self.twin_banks[name] = found[0]
            params = " ".join(Formatter()._fmt_pat(p, atom=True)
                              for p in eqn.params)
            head = f"{_copy_name(name)}{' ' + params if params else ''}"
            out.append(f"{head} = "
                       + (f"({body})" if params else f"at 0 ({body})")
                       + "\n")
        # A twin that only *calls* another inherits its bank, and the
        # chain can be any length: undertow's `barOf` reaches `chimes`
        # through `chimeNote`.
        growing = True
        while growing:
            growing = False
            for name, body in bodies.items():
                if name in self.twin_banks:
                    continue
                for called in re.findall(r"__nbf_(\w+?)__", body):
                    said = self.twin_banks.get(called)
                    if said:
                        self.twin_banks[name] = said
                        growing = True
                        break
        return "".join(out)

    def hidden_defs(self) -> str:
        # `at 0` is the identity translation, and `sowScore` passes a
        # seed through an `At` untouched — but its *signature* says
        # `[: a :]`, which is what anchors an overloaded `||` or `++`
        # in an unannotated definition to the score's own instance
        # rather than leaving the dictionary unresolved.
        return "".join(f"__nbd_{n}__ = at 0 ({t})\n"
                       for n, t in self._defs.items())


def _unassign(v, found: list, copies: frozenset = frozenset()):
    """`voices.<bank> e` → `' e`, everywhere inside a subterm.

    **An assigned score has no payload left to read.**  `voices.bass
    (Key k 96)` is a `[: Void :]` — the note went into the bank, and
    `Notable` has nothing to ask about it.  Chopin gets away with a
    top-level `>>= voices.piano` that the descent simply drops, but
    the modern idiom assigns *inside* the part (undertow's do-block),
    and refusing that would be refusing the idiom the newest examples
    teach.

    So the assignment is undone rather than worked around: `voices.B
    e` is exactly `' e` with the bank remembered, which is the same
    music one step earlier — before it was committed to a bank.  The
    banks met are appended to `found`, in reading order, because the
    roll colours by bank and the drop above cannot see these.
    """
    import dataclasses

    from .syntax import Val, VAlt, VApp, VPrefix, VWord

    if isinstance(v, VApp):
        bank = _bank_head(v.fn)
        if bank is not None:
            found.append(bank)
            return VPrefix("'", _unassign(v.arg, found, copies), v.span)
    # A mention of a declaration that assigns names its unassigned
    # twin instead, so the rewrite reaches through a call the descent
    # itself never enters.
    if isinstance(v, VWord) and v.value in copies:
        return VWord(_copy_name(v.value), v.span)
    if not isinstance(v, (Val, VAlt)):
        return v
    changed = {}
    for f in dataclasses.fields(v):
        if f.name == "span":
            continue
        val = getattr(v, f.name, None)
        if isinstance(val, (Val, VAlt)):
            changed[f.name] = _unassign(val, found, copies)
        elif isinstance(val, list) and any(isinstance(x, (Val, VAlt))
                                           for x in val):
            changed[f.name] = [_unassign(x, found, copies)
                               if isinstance(x, (Val, VAlt)) else x
                               for x in val]
    return dataclasses.replace(v, **changed) if changed else v


def _copy_name(name: str) -> str:
    return f"__nbf_{name}__"


#: The expanded spelling of a bank: `voices.bass` is `voicesBass` by
#: the time the expander is done, and the descent reads expanded text.
_EXPANDED_BANK = re.compile(r"^voices([A-Z]\w*)$")


def _bank_head(node) -> str | None:
    """The bank a node assigns to, in either spelling, or `None`."""
    from .syntax import VProj, VWord

    if isinstance(node, VProj) \
            and getattr(node.base, "value", None) == "voices":
        return str(node.index)
    if isinstance(node, VWord):
        m = _EXPANDED_BANK.match(node.value)
        if m:
            return m.group(1)[0].lower() + m.group(1)[1:]
    return None


def _assigning(module) -> dict:
    """Every declaration whose body commits a note to a bank.

    These are what an unassigned twin has to be made of: the descent
    never enters a function, so a leaf that *calls* one — undertow's
    `barOf (below 3 d) (below 5 p)` — would otherwise reach a
    `[: Void :]` whose payload the box has no way to read.
    """
    from .syntax import VSCDecl

    def assigns(node, depth=0) -> bool:
        import dataclasses

        from .syntax import Val, VAlt

        if depth > 96:
            return False
        if _bank_head(node) is not None:
            return True
        if not isinstance(node, (Val, VAlt)):
            return False
        for f in dataclasses.fields(node):
            val = getattr(node, f.name, None)
            if isinstance(val, (Val, VAlt)):
                if assigns(val, depth + 1):
                    return True
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, (Val, VAlt)) \
                            and assigns(item, depth + 1):
                        return True
        return False

    every = {item.name: item.equations[0] for item in module.items
             if isinstance(item, VSCDecl) and len(item.equations) == 1}
    out = {n: e for n, e in every.items() if assigns(e.body)}

    # **Transitively**: undertow's `barOf` names no bank itself — it
    # calls `chimeNote`, which does — and its result is a `[: Void :]`
    # all the same.  A twin is needed wherever the assignment is
    # reachable, or the rebuilt tree mixes payloads with voids and the
    # checker says so in terms of a name the author never wrote.
    growing = True
    while growing:
        growing = False
        for name, eqn in every.items():
            if name in out:
                continue
            if _mentions(eqn.body, set(out)):
                out[name] = eqn
                growing = True
    return out


def _mentions(v, names: set, depth: int = 0) -> bool:
    """Does this subterm name any of these declarations?"""
    import dataclasses

    from .syntax import Val, VAlt, VWord

    if depth > 96:
        return False
    if isinstance(v, VWord) and v.value in names:
        return True
    if not isinstance(v, (Val, VAlt)):
        return False
    for f in dataclasses.fields(v):
        val = getattr(v, f.name, None)
        if isinstance(val, (Val, VAlt)):
            if _mentions(val, names, depth + 1):
                return True
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, (Val, VAlt)) \
                        and _mentions(item, names, depth + 1):
                    return True
    return False


def _declarations(module) -> dict:
    """Single-equation, param-less declarations, by name — the ones a
    descent may enter: a definition with parameters is a function, and
    the descent never enters a function."""
    from .syntax import VSCDecl

    out = {}
    for item in module.items:
        if isinstance(item, VSCDecl) and len(item.equations) == 1 \
                and not item.equations[0].params:
            out[item.name] = item.equations[0]
    return out


# ── Building the take ───────────────────────────────────────────────────────


def _blank_asks(source: str) -> str:
    """The author's file with every ask line commented, same length —
    the descent parses this, so every span is a true file span."""
    out = []
    for line in source.splitlines():
        if _ASK.match(line) or re.match(r"^notes\s*$", line):
            out.append("#" + line[1:] if len(line) > 1 else "#")
        else:
            out.append(line)
    return "\n".join(out) + ("\n" if source.endswith("\n") else "")


def build_roll(source: str, expr: str, ask_line: int, rate: int,
               seed: int, *, fuel: int = FUEL,
               window_beats: int = WINDOW_BEATS) -> Roll:
    """The take the session's seed names, tagged with its provenance.

    `source` is the author's file; `expr` the ask's expression text;
    `ask_line` its 1-based line (spans of the expression itself point
    there).  Raises `RollError` with the margin's sentence when the
    program refuses — a missing `Notable` instance arrives here as the
    type checker's own complaint, naming the type and the class.
    """
    from .audioscore import ScoreError, assemble_performance
    from .gmachine import GmError, PushGlobal, Unwind, run
    from .midi import _force, _int, _list
    from .pipeline import compile as _compile
    from .syntax import ParseError, parse

    from .audiovoices import expand

    # The descent parses what the compiler parses: the *expanded*
    # text, where `voices` declarations are ordinary ones, sink and
    # canvas asks are rewritten line for line, and `voices.piano` is
    # `voicesPiano`.  The author's lines keep their numbers — the
    # expander appends what it generates — which is all a jump needs.
    # The notes asks are ours to blank first, the same way.
    blanked = expand(_blank_asks(source))
    wrapper = f"__nb_ask__ = {expr}\n"
    try:
        module = parse(blanked)
        wrapped = parse(wrapper)
    except ParseError as exc:
        raise RollError(f"the ask does not parse: {exc}") from exc

    assigning = _assigning(module)
    descent = _Descent(_declarations(module), frozenset(assigning))
    body = wrapped.items[0].equations[0].body
    # The twins first: a leaf that calls one takes its bank from the
    # table they fill in.
    twins = descent.twin_defs(assigning)
    root = descent.rebuild_ask(body, ask_line)
    window = window_beats * TICKS_PER_BEAT
    # The aux program is the *author's* text plus ours — expanded by
    # `assemble_performance` itself, so the internals check reads the
    # expander's output as the expander's, not as the author's.  The
    # descent read the expanded text only for its spans; nothing it
    # rebuilt mentions an expanded name, because the assign-binds are
    # exactly what it drops.
    aux = (_blank_asks(source)
           + "\n" + twins + descent.hidden_defs()
           + f"__nb_root__ = at 0 ({root})\n"
           + f"__nb_take__ = spreadTo {fuel} {window} "
             f"(sowScore {seed} __nb_root__)\n"
           + "__nb_fuel__ : Int\n"
           + "__nb_fuel__ = fst __nb_take__\n"
           # **The lambda takes the event whole, and `case` opens it.**
           # Not `map ((a, b, p) => …)`: a lambda whose parameter is a
           # *tuple pattern* resolves a constrained call in its body
           # against the wrong instance — `noteKey` picked `Notable
           # Int` off the tuple's first field and every note drew as
           # its own payload, silently (F136, with the four-line
           # repro).  Destructuring with `case` is the same program
           # and dispatches correctly.
           + "__nb_ev__ : List (Int, Int, Int, Int, Int)\n"
           + "__nb_ev__ = map (e => __nb_read__ e) (snd __nb_take__)\n"
           # Signed, and the constraint written out, so the payload
           # stays the caller's to determine — which it is: the take's
           # own element type.
           + "__nb_read__ : (Notable a) => (Int, Int, (Int, a)) "
             "-> (Int, Int, Int, Int, Int)\n"
           + "__nb_read__ e = case e of\n"
           + "    (a, b, p) -> case p of\n"
           + "        (k, x) -> (a, b, k, noteKey x, noteVel x)\n")
    try:
        state = _compile(assemble_performance(aux, "", rate))
    except (ScoreError, Exception) as exc:            # noqa: BLE001
        raise RollError(_first_line(exc)) from exc

    def _force_global(name):
        saved = (state._code, state._pc, state.stack, state.dump)
        state._code, state._pc = [PushGlobal(name), Unwind()], 0
        state.stack, state.dump = [], []
        try:
            run(state)
            return state.stack[0]
        finally:
            state._code, state._pc, state.stack, state.dump = saved

    try:
        fuel_left = _int(_force(_force_global("__nb_fuel__"), state),
                         state)
        events = []
        for e in _list(_force_global("__nb_ev__"), state):
            t = _force(e, state)
            events.append(tuple(_int(a, state) for a in t.args))
    except GmError as exc:
        raise RollError(_first_line(exc)) from exc

    leaves = descent.leaves
    return Roll(events=events, leaves=leaves,
                cut=fuel_left == 0,
                chancy=any(l.chancy for l in leaves), seed=seed)


def _first_line(exc) -> str:
    return str(exc).splitlines()[0] if str(exc) else repr(exc)


# ── The picture ─────────────────────────────────────────────────────────────

#: The roll's own size, in the canvas's pixels.  The view grants the
#: band; `Sized` reserves this much of it and the walk centres it.
ROLL_W, ROLL_H = 384, 116

#: Bank hues, assigned in reading order; the palette wraps.
_HUES = [(122, 200, 235), (235, 178, 110), (150, 220, 150),
         (220, 140, 190)]
_NIGHT = (32, 35, 43)
_DIM = 96          # take ink draws at this brightness of its hue


def _n(v: int) -> str:
    """A number as the language spells it.

    There is no unary minus: `-192` reads as a section of the
    subtraction operator, so a coordinate left of centre has to be
    written as the subtraction it is.
    """
    v = int(v)
    return str(v) if v >= 0 else f"(0 - {-v})"


def roll_program(roll: Roll, box: int = 0) -> tuple:
    """The box's standalone substrate program, and its jump table.

    Returns `(ges_text, {chan_name: line})`.  The program is ordinary
    substrate vocabulary — rects in a `Sized` box, one `TouchX` region
    per leaf — so the window walks it exactly as it walks any canvas
    ask, and a press writes a channel whose name the editor looks up.
    """
    events, leaves = roll.events, roll.leaves
    if not events:
        span_ticks = TICKS_PER_BEAT
    else:
        span_ticks = max(e[1] for e in events)
    keys = [e[3] for e in events] or [60]
    lo, hi = min(keys), max(keys)
    lo, hi = lo - 1, hi + 1
    body_h = ROLL_H - 20                       # the label's room
    x_of = lambda t: int(t * ROLL_W / max(1, span_ticks)) - ROLL_W // 2
    y_of = lambda k: (ROLL_H // 2 - 14
                      - int((k - lo) * body_h / max(1, hi - lo)))

    banks = []
    for leaf in leaves:
        if leaf.bank not in banks:
            banks.append(leaf.bank)

    def hue(leaf: Leaf) -> str:
        r, g, b = _HUES[banks.index(leaf.bank) % len(_HUES)]
        if leaf.chancy:
            r, g, b = (_DIM * r // 255, _DIM * g // 255, _DIM * b // 255)
        return f"RGB {r} {g} {b}"

    # **The notes travel as a list, not as nested `Over`s.**  A piece
    # is hundreds of notes and one `Over` per note is one parenthesis
    # per note: chopin's hundred and forty overflowed the *parser*.
    # `scoped.ges` already draws a trace by recursion over a list, and
    # this is the same picture built the same way — the chain stays
    # flat and the depth is a small function's.
    rows = []
    for on, off, k, key, vel in events:
        x0, x1 = x_of(on), x_of(off)
        w = max(2, x1 - x0) - 1
        leaf = leaves[k] if 0 <= k < len(leaves) else leaves[-1]
        tone = banks.index(leaf.bank) % len(_HUES)
        rows.append(f"({_n(x0 + (w + 1) // 2)}, {_n(y_of(key))}, "
                    f"{max(2, w)}, {tone}, {1 if leaf.chancy else 0})")
    listing = " :: ".join(rows + ["Nil"]) if rows else "Nil"

    hues = ["    _ -> RGB %d %d %d" % _HUES[0]]
    for i, (r, g, b) in enumerate(_HUES):
        hues.insert(i, f"    {i} -> RGB {r} {g} {b}")

    # One hand per leaf, and these *are* nested `Over`s: there are as
    # many as the piece has written places, which `MAX_LEAVES` keeps
    # to a depth a parser is happy with.
    jumps, regions = {}, []
    for k, leaf in enumerate(leaves):
        mine = [e for e in events if e[2] == k]
        if not mine:
            continue
        x0 = x_of(min(e[0] for e in mine))
        x1 = x_of(max(e[1] for e in mine))
        ys = [y_of(e[3]) for e in mine]
        y0, y1 = min(ys) - 4, max(ys) + 4
        w, h = max(4, x1 - x0), max(8, y1 - y0)
        # Unique across boxes: two rolls in one file are two walks in
        # one program's channel namespace, and a shared name would
        # make a press in either jump to whichever was built last.
        chan = f"__nb_c{box}_{k}__"
        jumps[chan] = leaf.line
        regions.append(f"Shift {_n(x0 + w // 2)} {_n(y0 + h // 2)} "
                       f"(Sized {w} {h} (TouchX {chan} (Gap 0 0)))")
    hands = "Gap 0 0"
    for r in regions:
        hands = f"Over ({hands}) ({r})"

    caption = f"TAKE {roll.seed}" if roll.chancy else "NOTES"
    if roll.cut:
        caption += " · CUT"

    chans = "".join(f"{c} : Chan Float\n{c} = chan\n" for c in jumps)
    text = (chans
            + "__nb_rows__ : List (Int, Int, Int, Int, Int)\n"
            + f"__nb_rows__ = {listing}\n\n"
            + "__nb_hue__ : Int -> Int -> Colour\n"
            + "__nb_hue__ t d = case d of\n"
            + "    0 -> __nb_lit__ t\n"
            + "    _ -> __nb_dim__ t\n\n"
            + "__nb_lit__ : Int -> Colour\n"
            + "__nb_lit__ t = case t of\n"
            + "\n".join(hues) + "\n\n"
            + "__nb_dim__ : Int -> Colour\n"
            + "__nb_dim__ t = case t of\n"
            + "\n".join(
                [f"    {i} -> RGB {_DIM * r // 255} {_DIM * g // 255} "
                 f"{_DIM * b // 255}" for i, (r, g, b) in enumerate(_HUES)]
                + ["    _ -> RGB %d %d %d"
                   % (_DIM * _HUES[0][0] // 255, _DIM * _HUES[0][1] // 255,
                      _DIM * _HUES[0][2] // 255)]) + "\n\n"
            + "__nb_one__ : (Int, Int, Int, Int, Int) -> Sub\n"
            + "__nb_one__ e = case e of\n"
            + "    (x, y, w, t, d) -> Shift x y (Rect w 3 (__nb_hue__ t d))\n\n"
            + "__nb_all__ : List (Int, Int, Int, Int, Int) -> Sub\n"
            + "__nb_all__ es = case es of\n"
            + "    Nil -> Gap 0 0\n"
            + "    e :: rest -> Over (__nb_one__ e) (__nb_all__ rest)\n\n"
            # **A constant signal, not a bare `Sub`.**  The roll never
            # animates — it is a take, and a take does not move — but
            # the canvas entry is a `Sig Sub`, and `!` of a computed
            # value is the constant signal of it.
            + "substrate : Sig Sub\n"
            + f"substrate = !(Sized {ROLL_W} {ROLL_H} (Over (Over (Over\n"
            + f"    (Rect {ROLL_W} {ROLL_H} (RGB {_NIGHT[0]} {_NIGHT[1]} "
              f"{_NIGHT[2]}))\n"
            + "    (__nb_all__ __nb_rows__))\n"
            + f"    (Shift 0 {ROLL_H // 2 - 8} (Label 120 12 \"{caption}\" "
              f"(RGB 120 124 134))))\n"
            + f"    ({hands})))\n")
    return text, jumps
