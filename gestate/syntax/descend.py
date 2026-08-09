"""Fixity resolution pass — precedence climbing.

Walks the AST and resolves every :class:`VOpPhrase` node into a tree
of :class:`VInfix`, :class:`VPrefix`, and :class:`VPostfix` nodes
using operator fixities (user-declared and built-in defaults).

The algorithm is standard Pratt-style precedence climbing adapted to
flat alternating ``[Val, op, Val, op, ...]`` phrases.
"""

from __future__ import annotations

from .ast import (
    Val, VWord, VConId, VNum, VStr,
    VApp, VFunc, VLet, VGiven, VCase, VAlt,
    VOpPhrase, VInfix, VPrefix, VPostfix,
    VTuple, VList, VSet, VProj, VAnnot, VConstraint,
    VBox, VUnbox, VFor, VFix, VGfix, VComment,
    VFixity, VCtor, VTypeDecl, VTypeAlias, VSig, VSCEqn, VSCDecl,
    VClass, VInstance, VKind, VModule, Pat, PVar, PCon, PLit,
    PTuple, PList, PAnnot, Span,
)


class FixityError(Exception):
    """A phrase that cannot be resolved against the fixity table."""


# ── Default fixities (from spec/syntax.md) ───────────────────────────────────

DEFAULT_INFIX: dict[str, tuple[str, int]] = {
    "->":   ("R", 1),
    "~>":   ("R", 1),   # monotone function arrow (type space only)
    "::":   ("R", 5),
    "++":   ("L", 4),
    # Music grouping, and the reason these three sit where they do
    # (`music.md`'s worked example): overlay is looser than duration
    # scaling, which is looser than sequencing, so
    # `'1 ++ '2 ++ '3 |* 2 || '5 |* 6` scales the whole sequence rather
    # than its last note.  `++` cannot move up instead — it would land on
    # `::`/`:::` at 5, and an `L` operator sharing a precedence with an `R`
    # one is ambiguous.
    "||":   ("L", 2),
    "==":   ("L", 6),
    "/=":   ("L", 6),
    "<":    ("L", 6),
    ">":    ("L", 6),
    "<=":   ("L", 6),
    ">=":   ("L", 6),
    "+":    ("L", 7),
    "-":    ("L", 7),
    "*":    ("L", 8),
    "/":    ("L", 8),
    "%":    ("L", 8),
    "^":    ("R", 9),
    # Function composition, the prelude's `(@)`.  Right at 9 for the same
    # reason Haskell's `.` is: composition associates either way, so the
    # associativity is about reading and the precedence is the point —
    # tighter than every other infix, so `f @ g` groups before whatever
    # is done with it.
    "@":    ("R", 9),
    "$":    ("R", 0),
    ">>=":  ("L", 1),
    ">>":   ("L", 1),
    "|*":   ("L", 6),
    "|/":   ("L", 6),
    ":::":  ("R", 5),
    "<*>":  ("L", 4),
    "<@>":  ("L", 4),
    "|>":   ("L", 4),
    "\\/":   ("L", 3),   # semilattice join (Datafun's ∨)
    "..":   ("L", 7),
}

DEFAULT_PREFIX: dict[str, int] = {
    "+":    7,
    "-":    7,
    "|<":   6,
    "'":    9,
    #: `!f x y` — lift an application over signals.  The parser itself
    #: binds `!` to the next atom (`parse._marks_head`), so the marker
    #: heads the spine and `desugar` reads the lifted arguments back off
    #: it; `!(f x)` keeps its parentheses in the tree and is the constant
    #: signal of the computed value.  The entry here still matters: it
    #: keeps `!` in `_PREFIX_ONLY_OPS` for argument position (`g !x`),
    #: and resolves the marker phrase itself (`['!', atom]`) to `VPrefix`.
    "!":    9,
}

DEFAULT_POSTFIX: dict[str, int] = {
    ">|":   6,
}

