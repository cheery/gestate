"""AST node definitions for the Gestate surface syntax.

'Everything is a value' -- all nodes derive from :class:`Val`.
Exact meaning is resolved by later compilation stages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union


@dataclass
class Pos:
    line: int = 0
    col: int = 0

    def __repr__(self):
        return f"Pos({self.line},{self.col})"


class ParseError(Exception):
    """A source text that is not a program.

    Here rather than in `parse.py` because the *tokenizer* has to raise it
    too — a backtick with no name in it is a mistake about the syntax, and
    every caller in this pipeline catches `ParseError` for exactly that.
    A second exception type would be a second thing for each of them to
    remember, and the first one forgotten is a traceback in someone's face.
    """

    def __init__(self, msg: str, pos: "Pos | None" = None):
        super().__init__(msg)
        self.pos = pos


@dataclass
class Span:
    start: Pos = field(default_factory=Pos)
    end: Pos = field(default_factory=Pos)

    def __repr__(self):
        return f"Span({self.start},{self.end})"


# ── Values ──────────────────────────────────────────────────────────────────

class Val:
    """Base for every parsed value."""


@dataclass
class VWord(Val):
    value: str
    span: Span = field(default_factory=Span)


@dataclass
class VConId(Val):
    value: str
    span: Span = field(default_factory=Span)


@dataclass
class VNum(Val):
    value: Union[int, float]
    span: Span = field(default_factory=Span)


@dataclass
class VStr(Val):
    value: str
    span: Span = field(default_factory=Span)


@dataclass
class VApp(Val):
    fn: Val
    arg: Val
    span: Span = field(default_factory=Span)


@dataclass
class VFunc(Val):
    params: list[Pat]
    body: Val
    span: Span = field(default_factory=Span)


@dataclass
class VLet(Val):
    is_rec: bool
    bindings: list[tuple[str, Val]]
    body: Val
    span: Span = field(default_factory=Span)


@dataclass
class VGiven(Val):
    bindings: list[tuple[str, Val]]
    body: Val
    span: Span = field(default_factory=Span)


@dataclass
class VCase(Val):
    scrut: Val
    alts: list[VAlt]
    span: Span = field(default_factory=Span)


@dataclass
class VAlt:
    pat: Pat
    body: Val
    span: Span = field(default_factory=Span)


@dataclass
class VOpPhrase(Val):
    """Flat operator phrase pre fixity-resolution.

    ``atoms`` alternates between sub-expressions and operator names,
    always starting and ending with an expression (length >= 3, odd).
    ``EOI`` (end-of-infix) markers may appear to delimit where a
    parenthesized infix segment ends.
    """
    atoms: list[Union[Val, str]]
    span: Span = field(default_factory=Span)


@dataclass
class VInfix(Val):
    left: Val
    op: str
    right: Val
    span: Span = field(default_factory=Span)


@dataclass
class VPrefix(Val):
    op: str
    arg: Val
    span: Span = field(default_factory=Span)


@dataclass
class VPostfix(Val):
    arg: Val
    op: str
    span: Span = field(default_factory=Span)


@dataclass
class VTuple(Val):
    items: list[Val]
    span: Span = field(default_factory=Span)


@dataclass
class VList(Val):
    items: list[Val]
    tail: Val | None = None
    span: Span = field(default_factory=Span)


@dataclass
class VSet(Val):
    items: list[Val]
    span: Span = field(default_factory=Span)


@dataclass
class VProj(Val):
    base: Val
    index: int | str
    span: Span = field(default_factory=Span)


@dataclass
class VAnnot(Val):
    expr: Val
    type_: Val
    span: Span = field(default_factory=Span)


@dataclass
class VConstraint(Val):
    constraints: list[Val]
    body: Val
    span: Span = field(default_factory=Span)


@dataclass
class VBox(Val):
    body: Val
    span: Span = field(default_factory=Span)


@dataclass
class VUnbox(Val):
    pat: Pat
    binding: Val
    body: Val
    span: Span = field(default_factory=Span)


@dataclass
class VFor(Val):
    bindings: list[tuple[Pat, Val]]
    body: Val
    span: Span = field(default_factory=Span)


@dataclass
class VFix(Val):
    body: Val
    span: Span = field(default_factory=Span)


@dataclass
class VGfix(Val):
    var: str
    body: Val
    span: Span = field(default_factory=Span)


@dataclass
class VComment(Val):
    text: str
    span: Span = field(default_factory=Span)


# ── Patterns ─────────────────────────────────────────────────────────────────

class Pat:
    """Base for patterns."""


@dataclass
class PVar(Pat):
    name: str
    span: Span = field(default_factory=Span)


@dataclass
class PCon(Pat):
    name: str
    args: list[Pat]
    span: Span = field(default_factory=Span)


@dataclass
class PLit(Pat):
    value: Union[int, float, str]
    span: Span = field(default_factory=Span)


@dataclass
class PTuple(Pat):
    items: list[Pat]
    span: Span = field(default_factory=Span)


@dataclass
class PList(Pat):
    items: list[Pat]
    tail: Pat | None = None
    span: Span = field(default_factory=Span)


@dataclass
class PSigCons(Pat):
    """A signal-cons pattern: ``x ::: xs``.

    Irrefutable — every ``Sig A`` matches — so it binds rather than
    dispatches: ``head`` for the value and ``tail`` for the delayed rest
    (Rizzo §2.4).  ``xs`` is therefore an ``ExL (Sig A)``, not a signal.
    """
    head: Pat
    tail: Pat
    span: Span = field(default_factory=Span)


@dataclass
class PBox(Pat):
    """A box pattern: ``Box p``.

    Datafun's ``[p]``, which gestate cannot spell that way — ``[p]`` is
    already a one-element *list* pattern.  ``Box`` is reserved and is
    already the term and type constructor, so it carries the pattern too.

    Irrefutable: every ``Box A`` matches.  It eliminates the box, so ``p``'s
    variables are bound *discretely* — the same thing ``unbox`` does, and
    the reason a box pattern is worth having is that it does it in a
    position where `unbox` cannot go, such as a function's parameter.
    """
    pat: Pat
    span: Span = field(default_factory=Span)


@dataclass
class PAnnot(Pat):
    pat: Pat
    type_: Val
    span: Span = field(default_factory=Span)


# ── Declarations ─────────────────────────────────────────────────────────────

@dataclass
class VFixity(Val):
    """``infixl 4 ++`` — or ``infixl 3 6 |*``, with two precedences.

    ``right`` is the precedence the operator binds with on its *right*
    side; ``None`` means it binds the same on both, which is what every
    ordinary operator wants.  They differ when the two operands are not the
    same kind of thing: see `syntax/descend.py`'s `RIGHT_PREC`.
    """
    mode: str
    prec: int
    op: str
    span: Span = field(default_factory=Span)
    right: int | None = None


@dataclass
class VCtor(Val):
    name: str
    fields: list[Val]
    constraints: list[Val] = field(default_factory=list)
    span: Span = field(default_factory=Span)


@dataclass
class VTypeDecl(Val):
    name: str
    params: list[str]
    constructors: list[VCtor]
    deriving: list[str] = field(default_factory=list)
    span: Span = field(default_factory=Span)


@dataclass
class VSig(Val):
    name: str
    type_: Val
    span: Span = field(default_factory=Span)


@dataclass
class VImplicit(Val):
    """``implicit n : τ`` — the declaration site of an implicit parameter.

    Implicits are resolved by *name*, so a name's type is a fact about the
    whole program rather than about any one function that needs it.  Saying
    it once here is what keeps it out of every signature along the call
    chain: a definition that acquires a requirement three levels down does
    not change type.
    """
    name: str
    type_: Val
    span: Span = field(default_factory=Span)


@dataclass
class VSCEqn(Val):
    name: str
    params: list[Pat]
    body: Val
    using_params: list[str] = field(default_factory=list)
    span: Span = field(default_factory=Span)


@dataclass
class VSCDecl(Val):
    name: str
    sig: Val | None
    equations: list[VSCEqn]
    span: Span = field(default_factory=Span)


@dataclass
class VClass(Val):
    name: str
    params: list[str]
    members: list[Val]
    context: list[Val] = field(default_factory=list)   # `Eq a => Ord a`
    span: Span = field(default_factory=Span)


@dataclass
class VInstance(Val):
    name: str
    params: list[Val]
    members: list[Val]
    context: list[Val] = field(default_factory=list)  # `(Eq a) => Eq [a]`
    span: Span = field(default_factory=Span)


@dataclass
class VKind(Val):
    name: str
    kind: Val
    span: Span = field(default_factory=Span)


@dataclass
class VTypeAlias(Val):
    name: str
    params: list[str]
    body: Val
    span: Span = field(default_factory=Span)


@dataclass
class VInternal(Val):
    """`internal` on a line of its own: the rest of this file is machinery.

    A **marker, not a block** — it takes no body and closes nothing, so a
    file says it once and everything below is private to it.  That is the
    shape the thing being described actually has: a library has a
    vocabulary at the top and the insides underneath, and asking an author
    to indent 93 of `synth.ges`'s 118 definitions to say so would be a
    worse file for a truer syntax.

    It carries only a position, because a position is the whole of its
    meaning: everything declared after it, up to the end of the file it was
    written in, is not to be named from anywhere else.
    """

    span: Span = field(default_factory=Span)


@dataclass
class VModule(Val):
    items: list[Val]
    span: Span = field(default_factory=Span)
