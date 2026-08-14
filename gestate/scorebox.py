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

#: Leaves beyond this are collapsed into their parent: a descent that
#: found a thousand spans is drawing a picture nobody can click.
MAX_LEAVES = 256

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


def asks(text: str) -> list:
    """Every `notes <expr>` ask: `(line_1based, expr_text)`."""
    out = []
    for i, line in enumerate(text.splitlines(), start=1):
        m = _ASK.match(line)
        if m and not m.group(1).startswith("#") \
                and not m.group(1).startswith("=") \
                and not m.group(1).startswith(":"):
            out.append((i, m.group(1)))
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

    def __init__(self, source: str, decls: dict):
        self._file_lines = source.splitlines()
        #: What spans currently slice from, and how their lines map to
        #: the author's file: the ask's expression parses inside a
        #: one-line wrapper, so while its nodes are being walked the
        #: context is the wrapper's text and every leaf wears the
        #: ask's own line.  Entering a named definition switches back.
        self._lines = self._file_lines
        self._bias = 0
        self._decls = decls           # name -> VSCEqn (single, param-less)
        self._visiting: set = set()
        self._defs: dict = {}         # name -> rebuilt hidden text
        self.leaves: list = []

    def rebuild_ask(self, wrapper: str, body, ask_line: int) -> str:
        self._lines = wrapper.splitlines()
        self._bias = ask_line - 1
        try:
            return self.rebuild(body)
        finally:
            self._lines, self._bias = self._file_lines, 0

    def _src(self, span) -> str:
        # Spans are end-exclusive — except that a parenthesized atom's
        # span stops *on* its closing paren rather than after it, so a
        # slice can come out one `)` short per nesting level.  Extend
        # while unbalanced; what stands past the end is always the
        # parens the parser ate.
        s, e = span.start, span.end
        if s.line == e.line:
            text = self._lines[s.line][s.col:e.col]
        else:
            parts = [self._lines[s.line][s.col:]]
            parts += self._lines[s.line + 1:e.line]
            parts.append(self._lines[e.line][:e.col])
            text = "\n".join(parts)
        tail, j = self._lines[e.line], e.col
        while text.count("(") > text.count(")") and j < len(tail) \
                and tail[j] == ")":
            text += ")"
            j += 1
        return text.strip()

    def _leaf(self, span, bank) -> str:
        text = self._src(span)
        k = len(self.leaves)
        if k >= MAX_LEAVES:
            # Collapsed into the last region rather than dropped: the
            # note still draws and still jumps somewhere true, just
            # not as finely as a smaller piece would.
            k = MAX_LEAVES - 1
            return f"(({text}) >>= (__nbx__ => ' (({k}, __nbx__))))"
        self.leaves.append(Leaf(line=span.start.line + 1 + self._bias,
                                bank=bank,
                                chancy=bool(_CHANCY.search(text))))
        return f"(({text}) >>= (__nbx__ => ' (({k}, __nbx__))))"

    def rebuild(self, v, bank=None) -> str:
        from .syntax import VApp, VInfix, VPrefix, VWord

        if isinstance(v, VInfix):
            if v.op in ("++", "||"):
                return (f"({self.rebuild(v.left, bank)} {v.op} "
                        f"{self.rebuild(v.right, bank)})")
            if v.op in ("|*", "|/"):
                return (f"({self.rebuild(v.left, bank)} {v.op} "
                        f"{self._src(v.right.span)})")
            if v.op == ">>=":
                right = self._src(v.right.span).strip()
                m = _ASSIGN.match(right)
                if m:
                    return self.rebuild(v.left, _bank_of(m) or bank)
                return self._leaf(v.span, bank)
            return self._leaf(v.span, bank)
        if isinstance(v, VApp):
            head, args = v, []
            while isinstance(head, VApp):
                args.insert(0, head.arg)
                head = head.fn
            if isinstance(head, VWord) and head.value in ("long", "at",
                                                          "sow") \
                    and len(args) == 2:
                return (f"({head.value} {self._src(args[0].span)} "
                        f"{self.rebuild(args[1], bank)})")
            if isinstance(head, VWord) and head.value == "cycle" \
                    and len(args) == 1:
                return f"(cycle {self.rebuild(args[0], bank)})"
            return self._leaf(v.span, bank)
        if isinstance(v, VWord):
            name = v.value
            eqn = self._decls.get(name)
            if eqn is None or name in self._visiting:
                # A library name, a parameter, or a recursive mention:
                # opaque, wearing the reference's own span.
                return self._leaf(v.span, bank)
            if name not in self._defs:
                self._visiting.add(name)
                self._defs[name] = "PENDING"
                # The definition's spans live in the file, whatever
                # text the reference itself was sliced from.
                saved = self._lines, self._bias
                self._lines, self._bias = self._file_lines, 0
                try:
                    self._defs[name] = self.rebuild(eqn.body, bank)
                finally:
                    self._lines, self._bias = saved
                self._visiting.discard(name)
            return f"__nbd_{name}__"
        return self._leaf(v.span, bank)

    def hidden_defs(self) -> str:
        # `at 0` is the identity translation, and `sowScore` passes a
        # seed through an `At` untouched — but its *signature* says
        # `[: a :]`, which is what anchors an overloaded `||` or `++`
        # in an unannotated definition to the score's own instance
        # rather than leaving the dictionary unresolved.
        return "".join(f"__nbd_{n}__ = at 0 ({t})\n"
                       for n, t in self._defs.items())


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

    descent = _Descent(blanked, _declarations(module))
    body = wrapped.items[0].equations[0].body
    root = descent.rebuild_ask(wrapper, body, ask_line)
    window = window_beats * TICKS_PER_BEAT
    # The aux program is the *author's* text plus ours — expanded by
    # `assemble_performance` itself, so the internals check reads the
    # expander's output as the expander's, not as the author's.  The
    # descent read the expanded text only for its spans; nothing it
    # rebuilt mentions an expanded name, because the assign-binds are
    # exactly what it drops.
    aux = (_blank_asks(source)
           + "\n" + descent.hidden_defs()
           + f"__nb_root__ = at 0 ({root})\n"
           + f"__nb_take__ = spreadTo {fuel} {window} "
             f"(sowScore {seed} __nb_root__)\n"
           + "__nb_fuel__ : Int\n"
           + "__nb_fuel__ = fst __nb_take__\n"
           + "__nb_ev__ : List (Int, Int, Int, Int, Int)\n"
           + "__nb_ev__ = map ((a, b, p) => __nb_read__ a b p) "
             "(snd __nb_take__)\n"
           + "__nb_read__ a b p = case p of\n"
           + "    (k, x) -> (a, b, k, noteKey x, noteVel x)\n")
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


