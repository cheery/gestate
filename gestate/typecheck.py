"""CLI entry point for type inference and checking.

Usage::

    python -m gestate.typecheck file.ges             # interleaved sigs + source
    python -m gestate.typecheck file.ges --sigs      # print only type signatures
    python -m gestate.typecheck file.ges --sig main  # print only main's signature
    python -m gestate.typecheck file.ges --query env # its type, place and prose
    python -m gestate.typecheck file.ges --holes     # every `_`, typed and placed
    python -m gestate.typecheck file.ges --fits "Sig Float"   # what could go there
    python -m gestate.typecheck file.ges --check     # print only errors (exit 1 if any)
    python -m gestate.typecheck -c "f x = x"         # inline code
    python -m gestate.typecheck file.ges -o out.ges  # write to file
"""

from __future__ import annotations

import argparse
import sys

from .syntax import parse, ParseError
from .coherence import CoherenceError
from .declarations import classify, DeclError
from .desugar import desugar_program, DesugarError
from .infer import infer_program, InferError
from .pipeline import _build_builtins, _kind_check_program, _merge_prelude
from .kindcheck import KindError
from .constraint import ConstraintError
from .unify import UnifyError
from .exhaust import check_program
from .types import Type, TVar, TCon, TFun, TApp, TInt, Scheme, scheme_mono, Subst


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="gestate.typecheck",
        description="Infer types for Gestate source and print results.",
    )
    ap.add_argument("file", nargs="?", help="Input file (reads stdin if omitted)")
    ap.add_argument("-c", dest="code", metavar="CODE",
                    help="Type-check an inline code string")
    ap.add_argument("-o", "--output", dest="output", metavar="FILE",
                    help="Write output to FILE instead of stdout")
    ap.add_argument("--sigs", action="store_true",
                    help="Print only type signatures (no source code)")
    ap.add_argument("--sig", metavar="NAME",
                    help="Print only the type signature for the given name")
    ap.add_argument("--check", action="store_true",
                    help="Print only errors, exit non-zero if any are found")
    ap.add_argument("--query", metavar="NAME",
                    help="A name's type, where it is declared, and the "
                         "comment block above that declaration")
    ap.add_argument("--holes", action="store_true",
                    help="Every `_` in the program: its type and its "
                         "line:column, for an editor to place")
    ap.add_argument("--audio", action="store_true",
                    help="Assemble as a synth — `signal.ges`, `audio.ges` "
                         "and `synth.ges` in front — so `Sig`, `Adsr` and "
                         "the rest are in scope and their prose is "
                         "reachable")
    ap.add_argument("--rate", type=int, default=22050,
                    help="Sample rate for --audio (default 22050)")
    ap.add_argument("--fits", metavar="TYPE",
                    help="What in scope could stand where TYPE is wanted — "
                         "exactly, or after n arguments")
    ap.add_argument("--prelude", dest="prelude", metavar="FILE", nargs="?",
                    default=None, const="",
                    help="Load standard library (default); --prelude FILE for custom")
    ap.add_argument("--no-prelude", dest="no_prelude", action="store_true",
                    help="Compile without the standard library")
    args = ap.parse_args(argv)

    try:
        source = _read_source(args)
    except SourceError as e:
        print(f"gestate: {e}", file=sys.stderr)
        return 1
    #: The author's own text, whatever is put in front of it — every
    #: position reported is one *this* has.
    authored = source
    if args.audio:
        # The same choice `audioperform.graph_of` and `audiospans.locate`
        # make, and it has to be the same one: a program with its own
        # `score` is assembled with the music prelude and its piece, and
        # checking a different assembly would be checking a different
        # program.
        from .audio import assemble
        from .audioperform import has_score
        from .audioscore import assemble_performance

        from .audio import AudioError
        from .audiovoices import VoicesError
        from .internals import InternalError

        # **Assembly refuses before the type checker gets a look**, and its
        # refusals are about the *program* rather than about types: a bank
        # colliding with a definition, a name below a library's `internal`
        # marker.  They used to escape as a traceback, which reads as the
        # compiler falling over rather than as the answer to a question —
        # and `internals.InternalError` in particular carries a
        # multi-line report that a stack trace buries.
        try:
            source = (assemble_performance(source, "", args.rate)
                      if has_score(source) else assemble(source, args.rate))
        except (VoicesError, InternalError, AudioError) as e:
            _err(str(e), args)
            return 1

    use_prelude = not args.no_prelude
    prelude_path = args.prelude if args.prelude != "" else None

    # Parse — must succeed to continue
    try:
        if use_prelude:
            module = _merge_prelude(source, prelude_path)
        else:
            module = parse(source)
    except ParseError as e:
        _err(f"parse error: {e}", args)
        return 1

    # Classify — must succeed to continue
    try:
        program = classify(module)
    except CoherenceError as e:
        _err(f"instance error: {e}", args)
        return 1
    except DeclError as e:
        _err(f"declaration error: {e}", args)
        return 1

    # Desugar — must succeed to continue
    try:
        scs = desugar_program(program)
    except DesugarError as e:
        _err(f"desugar error: {e}", args)
        return 1

    typed = [(name, arity, lam, sig) for (name, arity, lam, sig) in scs]
    builtins = _build_builtins()

    # --check mode: try to find as many errors as possible
    if args.check:
        errors = _find_errors(program, typed, builtins)
        if errors:
            for err in errors:
                _err(f"error: {err}", args)
            return 1
        if not args.output:
            # Quiet on success unless writing to file
            return 0

    # Kind-check
    try:
        _kind_check_program(program, typed)
    except KindError as e:
        _err(f"kind error: {e}", args)
        return 1

    # Infer
    try:
        results, per_sc, _givens = infer_program(
            typed, builtins, program.cons, program.classes,
            {sc.name: sc.sig_constraints for sc in program.scs})
    except (InferError, UnifyError, ConstraintError) as e:
        _err(f"type error: {e}", args)
        return 1

    # Exhaustiveness checking
    exhaust_errors = check_program(program)
    if exhaust_errors:
        for err in exhaust_errors:
            _err(f"error: {err}", args)
        return 1

    # Format output
    try:
        sigs, cons, sc_names, written = _format_results(
            program, typed, results, per_sc)
    except Exception as e:
        _err(f"internal error: {e}", args)
        return 1

    # A written signature answers a question as well as an inferred one.
    asked = dict(sigs)
    asked.update(written)

    if args.query:
        return _query(args.query, authored, asked, cons, args,
                      program, _prelude_texts(args))
    if args.holes:
        return _holes(authored, typed, args,
                      _source_offset(authored, args))
    if args.fits:
        return _fits(args.fits, program, results, builtins, args)

    if args.sig:
        if args.sig in asked:
            _out(_format_sig(args.sig, asked, cons), args)
        else:
            _err(f"no declaration named '{args.sig}'", args)
            return 1
    elif args.sigs:
        for name in sc_names:
            if name in sigs:
                _out(_format_sig(name, sigs, cons), args)
    else:
        _out(_interleave(source, sc_names, sigs, cons), args)

    return 0