#: Operators that bind *differently on each side*.
#:
#: `|*` and `|/` scale a score by a number, so their two operands are not
#: the same kind of thing and do not want the same precedence.  On the left
#: they should be loose, taking a whole phrase — `a ++ b |* 2` scales the
#: sequence, which is what `music.md` asks for.  On the right they should be
#: tight, taking a scaling factor and nothing more.
#:
#: With one precedence you get one or the other.  At 3 for both,
#: `a ++ b |* 2 ++ c` parses as `(a ++ b) |* (2 ++ c)` — the factor swallows
#: the rest of the piece, and the error surfaces as a type mismatch pages
#: away from the cause.  Writing music runs into it immediately.
#:
#: 6 is the highest value that still leaves arithmetic alone: it takes `+`
#: (7) and `*` (8), so `a |* 2 + 1` still scales by three, and stops before
#: `::` (5) and `++` (4).
RIGHT_PREC: dict[str, int] = {
}

#: Operators whose fixity a program may not declare.  `syntax.md` names
#: `->`; `~>` is the same form of type syntax and goes with it.  `!` is
#: grammar: the *parser* binds it to the next atom (`parse._marks_head`)
#: and `desugar` matches it by name, so a declared fixity could only
#: contradict the two of them.
_UNOVERRIDABLE = frozenset({"->", "~>", "!"})

# ── Fixity table ─────────────────────────────────────────────────────────────


def _build_fixity_table(module: VModule) -> dict[str, tuple[str, int]]:
    """Collect all user-declared fixities, overlay defaults."""
    table: dict[str, tuple[str, int]] = {}

    for item in module.items:
        if isinstance(item, VFixity):
            # `syntax.md`: "`->` is the only operator that cannot be
            # overrided."  It was overridable, silently — a user `infixl 9
            # ->` replaced the built-in `infixr 1` and re-associated every
            # function type in the program (`fixme.md` F24).  Rejected
            # rather than ignored: ignoring a declaration the user wrote is
            # its own surprise.
            if item.op in _UNOVERRIDABLE:
                what = ("the signal lift, parsed in the grammar"
                        if item.op == "!" else
                        "type syntax, not an expression operator")
                raise FixityError(
                    f"`{item.op}` has a fixed fixity and cannot be given "
                    f"one: it is {what}"
                )
            assoc_char = {"infixl": "L", "infixr": "R", "infix": "N",
                          "prefix": "P", "postfix": "O"}.get(item.mode, "L")
            # A declaration may give a second precedence for the right
            # operand; `item.right` is None when it did not, and the
            # operator then binds the same on both sides.
            right = item.right if item.right is not None else item.prec
            table[item.op] = (assoc_char, item.prec, right)

    for op, (assoc, prec) in DEFAULT_INFIX.items():
        if op not in table:
            table[op] = (assoc, prec, RIGHT_PREC.get(op, prec))
    for op, prec in DEFAULT_PREFIX.items():
        if op not in table:
            table[op] = ("P", prec, prec)
    for op, prec in DEFAULT_POSTFIX.items():
        if op not in table:
            table[op] = ("O", prec, prec)

    return table


# ── Main pass ────────────────────────────────────────────────────────────────


def descend(module: VModule) -> VModule:
    """Resolve all VOpPhrase nodes in *module* to concrete fixity trees."""
    table = _build_fixity_table(module)
    items = [_descend_val(item, table) for item in module.items]
    return VModule(items, module.span, comments=module.comments)


