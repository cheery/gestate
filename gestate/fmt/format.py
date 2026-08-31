"""Autoformatter for the Gestate surface syntax.

Walks a parsed :class:`VModule` and produces consistently formatted
source text.  The output can be re-parsed to the same AST (modulo
numeric literal formatting).

Usage::

    from gestate.fmt import format

    formatted = format(source)       # parse + format
    formatted = format_module(mod)   # format an already-parsed module
"""

from __future__ import annotations

from gestate.syntax import (
    Pat, PVar, PCon, PLit, PTuple, PList, PSigCons, PBox, PAnnot,
    Val, VWord, VConId, VNum, VStr,
    VApp, VFunc, VLet, VGiven, VCase, VAlt,
    VInfix, VPrefix, VPostfix,
    VTuple, VList, VSet, VProj, VAnnot, VConstraint,
    VBox, VUnbox, VFor, VFix, VGfix, VComment,
    VFixity, VCtor, VTypeDecl, VTypeAlias, VSig, VImplicit, VSCEqn, VSCDecl,
    VClass, VInstance, VKind, VModule,
    VOpPhrase,
)
from gestate.syntax import parse as syntax_parse
from gestate.syntax.descend import DEFAULT_INFIX


# ── Number formatting ────────────────────────────────────────────────────────


def _fmt_num(val: int | float) -> str:
    if isinstance(val, float):
        return repr(val)
    return str(val)


# ── Parenthesization helpers ─────────────────────────────────────────────────

_OPERATOR_CHARS = set("!@#$%^&*-+/\\~`<>?=:|")


def _is_operator(name: str) -> bool:
    return all(c in _OPERATOR_CHARS for c in name)


def _decl_name(name: str) -> str:
    """How a name is written where a *declaration* expects one.

    An operator is parenthesised there — `(@) : …`, `(++) xs ys = …` —
    because a line starting with a symbol is not a declaration at all.
    Printing `@ : (b -> c) -> (a -> b) -> a -> c` produced output the
    parser rejected with `expected declaration, got '@'`, which is a
    formatter that loses the program it was given.
    """
    return f"({name})" if _is_operator(name) else name


def _needs_parens(val: Val) -> bool:
    """True when *val* must be wrapped in ``( ... )`` if used as an
    argument to application."""
    return isinstance(val, (
        VApp,
        VInfix, VPrefix, VPostfix,
        VFunc, VLet, VGiven, VCase,
        VFor, VFix, VGfix, VUnbox, VBox,
        VAnnot, VConstraint,
    ))


def _paren_val(val: Val, fmt_text: str) -> str:
    if _needs_parens(val):
        return f"({fmt_text})"
    return fmt_text


def _infix_op(op: str) -> str:
    """How an infix operator is written back out.

    A name used as one is quoted again — it reached the AST as a plain
    `over`, and printing it plain would turn `x `over` y` into the
    application `x over y`, which is a different program.  The tokenizer is
    the only place the ticks exist, so this is the only place they come
    back.
    """
    return f"`{op}`" if (op[:1].isalpha() or op[:1] == "_") else op


def _prec_of(op: str) -> int:
    """Return the precedence of operator *op* (higher binds tighter)."""
    info = DEFAULT_INFIX.get(op)
    if info is not None:
        return info[1]
    return 0


# ── Formatter ────────────────────────────────────────────────────────────────