# ---------------------------------------------------------------------------
# --check mode: per-SC error recovery
# ---------------------------------------------------------------------------

def _find_errors(program, typed, builtins) -> list[str]:
    """Try to find as many type errors as possible, reporting per-SC.
    Returns a list of error messages (does not print them)."""
    errors: list[str] = []

    # Kind-check each type expression individually
    from .kindcheck import check_kind, build_kind_env
    kind_env = build_kind_env(program.cons, program.kind_decls)
    for ci in program.cons.values():
        try:
            check_kind(ci.type_, kind_env)
        except KindError as e:
            errors.append(str(e))
    for _, _, _, sig in typed:
        if sig is not None and isinstance(sig, Type):
            try:
                check_kind(sig, kind_env)
            except KindError as e:
                errors.append(str(e))

    # Full-program inference
    from .infer import InferError as IE
    from .unify import UnifyError as UE
    from .constraint import ConstraintError as CE
    try:
        results, per_sc, givens = infer_program(
            typed, builtins, program.cons, program.classes,
            {sc.name: sc.sig_constraints for sc in program.scs})
        # Run constraint solving to catch missing instances.  A constraint
        # the SC's *own context* grants is discharged by a dictionary
        # parameter, not by an instance — `pipeline.compile` filters those
        # and this did not, so every program was reported as missing
        # `Eq a` for the prelude's `elem : (Eq a) => …`.  The `NameError`
        # below was masking it.
        from .pipeline import _is_given
        all_constraints = [
            p for preds, gs in zip(per_sc, givens) for p in preds
            if not _is_given(p, gs)
        ]
        if all_constraints:
            from .constraint import solve_constraints
            solve_constraints(all_constraints, program.instances)
    except (IE, UE) as e:
        errors.append(str(e))
        # **A name that resolves to nothing stops here.**  The per-SC pass
        # below exists to collect more errors than the first, and it is
        # only sound once the environment holds every definition's type —
        # which an unresolved name prevents, because inference throws
        # before the environment is finished.  Running it anyway checked
        # the whole prelude against a half-built environment and reported
        # forty-five definitions as rigid, none of them wrong and none of
        # them near the typo that caused it.
        from .infer import UnresolvedName
        if isinstance(e, UnresolvedName):
            return errors
        # Try each SC individually for additional errors
        for name, arity, lam, sig in typed:
            try:
                _infer_one(typed, builtins, name, arity, lam, sig,
                           program.cons, program.classes)
            except (IE, UE) as e2:
                msg = str(e2)
                if msg not in errors:
                    errors.append(f"{name}: {msg}")
    except CE as e:
        errors.append(str(e))

    # Exhaustiveness checking on user SCs.  This called `check_scs`, which
    # does not exist — so `--check` (and every path reaching `_find_errors`)
    # died with a `NameError` rather than reporting anything.  Found by
    # running the CLI over `examples/`; nothing else in the suite used it.
    errors.extend(check_program(program))

    return errors