def _descend_val(val: Val, table: dict) -> Val:
    """Recursively resolve operator phrases in a single value."""
    if isinstance(val, VOpPhrase):
        return _resolve_phrase(val, table)
    if isinstance(val, VApp):
        return VApp(_descend_val(val.fn, table),
                    _descend_val(val.arg, table), val.span)
    if isinstance(val, VFunc):
        return VFunc(val.params,
                     _descend_val(val.body, table), val.span)
    if isinstance(val, VLet):
        bindings = [(n, _descend_val(v, table)) for n, v in val.bindings]
        return VLet(val.is_rec, bindings, _descend_val(val.body, table), val.span)
    if isinstance(val, VGiven):
        bindings = [(n, _descend_val(v, table)) for n, v in val.bindings]
        return VGiven(bindings, _descend_val(val.body, table), val.span)
    if isinstance(val, VCase):
        scrut = _descend_val(val.scrut, table)
        alts = [_descend_alt(a, table) for a in val.alts]
        return VCase(scrut, alts, val.span)
    if isinstance(val, VTuple):
        return VTuple([_descend_val(i, table) for i in val.items], val.span)
    if isinstance(val, VList):
        items = [_descend_val(i, table) for i in val.items]
        tail = _descend_val(val.tail, table) if val.tail else None
        return VList(items, tail, val.span)
    if isinstance(val, VSet):
        return VSet([_descend_val(i, table) for i in val.items], val.span)
    if isinstance(val, VProj):
        return VProj(_descend_val(val.base, table), val.index, val.span)
    if isinstance(val, VAnnot):
        return VAnnot(_descend_val(val.expr, table),
                      _descend_val(val.type_, table), val.span)
    if isinstance(val, VConstraint):
        constraints = [_descend_val(c, table) for c in val.constraints]
        return VConstraint(constraints, _descend_val(val.body, table), val.span)
    if isinstance(val, VBox):
        return VBox(_descend_val(val.body, table), val.span)
    if isinstance(val, VUnbox):
        return VUnbox(val.pat, _descend_val(val.binding, table),
                      _descend_val(val.body, table), val.span)
    if isinstance(val, VFor):
        bindings = [(p, _descend_val(v, table)) for p, v in val.bindings]
        return VFor(bindings, _descend_val(val.body, table), val.span)
    if isinstance(val, VFix):
        return VFix(_descend_val(val.body, table), val.span)
    if isinstance(val, VGfix):
        return VGfix(val.var, _descend_val(val.body, table), val.span)
    if isinstance(val, VFixity):
        return val
    if isinstance(val, VTypeDecl):
        ctors = [_descend_ctor(c, table) for c in val.constructors]
        return VTypeDecl(val.name, val.params, ctors, val.deriving, val.span)
    if isinstance(val, VSig):
        return VSig(val.name, _descend_val(val.type_, table), val.span)
    if isinstance(val, VSCEqn):
        return VSCEqn(val.name, val.params,
                      _descend_val(val.body, table), val.using_params, val.span)
    if isinstance(val, VSCDecl):
        eqns = [_descend_val(e, table) for e in val.equations]
        return VSCDecl(val.name,
                       _descend_val(val.sig, table) if val.sig else None,
                       eqns, val.span)
    if isinstance(val, VClass):
        members = [_descend_val(m, table) for m in val.members]
        return VClass(val.name, val.params, members, val.context, val.span)
    if isinstance(val, VInstance):
        members = [_descend_val(m, table) for m in val.members]
        return VInstance(val.name,
                         [_descend_val(p, table) for p in val.params],
                         members,
                         [_descend_val(c, table) for c in val.context],
                         val.span)
    if isinstance(val, VKind):
        return VKind(val.name, _descend_val(val.kind, table), val.span)
    if isinstance(val, VTypeAlias):
        return VTypeAlias(val.name, val.params,
                          _descend_val(val.body, table), val.span)
    if isinstance(val, VModule):
        items = [_descend_val(item, table) for item in val.items]
        return VModule(items, val.span)

    return val


def _descend_alt(alt: VAlt, table: dict) -> VAlt:
    return VAlt(alt.pat, _descend_val(alt.body, table), alt.span)


def _descend_ctor(ctor: VCtor, table: dict) -> VCtor:
    return VCtor(ctor.name,
                 [_descend_val(f, table) for f in ctor.fields],
                 [_descend_val(c, table) for c in ctor.constraints],
                 ctor.span)


# ── Phrase resolution ────────────────────────────────────────────────────────


