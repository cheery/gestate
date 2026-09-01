"""`spec/syntax.md`'s examples compile — checked, not asserted.

`fixme.md` F63: the constrained-ADT example read `ShowThis := (Show a) =>
ShowThis a`, which the kind checker refuses — `a` is not bound by the head
— and nothing read the page, so the correction could drift back without a
line changing colour.  The example is pulled out of the page here and
compiled, the way `test_manual.py` holds `doc/manual.md` to its word.
"""

from __future__ import annotations

import re
from pathlib import Path

from gestate.pipeline import compile

SYNTAX = Path(__file__).resolve().parent.parent / "spec" / "syntax.md"


def test_the_constrained_adt_example_compiles():
    text = SYNTAX.read_text()
    marker = "supports constraints to be supplied in type:"
    assert marker in text, "the example has moved; follow it"
    block = text.split(marker, 1)[1].lstrip("\n").split("\n\n", 1)[0]
    decl = "\n".join(line.strip() for line in block.splitlines())
    assert decl.startswith("ShowThis"), decl
    compile(decl + "\n\nmain : Int\nmain = 1\n")


# ── The page's two lists, against the two tables that implement them ────────
#
# `fixme.md` F23 and F25.  `Box` was reserved in the tokenizer and absent
# from the page's list; `..` had a binding power the page did not give it,
# so the implementation was inventing one.  Both were fixed by editing the
# page — and **nothing read the page**, so either could drift back without
# a line changing colour.  Batch 10 of `card:ungated-fixes.md` measured
# that: the `..` row deleted, `Box` deleted, 780 language tests green.
#
# These two hold the page and the tables to each other.  Neither is a
# tautology: they compare two independently written sources, and a drift
# in *either* direction goes red.

#: Words the tokenizer reserves and `spec/syntax.md`'s list does not name.
#: **This set may shrink and never grow** — it is an accepted baseline, not
#: a permission.  It held `do` and `internal` for one afternoon on
#: 2026-09-01 (`fixme.md` F193) and is empty since.
_UNLISTED_RESERVED: set[str] = set()

#: Operators the parser gives a default fixity and the page's table does
#: not list, for a reason the page gives: `->` has its `infixr 1` stated
#: in the prose above the table and again under §"Names used as
#: operators", and `!` is grammar rather than a declarable operator.
_STATED_IN_PROSE = {"->"}
_UNLISTED_PREFIX = {"!"}

#: And the ones it does not.  `%` at `infixl 8` was in the parser and
#: nowhere on the page until 2026-09-01 (`fixme.md` F193).  **This set may
#: shrink and never grow.**
_UNLISTED_INFIX: set[str] = set()


def _spec_text() -> str:
    return SYNTAX.read_text()


def _reserved_from_the_page() -> set[str]:
    text = _spec_text()
    marker = "Reserved words are:"
    assert marker in text, "the reserved-word list has moved; follow it"
    block = text.split(marker, 1)[1].lstrip("\n").split("\n\n", 1)[0]
    return set(block.split())


def test_the_pages_reserved_words_are_the_tokenizers():
    from gestate.syntax.tokenize import _RESERVED

    page = _reserved_from_the_page()
    assert page - _RESERVED == set(), (
        "the page reserves words the tokenizer does not: "
        f"{sorted(page - _RESERVED)}")
    assert _RESERVED - page == _UNLISTED_RESERVED, (
        "the tokenizer's reserved words and the page's list have drifted: "
        f"{sorted(_RESERVED - page)}")


def _fixity_rows_from_the_page() -> list[tuple[str, int, list[str]]]:
    """`(mode, precedence, [operators])` for every row of the table.

    Two escapes to undo before the row can be split on its pipes: the
    page writes `\\|` for a literal one, and `` `|*` `` carries an
    unescaped pipe inside backticks.  Both are masked, split, restored.
    """
    text = _spec_text().replace("\\|", "|")
    marker = "| Fixity       | Op       | Meaning"
    assert marker in text, "the fixity table has moved; follow it"
    body = text.split(marker, 1)[1].split("\n\n", 1)[0]
    rows = []
    for line in body.splitlines():
        masked = re.sub(r"`[^`]*`",
                        lambda m: m.group(0).replace("|", "\x00"), line)
        cells = [c.strip() for c in masked.strip().strip("|").split("|")]
        if len(cells) < 3 or set(cells[0]) <= set("-"):
            continue
        mode, prec = cells[0].strip("`").split()
        ops = [o.strip().strip("`").replace("\x00", "|")
               for o in cells[1].split(",")]
        rows.append((mode, int(prec), ops))
    assert len(rows) > 15, f"only {len(rows)} rows parsed; the table changed shape"
    return rows


def test_the_pages_default_fixities_are_the_parsers():
    from gestate.syntax.descend import (DEFAULT_INFIX, DEFAULT_PREFIX,
                                        DEFAULT_POSTFIX)

    assoc = {"infixl": "L", "infixr": "R", "infix": "N"}
    listed_infix, listed_prefix, listed_postfix = set(), set(), set()
    for mode, prec, ops in _fixity_rows_from_the_page():
        for op in ops:
            if mode in assoc:
                listed_infix.add(op)
                assert DEFAULT_INFIX.get(op) == (assoc[mode], prec), (
                    f"the page says `{mode} {prec}` for `{op}`, the parser "
                    f"says {DEFAULT_INFIX.get(op)}")
            elif mode == "prefix":
                listed_prefix.add(op)
                assert DEFAULT_PREFIX.get(op) == prec, (
                    f"the page says `prefix {prec}` for `{op}`, the parser "
                    f"says {DEFAULT_PREFIX.get(op)}")
            else:
                listed_postfix.add(op)
                assert DEFAULT_POSTFIX.get(op) == prec, (
                    f"the page says `postfix {prec}` for `{op}`, the parser "
                    f"says {DEFAULT_POSTFIX.get(op)}")

    assert set(DEFAULT_INFIX) - listed_infix == _UNLISTED_INFIX | _STATED_IN_PROSE
    assert set(DEFAULT_PREFIX) - listed_prefix == _UNLISTED_PREFIX
    assert set(DEFAULT_POSTFIX) - listed_postfix == set()