def _infer_one(typed, builtins, name, arity, lam, sig, cons, classes):
    """Try to infer a single SC, with all other SCs available as unresolved TVars."""
    from .infer import infer, check, Fresh
    env = {n: scheme_mono(t) for n, t in builtins.items()}
    fresh = Fresh()
    for sc_name, _, _, sc_sig in typed:
        if sc_name != name:
            env[sc_name] = scheme_mono(sc_sig if sc_sig is not None else fresh.tv())
    env[name] = scheme_mono(sig if sig is not None else fresh.tv())
    constraints: list = []
    if sig is not None:
        check(env, lam, sig, fresh, cons, classes, constraints)
    else:
        infer(env, lam, fresh, cons, classes, constraints)


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def _format_sig(name: str, sigs: dict[str, str],
                cons: dict[str, list[str]]) -> str:
    cs = cons.get(name, [])
    if cs:
        cstr = ", ".join(cs)
        return f"{name} : ({cstr}) => {sigs[name]}"
    return f"{name} : {sigs[name]}"


def _interleave(source: str, sc_names: list[str],
                sigs: dict[str, str],
                cons: dict[str, list[str]]) -> str:
    lines = source.split("\n")
    sc_lines: dict[str, int] = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        for name in sc_names:
            if name not in sc_lines and stripped.startswith(name) \
               and (len(stripped) == len(name)
                    or stripped[len(name)] in (' ', '=', ':', '(')):
                sc_lines[name] = i
                break

    entries: list[tuple[int, str]] = []
    for name in sc_names:
        if name in sigs and name in sc_lines:
            entries.append((sc_lines[name], _format_sig(name, sigs, cons)))

    entries.sort()
    result: list[str] = []
    entry_idx = 0
    for i, line in enumerate(lines):
        while entry_idx < len(entries) and entries[entry_idx][0] == i:
            result.append(entries[entry_idx][1])
            entry_idx += 1
        result.append(line)
    while entry_idx < len(entries):
        result.append(entries[entry_idx][1])
        entry_idx += 1

    return "\n".join(result)


# ---------------------------------------------------------------------------
# Type canonicalization
# ---------------------------------------------------------------------------

def _collect_tvars(t: Type, ids: set[int]) -> None:
    if isinstance(t, TVar):
        ids.add(t.id)
    elif isinstance(t, (TCon, TInt)):
        pass
    elif isinstance(t, TFun):
        _collect_tvars(t.arg, ids)
        _collect_tvars(t.ret, ids)
    elif isinstance(t, TApp):
        _collect_tvars(t.fn, ids)
        _collect_tvars(t.arg, ids)


def _remap(s: str, mapping: dict[int, str]) -> str:
    import re
    def repl(m):
        tid = int(m.group(1))
        return mapping.get(tid, m.group(0))
    return re.sub(r'\ba(\d+)\b', repl, s)


def _free_tvar_ids(t: Type) -> set[int]:
    ids: set[int] = set()
    _collect_tvars(t, ids)
    return ids


# ---------------------------------------------------------------------------
# Inference + formatting
# ---------------------------------------------------------------------------