def _resolve_phrase(phrase: VOpPhrase, table: dict) -> Val:
    atoms = phrase.atoms
    if not atoms:
        return phrase

    # Operator references: (+), (+_), (_+) pass through unchanged
    if _is_op_ref(atoms):
        return phrase

    core = list(atoms)
    while core and core[-1] == "EOI":
        core.pop()

    def is_postfix(op: str) -> bool:
        return _get_fixity(op, table)[0] == "O"

    def prefix_prec(op: str) -> int:
        """How tightly a prefix use of ``op`` binds its operand.

        `DEFAULT_PREFIX` first: `+` and `-` are declared both ways and the
        infix entry wins in the shared table, so the prefix precedence has
        to be read from where it was actually written down.
        """
        if op in DEFAULT_PREFIX:
            return DEFAULT_PREFIX[op]
        return _get_fixity(op, table)[1]

    def operand(pos: int) -> tuple[Val, int]:
        """One operand: a prefix use, or an atom followed by postfix uses.

        Prefix and postfix operators used to be peeled off the two *ends*
        of the phrase before climbing, which meant they only worked there:
        `'a ++ 'b` left `[a, "++", "'", b]` in the core, two operator
        strings running together, and precedence climbing read `++` as
        postfix and `'` as infix (`fixme.md` F59).  Recognising them at
        operand position instead is what makes a second one work — and a
        sequence of notes is nothing but that.
        """
        if pos >= len(core):
            raise FixityError(
                "operator phrase ends where an operand was expected"
            )
        atom = core[pos]
        if isinstance(atom, str):
            # An operator sitting where an operand belongs is a prefix use.
            # It takes an operand at its own precedence, so `'a ++ 'b` binds
            # `'` to `a` alone rather than to the whole sequence.
            arg, i = climb(prefix_prec(atom), pos + 1)
            return VPrefix(atom, arg, Span(phrase.span.start, arg.span.end)), i

        val = _descend_val(atom, table)
        i = pos + 1
        while i < len(core) and isinstance(core[i], str) and is_postfix(core[i]):
            val = VPostfix(val, core[i], Span(val.span.start, phrase.span.end))
            i += 1
        return val, i

    def climb(min_prec: int, pos: int) -> tuple[Val, int]:
        lhs, i = operand(pos)
        while i < len(core) and isinstance(core[i], str):
            op = core[i]
            # Two precedences: `prec` decides whether this operator may take
            # what has been built to its left, `right` how much it may take
            # to its right.  They are the same number for everything except
            # the score-scaling operators — see `RIGHT_PREC`.
            assoc, prec, right = _get_fixity(op, table)
            if prec < min_prec:
                break
            next_min = right + 1 if assoc in ("L", "N") else right
            rhs, i = climb(next_min, i + 1)
            lhs = VInfix(lhs, op, rhs, Span(lhs.span.start, rhs.span.end))
        return lhs, i

    result, _i = climb(0, 0)
    return result


def _is_op_ref(atoms: list) -> bool:
    """Check if a VOpPhrase atoms list represents an operator reference
    like (+), (+_), or (_+)."""
    if not atoms:
        return False
    # (+): single operator string
    if len(atoms) == 1 and isinstance(atoms[0], str):
        return True
    # (+_): operator string followed by the placeholder
    if len(atoms) == 2 and isinstance(atoms[0], str):
        if _is_placeholder(atoms[1]):
            return True
    # (_+): the placeholder followed by an operator string
    if len(atoms) == 2 and isinstance(atoms[1], str):
        if _is_placeholder(atoms[0]):
            return True
    return False


def _is_placeholder(atom) -> bool:
    """Is this the `_` an operator *reference* is written with?

    **Not every `_` beside an operator is one.**  `Parser._try_parse_op_ref`
    builds `(+_)` and `(_+)` with a `VWord("_", Span())` of its own — a
    placeholder standing for the missing operand, and placeless because it
    stands for nothing in the file.  A `_` the author actually wrote is a
    **hole**, and carries the span of the character they typed.

    Telling them apart is what makes `! _` mean "force a hole" rather than
    "the `!` operator, as a value".  It used to mean the latter, so a phrase
    the checker should have typed came out of fixity resolution still a
    `VOpPhrase` and reached `desugar` as `Unsupported expression form:
    VOpPhrase` — which is a sentence about the compiler's own AST, offered
    to someone who had written two characters and a space.

    A zero-width span is the test because the tokenizer never produces one:
    every token the author wrote covers at least the character it is.
    """
    return (isinstance(atom, VWord) and atom.value == "_"
            and atom.span.start == atom.span.end)


def _get_fixity(op: str, table: dict) -> tuple[str, int, int]:
    """Return (assoc_char, left precedence, right precedence).

    The two precedences are equal for every operator that has not asked
    otherwise.  An operator nobody has declared binds tightly and to the
    left, as before.
    """
    if op in table:
        return table[op]
    return ("L", 9, 9)
