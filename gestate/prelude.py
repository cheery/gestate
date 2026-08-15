"""Loading and merging the standard prelude.

The prelude is compiled as part of every program rather than linked, so its
declarations and the user's land in one flat namespace.  Two things follow,
and both are handled here.

**Spans.**  The two sources are parsed *separately* and their item lists
concatenated, so a user error reports the line the user wrote, not one
shifted by however long the prelude happens to be.  Fixity resolution runs
once over the merged module, so a user fixity declaration still governs
prelude operators.

**Shadowing.**  A user definition of a prelude name wins — as a module-level
definition wins over an implicit `Prelude` import in Haskell.  Merely
dropping the prelude's copy would be wrong, though: `concat` calls `append`,
so a user who redefines `append` would silently change `concat` too.  The
prelude's binding is therefore *renamed* rather than removed, and the
references inside prelude code are renamed with it.  User code sees its own
definition; prelude code keeps seeing the prelude's.  Nothing is renamed
unless a name is actually shadowed.
"""

from __future__ import annotations

import functools
import pathlib
from dataclasses import fields, is_dataclass, replace

from .syntax import parse
from .syntax.descend import descend
from .syntax.ast import (
    Pat, PAnnot, PCon, PList, PSigCons, PTuple, PVar,
    Val, VAlt, VCase, VFor, VFunc, VGfix, VGiven, VLet, VModule, VOpPhrase,
    VSCDecl, VSCEqn, VSig, VUnbox, VWord,
)


_PRELUDE: str | None = None
"""Cached prelude source text, or ``None`` if not yet loaded."""


def load(path: str | None = None) -> str:
    """Return the source text of the standard prelude.

    Parameters:
        path: Path to a ``.ges`` file, or ``None`` for the bundled
            ``gestate/prelude.ges``.
    """
    global _PRELUDE
    if path is not None:
        return pathlib.Path(path).read_text()
    if _PRELUDE is None:
        _PRELUDE = (pathlib.Path(__file__).parent / "prelude.ges").read_text()
    return _PRELUDE


def shadowed_name(name: str) -> str:
    """The internal name a shadowed prelude binding is moved to."""
    return f"__prelude_{name}__"


def library_shadowed_name(name: str) -> str:
    """The internal name a shadowed *library* binding is moved to.

    A different prefix from `shadowed_name`, because they are different
    libraries and a program may shadow a name in both.
    """
    return f"__library_{name}__"


def library_shadowed_con(name: str) -> str:
    """`library_shadowed_name`, for a type or constructor.

    Its own spelling because the case must survive: the tokenizer reads
    case as the namespace (`TT.CONID` against `TT.WORD`), so a
    constructor moved to `__library_Note__` would stop *being* a
    constructor and the library text would stop parsing.
    """
    return f"Library_{name}__"


def shadow_libraries(library: str, program: str) -> str:
    """`library`, with any name `program` also defines renamed out of the way.

    **The same rule as the prelude's, one layer out.**  `prelude.ges` is
    merged as a *module* and so gets `merge`'s shadowing for free; the audio
    libraries are concatenated as *text* by `audio.assemble`, so they had
    none — and a program defining `chorus`, which is what a composition
    calls its chorus, collided with `synth.ges`'s effect of that name and
    failed to compile at all (`examples/audio/quartet.ges`).

    Dropping the library's copy instead would be the wrong repair, and
    quietly: `synth.ges` calls `clamp` in eight places, so a program with
    its own `clamp` would rewire every filter cutoff, the nyquist limit and
    `echo`'s feedback to it, with no error and no warning.  The library's
    binding is renamed and the references inside library code renamed with
    it, exactly as `merge` does — the program sees its own definition, and
    the library goes on seeing the library's.

    **Both libraries, not just this one.**  `clamp` is in `prelude.ges`
    now, not `synth.ges`, and `synth.ges` still calls it; a reference here
    to a name defined *there* has to be renamed too, and to the prefix
    `merge` used rather than this one.  See `from_prelude` below — the
    distinction is which file holds the binding the reference must reach,
    and getting it wrong is silent.

    **Textual, and by token rather than by pattern.**  `assemble` has to
    hand back a *string*, so this cannot go through the AST and back; what
    keeps it honest is that the substitution is driven by the tokenizer, so
    only real identifiers move.  A `chorus` inside a `#:` comment or a
    string literal is not a `WORD` token and is left alone.

    Nothing is renamed unless a name is actually shadowed, which is the
    common case and costs one parse of the program.
    """
    from .syntax.tokenize import TT, tokenize

    renames, _ = _renames(library, program)
    if not renames:
        return library
    # `Pos` is a line and a column; the splice wants an offset.
    lines = library.split("\n")
    start_of, at = [], 0
    for line in lines:
        start_of.append(at)
        at += len(line) + 1

    edits = []
    for token in tokenize(library):
        if token.kind in (TT.WORD, TT.CONID) and token.value in renames:
            begin = start_of[token.pos.line] + token.pos.col
            edits.append((begin, begin + len(token.value),
                          renames[token.value]))
    # Back to front, so the offsets ahead of each edit stay true.
    out = library
    for begin, end, text in reversed(edits):
        out = out[:begin] + text + out[end:]
    return out


