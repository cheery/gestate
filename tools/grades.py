#: asked-by: Henri, 2026-10-02 — "build the mechanical grader over the scanE arms" — doc/trial/signals.md §"Case 5 graded by hand"
"""The grader over `scanE` arms — `doc/trial/signals.md` §"Case 5 graded by
hand", made re-runnable.

    python tools/grades.py                 # the five message arms and case 5's two drafts
    python tools/grades.py FILE...         # any program with a `scanE` in it

**What it asks.**  A `scanE f z e` is a cell, or a record of cells, that
steps when `e` arrives.  The step is run *symbolically*: each old cell an
atom, each message every shape the channel can arrive in — a `sync` of
several gives each alone and each together — and every function the
program defines inlined, to a depth.  Then every read of an old cell in a
new cell's value is one of three:

* **own** — the cell's own old value: the accumulator, an implicit `pre`.
* **plain** — a cell this instant does not write: its value is the
  current one either way.
* **stale** — the old value of a *different* cell this instant also
  writes.  The synchronous rule (within an instant every write precedes
  every read; the old value only through `pre`) says this read must be
  written `pre`, and a message arm has no way to write it, so it is
  printed as a demand.  A read of another cell's *new* value is not a
  stale read; it is printed as an edge, writer before reader.

**What it cannot see.**  Only `scanE`: a `scan` over a `zip` is a signal,
ordered by construction, and is named and passed over.  A reader of the
`scanE`'s output — `map heard model` — reads the instant's new value by
construction and is not graded.  A call deeper than the inlining limit
stays an opaque application whose arguments are still walked, so a read
is never lost, only possibly counted where an inlined body would have
shown it unused.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from gestate import expr as E  # noqa: E402

ARMS = ["blip", "knob", "bounce", "tic-tac-toe", "twoknobs"]
DEPTH = 40


# ── symbolic values ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Atom:
    name: str


@dataclass(frozen=True)
class Lit:
    n: object


@dataclass(frozen=True)
class Con:
    tag: int
    args: tuple


@dataclass(frozen=True)
class Op:
    """An application left opaque: a primitive, or a call past the depth."""
    name: str
    args: tuple


@dataclass(frozen=True)
class Choice:
    """A `case` on a value not known: every alternative, kept."""
    scrut: object
    alts: tuple


@dataclass(frozen=True, eq=False)
class Clo:
    params: tuple
    body: object
    env: dict
    bound: tuple = ()


@dataclass(frozen=True, eq=False)
class Fn:
    """A defined global, partly applied."""
    name: str
    args: tuple


class Sym:
    def __init__(self, analysis):
        self.defs = {s[0]: s for s in analysis.scs}
        self.cache: dict = {}

    def glob(self, name, depth):
        sc = self.defs.get(name)
        if sc is None:
            return Op(str(name), ())
        if sc[1] == 0:
            if name not in self.cache:
                lam = sc[2]
                body = lam.body if isinstance(lam, E.ELambda) else lam
                self.cache[name] = Op(str(name), ())       # a cycle reads as opaque
                self.cache[name] = self.ev(body, {}, depth)
            return self.cache[name]
        return Fn(name, ())

    def apply(self, f, x, depth):
        if isinstance(f, Clo):
            bound = f.bound + (x,)
            if len(bound) < len(f.params):
                return Clo(f.params, f.body, f.env, bound)
            env = dict(f.env)
            env.update(zip(f.params, bound))
            return self.ev(f.body, env, depth)
        if isinstance(f, Fn):
            args = f.args + (x,)
            name, arity, lam = self.defs[f.name][0], self.defs[f.name][1], self.defs[f.name][2]
            if len(args) < arity:
                return Fn(name, args)
            if depth > DEPTH:
                return Op(str(name), args)
            env = dict(zip(lam.params, args))
            return self.ev(lam.body, env, depth + 1)
        if isinstance(f, Op):
            return Op(f.name, f.args + (x,))
        return Op("apply", (f, x))

    def ev(self, e, env, depth):
        if isinstance(e, E.ENum):
            return Lit(e.n)
        if isinstance(e, E.EChr):
            return Lit(e.n)
        if isinstance(e, E.EVar):
            return env[e.name] if e.name in env else Op(str(e.name), ())
        if isinstance(e, E.EGlobal):
            return self.glob(e.name, depth)
        if isinstance(e, E.EAp):
            return self.apply(self.ev(e.fn, env, depth), self.ev(e.arg, env, depth), depth)
        if isinstance(e, E.ECon):
            return Con(e.tag, tuple(self.ev(a, env, depth) for a in e.args))
        if isinstance(e, E.ELambda):
            if not e.params:
                return self.ev(e.body, env, depth)
            return Clo(tuple(e.params), e.body, env)
        if isinstance(e, E.ELet):
            inner = dict(env)
            for name, d in e.defs:
                inner[name] = self.ev(d, inner if e.is_rec else env, depth)
            return self.ev(e.body, inner, depth)
        if isinstance(e, E.ECase):
            return self.case(self.ev(e.scrut, env, depth), e.alts, env, depth)
        return Op(type(e).__name__, ())

    def case(self, s, alts, env, depth):
        if isinstance(s, Con):
            for alt in alts:
                if alt.tag == s.tag or alt.tag is None:
                    inner = dict(env)
                    inner.update(zip(alt.names, s.args))
                    return self.ev(alt.body, inner, depth)
        if isinstance(s, Lit):
            for alt in alts:
                if alt.tag == s.n or alt.tag is None:
                    return self.ev(alt.body, dict(env), depth)
        outs = []
        for alt in alts:
            inner = dict(env)
            inner.update({n: Op("field", (s, Lit(i))) for i, n in enumerate(alt.names or ())})
            outs.append(self.ev(alt.body, inner, depth + 1) if depth <= DEPTH else Op("alt", (s,)))
        return Choice(s, tuple(outs))


# ── the walk ───────────────────────────────────────────────────────────────

def walk(v, stop, seen=None):
    """The old cells and payloads `v` reads, and the new values it reads
    whole — `stop` maps a new value's identity to its cell."""
    seen = set() if seen is None else seen
    olds, news = set(), set()
    todo = [v]
    while todo:
        x = todo.pop()
        if id(x) in seen:
            continue
        seen.add(id(x))
        if id(x) in stop:
            news.add(stop[id(x)])
            continue
        if isinstance(x, Atom):
            olds.add(x.name)
        elif isinstance(x, (Con, Op)):
            todo.extend(x.args)
        elif isinstance(x, Choice):
            todo.append(x.scrut)
            todo.extend(x.alts)
        elif isinstance(x, (Clo, Fn)):
            todo.extend(getattr(x, "bound", ()) or getattr(x, "args", ()))
            if isinstance(x, Clo):
                todo.extend(v for v in x.env.values())
    return olds, news


