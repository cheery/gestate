"""Gestate surface syntax parser.

Usage::

    from gestate.syntax import parse

    module = parse(source_text)
    # module is a VModule containing declarations etc.
"""

from __future__ import annotations

from .ast import (
    Pat, PVar, PCon, PLit, PTuple, PList, PSigCons, PBox, PAnnot,
    Val, VWord, VConId, VNum, VStr,
    VApp, VFunc, VLet, VGiven, VCase, VAlt,
    VOpPhrase, VInfix, VPrefix, VPostfix,
    VTuple, VList, VSet, VProj, VAnnot, VConstraint,
    VBox, VUnbox, VFor, VFix, VGfix, VComment, VReader,
    VFixity, VCtor, VTypeDecl, VTypeAlias, VSig, VImplicit, VSCEqn, VSCDecl,
    VClass, VInstance, VKind, VModule,
    Pos, Span,
)
from functools import lru_cache

from .tokenize import T, tokenize
from .parse import parse_module, ParseError
from .descend import descend

#: Assembled text → how many characters of it are the stable head.  An
#: assembly is a library stack in front of an author's file; the stack is
#: the same text on every compile and most of the tokens, so `note_seam`
#: lets `parse` tokenize it once and re-tokenize only the author's part.
#: Keyed by the exact string; the assemblers' own `lru_cache`s bound how
#: many distinct assemblies are alive, so this holds no more than they do.
_SEAMS: dict[str, int] = {}
_KEEP_SEAMS = 8


def note_seam(text: str, head_len: int) -> None:
    """Record that `text[:head_len]` is a stable library head.

    Only an assembler knows where its seam is, and only a seam on a line
    boundary is usable — `head_len` must sit just after a newline, with
    both sides at the top level.  `parse` composes the cached head tokens
    with the freshly tokenized rest; the streams splice exactly because a
    file boundary closes every layout block.
    """
    if not (0 < head_len <= len(text)) or text[head_len - 1] != "\n":
        return
    _SEAMS[text] = head_len
    while len(_SEAMS) > _KEEP_SEAMS:
        _SEAMS.pop(next(iter(_SEAMS)))


@lru_cache(maxsize=8)
def _head_tokens(head: str) -> tuple:
    """The head's tokens, EOF dropped, remembered by text."""
    return tuple(tokenize(head)[:-1])


def _shifted(tok: T, dn: int) -> T:
    p, s = tok.pos, tok.span
    return T(tok.kind, tok.value, Pos(p.line + dn, p.col),
             Span(Pos(s.start.line + dn, s.start.col),
                  Pos(s.end.line + dn, s.end.col)))


def parse(source: str, *, descend_fixity: bool = True,
          reader: bool = False) -> VModule:
    """Parse *source* into a resolved :class:`VModule` AST.

    Applies full pipeline: tokenize → parse → fixity resolution.  A text
    an assembler has registered with `note_seam` re-tokenizes only its
    author's part; positions come out identical either way.

    Parameters:
        descend_fixity: If ``False``, skip fixity resolution.  Useful
            when merging multiple modules before a single ``descend``
            pass.
        reader: If ``True``, the lines the reader handles — `include`
            lines and `reactor` blocks — come back as :class:`VReader`
            items where they stood, instead of failing the parse.  The
            formatter's reading; nothing that compiles asks for it.
    """
    if reader:
        return _with_reader_lines(source, descend_fixity)
    cut = _SEAMS.get(source)
    if cut is not None:
        head = source[:cut]
        dn = head.count("\n")
        tokens = list(_head_tokens(head))
        tokens += [_shifted(t, dn) for t in tokenize(source[cut:])]
    else:
        tokens = tokenize(source)
    module = parse_module(tokens)
    if descend_fixity:
        module = descend(module)
    return module


__all__ = [
    "parse",
    "ParseError",
    "tokenize",
    "parse_module",
    "descend",
    "Pat", "PVar", "PCon", "PLit", "PTuple", "PList", "PSigCons", "PBox",
    "PAnnot",
    "Val", "VWord", "VConId", "VNum", "VStr",
    "VApp", "VFunc", "VLet", "VGiven", "VCase", "VAlt",
    "VOpPhrase", "VInfix", "VPrefix", "VPostfix",
    "VTuple", "VList", "VSet", "VProj", "VAnnot", "VConstraint",
    "VReader", "VBox", "VUnbox", "VFor", "VFix", "VGfix", "VComment",
    "VFixity", "VCtor", "VTypeDecl", "VTypeAlias", "VSig", "VImplicit",
    "VSCEqn", "VSCDecl",
    "VClass", "VInstance", "VKind", "VModule",
    "Pos", "Span",
]


def _with_reader_lines(source: str, descend_fixity: bool) -> VModule:
    """`parse(source, reader=True)`: the reader's lines blanked, the rest
    parsed, and each run of them put back as one `VReader` in line order."""
    from ..notes import _INCLUDE
    from ..reactors import _blocks
    lines = source.split("\n")
    taken = set(_blocks(source)[1])
    taken |= {i for i, line in enumerate(lines) if _INCLUDE.match(line)}
    if not taken:
        return parse(source, descend_fixity=descend_fixity)
    runs: list[list[int]] = []
    for i in sorted(taken):
        if runs and runs[-1][-1] == i - 1 and not (
                _INCLUDE.match(lines[i]) or _INCLUDE.match(lines[i - 1])):
            runs[-1].append(i)
        else:
            runs.append([i])
    module = parse("\n".join("" if i in taken else line
                             for i, line in enumerate(lines)),
                   descend_fixity=descend_fixity)
    kept = [VReader("\n".join(lines[i].rstrip() for i in run),
                    Span(Pos(run[0], 0), Pos(run[-1], len(lines[run[-1]]))))
            for run in runs]
    module.items = sorted(module.items + kept,
                          key=lambda item: item.span.start.line)
    return module