def _format_results(program, typed, results, per_sc):
    sc_order = [sc.name for sc in program.scs]
    raw_sigs: dict[str, Type] = {}
    raw_preds: dict[str, list] = {}
    has_user_sig: dict[str, bool] = {}

    for i, name in enumerate(sc_order):
        if name in results:
            raw_sigs[name] = results[name]
        if i < len(per_sc):
            raw_preds[name] = per_sc[i]
        for sc in program.scs:
            if sc.name == name:
                has_user_sig[name] = sc.sig_type is not None
                break

    ids: set[int] = set()
    for t in raw_sigs.values():
        _collect_tvars(t, ids)

    filtered_preds: dict[str, list] = {}
    for name in sc_order:
        if name not in raw_sigs:
            continue
        t = raw_sigs[name]
        free_in_type = _free_tvar_ids(t)
        preds = raw_preds.get(name, [])
        kept = []
        for p in preds:
            if _free_tvar_ids(p.type_) & free_in_type:
                kept.append(p)
                ids |= _free_tvar_ids(p.type_)
        if kept:
            filtered_preds[name] = kept

    sorted_ids = sorted(ids)
    mapping: dict[int, str] = {}
    letters = "abcdefghijklmnopqrstuvwxyz"
    for i, tid in enumerate(sorted_ids):
        mapping[tid] = letters[i % 26] + (str(i // 26) if i >= 26 else "")

    sigs: dict[str, str] = {}
    written: dict[str, str] = {}
    cons: dict[str, list[str]] = {}

    for name in sc_order:
        if name in raw_sigs and not has_user_sig.get(name):
            sigs[name] = _remap(_show_type(raw_sigs[name]), mapping)
        elif name in raw_sigs:
            # Written by the author, so `--sigs` and the interleaved view
            # leave it alone — but a *question* about a name deserves an
            # answer whether or not its author wrote one down, so it is
            # recorded separately for `--sig` and `--query` to find.
            written[name] = _remap(_show_type(raw_sigs[name]), mapping)
        if name in filtered_preds:
            cons[name] = [_remap(_show_pred(p), mapping)
                          for p in filtered_preds[name]]

    return sigs, cons, sc_order, written


# ---------------------------------------------------------------------------
# Type rendering
# ---------------------------------------------------------------------------

def _show_type(t: Type) -> str:
    return _show(t, False)


def _show(t: Type, paren: bool) -> str:
    if isinstance(t, TVar):
        return f"a{t.id}"
    if isinstance(t, TInt):
        return str(t.n)
    if isinstance(t, TCon):
        return t.name
    if isinstance(t, TFun):
        s = f"{_show(t.arg, True)} -> {_show(t.ret, False)}"
        return f"({s})" if paren else s
    if isinstance(t, TApp):
        fn = _show(t.fn, True)
        arg = _show(t.arg, True)
        if isinstance(t.fn, TCon) and t.fn.name == "Set":
            return f"{{{arg}}}"
        if isinstance(t.fn, TApp) and isinstance(t.fn.fn, TCon) \
           and t.fn.fn.name == "Bounded":
            return f"{_show(t.fn.arg, False)} .. {arg}"
        return f"{fn} {arg}"
    return str(t)


def _show_pred(p) -> str:
    return f"{p.class_name} {_show_type(p.type_)}"


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Three tools for an editor
# ---------------------------------------------------------------------------
#
# Each answers one question a person has while writing, and each answers it
# about the *program as compiled* rather than about the text: the type comes
# from inference and the position from the parser, so neither can drift from
# what the compiler thinks.  `spec/frp_lesson.md` asked for the first two;
# the third is what makes a hole actionable.


#: The files a synth is assembled from, in order — what `--audio` adds.
_AUDIO_PRELUDES = ("signal.ges", "audio.ges", "synth.ges")


def _prelude_texts(args) -> tuple:
    """`[(label, text)]` for the files a name could otherwise come from.

    Only under `--audio`: the core prelude is merged as a *module* and its
    names are answered from the program anyway, while these three are
    prepended as text and are where a synth's vocabulary is written down.
    """
    from pathlib import Path as _Path

    if not getattr(args, "audio", False):
        return ()
    here = _Path(__file__).parent
    return tuple((name, (here / name).read_text())
                 for name in _AUDIO_PRELUDES)


def _source_offset(source: str, args) -> int:
    """How many lines the assembly put in front of the author's first.

    Zero without `--audio`, because the core prelude is merged rather than
    prepended and the author's line 1 is line 1.  With it, `audiospans`
    already knows the arithmetic and is the one place it should live.
    """
    if not getattr(args, "audio", False):
        return 0
    from .audiospans import _regions

    return _regions(source)[2]


def _doc_above(source: str, line: int) -> list[str]:
    """The comment block immediately above `line`, in source order.

    Consecutive `#` lines and nothing else: a blank line ends the block,
    because a comment separated from a declaration is about something else.
    `#:` is this project's doc-comment marker, and the leading marker is
    stripped either way — what a reader wants is the prose.
    """
    lines = source.split("\n")
    out: list[str] = []
    i = line - 2                      # `line` is 1-based; the one above it
    while i >= 0:
        text = lines[i].strip()
        if not text.startswith("#"):
            break
        out.append(text.lstrip("#:").lstrip("#").strip())
        i -= 1
    return list(reversed(out))


def _declared_at(source: str, name: str) -> tuple[int, str]:
    """`(1-based line, what was found)` for `name` — its signature first.

    The signature, because that is where an author writes what a thing *is*
    and therefore where they write the comment explaining it.  A definition
    with no signature is the fallback, and the difference is reported: an
    editor showing "from its definition" is telling the reader there is no
    declaration to read.
    """
    import re

    sig = re.compile(rf"^{re.escape(name)}\s*:(?![:=])")
    eqn = re.compile(rf"^{re.escape(name)}\s*(\S.*)?=")
    # A constructor is declared inside a `T := …`, which may name several.
    decl = re.compile(rf"^\w+\s*:=.*\b{re.escape(name)}\b")
    # **And most of them are on a continuation line.**  A sum worth
    # documenting is written down the page —
    #
    #     Shape := Rect Int Int Int Int Colour
    #            | Dot Int Int Int Colour
    #
    # — so a test that only read the `:=` line found `Rect` and nothing
    # else, and `?` on `Dot` came back with a type and a shrug.  A leading
    # `|` occurs nowhere but inside a type declaration, so the enclosing
    # one is simply the nearest `:=` above it.
    head = re.compile(r"^\w+\s*:=")
    alt = re.compile(rf"^\s*\|.*\b{re.escape(name)}\b")
    found_eqn = found_decl = last_head = 0
    for i, line in enumerate(source.split("\n"), start=1):
        if sig.match(line):
            return i, "declaration"
        if head.match(line):
            last_head = i
        if not found_decl and decl.match(line):
            found_decl = i
        # The *head* line, not this one: what a reader wants is the block
        # of prose above the declaration, and above an alternative is the
        # alternative before it.
        if not found_decl and last_head and alt.match(line):
            found_decl = last_head
        if not found_eqn and eqn.match(line):
            found_eqn = i
    if found_decl:
        return found_decl, "type declaration"
    if found_eqn:
        return found_eqn, "definition"
    return 0, ""


def _con_type(name: str, program) -> str:
    """`Order : Int -> Int -> Order`, if `name` is a constructor.

    Asked after the supercombinators, because a program's own names are
    what a reader is usually pointing at — but a constructor is a name in
    the same text and hovering one should not come back empty.
    """
    info = program.cons.get(name)
    return "" if info is None else f"{name} : {_show_type(info.type_)}"


def _query(name: str, source: str, sigs, cons, args, program=None,
           extra=()) -> int:
    """`--query NAME` — what it is, where it says so, and what it says.

    Three lines and then the prose, so a reader gets the type first and an
    editor can split on the labels without parsing prose.
    """
    if name in sigs:
        head = _format_sig(name, sigs, cons)
    elif program is not None and _con_type(name, program):
        head = _con_type(name, program)
    else:
        _err(f"no declaration named '{name}'", args)
        return 1

    out = [head]
    line, kind = _declared_at(source, name)
    if line:
        out.append(f"at: line {line} ({kind})")
        doc = _doc_above(source, line)
        if doc:
            out.append("")
            out.extend(doc)
    else:
        # Not in the author's file — the preludes are the other place a
        # name can come from, and hovering `adsr` should reach the
        # paragraph above it in `synth.ges` rather than come back with a
        # type and a shrug.
        for label, text in extra:
            line, kind = _declared_at(text, name)
            if not line:
                continue
            out.append(f"at: {label} line {line} ({kind})")
            doc = _doc_above(text, line)
            if doc:
                out.append("")
                out.extend(doc)
            break
        else:
            out.append("at: not in this file")
    _out("\n".join(out), args)
    return 0


def _holes(source: str, scs, args, offset: int = 0) -> int:
    """`--holes` — every `_`, its type, and where it is.

    Position included because the caller is an editor: a hole is a thing on
    a line, and a type without a place to put it is a fact about a program
    rather than about the cursor.  Lines are 1-based and columns 0-based —
    a text widget's convention, and `audiospans` reports the same way.
    """
    from .expr import EHole
    from .infer import _all_exprs
    from .show import show_type

    found = []
    for name, _arity, lam, _sig in scs:
        for node in _all_exprs(lam):
            if isinstance(node, EHole):
                found.append((node, str(name)))

    if not found:
        _out("no holes", args)
        return 0

    def place(node):
        # 1-based lines, 0-based columns — a text widget's convention, and
        # `audiospans` reports the same way.  `offset` takes the assembled
        # program's prelude back off, so a position is one the *author's*
        # file has.
        if node.span is None:
            return (0, 0)
        return (node.span.start.line + 1 - offset, node.span.start.col)

    lines = source.split("\n")
    out = []
    for node, owner in sorted(found, key=lambda p: place(p[0])):
        line, col = place(node)
        type_ = show_type(node.type_) if node.type_ is not None else "?"
        out.append(f"{line}:{col}: _ : {type_}   (in {owner})")
        if 0 < line <= len(lines):
            out.append(f"    {lines[line - 1].strip()}")
    _out("\n".join(out), args)
    return 0


def _fits(text: str, program, results, builtins, args) -> int:
    """`--fits TYPE` — what in scope could stand where that type is wanted.

    Deliberately *not* tied to holes: the question "what produces a
    `Sig Float`" is one a person asks while writing anything, and a tool
    that only answered it inside a `_` would be a tool you have to prepare
    for.  `--holes` says what the type is; this says what fits it; neither
    needs the other.

    A name fits **exactly** when its result unifies with no arguments, and
    **after n** when peeling n arrows off it does.  Ordered by n, because a
    thing you can use as it stands is worth more than one you must feed.
    """
    from .show import show_type

    try:
        wanted = read_type(text)
    except Exception as exc:                                # noqa: BLE001
        _err(f"could not read the type '{text}': {exc}", args)
        return 1

    matches = fits_in_scope(wanted, program, results, builtins)
    if not matches:
        _out(f"nothing in scope fits {show_type(wanted)}", args)
        return 0

    out = [f"what fits {show_type(wanted)}:"]
    for depth, name, type_ in matches:
        out.append(f"  {name} : {type_}{needed(depth)}")
    _out("\n".join(out), args)
    return 0


class FitsError(Exception):
    """`fits_in_source` could not get far enough to answer."""


def fits_in_source(text: str, source: str, *, rate: int = 22050,
                   audio: bool = True) -> tuple:
    """`(what fits, the type as the checker shows it)` for `text` in `source`.

    **`--fits` with no `argv` around it**, for a caller that has the
    program as a string rather than as a path — which is what an editor
    has: the text in the window, unsaved, is the program the question is
    about, and a version of this that read a file would answer about the
    last save.

    `audio` prepends `signal.ges`, `audio.ges` and `synth.ges` exactly as
    `--audio` does, because a synth's vocabulary is where the interesting
    answers are and a file being edited in the workbench is a synth.

    Raises `FitsError` with the compiler's own words when the program
    does not get as far as inference — which is the ordinary case while
    somebody is typing, and is a fact worth reporting rather than an
    empty answer that reads as *"nothing fits"*.
    """
    from .audio import assemble
    from .audioperform import has_score
    from .audioscore import assemble_performance
    from .show import show_type

    if audio:
        try:
            source = (assemble_performance(source, "", rate)
                      if has_score(source) else assemble(source, rate))
        except Exception as exc:                        # noqa: BLE001
            raise FitsError(str(exc)) from exc
    try:
        wanted = read_type(text)
    except Exception as exc:                            # noqa: BLE001
        raise FitsError(f"could not read the type `{text}`: {exc}") from exc
    try:
        program = classify(_merge_prelude(source, None))
        typed = [(n, a, l, s) for (n, a, l, s) in desugar_program(program)]
        builtins = _build_builtins()
        _kind_check_program(program, typed)
        results, _per_sc, _givens = infer_program(
            typed, builtins, program.cons, program.classes,
            {sc.name: sc.sig_constraints for sc in program.scs})
    except (ParseError, CoherenceError, DeclError, DesugarError, KindError,
            InferError, UnifyError, ConstraintError) as exc:
        raise FitsError(str(exc)) from exc

    matches = fits_in_scope(wanted, program, results, builtins)
    return [f"{name} : {type_}{needed(depth)}"
            for depth, name, type_ in matches], show_type(wanted)


def holes_in_source(source: str, *, rate: int = 22050,
                    audio: bool = True) -> list:
    """`(line, col, type)` per `_`, 1-based lines and 0-based columns.

    **`--holes` with no `argv` around it**, and for the same reason
    `fits_in_source` exists: the editor is asking about the text in the
    window, and the positions have to be the ones the *author's* file
    has — so the assembly's prelude is measured and taken back off,
    exactly as the CLI does it.

    Raises `FitsError` when the program does not reach inference, which
    while typing is the ordinary case and is a fact the caller reports
    rather than an empty list that reads as *"no holes"*.
    """
    from .audio import assemble
    from .audioperform import has_score
    from .audioscore import assemble_performance
    from .expr import EHole
    from .infer import _all_exprs
    from .show import show_type

    authored = source
    if audio:
        try:
            source = (assemble_performance(authored, "", rate)
                      if has_score(authored) else assemble(authored, rate))
        except Exception as exc:                        # noqa: BLE001
            raise FitsError(str(exc)) from exc
    # `audiospans` owns this arithmetic — how many lines the assembly put
    # in front of the author's first — and asking it here rather than
    # counting again is what keeps a hole's line the same number the
    # margin already draws a knob on.
    from .audiospans import _regions

    offset = _regions(authored)[2] if audio else 0
    try:
        program = classify(_merge_prelude(source, None))
        typed = [(n, a, l, s) for (n, a, l, s) in desugar_program(program)]
        builtins = _build_builtins()
        _kind_check_program(program, typed)
        infer_program(typed, builtins, program.cons, program.classes,
                      {sc.name: sc.sig_constraints for sc in program.scs})
    except (ParseError, CoherenceError, DeclError, DesugarError, KindError,
            InferError, UnifyError, ConstraintError) as exc:
        raise FitsError(str(exc)) from exc

    out = []
    for _name, _arity, lam, _sig in typed:
        for node in _all_exprs(lam):
            if not isinstance(node, EHole) or node.span is None:
                continue
            line = node.span.start.line + 1 - offset
            if line < 1:
                # The prelude's own, if it ever had one — not the
                # author's file and not their business.
                continue
            out.append((line, node.span.start.col,
                        show_type(node.type_) if node.type_ is not None
                        else "?"))
    return sorted(set(out))


def signatures_in_source(source: str, *, rate: int = 22050,
                         audio: bool = True) -> dict:
    """`name -> the signature the checker inferred`, for names without one.

    **Only the ones nobody wrote.**  A declaration that already carries a
    signature is not offered one: the author's spelling is the
    authority, and replacing `Sig Float` with an equal type spelled
    differently would be a diff with no change in it.

    The half of `--sigs` with no `argv` around it, so the editor writes
    the same answer the command line prints — one door, and the two
    cannot drift.  Raises `FitsError` with the compiler's words when the
    program does not reach inference, which while typing is the ordinary
    case.
    """
    from .audio import assemble
    from .audioperform import has_score
    from .audioscore import assemble_performance

    authored = source
    if audio:
        try:
            source = (assemble_performance(source, "", rate)
                      if has_score(source) else assemble(source, rate))
        except Exception as exc:                        # noqa: BLE001
            raise FitsError(str(exc)) from exc
    try:
        program = classify(_merge_prelude(source, None))
        typed = [(n, a, l, s) for (n, a, l, s) in desugar_program(program)]
        builtins = _build_builtins()
        _kind_check_program(program, typed)
        results, per_sc, _givens = infer_program(
            typed, builtins, program.cons, program.classes,
            {sc.name: sc.sig_constraints for sc in program.scs})
        sigs, cons, _sc_names, _written = _format_results(
            program, typed, results, per_sc)
    except (ParseError, CoherenceError, DeclError, DesugarError, KindError,
            InferError, UnifyError, ConstraintError) as exc:
        raise FitsError(str(exc)) from exc

    # **Only what this file declares.**  The assembly puts three
    # libraries in front, and offering to annotate `synth.ges`'s names in
    # somebody's synth would be absurd — so the answer is intersected
    # with the names the author's own text defines.
    mine = _defined_lines(authored)
    return {name: _format_sig(name, sigs, cons)
            for name in sigs if name in mine}


def _defined_lines(source: str) -> dict:
    """`name -> the 1-based line it is defined on`, read from the text.

    Read rather than parsed, and deliberately: `session.py` already
    reads declarations this way for `goto`, the language's layout rule
    guarantees a declaration starts at the left margin, and a second
    front end here could disagree with the real one about a file that
    the real one accepts.
    """
    out = {}
    for n, line in enumerate(source.splitlines(), start=1):
        if not line[:1].isalpha():
            continue
        head = line.split("=", 1)[0].split(":", 1)[0].split()
        # **The first word, because a definition may take parameters.**
        # `double x = x * 2.0` declares `double`; reading the whole left
        # side gives `double x`, which is not an identifier, so every
        # function of an argument went unfound — the names most worth
        # annotating being exactly the ones with arguments.
        if head and head[0].isidentifier() and ("=" in line or ":" in line):
            out.setdefault(head[0], n)
    return out


def read_type(text: str):
    """The type an author would write, as the checker's own.

    Parsed as a *signature* so the type language is the one they write —
    `Sig Float`, `Int -> Float`, `Maybe (List Int)`.
    """
    from .declarations import desugar_type
    from .syntax import parse

    module = parse(f"__fits__ : {text}\n__fits__ = __fits__\n")
    return desugar_type(module.items[0].type_, {})


def needed(depth: int) -> str:
    """How a `--fits` answer says a name has to be fed first."""
    return "" if depth == 0 else \
        f"   (after {depth} argument{'s' if depth > 1 else ''})"


def fits_in_scope(wanted, program, results, builtins) -> list:
    """`(depth, name, type)` for everything in scope that fits `wanted`.

    The half of `--fits` that has no command line in it, so an editor can
    ask the same question of a **hole's own type** rather than of a string a
    person retyped.  The CLI reads its type out of `argv` and this does
    not, and that is the whole difference.

    Two callers, and the split is what lets them share: `_fits` reads its
    type out of `argv`, and `fits_in_source` is handed one by the editor's
    `fits` command.  Neither retypes the search, which is the whole point
    of the half without an `argv` in it.
    """
    from .show import show_type
    from .types import TFun

    # Every name with a type: the program's own, the built-ins, and the
    # constructors — a constructor is a way to make one of these too.
    known: dict[str, object] = {}
    for name, type_ in (builtins or {}).items():
        known[str(name)] = getattr(type_, "type_", type_)
    for info in program.cons.values():
        known[info.name] = info.type_
    for name, type_ in results.items():
        known[str(name)] = type_

    matches: list[tuple[int, str, str]] = []
    for name, type_ in known.items():
        if name.startswith("__") or not isinstance(type_, object):
            continue
        rest, depth = type_, 0
        while depth <= 4:
            # **A bare variable is not an answer.**  `id : a -> a`,
            # `const : a -> b -> a` and `(@)` unify with everything,
            # so listing them is listing the prelude in a different order.
            # What a reader wants is the names whose *shape* is the one
            # asked for, and the test for that is where the two run out of
            # arrows together: if the candidate ends in a variable there,
            # it fits by being unconstrained rather than by being right.
            if _shaped_like(rest, wanted) and _unifies(rest, wanted):
                matches.append((depth, name, show_type(type_)))
                break
            if not isinstance(rest, TFun):
                break
            rest, depth = rest.ret, depth + 1
    return sorted(matches, key=lambda m: (m[0], m[1]))


def _shaped_like(candidate, wanted) -> bool:
    """Does `candidate` end in something, where `wanted` ends?

    Peels one arrow from each together; what is left of the candidate when
    `wanted` runs out has to be a real type.  A variable there is what
    makes `id` fit every question ever asked.  When `wanted` is itself a
    variable the question is "anything at all", and then it does.
    """
    from .types import TFun, TVar

    if isinstance(wanted, TVar):
        return True
    while isinstance(wanted, TFun) and isinstance(candidate, TFun):
        candidate, wanted = candidate.ret, wanted.ret
    return not isinstance(candidate, TVar)


def _unifies(a, b) -> bool:
    """Would these two types unify?  Asked without committing to it.

    A fresh instantiation each time, because unification is destructive
    here (`fixme.md` F78's union-find store) and one candidate must not
    leave its bindings behind for the next.
    """
    from .infer import Fresh, instantiate
    from .types import Scheme, free_vars, unifying
    from .unify import unify, UnifyError

    fresh = Fresh()
    try:
        with unifying():
            left, _ = instantiate(Scheme(frozenset(free_vars(a)), a, ()), fresh)
            right, _ = instantiate(Scheme(frozenset(free_vars(b)), b, ()), fresh)
            unify(left, right)
            return True
    except (UnifyError, Exception):
        return False


class SourceError(Exception):
    """A file the tool could not read — reported, not raised at the user."""


def _read_source(args) -> str:
    if args.code is not None:
        return args.code
    if args.file:
        # `OSError` as a sentence.  A name that does not exist is the
        # commonest mistake there is at a command line, and it came out of
        # here as a `FileNotFoundError` traceback — nine frames of the
        # compiler's own call stack in front of the one fact that mattered.
        try:
            with open(args.file) as f:
                return f.read()
        except OSError as exc:
            raise SourceError(f"{args.file}: {exc.strerror}") from None
    return sys.stdin.read()


def _out(text: str, args) -> None:
    if args.output:
        with open(args.output, "a") as f:
            f.write(text)
            if not text.endswith("\n"):
                f.write("\n")
    else:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")


def _err(text: str, args) -> None:
    if args.output:
        with open(args.output, "a") as f:
            f.write(text)
            if not text.endswith("\n"):
                f.write("\n")
    else:
        sys.stderr.write(text)
        if not text.endswith("\n"):
            sys.stderr.write("\n")


if __name__ == "__main__":
    sys.exit(main())