def stands_alone(library: str, program: str) -> bool:
    """May the head of this assembly be analysed **without** the program?

    What the answer buys is `syntax.note_seam` and with it the staged
    front end: a head that stands alone is analysed once and kept, and a
    rebuild infers only the author's part (`pipeline._analyse_staged`).

    An unshadowed head always stands alone, and that used to be the
    whole of the test — three assemblers each wrote `if shadowed is
    library`.  It is the wrong question by one word.  A **library**
    name the program takes over is renamed on both sides at once,
    binding and references together, so the head goes on referring only
    to names it defines itself and is as standalone as it ever was.  A
    name out of `prelude.ges` is not: the head is left calling
    `__prelude_envAt__`, which nothing defines until `merge` moves the
    prelude's binding, and that happens only once the program is in
    front of it.

    The distinction is worth the function because of which names it is
    about.  `bar`, `chorus`, `Note`, `gain` — the words a piece is made
    of — are library names, and asking the coarse question cost every
    file using one its whole staged front end: 2.40 s → 1.24 s on
    `noted.ges`, 3.36 → 2.65 on `quartet.ges`, per save.
    """
    _, from_prelude = _renames(library, program)
    return not from_prelude


def _renames(library: str, program: str) -> tuple[dict, bool]:
    """`(name → what it becomes in the library, does it reach the prelude)`.

    One computation, because `shadow_libraries` and `stands_alone` are
    two questions about the same fact and a second implementation of it
    would put its bugs between them.
    """
    program_items = _parsed(program).items
    taken = _defined_names(program_items)
    taken_types = _type_names(program_items)
    if not taken and not taken_types:
        return {}, False
    library_items = _parsed(library).items
    defines = _defined_names(library_items)
    shadowed = defines & taken
    # **Types and constructors shadow too, and by the same rule.**  A
    # program's `Note := Note Int` beside `Score a := Note a` used to
    # leave two constructors wearing one name — the tokenizer separates
    # the namespaces by case, so the identifier renames below never saw
    # them — and the `Monad Score` instance then dispatched on whichever
    # one the cons table kept.  The failure was `unknown global '>>='`
    # at *performance* time, which names neither the collision nor the
    # file it started in.  Constructors the library reads back **by
    # name** from the heap (`Step`, `Ramp`) need no lookup indirection:
    # a program that shadows one can no longer build the library's
    # type at all, so the value the host reads is typed before it is
    # read.
    shadowed_types = _type_names(library_items) & taken_types

    # **Names the program shadows out of `prelude.ges` rather than out of
    # these libraries.**  `merge` renames the prelude's binding and rewrites
    # prelude-internal references with it — but it is handed the *assembled*
    # text, in which these libraries have already been prepended to the
    # program, so it reads them as the author's own code and binds their
    # references to the author's definition.
    #
    # That is how moving `clamp`, `min`, `max` and `mix` out of `synth.ges`
    # and into `prelude.ges` broke it.  The names left the set this function
    # looks at and arrived in a set it did not look at, so a program with
    # its own `clamp` silently rewired `echo`'s feedback, every filter
    # cutoff and the nyquist limit to it — the precise failure the renaming
    # exists to prevent, reintroduced by a move that touched neither.
    # Nothing caught it but `test_a_program_redefining_clamp_...`, which is
    # why that test renders instead of inspecting names.
    from_prelude = (_defined_names(_parsed(load()).items) & taken) - defines

    if not shadowed and not from_prelude and not shadowed_types:
        return {}, False

    # Two prefixes, because they are two libraries and the binding each
    # reference has to reach is in a different one.  A name the library
    # defines *itself* is not in `from_prelude`, so the library's own copy
    # keeps winning for it.
    renames = {n: library_shadowed_name(n) for n in shadowed}
    renames.update({n: shadowed_name(n) for n in from_prelude})
    # Prelude *constructors* a program shadows (`Just`, `Cons`…) are
    # `merge`'s question, one layer down, and are not answered here.
    renames.update({n: library_shadowed_con(n) for n in shadowed_types})
    return renames, bool(from_prelude)