class Formatter:
    """Collects formatted output."""

    def __init__(self, indent: int = 4):
        self._indent = indent
        self._level = 0
        self._buf: list[str] = []
        self._pending_comments: list[VComment] = []
        self._line_empty = True
        #: The source line the last thing printed ended on, so a gap the
        #: author left between two items can be kept.  `None` until
        #: something has been printed — a file does not open on a blank.
        self._last_line: int | None = None

    # -- low-level output --

    def _w(self, text: str):
        self._buf.append(text)
        if text:
            self._line_empty = False

    def _nl(self):
        self._buf.append("\n")
        self._line_empty = True

    def _blank(self):
        if not self._line_empty:
            self._nl()

    def _indent_str(self) -> str:
        return " " * (self._level * self._indent)

    def _start_line(self):
        if self._line_empty:
            self._w(self._indent_str())

    def _ln(self, text: str = ""):
        self._start_line()
        if text:
            self._w(text)
        self._nl()

    def _flush_comments(self):
        for c in self._pending_comments:
            self._space_before(c)
            self._ln(f"#{c.text}")
            # A comment is a thing on a line too, so the gap after it is
            # measured from *it* — without this, a header immediately
            # above its declaration was pushed away from it by the gap
            # that belonged before the header.
            self._note_line(c)
        self._pending_comments.clear()

    def _space_before(self, item) -> None:
        """One blank line where the author left one or more.

        **Blank lines are the author's paragraphing, and dropping them
        rewrote every file into one wall of declarations.**  The
        formatter owns spacing *within* a declaration; between them, the
        grouping is a decision somebody made about their own program and
        there is nothing in the tree that could reconstruct it.

        One blank for any gap, rather than the exact count: two blank
        lines and three mean the same thing to a reader, and the
        alternative is a formatter that cannot make a file idempotent
        because it keeps whatever it was handed.
        """
        span = getattr(item, "span", None)
        if span is None or self._last_line is None:
            return
        if span.start.line <= self._last_line + 1:
            return
        # **Not `_blank`**, which only ends a line that has something on
        # it — after `_ln` the line is already empty, so asking for a
        # blank there did nothing at all.  What is wanted here is an
        # empty *line*, and the guard is against writing two.
        if not self._buf or not "".join(self._buf[-2:]).endswith("\n\n"):
            self._nl()

    def _note_line(self, item) -> None:
        """Remember where this item ended, for the gap after it."""
        span = getattr(item, "span", None)
        if span is not None:
            self._last_line = max(getattr(self, "_last_line", None) or 0,
                                  span.end.line)

    # -- entry points --

    def format(self, module: VModule) -> str:
        self._format_module(module)
        return "".join(self._buf)

    def _format_module(self, module: VModule):
        items = module.items
        # Trivia — comments the parser met *inside* declarations
        # (`VModule.comments`).  Reattached after the item whose lines
        # they fell in, as full-line comments: the exact column is gone
        # once the item is reformatted, but the comment and its
        # neighbourhood survive, which is the promise (`spec/comments.md`).
        trivia = list(getattr(module, "comments", []))
        for i, item in enumerate(items):
            if isinstance(item, VComment):
                self._pending_comments.append(item)
                continue
            self._flush_comments()
            self._space_before(item)
            self._format_top_item(item)
            self._note_line(item)
            trivia = self._flush_trivia_in(item, trivia)
            if i + 1 < len(items) and not isinstance(items[i + 1], VComment):
                if self._should_blank_after(item, items, i):
                    self._blank()
            self._start_line()
        for c in trivia:
            self._ln(f"#{c.text}")

    def _flush_trivia_in(self, item: Val, trivia: list) -> list:
        """Print the trivia that fell inside `item`; return the rest."""
        left = []
        for c in trivia:
            span = getattr(item, "span", None)
            if (span is not None
                    and span.start.line <= c.span.start.line <= span.end.line):
                self._ln(f"#{c.text}")
            else:
                left.append(c)
        return left

    def _should_blank_after(self, item: Val, items: list[Val], i: int) -> bool:
        """Insert a blank line after *item* if the next item is a different
        top-level group."""
        if i + 1 >= len(items):
            return False
        nxt = items[i + 1]
        # Blank between fixity and non-fixity
        if isinstance(item, VFixity) and not isinstance(nxt, VFixity):
            return True
        if not isinstance(item, VFixity) and isinstance(nxt, VFixity):
            return True
        # Blank between kind and other
        if isinstance(item, VKind) != isinstance(nxt, VKind):
            return True
        # Blank after VSCDecl unless next is a continuation
        return False

    # ── Top-level items ──────────────────────────────────────────────────

    def _format_top_item(self, item: Val):
        if isinstance(item, VFixity):
            right = f" {item.right}" if item.right is not None else ""
            self._ln(f"{item.mode} {item.prec}{right} {item.op}")
        elif isinstance(item, VKind):
            self._ln(f"kind {item.name} : {self._fmt_val(item.kind)}")
        elif isinstance(item, VTypeAlias):
            self._format_type_alias(item)
        elif isinstance(item, VTypeDecl):
            self._format_type_decl(item)
        elif isinstance(item, VSig):
            self._ln(f"{_decl_name(item.name)} : {self._fmt_val(item.type_)}")
        elif isinstance(item, VImplicit):
            self._ln(f"implicit {_decl_name(item.name)} : "
                     f"{self._fmt_val(item.type_)}")
        elif isinstance(item, VSCDecl):
            self._format_sc_decl(item)
        elif isinstance(item, VClass):
            self._format_class(item)
        elif isinstance(item, VInstance):
            self._format_instance(item)
        else:
            self._ln(self._fmt_val(item))

    def _format_type_decl(self, td: VTypeDecl):
        params = " ".join(td.params)
        header = f"{td.name} {params} :=".rstrip()
        for i, ctor in enumerate(td.constructors):
            fields = " ".join(self._fmt_val(f) for f in ctor.fields)
            constraints = ""
            if ctor.constraints:
                cons = ", ".join(self._fmt_val(c) for c in ctor.constraints)
                constraints = f"({cons}) => "
            if i == 0:
                self._ln(f"{header} {constraints}{ctor.name} {fields}".rstrip())
            else:
                prefix = " " * (len(td.name) + 1)
                self._ln(f"{prefix}| {constraints}{ctor.name} {fields}".rstrip())

    def _format_type_alias(self, ta: VTypeAlias):
        params = " ".join(ta.params)
        body = self._fmt_val(ta.body)
        self._ln(f"type {ta.name} {params} = {body}".rstrip())

    def _format_sc_decl(self, scd: VSCDecl):
        if scd.sig:
            self._ln(f"{_decl_name(scd.name)} : {self._fmt_val(scd.sig)}")
        for eqn in scd.equations:
            self._format_sc_eqn(eqn)

    def _format_sc_eqn(self, eqn: VSCEqn):
        pats = [self._fmt_pat(p, atom=True) for p in eqn.params]
        body = self._fmt_val(eqn.body)
        name = eqn.name
        using = ""
        if eqn.using_params:
            using = f"(using {' '.join(eqn.using_params)}) "
        # **No infix definition form here**, though there is one inside an
        # instance.  A two-operand operator used to be written back as
        # `x <+> y = …`, which the parser does not accept at the top level:
        # `expected pattern, got '<+>'`.  So the prefix form is the only
        # one, and the formatter's output re-parses.
        head = f"{_decl_name(name)} {using}{' '.join(pats)}".rstrip()
        self._ln(f"{head} = {body}")

    def _format_class(self, cls: VClass):
        params = " ".join(cls.params)
        self._ln(f"class {cls.name} {params} where".rstrip())
        self._level += 1
        for m in cls.members:
            self._format_class_member(m)
        self._level -= 1

    def _format_class_member(self, m: Val):
        if isinstance(m, VKind):
            kind_text = self._fmt_val(m.kind)
            self._ln(f"type {m.name} : {kind_text}")
        elif isinstance(m, VSig):
            # Was a hand-kept list of the operators the libraries happened
            # to declare, which is a list that goes stale by being right
            # today: `_is_operator` asks the question directly.
            self._ln(f"{_decl_name(m.name)} : {self._fmt_val(m.type_)}")
        elif isinstance(m, VSCEqn):
            self._format_sc_eqn(m)
        else:
            self._ln(self._fmt_val(m))

    def _format_instance(self, inst: VInstance):
        params = " ".join(_paren_val(p, self._fmt_val(p)) for p in inst.params)
        context = ""
        if inst.context:
            preds = ", ".join(self._fmt_val(c) for c in inst.context)
            context = f"({preds}) => "
        self._ln(f"instance {context}{inst.name} {params} where".rstrip())
        self._level += 1
        for m in inst.members:
            self._format_instance_member(m)
        self._level -= 1

    def _format_instance_member(self, m: Val):
        if isinstance(m, VKind):
            self._ln(f"type {m.name} = {self._fmt_val(m.kind)}")
        elif isinstance(m, VSCEqn):
            pats = [self._fmt_pat(p, atom=True) for p in m.params]
            body = self._fmt_val(m.body)
            if _is_operator(m.name) and len(pats) == 2:
                self._ln(f"{pats[0]} {m.name} {pats[1]} = {body}")
            else:
                head = f"{_decl_name(m.name)} {' '.join(pats)}".rstrip()
                self._ln(f"{head} = {body}")
        elif isinstance(m, VSig):
            self._ln(f"{_decl_name(m.name)} : {self._fmt_val(m.type_)}")
        else:
            self._ln(self._fmt_val(m))

    # ── Values ───────────────────────────────────────────────────────────

    def _fmt_val(self, val: Val) -> str:
        if isinstance(val, VWord):
            return val.value
        if isinstance(val, VConId):
            return val.value
        if isinstance(val, VNum):
            return _fmt_num(val.value)
        if isinstance(val, VStr):
            return self._fmt_string(val.value)
        if isinstance(val, VApp):
            return self._fmt_app(val)
        if isinstance(val, VFunc):
            return self._fmt_func(val)
        if isinstance(val, VLet):
            return self._fmt_let(val)
        if isinstance(val, VGiven):
            return self._fmt_given(val)
        if isinstance(val, VCase):
            return self._fmt_case(val)
        if isinstance(val, VInfix):
            return self._fmt_infix(val)
        if isinstance(val, VPrefix):
            return self._fmt_prefix(val)
        if isinstance(val, VPostfix):
            return self._fmt_postfix(val)
        if isinstance(val, VTuple):
            return self._fmt_tuple(val)
        if isinstance(val, VList):
            return self._fmt_list(val)
        if isinstance(val, VSet):
            return self._fmt_set(val)
        if isinstance(val, VProj):
            return self._fmt_proj(val)
        if isinstance(val, VAnnot):
            return f"{self._fmt_val(val.expr)} : {self._fmt_val(val.type_)}"
        if isinstance(val, VConstraint):
            return self._fmt_constraint(val)
        if isinstance(val, VBox):
            inner = self._fmt_val(val.body)
            return f"Box {_paren_val(val.body, inner)}"
        if isinstance(val, VUnbox):
            return self._fmt_unbox(val)
        if isinstance(val, VFor):
            return self._fmt_for(val)
        if isinstance(val, VFix):
            return f"fix {self._fmt_val(val.body)}"
        if isinstance(val, VGfix):
            return f"gfix {val.var} => {self._fmt_val(val.body)}"
        if isinstance(val, VComment):
            return f"#{val.text}"
        if isinstance(val, VOpPhrase):
            return self._fmt_op_phrase(val)
        return f"<{type(val).__name__}>"

    def _fmt_string(self, s: str) -> str:
        esc = s.replace("\\", "\\\\").replace('"', '\\"')
        esc = esc.replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")
        return f'"{esc}"'

    def _fmt_app(self, app: VApp) -> str:
        parts: list[str] = []
        cur: Val = app
        while isinstance(cur, VApp):
            arg_text = self._fmt_val(cur.arg)
            parts.append(_paren_val(cur.arg, arg_text))
            cur = cur.fn
        # The head is juxtaposed like every argument, so it wants the same
        # question asked of it (`fixme.md` F186).  It was written bare, and
        # a head that runs to the end of the expression — a lambda, a `let`,
        # a `case` — then swallowed the argument standing next to it.  The
        # loop has already left `VApp` behind, so this never re-parenthesises
        # a spine.
        parts.append(_paren_val(cur, self._fmt_val(cur)))
        return " ".join(reversed(parts))

    def _fmt_func(self, func: VFunc) -> str:
        pats = " ".join(self._fmt_pat(p, atom=True) for p in func.params)
        return f"{pats} => {self._fmt_val(func.body)}"

    def _fmt_let(self, l: VLet) -> str:
        kw = "letrec" if l.is_rec else "let"
        lines: list[str] = []
        for i, (name, val) in enumerate(l.bindings):
            if i == 0:
                lines.append(f"{kw} {name} = {self._fmt_val(val)}")
            else:
                lines.append(f"{' ' * self._indent}{name} = {self._fmt_val(val)}")
        body = self._fmt_val(l.body)
        if len(lines) == 1:
            return f"{kw} {l.bindings[0][0]} = {self._fmt_val(l.bindings[0][1])} in {body}"
        return "\n".join(lines) + f"\nin {body}"

    def _fmt_given(self, g: VGiven) -> str:
        lines: list[str] = []
        for i, (name, val) in enumerate(g.bindings):
            if i == 0:
                lines.append(f"given {name} = {self._fmt_val(val)}")
            else:
                lines.append(f"{' ' * self._indent}{name} = {self._fmt_val(val)}")
        body = self._fmt_val(g.body)
        if len(lines) == 1:
            return f"given {g.bindings[0][0]} = {self._fmt_val(g.bindings[0][1])} in {body}"
        return "\n".join(lines) + f"\nin {body}"

    def _fmt_case(self, case: VCase) -> str:
        scrut = self._fmt_val(case.scrut)
        lines = [f"case {scrut} of"]
        for alt in case.alts:
            pat = self._fmt_pat(alt.pat)
            body = self._fmt_val(alt.body)
            lines.append(f"{' ' * self._indent}{pat} -> {body}")
        return "\n".join(lines)

    #: Forms whose body runs to the end of the enclosing expression.  As an
    #: operand of an infix they must be parenthesised or they swallow the
    #: operator: `(x => e) + 1` reprinted as `x => e + 1` is a different
    #: program.
    _TRAILING = (VFunc, VLet, VGiven, VCase, VFor, VFix, VGfix, VUnbox,
                 VAnnot, VConstraint)

    def _fmt_infix(self, inf: VInfix) -> str:
        assoc, p = DEFAULT_INFIX.get(inf.op, ("L", _prec_of(inf.op)))

        def operand(val: Val, side: str) -> str:
            text = self._fmt_val(val)
            if isinstance(val, self._TRAILING):
                return f"({text})"
            if isinstance(val, VInfix):
                q = _prec_of(val.op)
                # Equal precedence needs parens on the side the operator
                # does *not* associate towards.
                if q < p or (q == p and assoc != side):
                    return f"({text})"
            return text

        return f"{operand(inf.left, 'L')} {_infix_op(inf.op)} " \
               f"{operand(inf.right, 'R')}"

    def _fmt_prefix(self, pf: VPrefix) -> str:
        arg = self._fmt_val(pf.arg)
        return f"{pf.op}{_paren_val(pf.arg, arg)}" if _needs_parens(pf.arg) else f"{pf.op}{arg}"

    def _fmt_postfix(self, pf: VPostfix) -> str:
        arg = self._fmt_val(pf.arg)
        return f"{_paren_val(pf.arg, arg)}{pf.op}" if _needs_parens(pf.arg) else f"{arg}{pf.op}"

    def _fmt_tuple(self, tup: VTuple) -> str:
        if not tup.items:
            return "()"
        items = ", ".join(self._fmt_val(i) for i in tup.items)
        return f"({items})"

    def _fmt_list(self, lst: VList) -> str:
        if not lst.items and lst.tail is None:
            return "[]"
        items = ", ".join(self._fmt_val(i) for i in lst.items)
        if lst.tail is not None:
            tail = self._fmt_val(lst.tail)
            items = f"{items} | {tail}" if items else tail
        return f"[{items}]"

    def _fmt_set(self, s: VSet) -> str:
        if not s.items:
            return "{}"
        items = ", ".join(self._fmt_val(i) for i in s.items)
        return "{{{}}}".format(items)

    def _fmt_proj(self, proj: VProj) -> str:
        base = self._fmt_val(proj.base)
        idx = str(proj.index)
        return f"{base}.{idx}"

    def _fmt_constraint(self, c: VConstraint) -> str:
        items = ", ".join(self._fmt_val(i) for i in c.constraints)
        return f"({items}) => {self._fmt_val(c.body)}"

    def _fmt_unbox(self, u: VUnbox) -> str:
        pat = self._fmt_pat(u.pat)
        bind = self._fmt_val(u.binding)
        body = self._fmt_val(u.body)
        return f"unbox {pat} = {bind} in {body}"

    def _fmt_for(self, f: VFor) -> str:
        bindings: list[str] = []
        for pat, val in f.bindings:
            bindings.append(f"{self._fmt_pat(pat)} in {self._fmt_val(val)}")
        body = self._fmt_val(f.body)
        return f"for ({', '.join(bindings)}) {body}"

    def _fmt_op_phrase(self, phrase: VOpPhrase) -> str:
        atoms = phrase.atoms
        if not atoms:
            return "()"
        # (+): single infix operator
        if len(atoms) == 1 and isinstance(atoms[0], str):
            return f"({atoms[0]})"
        # (+_): prefix operator reference
        if len(atoms) == 2 and isinstance(atoms[0], str):
            a1 = atoms[1]
            if isinstance(a1, VWord) and a1.value == "_":
                return f"({atoms[0]}_)"
        # (_+): postfix operator reference
        if len(atoms) == 2 and isinstance(atoms[1], str):
            a0 = atoms[0]
            if isinstance(a0, VWord) and a0.value == "_":
                return f"(_{atoms[1]})"
        # Fallback: format as expression
        parts: list[str] = []
        for a in atoms:
            if isinstance(a, str):
                parts.append(a)
            else:
                parts.append(self._fmt_val(a))
        return " ".join(parts)

    # ── Patterns ─────────────────────────────────────────────────────────

    def _fmt_pat(self, pat: Pat, atom: bool = False) -> str:
        """Format ``pat``.

        ``atom`` is set where the grammar expects an atomic pattern — an
        equation's parameters and a constructor's arguments, which are
        juxtaposed — so that a compound pattern is parenthesised there and
        left bare where it stands alone (a ``case`` alternative).
        """
        if isinstance(pat, PVar):
            return pat.name
        if isinstance(pat, PCon):
            args = " ".join(self._fmt_pat(a, atom=True) for a in pat.args)
            if pat.args:
                return f"({pat.name} {args})" if atom else f"{pat.name} {args}"
            return pat.name
        if isinstance(pat, PLit):
            if isinstance(pat.value, str):
                return self._fmt_string(pat.value)
            return _fmt_num(pat.value)
        if isinstance(pat, PTuple):
            items = ", ".join(self._fmt_pat(i) for i in pat.items)
            return f"({items})"
        if isinstance(pat, PList):
            if not pat.items and pat.tail is None:
                return "[]"
            items_str = ", ".join(self._fmt_pat(i) for i in pat.items)
            if pat.tail is not None:
                tail = self._fmt_pat(pat.tail)
                if len(pat.items) == 1 and not isinstance(pat.items[0], (PTuple,)):
                    # A cons pattern binds looser than juxtaposition, so
                    # `f (x :: xs)` must not come back as `f x :: xs`.
                    cons = f"{items_str} :: {tail}"
                    return f"({cons})" if atom else cons
                return f"[{items_str} :: {tail}]" if items_str else f"[{tail}]"
            return f"[{items_str}]"
        if isinstance(pat, PBox):
            # `Box p` takes one *atomic* sub-pattern, the way a constructor
            # takes each of its arguments, and is itself juxtaposed wherever
            # `atom` is set.  Without this branch it fell through to the
            # placeholder below and printed `<PBox>` (`fixme.md` F188).
            inner = self._fmt_pat(pat.pat, atom=True)
            return f"(Box {inner})" if atom else f"Box {inner}"
        if isinstance(pat, PSigCons):
            cons = f"{self._fmt_pat(pat.head)} ::: {self._fmt_pat(pat.tail)}"
            return f"({cons})" if atom else cons
        if isinstance(pat, PAnnot):
            return f"({self._fmt_pat(pat.pat)} : {self._fmt_val(pat.type_)})"
        return f"<{type(pat).__name__}>"


# ── Public API ───────────────────────────────────────────────────────────────


def format_module(module: VModule) -> str:
    """Format an already-parsed *module*, returning source text."""
    return Formatter().format(module)


def format_source(source: str) -> str:
    """Parse *source* and return formatted output (idempotent-style)."""
    mod = syntax_parse(source)
    return format_module(mod)


# For brevity
format = format_source
