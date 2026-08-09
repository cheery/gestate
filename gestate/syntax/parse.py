"""Recursive-descent parser for the Gestate surface syntax.

Converts a token stream (including INDENT/DEDENT layout tokens)
into a :class:`VModule` AST.

Operator phrases are left flat as :class:`VOpPhrase` nodes; fixity
resolution is performed by the post-pass in :mod:`.descend`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from .ast import (
    Pat, PVar, PCon, PLit, PTuple, PList, PSigCons, PAnnot, PBox,
    Val, VWord, VConId, VNum, VStr, VApp, VFunc, VLet, VGiven, VCase, VAlt,
    VOpPhrase, VTuple, VList, VSet, VProj, VAnnot, VConstraint,
    VBox, VUnbox, VFor, VFix, VGfix, VComment,
    VFixity, VCtor, VTypeDecl, VTypeAlias, VSig, VImplicit, VSCEqn, VSCDecl,
    VClass, VInstance, VKind, VInternal, VModule,
    Pos, Span, ParseError,
)
from .tokenize import TT, T
from .descend import DEFAULT_INFIX, DEFAULT_PREFIX, DEFAULT_POSTFIX

#: Symbols that may be used postfix.  A user `postfix` declaration is not
#: visible here — fixities are collected in a later pass — so this is the
#: built-in set; anything else is read as infix or prefix by position.
_POSTFIX_OPS = frozenset(DEFAULT_POSTFIX)

#: Symbols that can *only* be prefix — declared prefix and never infix.
#: `'` is the note constructor and `|<` shifts a score; neither has an
#: infix reading, so a symbol from this set standing after a complete
#: operand cannot be an infix operator.  It starts another argument.
#: Without this, `four '38` read as `four ' 38` — `'` infix — and every
#: note passed to a function needed parentheses (`doc/manual.md` §9).
_PREFIX_ONLY_OPS = frozenset(DEFAULT_PREFIX) - frozenset(DEFAULT_INFIX)


# ── Errors ───────────────────────────────────────────────────────────────────


#: Defined in `ast.py` and re-exported here, where every caller looks for
#: it: the tokenizer raises it too and cannot import from this module.
ParseError = ParseError


# ── Parser ───────────────────────────────────────────────────────────────────


def _span(a: Span, b: Span) -> Span:
    return Span(a.start, b.end)


def _apply_all(head: Val, args: list[Val]) -> Val:
    """Build the application ``head arg1 … argn``."""
    for a in args:
        head = VApp(head, a, Span(head.span.start, a.span.end))
    return head


class Parser:
    """Recursive-descent parser driven by a token iterator."""

    def __init__(self, tokens: list[T]):
        self._ts = tokens
        self._i = 0
        #: Counter for the fresh variables `_guardN` that comprehension
        #: guards bind.  Per-parse, and the body never mentions them.
        self._guard_n = 0

    # -- low-level helpers --

    @property
    def _cur(self) -> T | None:
        if self._i < len(self._ts):
            return self._ts[self._i]
        return None

    #: Closing brackets end any layout block opened inside them, so the
    #: tokenizer emits the block's ``DEDENT`` just before them.  The block
    #: parser needs to see that ``DEDENT`` to know it is finished; whoever
    #: then wants the bracket has to step over it.
    _CLOSERS = (")", "]", "}")

    def _at(self, kind: TT, val: str | None = None) -> bool:
        if kind is TT.SEP and val in self._CLOSERS:
            self._drop_dedents_before(val)
        t = self._cur
        if t is None:
            return False
        if t.kind != kind:
            return False
        if val is not None and t.value != val:
            return False
        return True

    def _drop_dedents_before(self, closer: str) -> None:
        """Consume ``DEDENT``s that sit directly in front of ``closer``.

        Only when the closer really follows: otherwise the ``DEDENT``s
        belong to a block the caller is still reading and must be left
        alone.
        """
        j = self._i
        while j < len(self._ts) and self._ts[j].kind is TT.DEDENT:
            j += 1
        if j != self._i and j < len(self._ts):
            t = self._ts[j]
            if t.kind is TT.SEP and t.value == closer:
                self._i = j

    def _adv(self) -> T:
        t = self._cur
        if t is None:
            raise ParseError("unexpected end of file")
        self._i += 1
        return t

    def _eat(self, kind: TT, val: str | None = None) -> T:
        if not self._at(kind, val):
            expected = f"{kind.name}"
            if val:
                expected += f" {val!r}"
            got = f"{self._cur.kind.name} {self._cur.value!r}" if self._cur else "EOF"
            raise ParseError(
                f"expected {expected}, got {got}",
                self._cur.pos if self._cur else None,
            )
        return self._adv()

    def _try(self, kind: TT, val: str | None = None) -> T | None:
        if self._at(kind, val):
            return self._adv()
        return None

    def _eat_symbol(self, val: str) -> T:
        if self._at(TT.SEP, val):
            return self._eat(TT.SEP, val)
        if self._at(TT.SYMBOL, val):
            return self._eat(TT.SYMBOL, val)
        raise ParseError(f"expected symbol {val!r}, got {self._cur}", self._cur.pos if self._cur else None)

    # -- layout helpers --

    def _skip_nl(self):
        while self._at(TT.NEWLINE):
            self._adv()

    def _skip_trivia(self):
        """Newlines *and* comments — for places a comment must not end.

        A comment is an item at the top level, where the formatter keeps
        it, but inside a declaration it is only trivia, and treating it as
        a terminator lets it change what a program means.
        """
        while self._at(TT.NEWLINE) or self._at(TT.COMMENT):
            self._adv()

    def _at_bol(self) -> bool:
        """True when an INDENT, DEDENT, or real token after NEWLINE."""
        return self._at(TT.INDENT) or self._at(TT.DEDENT)

    def _expect_indent(self):
        self._skip_nl()
        if self._at(TT.INDENT):
            self._adv()
        else:
            raise ParseError("expected INDENT", self._cur.pos if self._cur else None)

    # -- entry point --

    def parse(self) -> VModule:
        items: list[Val] = []
        self._skip_nl()

        while not self._at(TT.EOF):
            while self._at(TT.COMMENT):
                items.append(self._parse_comment())
                self._skip_nl()
            if self._at(TT.EOF):
                break
            # Skip DEDENT tokens that close layout blocks nested
            # inside top-level declarations (e.g. case/of).
            if self._at(TT.DEDENT):
                self._adv()
                self._skip_nl()
                continue

            items.append(self._parse_top_item())
            self._skip_nl()

        return VModule(items, Span(items[0].span.start if items else Pos(), Pos()))

    # ── Top-level items ──────────────────────────────────────────────────

    def _parse_top_item(self) -> Val:
        t = self._cur
        assert t is not None

        # fixity declaration
        if t.kind == TT.WORD and t.value in ("infixl", "infixr", "infix", "prefix", "postfix"):
            return self._parse_fixity()

        # type alias
        if self._at(TT.RESERVED, "type"):
            return self._parse_type_alias()

        # kind declaration
        if self._at(TT.RESERVED, "kind"):
            return self._parse_kind()

        # implicit parameter declaration
        if self._at(TT.RESERVED, "implicit"):
            return self._parse_implicit()

        # `internal` — everything below this line is private to the file.
        if self._at(TT.RESERVED, "internal"):
            return self._parse_internal()

        # class declaration
        if self._at(TT.RESERVED, "class"):
            return self._parse_class()

        # instance declaration
        if self._at(TT.RESERVED, "instance"):
            return self._parse_instance()

        # A parenthesized operator name — `(++) : …` and `(++) xs ys = …`.
        # A class or instance member could always be named this way; a
        # top-level definition could not, so an operator with a default
        # fixity and no definition — `++` — was unusable *and* unfixable
        # (`fixme.md` F65).  Every operator in the language was therefore
        # either a class method or built into the compiler, which is a
        # blocker for music: `++`, `||`, `|*` and `|/` all need bodies.
        if self._at(TT.SEP, "("):
            name = self._parse_paren_op_name()
            if self._at(TT.SEP, ":"):
                return self._parse_sig(name, t.pos)
            return self._parse_sc_eqn_or_group(name, t.pos)

        # must be name-led: type-decl, sig, or sc-equation
        if t.kind not in (TT.WORD, TT.CONID):
            raise ParseError(f"expected declaration, got {t}", t.pos)

        name = self._adv().value
        start = t.pos

        # collect optional type params (for type decl)
        params: list[str] = []
        peek_i = self._i
        while peek_i < len(self._ts) and self._ts[peek_i].kind == TT.WORD:
            params.append(self._ts[peek_i].value)
            peek_i += 1

        # check what comes after name [+ params]
        next_t = self._ts[peek_i] if peek_i < len(self._ts) else None

        if next_t and next_t.kind == TT.SEP and next_t.value == ":=":
            # type declaration: consume params and `:=`
            for _ in params:
                self._adv()
            return self._parse_type_decl(name, params, start)

        # If `:` follows (directly, no extra params): type signature
        if self._at(TT.SEP, ":"):
            # note: we haven't consumed params yet, but sig has no params
            # so if there were WORDs between name and `:`, treat as pattern
            return self._parse_sig_or_sc(name, start)

        # Otherwise: supercombinator equation (name followed by patterns)
        return self._parse_sc_eqn_or_group(name, start)

    # ── Fixity ───────────────────────────────────────────────────────────

    def _parse_fixity(self) -> VFixity:
        mode = self._adv().value
        prec_t = self._eat(TT.NUMBER)
        try:
            prec = int(prec_t.value)
        except ValueError:
            raise ParseError(f"invalid precedence {prec_t.value!r}", prec_t.pos)
        if not (0 <= prec <= 20):
            raise ParseError(f"precedence must be 0..20, got {prec}", prec_t.pos)
        # An optional second precedence, for the right operand.  `infixl 3 6
        # |*` binds loosely enough on the left to take a whole phrase and
        # tightly enough on the right to take only a scaling factor.
        right = None
        if self._at(TT.NUMBER):
            right_t = self._adv()
            try:
                right = int(right_t.value)
            except ValueError:
                raise ParseError(
                    f"invalid precedence {right_t.value!r}", right_t.pos)
            if not (0 <= right <= 20):
                raise ParseError(
                    f"precedence must be 0..20, got {right}", right_t.pos)
            if mode in ("prefix", "postfix"):
                raise ParseError(
                    f"`{mode}` takes one precedence: it has only one operand",
                    right_t.pos)
        op_t = self._eat_either(TT.SYMBOL, TT.SEP)
        return VFixity(mode, prec, op_t.value,
                       Span(Pos(), op_t.span.end), right)

    # ── Kind ─────────────────────────────────────────────────────────────

    def _parse_internal(self) -> VInternal:
        """`internal`, alone on its line.  A marker, so there is nothing
        after it to parse — see `VInternal`."""
        t = self._eat(TT.RESERVED, "internal")
        return VInternal(Span(t.pos, t.pos))

    def _parse_kind(self) -> VKind:
        self._eat(TT.RESERVED, "kind")
        name = self._eat_either(TT.WORD, TT.CONID).value
        self._eat(TT.SEP, ":")
        k = self._parse_type()
        return VKind(name, k, Span(Pos(), k.span.end))

    # ── Type declaration ─────────────────────────────────────────────────

    def _parse_type_decl(self, name: str, params: list[str], start: Pos) -> VTypeDecl:
        self._eat(TT.SEP, ":=")
        ctors: list[VCtor] = []
        ctors.append(self._parse_ctor())
        # Comments as well as newlines: a trailing `# …` on a constructor
        # line left the `COMMENT` token in front of the `INDENT`, the loop
        # below never started, and the declaration silently ended after its
        # first constructor — so a *comment* decided whether the program
        # parsed (`fixme.md` F70).
        self._skip_trivia()
        self._try(TT.INDENT)
        while self._at(TT.SEP, "|"):
            self._adv()
            ctors.append(self._parse_ctor())
            self._skip_trivia()
        self._try(TT.DEDENT)
        end = ctors[-1].span.end
        derives = self._parse_deriving()
        return VTypeDecl(name, params, ctors, derives, Span(start, end))

    def _parse_deriving(self) -> list[str]:
        """``deriving (Show, Eq)`` or ``deriving Show``, both optional."""
        self._skip_nl()
        if not self._at(TT.RESERVED, "deriving"):
            return []
        self._adv()
        names: list[str] = []
        if self._at(TT.SEP, "("):
            self._adv()
            names.append(self._eat(TT.CONID).value)
            while self._at(TT.SEP, ","):
                self._adv()
                names.append(self._eat(TT.CONID).value)
            self._eat(TT.SEP, ")")
        else:
            names.append(self._eat(TT.CONID).value)
        return names

    def _parse_type_alias(self) -> VTypeAlias:
        start = self._eat(TT.RESERVED, "type").pos
        name = self._eat_either(TT.WORD, TT.CONID).value
        params: list[str] = []
        while self._at(TT.WORD):
            params.append(self._adv().value)
        self._eat(TT.SEP, "=")
        body = self._parse_type()
        return VTypeAlias(name, params, body, Span(start, body.span.end))

    def _parse_ctor(self) -> VCtor:
        constraints: list[Val] = []

        if self._at(TT.SEP, "("):
            saved = self._i
            self._adv()
            try:
                cons_val = self._parse_val()
                if self._at(TT.SEP, ","):
                    constraints = [cons_val]
                    while self._at(TT.SEP, ","):
                        self._adv()
                        constraints.append(self._parse_val())
                    if self._at(TT.SEP, ")"):
                        self._adv()
                        if not self._at(TT.SEP, "=>"):
                            self._i = saved
                            constraints = []
                    else:
                        self._i = saved
                        constraints = []
                elif self._at(TT.SEP, ")"):
                    self._adv()
                    if self._at(TT.SEP, "=>"):
                        self._adv()
                        constraints = [cons_val]
                    else:
                        self._i = saved
                else:
                    self._i = saved
            except ParseError:
                self._i = saved

        start = self._cur
        if start is None:
            raise ParseError("expected a constructor name, got end of file")
        if start.kind is TT.RESERVED:
            # `Shape := Box …` said only "expected constructor name", which
            # is true and unhelpful: `Box` is reserved (it is the box type,
            # term and pattern constructor) and the message never said so.
            raise ParseError(
                f"`{start.value}` is a reserved word, so it cannot name a "
                f"constructor — pick another name",
                start.pos)
        if start.kind not in (TT.WORD, TT.CONID):
            raise ParseError(
                f"expected a constructor name, got {start.value!r}",
                start.pos)
        name = self._adv().value

        fields: list[Val] = []
        while self._cur and self._cur.kind in (TT.WORD, TT.CONID, TT.SEP, TT.SYMBOL):
            if self._at(TT.SEP, "|") or self._at(TT.SEP, ":=") or self._at(TT.NEWLINE) or self._at(TT.EOF) or self._at(TT.DEDENT) or self._at(TT.INDENT):
                break
            fields.append(self._parse_atomic_type())
        end = fields[-1].span.end if fields else start.span.end
        return VCtor(name, fields, constraints, Span(start.pos, end))

    # ── Type signatures & SC equations ───────────────────────────────────

    def _parse_sig_or_sc(self, name: str, start: Pos) -> Val:
        """Parse either a type signature (`name : type`) or an SC equation.

        If `:` appears right after the name, it's a type signature.
        Otherwise try to parse patterns and find `=` for an SC equation.
        """
        if self._at(TT.SEP, ":"):
            return self._parse_sig(name, start)
        return self._parse_sc_eqn(name, start)

    def _parse_sig(self, name: str, start: Pos) -> VSig:
        self._eat(TT.SEP, ":")
        ty = self._parse_type()
        return VSig(name, ty, Span(start, ty.span.end))

    def _parse_implicit(self) -> VImplicit:
        """``implicit n : τ`` — one name, one type, at the top level."""
        start = self._cur.pos
        self._eat(TT.RESERVED, "implicit")
        if not self._at(TT.WORD):
            raise ParseError(
                f"`implicit` needs a name, got {self._cur}", self._cur.pos)
        name = self._adv().value
        self._eat(TT.SEP, ":")
        ty = self._parse_type()
        return VImplicit(name, ty, Span(start, ty.span.end))

    def _parse_sc_eqn_or_group(self, name: str, start: Pos) -> VSCDecl:
        """Parse one or more SC equations that share a name."""
        eqns: list[VSCEqn] = []
        eqns.append(self._parse_sc_eqn(name, start))
        self._skip_nl()
        while not self._at(TT.EOF):
            if self._at(TT.COMMENT):
                break
            if self._at(TT.WORD) and self._cur and self._cur.value == name:
                eqn_start = self._adv().pos
                eqns.append(self._parse_sc_eqn(name, eqn_start))
                self._skip_nl()
            elif self._at(TT.CONID) and self._cur and self._cur.value == name:
                eqn_start = self._adv().pos
                eqns.append(self._parse_sc_eqn(name, eqn_start))
                self._skip_nl()
            elif self._at(TT.SEP, "(") and self._peek_paren_op() == name:
                # A further clause of an operator definition, written the
                # same way as the first: `(++) [] ys = …`.
                eqn_start = self._cur.pos
                self._parse_paren_op_name()
                eqns.append(self._parse_sc_eqn(name, eqn_start))
                self._skip_nl()
            else:
                break
        end = eqns[-1].span.end
        return VSCDecl(name, None, eqns, Span(start, end))

    def _parse_sc_eqn(self, name: str, start: Pos) -> VSCEqn:
        """Parse a supercombinator equation: name (using ...)? pat* = body.
        The name token has already been consumed by the caller."""
        using_params: list[str] = []
        if self._at(TT.SEP, "("):
            saved = self._i
            self._adv()
            if self._at(TT.RESERVED, "using"):
                self._adv()
                while self._at(TT.WORD):
                    using_params.append(self._adv().value)
                if self._at(TT.SEP, ")"):
                    self._adv()
                else:
                    self._i = saved
                    using_params = []
            else:
                self._i = saved

        pats: list[Pat] = []
        while not self._at(TT.SEP, "=") and not self._at(TT.EOF):
            if self._at(TT.RESERVED, "where"):
                break
            if self._at(TT.NEWLINE):
                break
            # A parameter list takes *atoms*: `f Nothing (x :: xs)` is two
            # parameters.  Anything bigger needs parentheses, as in Haskell.
            pats.append(self._parse_pat_atom())
        self._eat(TT.SEP, "=")
        body = self._parse_val()
        end = body.span.end
        return VSCEqn(name, pats, body, using_params, Span(start, end))

    # ── Patterns ─────────────────────────────────────────────────────────

    # Patterns follow Haskell's three levels.  Keeping them apart is what
    # lets a constructor take parenthesized sub-patterns (`Just (Just x)`)
    # without a *parameter list* swallowing the next parameter: `f Nothing
    # (x :: xs)` is two arguments, not `Nothing` applied to one.
    #
    #   pat   ::= pat10 [ '::' pat | ':::' pat ]      -- infix
    #   pat10 ::= CONID apat*  |  apat                -- application
    #   apat  ::= var | '_' | literal | CONID | '(' pat ')' | '[' pats ']'

    def _parse_pat(self) -> Pat:
        pat = self._parse_pat_app()
        while self._at(TT.SEP, "::") or self._at(TT.SEP, ":::"):
            sep = self._cur.value
            self._adv()
            tail = self._parse_pat()
            span = Span(pat.span.start, tail.span.end)
            pat = (PSigCons(pat, tail, span) if sep == ":::"
                   else PList([pat], tail, span))
        return pat

    def _parse_pat_app(self) -> Pat:
        t = self._cur
        if t is not None and t.kind == TT.CONID:
            name = self._adv().value
            start = t.pos
            args: list[Pat] = []
            while self._can_start_pat(self._cur) and not self._at(TT.RESERVED):
                args.append(self._parse_pat_atom())
            end = args[-1].span.end if args else Pos(start.line, start.col + len(name))
            return PCon(name, args, Span(start, end))
        return self._parse_pat_atom()

    def _parse_pat_atom(self) -> Pat:
        t = self._cur
        if t is None:
            raise ParseError("expected pattern, got EOF")

        # parenthesized pattern
        if self._at(TT.SEP, "("):
            return self._parse_pat_paren()

        # list pattern
        if self._at(TT.SEP, "["):
            return self._parse_pat_list()

        # box pattern `Box p` — Datafun's `[p]`, which cannot be spelled
        # that way here because `[p]` is a one-element list pattern.  It
        # takes exactly one *atomic* sub-pattern, like a constructor would.
        if self._at(TT.RESERVED, "Box"):
            start = self._adv().pos
            inner = self._parse_pat_atom()
            return PBox(inner, Span(start, inner.span.end))

        # a bare constructor — its arguments, if any, are read by
        # `_parse_pat_app`, so an *atom* is always nullary
        if t.kind == TT.CONID:
            tok = self._adv()
            end = Pos(tok.pos.line, tok.pos.col + len(tok.value))
            return PCon(tok.value, [], Span(tok.pos, end))

        # literal
        if t.kind == TT.NUMBER:
            tok = self._adv()
            return PLit(self._parse_number(tok), tok.span)

        if t.kind == TT.STRING:
            tok = self._adv()
            return PLit(tok.value, tok.span)

        # variable
        if t.kind == TT.WORD:
            tok = self._adv()
            return PVar(tok.value, tok.span)

        raise ParseError(f"expected pattern, got {t}", t.pos)

    def _parse_pat_paren(self) -> Pat:
        start = self._eat(TT.SEP, "(").pos
        pats: list[Pat] = []
        pats.append(self._parse_pat())
        if self._at(TT.SEP, ","):
            while self._at(TT.SEP, ","):
                self._adv()
                pats.append(self._parse_pat())
        if self._at(TT.SEP, ":"):
            self._adv()
            ty = self._parse_type()
            end = self._eat(TT.SEP, ")").span.end
            pat = PTuple(pats, Span(start, end)) if len(pats) > 1 else pats[0]
            return PAnnot(pat, ty, Span(start, end))
        end = self._eat(TT.SEP, ")").span.end
        if len(pats) > 1:
            return PTuple(pats, Span(start, end))
        return pats[0]

    def _parse_pat_list(self) -> Pat:
        start = self._eat(TT.SEP, "[").pos
        if self._at(TT.SEP, "]"):
            end = self._adv().span.end
            return PList([], None, Span(start, end))
        items: list[Pat] = []
        items.append(self._parse_pat())
        while self._at(TT.SEP, ","):
            self._adv()
            items.append(self._parse_pat())
        tail: Pat | None = None
        if self._at(TT.SEP, "|"):
            self._adv()
            tail = self._parse_pat()
        end = self._eat(TT.SEP, "]").span.end
        return PList(items, tail, Span(start, end))

    # ── Values (expressions) ─────────────────────────────────────────────

    def _parse_val(self) -> Val:
        return self._parse_op_phrase()

    def _parse_op_phrase(self) -> Val:
        """Parse an expression as a flat operator phrase.

        Structure: segment (SYMBOL_SEP segment)*
        where SYMBOL_SEP is a SYMBOL token or a SEP token that acts as infix operator.
        If only one segment, return it directly. Otherwise return VOpPhrase.
        """
        segments: list[Val] = []
        ops: list[T] = []

        seg = self._parse_segment()
        segments.append(seg)

        while self._cur and self._is_infix_op(self._cur):
            ops.append(self._adv())
            seg = self._parse_segment()
            segments.append(seg)

        if len(segments) == 1:
            return segments[0]

        atoms: list[Val | str] = []
        for i, seg in enumerate(segments):
            atoms.append(seg)
            if i < len(ops):
                atoms.append(ops[i].value)

        start = segments[0].span.start
        end = segments[-1].span.end
        return VOpPhrase(atoms, Span(start, end))

    def _is_infix_op(self, t: T) -> bool:
        """Check if token can act as an infix operator in the current context."""
        if t.kind == TT.SYMBOL:
            return True
        if t.kind == TT.SEP and t.value in ("::", "->", ":::", ".."):
            return True
        # `|` is *not* an expression operator.  It separates a list's items
        # from its tail (`[x | xs]`), an ADT's constructors, and (later) a
        # guard from its equation — all of which read it directly.  Treating
        # it as infix here made `_parse_val` swallow it, which is why the
        # expression-side tail syntax never worked: `[1 | xs]` parsed as a
        # one-element list holding `1 | xs`.
        return False

    def _parse_segment(self) -> Val:
        """Parse a segment: prefix_ops* (lambda | app_expr) postfix_ops*."""
        prefix_ops: list[str] = []
        while self._cur and self._is_prefix_op(self._cur):
            # `!` binds the *next atom*, not the segment — stop collecting
            # and let `_parse_app_expr` take it as the head, so `!f x` is
            # `(!f) x` and `!(f x)` keeps its parentheses in the tree.
            if self._marks_head(self._cur):
                break
            prefix_ops.append(self._adv().value)

        # Try to parse a lambda: `pat+ => body`
        saved = self._i
        pats = self._try_parse_pats()
        if pats is not None and self._at(TT.SEP, "=>"):
            self._adv()
            body = self._parse_val()
            val: Val = VFunc(pats, body, Span(pats[0].span.start, body.span.end))
        else:
            self._i = saved
            val = self._parse_app_expr()

        for op in reversed(prefix_ops):
            val = VOpPhrase([op, val], Span(Pos(), val.span.end))

        while self._cur and self._is_postfix_op(self._cur):
            op = self._adv()
            val = VOpPhrase([val, op.value], Span(val.span.start, op.span.end))

        return val

    def _try_parse_pats(self) -> list[Pat] | None:
        """Try parsing one or more patterns. Returns None if the first
        token cannot start a pattern or if parsing fails."""
        try:
            pats: list[Pat] = []
            if not self._can_start_pat(self._cur):
                return None
            # Full patterns, not atoms: this path also reads a signature's
            # class context, where `Sum a => …` parses the constraint as a
            # `VFunc` parameter (see `desugar_signature`).
            pats.append(self._parse_pat())
            while self._can_start_pat(self._cur):
                pats.append(self._parse_pat())
            return pats
        except ParseError:
            return None

    def _can_start_pat(self, t: T | None) -> bool:
        if t is None:
            return False
        if t.kind in (TT.WORD, TT.CONID, TT.NUMBER, TT.STRING):
            return True
        if t.kind == TT.SEP and t.value in ("(", "[",):
            return True
        return False

    def _is_prefix_op(self, t: T) -> bool:
        if t.kind == TT.SYMBOL:
            return True
        return False

    def _is_postfix_op(self, t: T) -> bool:
        """Check for postfix operator after an expression. Must be followed by
        an infix operator or end-of-expression token to avoid ambiguity with
        the start of a new segment."""
        if t.kind != TT.SYMBOL:
            return False
        # …and must actually *be* a postfix operator.  Without this, any
        # symbol followed by another symbol read as postfix, so in
        # `'a ++ 'b` the `++` — followed by the prefix `'` — was taken as
        # a postfix use and the phrase came out as `(('a)++) ' b`
        # (`fixme.md` F59).  `++ '` is ambiguous between "infix then
        # prefix" and "postfix then infix"; only the first is ever what a
        # program means, and a sequence of notes is nothing else.
        if t.value not in _POSTFIX_OPS:
            return False
        lookahead = self._ts[self._i + 1] if self._i + 1 < len(self._ts) else None
        if lookahead is None:
            return True
        if lookahead.kind in (TT.NEWLINE, TT.EOF, TT.DEDENT, TT.INDENT, TT.COMMENT):
            return True
        if lookahead.kind == TT.SEP and lookahead.value in (")", "]", "}", ",", ";", "in", "of"):
            return True
        if self._is_infix_op(lookahead):
            return True
        if lookahead.kind == TT.RESERVED:
            return True
        return False

    def _parse_app_expr(self) -> Val:
        """Parse an application expression: atom+ (. INT | . WORD)*

        Multiple consecutive atoms form left-nested application.
        Projections (`.0`, `.field`) bind tightly to the preceding atom.
        """
        if self._cur is not None and self._marks_head(self._cur):
            # `!f x` — the marker takes one atom, the head, exactly as it
            # does in argument position below.  The application it heads
            # is then folded by this loop like any other, so `!f x` and
            # `!(f x)` are *different* trees: the first lifts `f` over
            # `x`, the second is the constant signal of `f x`.
            op = self._adv()
            inner = self._parse_projections(self._parse_atom())
            val: Val = VOpPhrase([op.value, inner],
                                 Span(op.pos, inner.span.end))
        else:
            val = self._parse_projections(self._parse_atom())
        while self._cur:
            if self._can_start_atom(self._cur):
                arg = self._parse_projections(self._parse_atom())
            elif self._starts_prefix_arg():
                # `f 'x` — a prefix-only operator applied to the atom after
                # it, taken whole as one argument.  The operand is an atom,
                # not a phrase, so `f 'x ++ 'y` still sequences: the `++`
                # belongs to the phrase around the application.
                op = self._adv()
                inner = self._parse_projections(self._parse_atom())
                arg = VOpPhrase([op.value, inner],
                                Span(op.pos, inner.span.end))
            else:
                break
            val = VApp(val, arg, Span(val.span.start, arg.span.end))
        return val

    def _starts_prefix_arg(self) -> bool:
        """Is the parser looking at `'x` where an argument may stand?"""
        t = self._cur
        if t is None or t.kind != TT.SYMBOL or t.value not in _PREFIX_ONLY_OPS:
            return False
        nxt = self._ts[self._i + 1] if self._i + 1 < len(self._ts) else None
        return nxt is not None and self._can_start_atom(nxt)

    def _marks_head(self, t: T) -> bool:
        """Is `t` a `!` about to mark the head of an application?

        Only `!` — `'` and `|<` keep their phrase behaviour.  The marker
        binding one atom is what lets parentheses distinguish `!f x`
        (lift `f` over `x`) from `!(f x)` (the constant signal of the
        value `f x`): the parens are not recorded anywhere, they simply
        change which atom follows the marker, the same way they change
        which atom follows `f` in `f (g x)`.
        """
        if t.kind != TT.SYMBOL or t.value != "!":
            return False
        nxt = self._ts[self._i + 1] if self._i + 1 < len(self._ts) else None
        return nxt is not None and self._can_start_atom(nxt)

    def _parse_projections(self, val: Val) -> Val:
        """Attach any `.0` / `.field` suffixes to the atom just parsed.

        Per *atom*, which is what the surrounding docstring always claimed
        and what the code did not do: the loop used to run after the whole
        application, so `show p.1` read as `(show p).1`.  Nothing could
        depend on that — projection did nothing at all until `fixme.md` F28
        — and `f x.0` meaning `f (x.0)` is the only sensible reading.
        """
        while self._at(TT.SEP, "."):
            dot_tok = self._adv()
            if self._at(TT.NUMBER):
                idx_tok = self._adv()
                try:
                    idx = int(idx_tok.value)
                except ValueError:
                    idx = 0
                val = VProj(val, idx, Span(val.span.start, idx_tok.span.end))
            elif self._at(TT.WORD) or self._at(TT.CONID):
                field = self._adv()
                val = VProj(val, field.value, Span(val.span.start, field.span.end))
            else:
                raise ParseError(
                    f"expected field index or name after '.', got {self._cur}",
                    dot_tok.pos)
        return val

    def _can_start_atom(self, t: T) -> bool:
        """Check if t can start an atom (for application parsing)."""
        if t.kind in (TT.WORD, TT.CONID, TT.NUMBER, TT.STRING, TT.COMMENT):
            return True
        if t.kind == TT.SEP and t.value in ("(", "[", "{"):
            return True
        if t.kind == TT.RESERVED and t.value in ("let", "letrec", "given", "case", "for", "fix", "gfix", "unbox", "Box"):
            return True
        return False

    def _parse_atom(self) -> Val:
        t = self._cur
        if t is None:
            raise ParseError("expected atom, got EOF")

        # comment
        if t.kind == TT.COMMENT:
            return self._parse_comment()

        # parenthesized
        if self._at(TT.SEP, "("):
            return self._parse_paren()

        # list
        if self._at(TT.SEP, "["):
            return self._parse_list()

        # set / eq-set / score-type
        if self._at(TT.SEP, "{"):
            return self._parse_brace()

        # keywords
        if t.kind == TT.RESERVED:
            return self._parse_keyword_atom()

        # identifiers
        if t.kind == TT.WORD:
            tok = self._adv()
            return VWord(tok.value, tok.span)

        if t.kind == TT.CONID:
            tok = self._adv()
            return VConId(tok.value, tok.span)

        # literals
        if t.kind == TT.NUMBER:
            tok = self._adv()
            return VNum(self._parse_number(tok), tok.span)

        if t.kind == TT.STRING:
            tok = self._adv()
            return VStr(tok.value, tok.span)

        raise ParseError(f"expected atom, got {t}", t.pos)

    @staticmethod
    def _parse_number(tok: T) -> int | float:
        raw = tok.value
        if raw.startswith("0x") or raw.startswith("0X"):
            return int(raw, 16)
        if "." in raw or "e" in raw.lower():
            return float(raw)
        return int(raw)

    def _parse_comment(self) -> VComment:
        tok = self._eat(TT.COMMENT)
        return VComment(tok.value, tok.span)

    def _parse_paren(self) -> Val:
        start_pos = self._eat(TT.SEP, "(").pos

        # empty
        if self._at(TT.SEP, ")"):
            end = self._adv().span.end
            return VTuple([], Span(start_pos, end))

        # operator reference: (+), (+_), (_+)
        op_ref = self._try_parse_op_ref(start_pos)
        if op_ref is not None:
            return op_ref

        # Try to parse as value first
        val = self._parse_val()

        # lambda: (Pat+ => Val)
        if self._at(TT.SEP, "=>"):
            self._adv()
            pats = self._collect_pats(val)
            body = self._parse_val()
            end = self._eat(TT.SEP, ")").span.end
            return VFunc(pats, body, Span(start_pos, end))

        # comma: tuple, constraint, or nothing
        if self._at(TT.SEP, ","):
            constraints = [val]
            while self._at(TT.SEP, ","):
                self._adv()
                constraints.append(self._parse_val())
            if self._at(TT.SEP, ")"):
                self._adv()
                if self._at(TT.SEP, "=>"):
                    self._adv()
                    body = self._parse_val()
                    return VConstraint(constraints, body, Span(start_pos, body.span.end))
                return VTuple(constraints, Span(start_pos, constraints[-1].span.end))
            end = self._eat(TT.SEP, ")").span.end
            return VTuple(constraints, Span(start_pos, end))

        # type annotation: (val : type)
        if self._at(TT.SEP, ":"):
            self._adv()
            ty = self._parse_type()
            end = self._eat(TT.SEP, ")").span.end
            return VAnnot(val, ty, Span(start_pos, end))

        # simple parenthesized expr
        end = self._eat(TT.SEP, ")").span.end
        return val

    def _try_parse_op_ref(self, start_pos: Pos) -> Val | None:
        """Try to parse an operator reference: (+)  (+_)  (_+)"""
        saved = self._i

        # (+): infix operator reference, or (+_): prefix operator reference
        if self._at(TT.SYMBOL):
            op = self._adv().value
            if self._at(TT.SEP, ")"):
                return VOpPhrase([op], Span(start_pos, self._adv().span.end))
            if self._at(TT.WORD) and self._cur is not None and self._cur.value == "_":
                self._adv()
                if self._at(TT.SEP, ")"):
                    return VOpPhrase([op, VWord("_", Span())], Span(start_pos, self._adv().span.end))
            self._i = saved

        # (_+): postfix operator reference
        if self._at(TT.WORD) and self._cur is not None and self._cur.value == "_":
            self._adv()
            if self._at(TT.SYMBOL):
                op = self._adv().value
                if self._at(TT.SEP, ")"):
                    return VOpPhrase([VWord("_", Span()), op], Span(start_pos, self._adv().span.end))
            self._i = saved

        return None

    @staticmethod
    def _collect_pats(val: Val) -> list[Pat]:
        """Flatten a value chain into a list of patterns (for lambda params)."""
        if isinstance(val, PVar):
            return [val]
        if isinstance(val, VWord):
            return [PVar(val.value, val.span)]
        if isinstance(val, VApp):
            lhs = Parser._collect_pats(val.fn)
            if lhs and isinstance(lhs[-1], PCon):
                lhs[-1].args.append(Parser._to_pat(val.arg))
                return lhs
            return lhs + [Parser._to_pat(val.arg)]
        if isinstance(val, VTuple):
            pats: list[Pat] = []
            for item in val.items:
                pats.extend(Parser._collect_pats(item))
            return pats
        return [Parser._to_pat(val)]

    @staticmethod
    def _to_pat(val: Val) -> Pat:
        if isinstance(val, VWord):
            return PVar(val.value, val.span)
        if isinstance(val, VConId):
            return PCon(val.value, [], val.span)
        if isinstance(val, VApp):
            pats = Parser._collect_pats(val)
            if len(pats) == 1:
                return pats[0]
            return PTuple(pats, val.span)
        if isinstance(val, VNum):
            return PLit(val.value, val.span)
        if isinstance(val, VStr):
            return PLit(val.value, val.span)
        if isinstance(val, VTuple):
            return PTuple([Parser._to_pat(i) for i in val.items], val.span)
        return PVar("_", val.span)

    def _parse_list(self) -> Val:
        start = self._eat(TT.SEP, "[").pos

        if self._at(TT.SEP, "]"):
            end = self._adv().span.end
            return VList([], None, Span(start, end))

        # `[: a :]` — the Score type (`syntax.md`, `music.md`).  This branch
        # used to read `[: a ]` and build a *List*, which meant the closing
        # `:]` was a parse error and `[: a :]` — the syntax both specs give
        # for `Score` — could not be written in a signature at all.  Type
        # annotations are parsed with the *expression* grammar and converted
        # afterwards, so this is the copy that matters; the one in
        # `_parse_atomic_type` is reached only from an instance head.
        if self._at(TT.SEP, ":"):
            self._adv()
            ty = self._parse_type()
            self._eat(TT.SEP, ":")
            end = self._eat(TT.SEP, "]").span.end
            return VApp(VConId("Score", Span(start, start)), ty, Span(start, end))

        first = self._parse_val()
        if self._at(TT.SEP, ","):
            items = [first]
            while self._at(TT.SEP, ","):
                self._adv()
                items.append(self._parse_val())
            tail: Val | None = None
            if self._at(TT.SEP, "|"):
                self._adv()
                if not self._at(TT.SEP, "]"):
                    tail = self._parse_val()
            end = self._eat(TT.SEP, "]").span.end
            return VList(items, tail, Span(start, end))

        if self._at(TT.SEP, "|"):
            self._adv()
            tail = self._parse_val()
            end = self._eat(TT.SEP, "]").span.end
            return VList([first], tail, Span(start, end))

        end = self._eat(TT.SEP, "]").span.end
        return VList([first], None, Span(start, end))

    def _parse_brace(self) -> Val:
        start = self._eat(TT.SEP, "{").pos

        if self._at(TT.SEP, "}"):
            end = self._adv().span.end
            return VSet([], Span(start, end))

        if self._at(TT.SEP, ":"):
            return self._parse_eq_set(start)

        first = self._parse_val()

        # `{e | C}` — the comprehension.  Fig. 2.2 defines it as `for (C) {e}`
        # and that is exactly what it becomes, so everything downstream sees
        # an ordinary `for` over an ordinary singleton.
        if self._at(TT.SEP, "|"):
            self._adv()
            clauses = self._parse_clauses()
            end = self._eat(TT.SEP, "}").span.end
            span = Span(start, end)
            return VFor(clauses, VSet([first], span), span)

        items = [first]
        while self._at(TT.SEP, ","):
            self._adv()
            items.append(self._parse_val())
        end = self._eat(TT.SEP, "}").span.end
        return VSet(items, Span(start, end))

    def _parse_eq_set(self, start: Pos) -> Val:
        self._eat(TT.SEP, ":")
        if self._at(TT.SEP, ":"):
            end = self._adv().span.end
            self._eat(TT.SEP, "}")
            return VConId("EqSet", Span(start, end))
        if self._at(TT.SEP, "}"):
            end = self._adv().span.end
            return VApp(VConId("EqSet", Span(start, start)), VTuple([], Span(start, end)), Span(start, end))
        ty = self._parse_type()
        if self._at(TT.SEP, ","):
            items = [ty]
            while self._at(TT.SEP, ","):
                self._adv()
                items.append(self._parse_val())
            if self._at(TT.SEP, ":"):
                self._adv()
                if self._at(TT.SEP, "}"):
                    end = self._adv().span.end
                    return VApp(VConId("EqSet", Span(start, start)), VTuple(items, Span(start, end)), Span(start, end))
            end = self._eat(TT.SEP, "}").span.end
            return VApp(VConId("EqSet", Span(start, start)), VTuple(items, Span(start, end)), Span(start, end))
        end = self._eat(TT.SEP, ":")
        end_pos = end.span.end
        self._eat(TT.SEP, "}")
        return VApp(VConId("EqSet", Span(start, start)), ty, Span(start, end_pos))

    def _parse_keyword_atom(self) -> Val:
        kw = self._cur
        assert kw is not None

        if kw.value == "let":
            return self._parse_let(False)
        if kw.value == "letrec":
            return self._parse_let(True)
        if kw.value == "given":
            return self._parse_given()
        if kw.value == "case":
            return self._parse_case()
        if kw.value == "for":
            return self._parse_for()
        if kw.value == "fix":
            return self._parse_fix()
        if kw.value == "gfix":
            return self._parse_gfix()
        if kw.value == "unbox":
            return self._parse_unbox()
        if kw.value == "Box":
            return self._parse_box()

        raise ParseError(f"unexpected keyword {kw.value}", kw.pos)

    # ── Let / Letrec ─────────────────────────────────────────────────────

    def _parse_let(self, is_rec: bool) -> VLet:
        start = self._adv().pos  # consume let/letrec
        bindings: list[tuple[str, Val]] = []
        self._skip_nl()
        if self._at(TT.INDENT):
            self._adv()
            while not self._at(TT.DEDENT) and not self._at(TT.EOF):
                self._skip_nl()
                if self._at(TT.DEDENT) or self._at(TT.EOF):
                    break
                bindings.append(self._parse_binding())
                self._skip_nl()
            if self._at(TT.DEDENT):
                self._adv()
        else:
            bindings.append(self._parse_binding())
            self._skip_nl()
            # `;` and `,` both separate: `given` reads as `let`, and a
            # comma is what a reader writes for several bindings on a line.
            if self._at(TT.SEP, ";") or self._at(TT.SEP, ","):
                while self._at(TT.SEP, ";") or self._at(TT.SEP, ","):
                    self._adv()
                    self._skip_nl()
                    bindings.append(self._parse_binding())
                    self._skip_nl()
            elif self._at(TT.INDENT):
                self._adv()
                while not self._at(TT.DEDENT) and not self._at(TT.EOF):
                    self._skip_nl()
                    if self._at(TT.DEDENT) or self._at(TT.EOF):
                        break
                    bindings.append(self._parse_binding())
                    self._skip_nl()
                if self._at(TT.DEDENT):
                    self._adv()
        self._skip_nl()
        self._eat(TT.RESERVED, "in")
        body = self._parse_val()
        end = body.span.end
        return VLet(is_rec, bindings, body, Span(start, end))

    def _parse_binding(self) -> tuple[str, Val]:
        name = self._eat(TT.WORD).value
        self._eat(TT.SEP, "=")
        val = self._parse_val()
        return (name, val)

    # ── Given ─────────────────────────────────────────────────────────────

    def _parse_given(self) -> VGiven:
        start = self._eat(TT.RESERVED, "given").pos
        bindings: list[tuple[str, Val]] = []
        self._skip_nl()
        if self._at(TT.INDENT):
            self._adv()
            while not self._at(TT.DEDENT) and not self._at(TT.EOF):
                self._skip_nl()
                if self._at(TT.DEDENT) or self._at(TT.EOF):
                    break
                bindings.append(self._parse_binding())
                self._skip_nl()
            if self._at(TT.DEDENT):
                self._adv()
        else:
            bindings.append(self._parse_binding())
            self._skip_nl()
            # `;` and `,` both separate: `given` reads as `let`, and a
            # comma is what a reader writes for several bindings on a line.
            if self._at(TT.SEP, ";") or self._at(TT.SEP, ","):
                while self._at(TT.SEP, ";") or self._at(TT.SEP, ","):
                    self._adv()
                    self._skip_nl()
                    bindings.append(self._parse_binding())
                    self._skip_nl()
            elif self._at(TT.INDENT):
                self._adv()
                while not self._at(TT.DEDENT) and not self._at(TT.EOF):
                    self._skip_nl()
                    if self._at(TT.DEDENT) or self._at(TT.EOF):
                        break
                    bindings.append(self._parse_binding())
                    self._skip_nl()
                if self._at(TT.DEDENT):
                    self._adv()
        self._skip_nl()
        self._eat(TT.RESERVED, "in")
        body = self._parse_val()
        end = body.span.end
        return VGiven(bindings, body, Span(start, end))

    # ── Case ─────────────────────────────────────────────────────────────

    def _parse_case(self) -> VCase:
        start = self._eat(TT.RESERVED, "case").pos
        scrut = self._parse_val()
        self._eat(TT.RESERVED, "of")
        self._skip_nl()
        if self._at(TT.INDENT):
            self._adv()
        alts: list[VAlt] = []

        def alt() -> None:
            # An alternative whose body is itself a block leaves that
            # block's `DEDENT` behind; without closing it here the *outer*
            # `case` would read it as its own end, and every alternative
            # after a nested one fell out of the match.
            #
            # Trivia, not newlines: a comment between two alternatives is a
            # comment, and reading it as the start of a pattern rejected a
            # `case` that anyone would write.  A comment at the *outer*
            # indentation still ends the block, because the tokenizer emits
            # the `DEDENT` before it.
            self._skip_trivia()
            start_i = self._i
            alts.append(self._parse_alt())
            self._close_inner_blocks(start_i)
            self._skip_trivia()

        def at_end() -> bool:
            # A `case` written on one line inside brackets has no block to
            # close, so it never reaches the `DEDENT` machinery F45 added
            # for the multi-line form — the alternative loop ran on and
            # read the closing bracket as the start of another pattern
            # (`fixme.md` F72).
            return (self._at(TT.DEDENT) or self._at(TT.EOF)
                    or any(self._at(TT.SEP, c) for c in (")", "]", "}", ",")))

        alt()
        while not at_end():
            if self._at(TT.SEP, ";"):
                self._adv()
                self._skip_nl()
            alt()
            if at_end():
                break
        # Leave DEDENT unconsumed — the caller's application-parsing
        # loop will see it and stop, preventing spurious consumption
        # of subsequent top-level declarations as function arguments.
        end = alts[-1].body.span.end
        return VCase(scrut, alts, Span(start, end))

    def _parse_alt(self) -> VAlt:
        start_p = self._cur.pos if self._cur else Pos()
        pat = self._parse_pat()
        self._eat(TT.SEP, "->")
        body = self._parse_val()
        return VAlt(pat, body, Span(start_p, body.span.end))

    # ── For ──────────────────────────────────────────────────────────────

    def _parse_for(self) -> VFor:
        start = self._eat(TT.RESERVED, "for").pos
        self._eat(TT.SEP, "(")
        bindings = self._parse_clauses()
        self._eat(TT.SEP, ")")
        body = self._parse_val()
        return VFor(bindings, body, Span(start, body.span.end))

    def _parse_clauses(self) -> list[tuple[Pat, Val]]:
        """Fig. 2.2's `C ::= p ∈ e | e | C,D` — the comma-separated clauses
        shared by `for (C) e` and the comprehension `{e | C}`."""
        clauses = [self._parse_clause()]
        while self._at(TT.SEP, ","):
            self._adv()
            clauses.append(self._parse_clause())
        return clauses

    def _parse_clause(self) -> tuple[Pat, Val]:
        """One clause: a binding `p in e`, or a bare boolean guard `e`.

        Which one it is cannot be decided by the first token — `x` begins
        both a pattern and an expression — so a binding is *attempted* and
        the guard is the fallback.  Backtracking is free here: the token
        list is fully materialised, so restoring `_i` restores everything.
        """
        saved = self._i
        try:
            pat = self._parse_pat()
            if self._at(TT.RESERVED, "in"):
                self._adv()
                return (pat, self._parse_val())
        except ParseError:
            pass
        self._i = saved
        return self._guard_clause(self._parse_val())

    def _guard_clause(self, val: Val) -> tuple[Pat, Val]:
        """`for (e) f` ⇝ `for (x ∈ guard e) f` at a fresh, unused `x`.

        The `for`-over-a-boolean *is* fig. 2.2's one-sided conditional, so a
        guard needs no construct of its own: it is a binding whose variable
        the body never mentions, over a set that is either `{()}` or `{}`.

        `guard` is the class method, not a coercion built in here, so the
        clause accepts either boolean — `Prop` at the identity, `Bool` by
        `case` (`errata.md` D5).  Doing it with a class rather than by
        inspecting the type is what lets this run in the *parser*: types do
        not exist yet, and will not until long after desugaring.
        """
        self._guard_n += 1
        span = val.span
        # `#` cannot occur in an identifier — it opens a comment — so the
        # binder is unwritable rather than merely unlikely, and the body can
        # never read it in place of one of its own names.
        return (PVar(f"_guard{self._guard_n}#", span),
                VApp(VWord("guard", span), val, span))

    # ── Fix / Gfix ─────────────────────────────────────────────────────

    def _parse_fix(self) -> VFix:
        start = self._eat(TT.RESERVED, "fix").pos
        body = self._parse_val()
        # `fix r => e` — and the parenthesised `fix (r => e)` — is sugar for
        # `fix Box (r => e)`.  `fix` wants a *boxed* monotone function, and
        # an unboxed lambda here could never be well-typed, so there is no
        # form this steals: it only makes the box stop being busywork.
        if isinstance(body, VFunc):
            body = VBox(body, body.span)
        return VFix(body, Span(start, body.span.end))

    def _parse_gfix(self) -> VGfix:
        start = self._eat(TT.RESERVED, "gfix").pos
        var = self._eat(TT.WORD).value
        self._eat(TT.SEP, "=>")
        body = self._parse_val()
        return VGfix(var, body, Span(start, body.span.end))

    # ── Unbox ────────────────────────────────────────────────────────────

    def _parse_unbox(self) -> VUnbox:
        start = self._eat(TT.RESERVED, "unbox").pos
        pat = self._parse_pat()
        self._eat(TT.SEP, "=")
        binding = self._parse_val()
        self._eat(TT.RESERVED, "in")
        body = self._parse_val()
        return VUnbox(pat, binding, body, Span(start, body.span.end))

    # ── Box ──────────────────────────────────────────────────────────────

    def _parse_box(self) -> VBox:
        start = self._eat(TT.RESERVED, "Box").pos
        body = self._parse_atom()
        return VBox(body, Span(start, body.span.end))

    # ── Types ────────────────────────────────────────────────────────────

    def _parse_type(self) -> Val:
        """Parse a type expression. Uses same value grammar but stops at
        certain delimiters."""
        return self._parse_op_phrase()

    def _parse_atomic_type(self) -> Val:
        t = self._cur
        if t is None:
            raise ParseError("expected type, got EOF")

        if t.kind == TT.WORD:
            tok = self._adv()
            return VWord(tok.value, tok.span)
        if t.kind == TT.CONID:
            tok = self._adv()
            return VConId(tok.value, tok.span)
        if self._at(TT.SEP, "("):
            start = self._eat(TT.SEP, "(").pos
            # `()` is the unit type, fig. 2.1's `1`.  Expression space has
            # always had the value; type space rejected it, which is why
            # `Prop = {()}` could not be written (`errata.md` D5).
            if self._at(TT.SEP, ")"):
                end = self._eat(TT.SEP, ")").span.end
                return VTuple([], Span(start, end))
            ty = self._parse_type()
            if self._at(TT.SEP, ","):
                items = [ty]
                while self._at(TT.SEP, ","):
                    self._adv()
                    items.append(self._parse_type())
                end = self._eat(TT.SEP, ")").span.end
                return VTuple(items, Span(start, end))
            end = self._eat(TT.SEP, ")").span.end
            return ty
        if self._at(TT.SEP, "["):
            start = self._eat(TT.SEP, "[").pos
            if self._at(TT.SEP, ":"):
                return self._parse_score_type(start)
            ty = self._parse_type()
            end = self._eat(TT.SEP, "]").span.end
            return VApp(VConId("List", Span(start, start)), ty, Span(start, end))
        raise ParseError(f"expected type, got {t}", t.pos)

    def _parse_score_type(self, start: Pos) -> Val:
        self._eat(TT.SEP, ":")
        ty = self._parse_type()
        self._eat(TT.SEP, ":")
        end = self._eat(TT.SEP, "]").span.end
        return VApp(VConId("Score", Span(start, start)), ty, Span(start, end))

    # ── Class ────────────────────────────────────────────────────────────

    def _parse_class(self) -> VClass:
        start = self._eat(TT.RESERVED, "class").pos

        # Optional superclass context, spelled like an instance's:
        # `class (Eq a, Show a) => Ord a where` or `class Eq a => Ord a where`.
        context: list[Val] = []
        if self._at(TT.SEP, "("):
            saved = self._i
            group = self._parse_atomic_type()
            if self._at(TT.SEP, "=>"):
                self._adv()
                context = list(group.items) if isinstance(group, VTuple) \
                    else [group]
            else:
                self._i = saved

        name = self._eat_either(TT.WORD, TT.CONID).value
        params: list[str] = []
        while self._at(TT.WORD):
            params.append(self._adv().value)
        if self._at(TT.SEP, "=>"):
            # Unparenthesized single superclass: what we just read was it.
            self._adv()
            context.append(_apply_all(VConId(name, Span(start, start)),
                                      [VWord(p, Span(start, start))
                                       for p in params]))
            name = self._eat_either(TT.WORD, TT.CONID).value
            params = []
            while self._at(TT.WORD):
                params.append(self._adv().value)

        self._eat(TT.RESERVED, "where")
        self._expect_indent()
        members: list[Val] = []
        while not self._at(TT.DEDENT) and not self._at(TT.EOF):
            while self._at(TT.COMMENT):
                members.append(self._parse_comment())
                self._skip_nl()
            if self._at(TT.DEDENT) or self._at(TT.EOF):
                break
            if self._at(TT.NEWLINE):
                self._adv()
                continue
            _member_start = self._i
            members.append(self._parse_class_member())
            self._close_inner_blocks(_member_start)
            self._skip_nl()
        if self._at(TT.DEDENT):
            self._adv()
        end = members[-1].span.end if members else Pos()
        return VClass(name, params, members, context, Span(start, end))

    def _parse_class_member(self) -> Val:
        if not self._cur:
            raise ParseError("expected class member")
        if self._at(TT.RESERVED, "type"):
            start = self._adv().pos
            name = self._eat_either(TT.WORD, TT.CONID).value
            # Consume associated type parameters (class type params)
            params: list[Val] = []
            while self._at(TT.WORD) or self._at(TT.CONID):
                params.append(VConId(self._adv().value, Span(Pos(), Pos())))
            kind: Val | None = None
            if self._at(TT.SEP, ":"):
                self._adv()
                kind = self._parse_type()
            if kind is None:
                kind = VConId("Type", Span(Pos(), Pos()))
            # Store params in a VApp chain for the kind's type expression context
            return VKind(name, kind, Span(start, Pos()))
        if self._at(TT.SEP, "("):
            name = self._parse_paren_op_name()
        elif self._at(TT.SYMBOL):
            name = self._adv().value
        else:
            name = self._eat_either(TT.WORD, TT.CONID).value
        if self._at(TT.SEP, "::"):
            self._adv()
        else:
            self._eat(TT.SEP, ":")
        ty = self._parse_type()
        return VSig(name, ty, Span(Pos(), ty.span.end))

    def _peek_paren_op(self) -> str | None:
        """The operator name in `( sym )` at the cursor, without consuming."""
        if (self._i + 2 < len(self._ts)
                and self._ts[self._i].kind is TT.SEP
                and self._ts[self._i].value == "("
                and self._ts[self._i + 1].kind is TT.SYMBOL
                and self._ts[self._i + 2].kind is TT.SEP
                and self._ts[self._i + 2].value == ")"):
            return self._ts[self._i + 1].value
        return None

    def _parse_paren_op_name(self) -> str:
        self._eat(TT.SEP, "(")
        name = self._eat(TT.SYMBOL).value
        self._eat(TT.SEP, ")")
        return name

    def _eat_either(self, *kinds: TT) -> T:
        for k in kinds:
            if self._at(k):
                return self._adv()
        raise ParseError(f"expected one of {[k.name for k in kinds]}", self._cur.pos if self._cur else None)

    # ── Instance ─────────────────────────────────────────────────────────

    def _parse_instance(self) -> VInstance:
        start = self._eat(TT.RESERVED, "instance").pos

        # Optional context: `(Eq a, Show a) => C t` or `Eq a => C t`.
        context: list[Val] = []
        if self._at(TT.SEP, "("):
            saved = self._i
            group = self._parse_atomic_type()
            if self._at(TT.SEP, "=>"):
                self._adv()
                context = list(group.items) if isinstance(group, VTuple) \
                    else [group]
            else:
                self._i = saved

        name, params = self._parse_instance_head()
        if self._at(TT.SEP, "=>"):
            # Unparenthesized single predicate: what we just read was it.
            self._adv()
            context.append(_apply_all(VConId(name, Span(start, start)), params))
            name, params = self._parse_instance_head()

        self._eat(TT.RESERVED, "where")
        self._expect_indent()
        members: list[Val] = []
        while not self._at(TT.DEDENT) and not self._at(TT.EOF):
            while self._at(TT.COMMENT):
                members.append(self._parse_comment())
                self._skip_nl()
            if self._at(TT.DEDENT) or self._at(TT.EOF):
                break
            if self._at(TT.NEWLINE):
                self._adv()
                continue
            _member_start = self._i
            members.append(self._parse_instance_member())
            self._close_inner_blocks(_member_start)
            self._skip_nl()
        if self._at(TT.DEDENT):
            self._adv()
        end = members[-1].span.end if members else Pos()
        return VInstance(name, params, members, context, Span(start, end))

    def _parse_instance_head(self) -> tuple[str, list[Val]]:
        """Parse ``C t1 … tn`` — a class name and its (atomic) arguments."""
        name = self._eat_either(TT.WORD, TT.CONID).value
        params: list[Val] = []
        while self._cur and (self._cur.kind in (TT.WORD, TT.CONID)
                             or self._at(TT.SEP, "(")
                             or self._at(TT.SEP, "[")):
            if self._at(TT.RESERVED, "where"):
                break
            params.append(self._parse_atomic_type())
        return name, params

    def _close_inner_blocks(self, i0: int) -> None:
        """Consume the ``DEDENT``s left behind by blocks opened since ``i0``.

        A multi-line ``case`` deliberately leaves its closing ``DEDENT`` for
        the caller: at the top level the application-parsing loop needs to
        see it, or `case … of …` would swallow the next declaration as an
        argument.  Inside a ``class``/``instance`` body that same ``DEDENT``
        reads as the end of the *body*, which silently moved every member
        after a multi-line one out to the top level.  Counting what the
        member opened tells the two apart.
        """
        opened = 0
        for t in self._ts[i0:self._i]:
            if t.kind == TT.INDENT:
                opened += 1
            elif t.kind == TT.DEDENT:
                opened -= 1
        while opened > 0 and self._at(TT.DEDENT):
            self._adv()
            opened -= 1

    def _parse_instance_member(self) -> Val:
        if not self._cur:
            raise ParseError("expected instance member")
        if self._at(TT.RESERVED, "type"):
            start = self._adv().pos
            name = self._eat_either(TT.WORD, TT.CONID).value
            # Consume the associated type's parameters (e.g. [a] in Elem [a])
            _ = self._parse_type()
            self._eat(TT.SEP, "=")
            ty = self._parse_type()
            return VKind(name, ty, Span(start, ty.span.end))
        if self._at(TT.SEP, "("):
            # A parenthesized operator name, as a class declares it:
            # `(==) a b = …`.  Prefix form is the only way to give an
            # operator method parameters that are not both patterns.
            start = self._cur.pos
            name = self._parse_paren_op_name()
            return self._parse_sc_eqn(name, start)
        if self._at(TT.SYMBOL):
            name_t = self._adv()
            self._eat(TT.SEP, "=")
            body = self._parse_val()
            return VSCEqn(name_t.value, [], body, Span(name_t.pos, body.span.end))
        if self._at(TT.WORD) or self._at(TT.CONID):
            saved = self._i
            name_t = self._adv()
            if self._at(TT.SEP, "="):
                return self._parse_sc_eqn(name_t.value, name_t.pos)
            # Prefix method: `show x y = body`
            if self._at(TT.WORD) or self._at(TT.CONID) or self._at(TT.NUMBER) or self._at(TT.STRING) or self._at(TT.SEP):
                return self._parse_sc_eqn(name_t.value, name_t.pos)
            self._i = saved
            pat = self._parse_pat()
            op_t = self._eat_either(TT.SYMBOL, TT.SEP)
            name = op_t.value
            pat2 = self._parse_pat()
            self._eat(TT.SEP, "=")
            body = self._parse_val()
            return VSCEqn(name, [pat, pat2], body,
                          Span(pat.span.start, body.span.end))
        raise ParseError(f"expected instance member", self._cur.pos if self._cur else None)


# ── Public API ───────────────────────────────────────────────────────────────


def parse_module(tokens: list[T]) -> VModule:
    return Parser(tokens).parse()