@functools.lru_cache(maxsize=16)
def _parsed(source: str) -> VModule:
    """`parse(source, descend_fixity=False)`, remembered.

    The prelude is the same thousand lines on every compile, and parsing it
    was a quarter of the cost of compiling anything.  The editor rebuilds a
    synth on every Ctrl-S, so that quarter is paid while somebody is
    waiting for a sound to change.

    **Safe because nothing downstream edits the surface AST.**  `descend`
    rebuilds every node it visits rather than resolving fixity in place,
    `_rename` below does the same, and `classify`/`desugar` read.  The one
    rule this depends on is therefore worth stating: a pass over `V*` nodes
    must return new ones.  Inference does annotate — `expr.type_ = t` —
    but that is on the *desugared* `Expr` tree, which is built fresh each
    time.

    **Every read-only parse goes through here**, not only the prelude's:
    an editor start asks `mentions`, `shadow_libraries`, `_authored` and
    the `voices` readers about the same handful of texts, and measured on
    `quartet.ges` that was 24 parses of which 11 were re-parses.  Sixteen
    entries holds a start's worth of distinct texts.  Keyed by text, so an
    edited file that has been re-read is a different key rather than a
    stale hit.
    """
    return parse(source, descend_fixity=False)


def merge(user_source: str, prelude_path: str | None = None) -> VModule:
    """Parse the prelude and ``user_source`` and merge them into one module."""
    prelude_module = _parsed(load(prelude_path))
    user_module = _parsed(user_source)

    shadowed = _defined_names(prelude_module.items) & _defined_names(user_module.items)
    items = list(prelude_module.items)
    if shadowed:
        renames = {n: shadowed_name(n) for n in shadowed}
        items = [_rename(i, renames, frozenset()) for i in items]

    return descend(VModule(items + list(user_module.items)))


# ---------------------------------------------------------------------------
# Which names a set of items defines
# ---------------------------------------------------------------------------

def _defined_names(items: list[Val]) -> set[str]:
    """The supercombinator names declared by ``items``.

    Signatures count: `map : Int -> Int` with no equation is still the user
    laying claim to the name, and leaving the prelude's definition visible
    under a user signature is the confusing half of the old behaviour.
    """
    out: set[str] = set()
    for item in items:
        if isinstance(item, (VSCDecl, VSig)):
            out.add(item.name)
    return out


def _type_names(items: list[Val]) -> set[str]:
    """The type, alias and constructor names declared by ``items``.

    One set for all three, because the tokenizer keeps them one
    namespace: every `CONID` token of a shadowed name moves, whether it
    stood for the type or its constructor.
    """
    from .syntax.ast import VTypeAlias, VTypeDecl

    out: set[str] = set()
    for item in items:
        if isinstance(item, VTypeDecl):
            out.add(item.name)
            out.update(c.name for c in item.constructors)
        elif isinstance(item, VTypeAlias):
            out.add(item.name)
    return out


# ---------------------------------------------------------------------------
# Renaming free occurrences
# ---------------------------------------------------------------------------
#
# `bound` carries the binders in scope, so a prelude lambda whose parameter
# happens to be called `map` still shadows the global of that name.

