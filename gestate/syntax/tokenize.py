"""Tokenizer for the Gestate surface syntax.

Tokenizes source text into a stream of tokens, tracking source
positions and handling indentation (offside rule) via virtual
INDENT/DEDENT tokens.

Comments are emitted as COMMENT tokens.

Token kinds
-----------
* word          – lowercase identifier  (``WORD``)
* conid         – uppercase identifier  (``CONID``)
* number        – numeric literal       (``NUMBER``)
* string        – string literal        (``STRING``)
* symbol        – operator/symbol       (``SYMBOL``)
* reserved      – reserved keyword      (``RESERVED``)
* separator     – punctuation           (``SEP``)
* comment       – line comment          (``COMMENT``)
* newline       – significant newline   (``NEWLINE``)
* indent/dedent – virtual layout tokens (``INDENT``, ``DEDENT``)
* eof           – end of file           (``EOF``)
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Iterator

from .ast import ParseError, Pos, Span

# ── Token types ──────────────────────────────────────────────────────────────


class TT(Enum):
    WORD = auto()
    CONID = auto()
    NUMBER = auto()
    STRING = auto()
    SYMBOL = auto()
    RESERVED = auto()
    SEP = auto()
    COMMENT = auto()
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()


# ── Reserved words ───────────────────────────────────────────────────────────

_RESERVED = frozenset({
    "class", "instance", "case", "let", "letrec",
    "where", "in", "for", "of", "type", "kind",
    "gfix", "fix", "unbox", "Box", "given", "using",
    "deriving", "implicit", "internal",
})

# ── Token ────────────────────────────────────────────────────────────────────


@dataclass
class T:
    kind: TT
    value: str
    pos: Pos = field(default_factory=Pos)
    span: Span = field(default_factory=Span)

    def __repr__(self):
        return f"T({self.kind.name},{self.value!r},{self.pos})"


# ── Tokenizer ────────────────────────────────────────────────────────────────


def _is_ident_start(ch: str) -> bool:
    return ch == "_" or unicodedata.category(ch).startswith("L")


def _is_ident_continue(ch: str) -> bool:
    # `'` continues an identifier — `x'`, `r'`, `f'` — as in Haskell, and as
    # `spec/syntax.md` and `spec/data.md` already write them.  It cannot
    # *start* one, so a lone `'` is still a symbol.
    cat = unicodedata.category(ch)
    return ch in "_'" or cat.startswith("L") or cat.startswith("N")


def _is_hex_digit(ch: str) -> bool:
    return ch in "0123456789abcdefABCDEF"


class Tokenizer:
    """Iterable tokenizer that reads a source string."""

    def __init__(self, source: str):
        self._src = source
        self._i = 0
        self._n = len(source)
        self._line = 0
        self._col = 0

    # -- helpers --

    def _peek(self, k: int = 0) -> str:
        j = self._i + k
        return self._src[j] if j < self._n else ""

    def _peek2(self, s: str) -> bool:
        return self._src[self._i:self._i + len(s)] == s

    def _adv(self, n: int = 1) -> str:
        ch = self._peek()
        self._i += n
        if ch == "\n":
            self._line += 1
            self._col = 0
        else:
            self._col += n
        return ch

    def _pos(self) -> Pos:
        return Pos(self._line, self._col)

    def _skip_whitespace(self):
        while self._i < self._n and self._peek() in " \t":
            self._adv()

    def _skip_line(self):
        while self._i < self._n and self._peek() != "\n":
            self._adv()

    # -- tokenize a single token --

    def _next_token(self) -> T | None:
        # skip spaces (but not newlines)
        self._skip_whitespace()
        if self._i >= self._n:
            return None

        start = self._pos()
        ch = self._peek()

        # newline
        if ch == "\n":
            self._adv()
            return T(TT.NEWLINE, "\n", start, Span(start, self._pos()))

        # comment
        if ch == "#":
            start = self._pos()
            self._adv()
            begin = self._i
            self._skip_line()
            text = self._src[begin:self._i]
            return T(TT.COMMENT, text.strip(), start, Span(start, self._pos()))

        # string
        if ch == '"':
            return self._read_string(start)

        # a name in backticks, used as an operator
        if ch == "`":
            return self._read_backticked(start)

        # identifier or reserved word
        if _is_ident_start(ch):
            return self._read_word(start)

        # number
        if ch.isdigit():
            return self._read_number(start)

        # multi-char reserved sequences (longest match first)
        if self._peek2(":::"):
            return self._read_fixed(":::", TT.SEP, start)
        if self._peek2("::"):
            return self._read_fixed("::", TT.SEP, start)
        if self._peek2(".."):
            return self._read_fixed("..", TT.SEP, start)
        if self._peek2(":="):
            return self._read_fixed(":=", TT.SEP, start)
        if self._peek2("->"):
            return self._read_fixed("->", TT.SEP, start)
        if self._peek2("=>"):
            return self._read_fixed("=>", TT.SEP, start)

        # single-char always-separate tokens
        if ch in "()[]{};,:":
            self._adv()
            return T(TT.SEP, ch, start, Span(start, self._pos()))

        if ch == ".":
            self._adv()
            return T(TT.SEP, ".", start, Span(start, self._pos()))

        # symbol: anything else non-whitespace, non-#, greedily joined
        return self._read_symbol(start)

    def _read_fixed(self, text: str, kind: TT, start: Pos) -> T:
        for _ in text:
            self._adv()
        return T(kind, text, start, Span(start, self._pos()))

    def _read_word(self, start: Pos) -> T:
        buf = [self._adv()]
        while self._i < self._n and _is_ident_continue(self._peek()):
            buf.append(self._adv())
        # A trailing `?` belongs to the identifier, so `empty?` is one name
        # rather than `empty` applied to a symbol.  Only one, and only at
        # the end: `empty??` is `empty?` then `?`.  Note this takes the `?`
        # greedily — `a?b` reads as `a?` applied to `b`, so an infix `?`
        # operator has to be written with spaces around it.
        if self._i < self._n and self._peek() == "?":
            buf.append(self._adv())
        value = "".join(buf)
        kind = TT.CONID if value[0].isupper() else TT.WORD
        if value in _RESERVED:
            kind = TT.RESERVED
        return T(kind, value, start, Span(start, self._pos()))

    def _read_number(self, start: Pos) -> T:
        buf = [self._adv()]
        if buf[0] == "0" and self._peek().lower() == "x":
            return self._read_hex_number(start, buf)
        while self._i < self._n and (self._peek().isdigit() or self._peek() == "_"):
            buf.append(self._adv())
        if self._peek() == "." and self._peek(1).isdigit():
            buf.append(self._adv())
            while self._i < self._n and (self._peek().isdigit() or self._peek() == "_"):
                buf.append(self._adv())
        if self._peek().lower() == "e":
            buf.append(self._adv())
            if self._peek() in "+-":
                if self._peek(1).isdigit():
                    buf.append(self._adv())
                else:
                    pass
            while self._i < self._n and (self._peek().isdigit() or self._peek() == "_"):
                buf.append(self._adv())
        raw = "".join(buf)
        clean = raw.replace("_", "")
        if "." in clean or "e" in clean.lower():
            return T(TT.NUMBER, clean, start, Span(start, self._pos()))
        return T(TT.NUMBER, clean, start, Span(start, self._pos()))

    def _read_hex_number(self, start: Pos, buf: list[str]) -> T:
        buf.append(self._adv())
        while self._i < self._n and (_is_hex_digit(self._peek()) or self._peek() == "_"):
            buf.append(self._adv())
        raw = "".join(buf)
        clean = raw.replace("_", "")
        return T(TT.NUMBER, clean, start, Span(start, self._pos()))

    def _read_string(self, start: Pos) -> T:
        self._adv()
        buf = []
        while self._i < self._n:
            ch = self._peek()
            if ch == "\n":
                self._adv()
                buf.append("\n")
                continue
            if ch == '"':
                self._adv()
                return T(TT.STRING, "".join(buf), start, Span(start, self._pos()))
            if ch == "\\":
                self._adv()
                esc = self._peek()
                if esc == "n":
                    buf.append("\n")
                elif esc == "t":
                    buf.append("\t")
                elif esc == "r":
                    buf.append("\r")
                elif esc == "\\":
                    buf.append("\\")
                elif esc == '"':
                    buf.append('"')
                elif esc == "u":
                    self._adv()
                    hex_digits = []
                    for _ in range(4):
                        if self._i >= self._n:
                            break
                        if _is_hex_digit(self._peek()):
                            hex_digits.append(self._adv())
                    if hex_digits:
                        buf.append(chr(int("".join(hex_digits), 16)))
                    continue
                else:
                    buf.append(esc)
                self._adv()
                continue
            buf.append(self._adv())
        return T(TT.STRING, "".join(buf), start, Span(start, self._pos()))

    def _read_backticked(self, start: Pos) -> T:
        """`` `over` `` — an ordinary name, used as an operator.

        **A `SYMBOL` carrying the name**, which is the whole implementation:
        everything downstream of here already knows what to do with an
        operator, and what it does with one it has never heard of is bind
        it tightly and to the left.  So `x `over` y` picks up precedence
        climbing, `infixl` declarations, sections and the formatter for
        free, and the desugarer's fallback — apply the name to two
        arguments — is exactly what the notation means.

        Any name may be quoted, including a constructor's: `` a `Cons` b ``
        is the pair of them, the same way `Cons a b` is.
        """
        self._adv()                                     # the opening tick
        if not _is_ident_start(self._peek()):
            raise ParseError(
                f"{start.line + 1}:{start.col}: a backtick quotes a *name* "
                f"used as an operator — `x \\`over\\` y`")
        word = self._read_word(self._pos())
        if self._peek() != "`":
            raise ParseError(
                f"{start.line + 1}:{start.col}: this backtick is not closed: "
                f"a name used as an operator is written `\\`{word.value}\\``")
        self._adv()                                     # the closing tick
        return T(TT.SYMBOL, word.value, start, Span(start, self._pos()))

    def _read_symbol(self, start: Pos) -> T:
        buf = [self._adv()]
        while self._i < self._n:
            ch = self._peek()
            if ch in " \t\n\r#\"()[]{};,:.'" or _is_ident_start(ch) or ch.isdigit():
                break
            if ch == "-" and self._peek(1) == ">":
                break
            if ch == "=" and self._peek(1) == ">":
                break
            buf.append(self._adv())
        value = "".join(buf)
        if value == "|":
            return T(TT.SEP, "|", start, Span(start, self._pos()))
        if value == "=":
            return T(TT.SEP, "=", start, Span(start, self._pos()))
        return T(TT.SYMBOL, value, start, Span(start, self._pos()))

    # -- iterator yielding tokens with layout --

    def __iter__(self) -> Iterator[T]:
        return self._iter_with_layout()

    def _iter_with_layout(self) -> Iterator[T]:
        indent_stack: list[int] = [0]
        # Bracket depth in effect when each layout level was opened, so a
        # block started inside a bracket can be closed by that bracket.
        # The offside rule alone cannot end such a block: the dedent only
        # arrives on the next line, by which time the `)` has already been
        # handed to a parser still reading block items.  This is Haskell's
        # parse-error rule, narrowed to the one case that provokes it.
        depth_stack: list[int] = [0]
        depth = 0

        def at_line_start() -> bool:
            if not hasattr(self, "_last"):
                return True
            return self._last.kind == TT.NEWLINE

        def line_indent() -> int:
            """The indentation of the next line that has something on it.

            **A blank line does not close a layout block**, and neither
            does a comment-only line.  The comment half was always true;
            the blank half was not, and the cost of that was steep enough
            to be worth stating.

            An instance or a class whose members were separated by a blank
            line — which is how anyone would write two methods with a
            paragraph of reasoning between them — silently ended after the
            first one.  The second member fell out to the top level as an
            ordinary definition, and what the compiler then said was

                Signature variable 'm' is rigid ... may not use it as
                'Score'

            followed by nine further errors about `reverse`, `sum`,
            `showNat` and `showFloat` — every one of them in the prelude,
            none of them within thirty lines of the blank line that caused
            it.  There is no reading of that message that leads a person to
            press backspace on an empty line.

            So the rule is the one a reader already assumes: indentation
            decides a block, and whitespace between items is whitespace.
            Consecutive blank lines, comment lines and mixtures of the two
            are skipped together, because a comment separated from its
            declaration by a blank line is the same shape again.
            """
            j = self._i
            while True:
                col = 0
                while j < self._n and self._src[j] in " \t":
                    col += 1
                    j += 1
                if j >= self._n:
                    # End of file closes everything, which the trailing
                    # DEDENT loop does anyway; report column 0 so it does.
                    return 0
                if self._src[j] == "\n":
                    j += 1
                    continue
                if self._src[j] == "#":
                    while j < self._n and self._src[j] != "\n":
                        j += 1
                    if j < self._n:
                        j += 1
                    continue
                return col

        #: The last token that was not layout — what a continuation line is
        #: continuing *from*.
        prev_real: T | None = None

        def peek_next_token() -> T | None:
            """The next real token, without consuming it."""
            save = (self._i, self._line, self._col)
            try:
                t = self._next_token()
                while t is not None and t.kind in (TT.NEWLINE, TT.COMMENT):
                    t = self._next_token()
                return t
            finally:
                self._i, self._line, self._col = save

        #: A deeper line right after one of these is the block's first
        #: item, whatever it starts with — a case alternative may be
        #: `(a, b) -> …` and a class member may be `(==) : …`, and both
        #: would otherwise look exactly like a continuation.
        openers = ("of", "where", "let", "letrec", "given")

        def next_line_binds() -> bool:
            """Does the coming line contain a top-level `=`?

            Which is what tells a block *item* from a continuation when the
            line starts with an ordinary word: `y = 6` under a `let` binds
            a name and begins an item, while `x` under a broken
            application does not and continues one.  Bracketed `=` does not
            count, and `==` is a `SYMBOL` rather than a `SEP`, so neither
            can be mistaken for a binding.
            """
            save = (self._i, self._line, self._col)
            try:
                d = 0
                seen = False
                while True:
                    t = self._next_token()
                    if t is None or t.kind is TT.EOF:
                        return False
                    if t.kind is TT.NEWLINE:
                        return False if not seen else False
                    seen = True
                    if t.kind is TT.SEP:
                        if t.value in ("(", "[", "{"):
                            d += 1
                        elif t.value in (")", "]", "}"):
                            d -= 1
                        elif t.value == "=" and d == 0:
                            return True
            finally:
                self._i, self._line, self._col = save

        def is_continuation() -> bool:
            """Does the coming, more-indented line continue this one?

            A deeper line is normally a layout *block* — `case … of`, a
            `let`, a `class` body.  But a declaration body could not be
            broken across lines at all, which for a language whose phrases
            are long chains of notes is a real cost (`fixme.md` F82).

            Two shapes are unambiguous, and only those two are taken:

            * **The line begins with an operator.**  Nothing that starts a
              new item — a declaration, a binding, a case alternative —
              begins with one, so such a line has nowhere else to belong.
            * **The previous line ended with `=`.**  A definition whose
              body starts on the next line; there is no other reading.

            Everything else opens a block exactly as before, which is what
            keeps `let x = 5` with its remaining bindings indented under it
            working — `y = 6` could begin an item, so it still does.
            """
            if prev_real is not None and prev_real.kind is TT.RESERVED \
                    and prev_real.value in openers:
                return False
            # **Inside a bracket opened since this block began, a newline
            # is not a newline.**  Implicit line joining, as every
            # bracketed language has it: a list or a parenthesised
            # expression may be laid out over as many lines as it needs,
            # and no continuation rule has to be learned for it.
            #
            # `depth_stack[-1]` and not simply `depth > 0`, because a
            # layout block may be *opened* inside a bracket — `foldr (x b
            # => case p x of` in `prelude.ges` is one — and inside that
            # block the offside rule is in force again.  `depth_stack[-1]`
            # is the bracket depth the current block began at, so this asks
            # exactly the right question: are we deeper in brackets than
            # this block is?
            #
            # **After the opener check, and that is the whole of it.**
            # Tried before it, the same comparison swallowed the newline
            # after `of` in the line above and `all`/`any` silently became
            # one-alternative `case`s — non-exhaustive, and reported
            # against the *prelude*, from a program that had touched
            # neither.
            if depth > depth_stack[-1]:
                return True
            if prev_real is not None and prev_real.kind is TT.SEP \
                    and prev_real.value == "=":
                return True
            t = peek_next_token()
            if t is None:
                return False
            if t.kind is TT.SYMBOL:
                return True
            # `(` too: an argument or a bracketed subexpression carried onto
            # the next line is the commonest way to break a long call, and
            # the only other thing a deeper `(` can begin — a tuple-pattern
            # alternative, an operator class member — follows a block opener
            # and is excluded above.
            if t.kind is TT.SEP and t.value in ("->", "::", ":::", "..", "("):
                return True
            # **An ordinary word, number or constructor — unless the line
            # binds something.**  This is the one shape that was left out,
            # and it is the commonest way to break a long expression:
            #
            #     sound = gain 0.4
            #         (lowpass cutoff osc)
            #
            # It could not simply be allowed, because a `let` block's
            # second binding looks identical from one token of lookahead —
            # `y = 6` starts with a word too.  What separates them is the
            # `=`: an item binds a name and a continuation does not, so the
            # line is scanned to its end and asked.
            if t.kind in (TT.WORD, TT.NUMBER, TT.CONID):
                return not next_line_binds()
            return False

        skip_newlines = False
        tok = self._next_token()

        while tok is not None:
            self._last = tok

            if tok.kind == TT.NEWLINE:
                if skip_newlines:
                    skip_newlines = False
                    tok = self._next_token()
                    continue
                indent = line_indent()
                if indent > indent_stack[-1] and is_continuation():
                    # One logical line: no newline, no block, no level.
                    tok = self._next_token()
                    continue
                if indent > indent_stack[-1]:
                    indent_stack.append(indent)
                    depth_stack.append(depth)
                    yield tok
                    yield T(TT.INDENT, "", Pos(tok.pos.line, indent))
                elif indent < indent_stack[-1]:
                    while indent_stack and indent < indent_stack[-1]:
                        indent_stack.pop()
                        depth_stack.pop()
                        yield T(TT.DEDENT, "", self._pos())
                    if indent_stack and indent != indent_stack[-1]:
                        yield tok
                else:
                    yield tok
                tok = self._next_token()
                continue

            if tok.kind == TT.SEP and tok.value in ("(", "[", "{"):
                depth += 1
            elif tok.kind == TT.SEP and tok.value in (")", "]", "}"):
                # Close every layout block opened inside this bracket
                # *before* handing the closer to the parser.
                while len(indent_stack) > 1 and depth_stack[-1] >= depth:
                    indent_stack.pop()
                    depth_stack.pop()
                    yield T(TT.DEDENT, "", tok.pos)
                depth -= 1

            prev_real = tok
            yield tok
            tok = self._next_token()

        while len(indent_stack) > 1:
            indent_stack.pop()
            depth_stack.pop()
            yield T(TT.DEDENT, "", self._pos())

        yield T(TT.EOF, "", self._pos())


def tokenize(source: str) -> list[T]:
    """Tokenize *source* into a list of tokens (including layout tokens)."""
    return list(Tokenizer(source))