# ── finding the scanE, its cells, and its messages ─────────────────────────

def scanes(e, found=None):
    found = [] if found is None else found
    if isinstance(e, E.EAp):
        f, args = e, []
        while isinstance(f, E.EAp):
            args.append(f.arg)
            f = f.fn
        if isinstance(f, E.EGlobal) and f.name == "scanE" and len(args) == 3:
            found.append(tuple(reversed(args)))
    for v in vars(e).values() if hasattr(e, "__dict__") else ():
        for x in (v if isinstance(v, (list, tuple)) else [v]):
            if isinstance(x, E.Expr):
                scanes(x, found)
            elif hasattr(x, "body") and isinstance(getattr(x, "body"), E.Expr):
                scanes(x.body, found)
            elif isinstance(x, tuple):
                for y in x:
                    if isinstance(y, E.Expr):
                        scanes(y, found)
    return found


def _head(t):
    while hasattr(t, "fn"):
        t = t.fn
    return getattr(t, "name", None)


def _result(t):
    """A constructor's type, past its arrows: the type it builds."""
    from gestate.types import TFun
    while isinstance(t, TFun):
        t = t.ret
    return t


class Program:
    def __init__(self, src: str):
        from gestate.audio import assemble, has_substrate
        from gestate.gui import assembled
        from gestate.pipeline import analyse
        self.src = src
        whole = assembled(src, 44100) if has_substrate(src) else assemble(src, 44100)
        self.a = analyse(whole)
        self.sym = Sym(self.a)
        self.by_tag = {c.tag: c for c in self.a.program.cons.values()}
        self.by_name = {c.name: c for c in self.a.program.cons.values()}
        own = set(re.findall(r"^([a-z]\w*)\s*:", src, re.M))
        self.own = [s for s in self.a.scs if s[0] in own]

    def labels(self, con: str, arity: int) -> list[str]:
        """The cells' names as the author's first pattern on the
        constructor spells them — labels only; the grading never reads
        them."""
        m = re.search(rf"\b{con}((?:\s+[a-z]\w*){{{arity}}})\s*->", self.src)
        return m.group(1).split() if m else [f"{con}.{i}" for i in range(arity)]

    def _product(self, tag: int) -> bool:
        return len(self.cons_of(_head(_result(self.by_tag[tag].type_)))) == 1

    def scans(self) -> list[str]:
        """The definitions holding a signal `scan` — passed over, named."""
        def has(e):
            if isinstance(e, E.EGlobal) and e.name == "scan":
                return True
            return any(has(x) for v in vars(e).values()
                       for x in (v if isinstance(v, (list, tuple)) else [v])
                       if isinstance(x, E.Expr)) if hasattr(e, "__dict__") else False
        return [s[0] for s in self.own if has(s[2])]

    def cons_of(self, tname: str) -> list:
        out = []
        for c in self.a.program.cons.values():
            if _head(_result(c.type_)) == tname:
                out.append(c)
        return sorted(out, key=lambda c: c.tag)

    def messages(self, e) -> list[tuple[str, object]]:
        """Every shape `e` can arrive in, as (label, symbolic value)."""
        if isinstance(e, E.EGlobal) and e.name in self.sym.defs and self.sym.defs[e.name][1] == 0:
            return self.messages(self.sym.defs[e.name][2].body)
        if isinstance(e, E.EWait):
            chan = e.chan.name if isinstance(e.chan, E.EGlobal) else "chan"
            t = self.a.types.get(chan)
            elem = t.arg if t is not None and hasattr(t, "arg") else None
            name = _head(elem)
            cs = self.cons_of(name) if name and name not in ("Int", "Float", "Bool") else []
            if not cs:
                return [(chan, Atom(f"{chan}?"))]
            return [(f"{chan}.{c.name}",
                     Con(c.tag, tuple(Atom(f"{chan}.{c.name}.{i}?") for i in range(c.arity))))
                    for c in cs]
        if isinstance(e, E.ESync):
            L, R = self.messages(e.left), self.messages(e.right)
            sl, sr, sb = (self.by_name[n].tag for n in ("SyncLeft", "SyncRight", "SyncBoth"))
            return ([(l, Con(sl, (lv,))) for l, lv in L]
                    + [(r, Con(sr, (rv,))) for r, rv in R]
                    + [(f"{l} + {r}", Con(sb, (lv, rv))) for l, lv in L for r, rv in R])
        return [("?", Atom("msg?"))]

    def grade(self):
        out = []
        for name, _, lam, _sig in self.own:
            for f, z, e in scanes(lam):
                out.append(self._one(name, f, z, e))
        return out

    def _one(self, where, f, z, e):
        z0 = self.sym.ev(z, {}, 0)
        # A record of cells only if its type has one constructor: a list's
        # `Cons` is a value, not two cells.
        if isinstance(z0, Con) and self._product(z0.tag):
            con = self.by_tag[z0.tag].name
            cells = self.labels(con, len(z0.args))
            state = Con(z0.tag, tuple(Atom(c) for c in cells))
        else:
            cells, state = [where], Atom(where)
        step = self.sym.ev(f, {}, 0)
        rows = []
        for label, msg in self.messages(e):
            new = self.sym.apply(self.sym.apply(step, state, 0), msg, 0)
            if isinstance(new, Con) and isinstance(state, Con) and new.tag == state.tag:
                news = dict(zip(cells, new.args))
            elif isinstance(state, Con):
                news = {c: Op("field", (new, Lit(i))) for i, c in enumerate(cells)}
            else:
                news = {cells[0]: new}
            written = [c for c in cells if news[c] != Atom(c)]
            # A new value that is itself an atom — `m := n`, the message
            # stored as it came — is not a value anyone computed, and a
            # read of it is a read of the message, not an edge.
            stop = {id(news[c]): c for c in written if not isinstance(news[c], Atom)}
            reads = {}
            for c in written:
                olds, edges = walk(news[c], {k: v for k, v in stop.items() if v != c})
                reads[c] = (sorted(o for o in olds if o in cells), sorted(edges),
                            sorted(o for o in olds if o not in cells))
            rows.append((label, written, reads))
        return where, cells, rows