def _pat_names(pat: Pat) -> set[str]:
    if isinstance(pat, PVar):
        return {pat.name}
    if isinstance(pat, PCon):
        return set().union(*(_pat_names(a) for a in pat.args)) if pat.args else set()
    if isinstance(pat, PTuple):
        return set().union(*(_pat_names(i) for i in pat.items)) if pat.items else set()
    if isinstance(pat, PList):
        names = set().union(*(_pat_names(i) for i in pat.items)) if pat.items else set()
        return names | (_pat_names(pat.tail) if pat.tail is not None else set())
    if isinstance(pat, PSigCons):
        return _pat_names(pat.head) | _pat_names(pat.tail)
    if isinstance(pat, PAnnot):
        return _pat_names(pat.pat)
    return set()


def _rename(node, renames: dict[str, str], bound: frozenset):
    if isinstance(node, VWord):
        if node.value in renames and node.value not in bound:
            return VWord(renames[node.value], node.span)
        return node

    if isinstance(node, VSig):
        if node.name in renames:
            return replace(node, name=renames[node.name])
        return node

    if isinstance(node, VSCDecl):
        name = renames.get(node.name, node.name)
        return replace(node, name=name,
                       equations=[_rename(e, renames, bound)
                                  for e in node.equations])

    if isinstance(node, VSCEqn):
        inner = bound | frozenset().union(
            *( [_pat_names(p) for p in node.params] or [set()] ))
        inner |= frozenset(node.using_params)
        return replace(node,
                       name=renames.get(node.name, node.name),
                       body=_rename(node.body, renames, inner))

    if isinstance(node, VFunc):
        inner = bound | frozenset().union(
            *( [_pat_names(p) for p in node.params] or [set()] ))
        return replace(node, body=_rename(node.body, renames, inner))

    if isinstance(node, (VLet, VGiven)):
        binders = frozenset(n for n, _ in node.bindings)
        rhs_scope = bound | binders if getattr(node, "is_rec", False) else bound
        return replace(
            node,
            bindings=[(n, _rename(v, renames, rhs_scope)) for n, v in node.bindings],
            body=_rename(node.body, renames, bound | binders),
        )

    if isinstance(node, VCase):
        return replace(node,
                       scrut=_rename(node.scrut, renames, bound),
                       alts=[_rename(a, renames, bound) for a in node.alts])

    if isinstance(node, VAlt):
        return replace(node, body=_rename(node.body, renames,
                                          bound | _pat_names(node.pat)))

    if isinstance(node, VFor):
        binders = frozenset().union(
            *( [_pat_names(p) for p, _ in node.bindings] or [set()] ))
        return replace(
            node,
            bindings=[(p, _rename(v, renames, bound)) for p, v in node.bindings],
            body=_rename(node.body, renames, bound | binders),
        )

    if isinstance(node, VUnbox):
        return replace(node,
                       binding=_rename(node.binding, renames, bound),
                       body=_rename(node.body, renames,
                                    bound | _pat_names(node.pat)))

    if isinstance(node, VGfix):
        return replace(node, body=_rename(node.body, renames,
                                          bound | {node.var}))

    if isinstance(node, VOpPhrase):
        # `atoms` interleaves operands with operator *strings*; only the
        # operands are expressions.
        return replace(node, atoms=[
            _rename(a, renames, bound) if isinstance(a, Val) else a
            for a in node.atoms
        ])

    return _map_fields(node, lambda v: _rename(v, renames, bound))


def _map_fields(node, f):
    """Rebuild ``node`` with ``f`` over every sub-``Val``, fields-driven.

    The binder-carrying forms are handled above; everything else — every
    application, annotation, literal and Datafun/FRP node — is a plain
    structural walk that stays total as the AST grows.
    """
    if not is_dataclass(node):
        return node
    changes = {}
    for fld in fields(node):
        v = getattr(node, fld.name)
        if isinstance(v, Val):
            changes[fld.name] = f(v)
        elif isinstance(v, list) and v and all(isinstance(x, Val) for x in v):
            changes[fld.name] = [f(x) for x in v]
    return replace(node, **changes) if changes else node