def roll_program(roll: Roll) -> tuple:
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

    parts = [f"Rect {ROLL_W} {ROLL_H} (RGB {_NIGHT[0]} {_NIGHT[1]} "
             f"{_NIGHT[2]})"]
    for on, off, k, key, vel in events:
        x0, x1 = x_of(on), x_of(off)
        w = max(2, x1 - x0)
        cx = x0 + w // 2
        leaf = leaves[k] if 0 <= k < len(leaves) else leaves[-1]
        parts.append(f"Shift {cx} {y_of(key)} (Rect {w - 1} 3 "
                     f"({hue(leaf)}))")

    # One hand per leaf: the touch region is the provenance region —
    # its tick range wide, its own notes' key range tall.
    jumps = {}
    regions = []
    for k, leaf in enumerate(leaves):
        mine = [e for e in events if e[2] == k]
        if not mine:
            continue
        x0 = x_of(min(e[0] for e in mine))
        x1 = x_of(max(e[1] for e in mine))
        ys = [y_of(e[3]) for e in mine]
        y0, y1 = min(ys) - 4, max(ys) + 4
        w, h = max(4, x1 - x0), max(8, y1 - y0)
        cx, cy = x0 + w // 2, y0 + h // 2
        chan = f"__nb_c{k}__"
        jumps[chan] = leaf.line
        regions.append(f"Shift {cx} {cy} (Sized {w} {h} "
                       f"(TouchX {chan} (Gap 0 0)))")

    caption = (f"TAKE {roll.seed}" if roll.chancy else "NOTES")
    if roll.cut:
        caption += " · CUT"
    parts.append(f"Shift 0 {ROLL_H // 2 - 8} (Label 120 12 "
                 f"\"{caption}\" (RGB 120 124 134))")

    over = parts[0]
    for p in parts[1:] + regions:
        over = f"Over ({over}) ({p})"
    chans = "".join(f"{c} : Chan Float\n{c} = chan\n" for c in jumps)
    text = (chans + "substrate : Sub\n"
            + f"substrate = Sized {ROLL_W} {ROLL_H} ({over})\n")
    return text, jumps
