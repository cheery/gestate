"""Gestate surface syntax parser.

Usage::

    from gestate.syntax import parse

    module = parse(source_text)
    # module is a VModule containing declarations etc.
"""

from __future__ import annotations

from .ast import (
    Pat, PVar, PCon, PLit, PTuple, PList, PSigCons, PAnnot,
    Val, VWord, VConId, VNum, VStr,
    VApp, VFunc, VLet, VGiven, VCase, VAlt,
    VOpPhrase, VInfix, VPrefix, VPostfix,
    VTuple, VList, VSet, VProj, VAnnot, VConstraint,
    VBox, VUnbox, VFor, VFix, VGfix, VComment,
    VFixity, VCtor, VTypeDecl, VTypeAlias, VSig, VImplicit, VSCEqn, VSCDecl,
    VClass, VInstance, VKind, VModule,
    Pos, Span,
)
from .tokenize import tokenize
from .parse import parse_module, ParseError
from .descend import descend


def parse(source: str, *, descend_fixity: bool = True) -> VModule:
    """Parse *source* into a resolved :class:`VModule` AST.

    Applies full pipeline: tokenize → parse → fixity resolution.

    Parameters:
        descend_fixity: If ``False``, skip fixity resolution.  Useful
            when merging multiple modules before a single ``descend``
            pass.
    """
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
    "Pat", "PVar", "PCon", "PLit", "PTuple", "PList", "PSigCons", "PAnnot",
    "Val", "VWord", "VConId", "VNum", "VStr",
    "VApp", "VFunc", "VLet", "VGiven", "VCase", "VAlt",
    "VOpPhrase", "VInfix", "VPrefix", "VPostfix",
    "VTuple", "VList", "VSet", "VProj", "VAnnot", "VConstraint",
    "VBox", "VUnbox", "VFor", "VFix", "VGfix", "VComment",
    "VFixity", "VCtor", "VTypeDecl", "VTypeAlias", "VSig", "VImplicit",
    "VSCEqn", "VSCDecl",
    "VClass", "VInstance", "VKind", "VModule",
    "Pos", "Span",
]