def stale(src: str) -> set[tuple[str, str, str]]:
    """Every stale read, as (message shape, the cell written, the cell read)."""
    out = set()
    for _where, _cells, rows in Program(src).grade():
        for label, written, reads in rows:
            for c in written:
                out |= {(label, c, o) for o in reads[c][0] if o != c and o in written}
    return out


def draft(n: int) -> str:
    """Case 5's draft `n`, rebuilt as `tools/signalcase.py drafts` does."""
    from signalcase import DRAFTS
    _label, subs, extra = DRAFTS[n - 1]
    src = (ROOT / "doc/trial/signals/twoknobs.ges").read_text()
    for old, new in subs:
        src = src.replace(old, new)
    return src + extra


# ── the report ─────────────────────────────────────────────────────────────

def report(title: str, src: str) -> int:
    print(f"{title}")
    stale_total = 0
    prog = Program(src)
    for where, cells, rows in prog.grade():
        print(f"  scanE in `{where}` — cells {', '.join(cells)}")
        for label, written, reads in rows:
            if not written:
                print(f"    {label:<28} writes nothing")
                continue
            print(f"    {label:<28} writes {', '.join(written)}")
            for c in written:
                olds, edges, payload = reads[c]
                parts = []
                for o in olds:
                    kind = "own" if o == c else ("STALE" if o in written else "plain")
                    stale_total += kind == "STALE"
                    parts.append(f"{kind} {o}" if kind != "STALE" else f"STALE {o} — needs `pre {o}`")
                parts += [f"new {n} (so {n} before {c})" for n in edges]
                if payload:
                    parts.append("the message")
                print(f"      {c:<6} reads {'; '.join(parts) or 'nothing'}")
    for where in prog.scans():
        print(f"  signal `scan` in `{where}` — ordered by its `zip`s, not graded")
    print(f"  → {stale_total} stale read{'s' if stale_total != 1 else ''}\n")
    return stale_total


def main(argv=None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if args:
        for a in args:
            report(a, Path(a).read_text())
        return 0
    for name in ARMS:
        path = ROOT / "doc/trial/signals" / f"{name}.ges"
        report(str(path.relative_to(ROOT)), path.read_text())
    from signalcase import DRAFTS
    for n, (label, _subs, _extra) in enumerate(DRAFTS, 1):
        report(f"twoknobs, {label}", draft(n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
