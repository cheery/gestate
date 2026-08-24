#: asked-by: Henri, 2026-08-23 — "tätä varten voi tehdä kortin ... tee siitä portti kun suite on ajettu"
"""Who asked for each tool on this bench — and which nobody can say.

    python tools/asked.py            # the register, grouped by who asked
    python tools/asked.py --bare     # one line per tool, for grepping
    python tools/asked.py --graph    # asked-by × needed-by, in four quadrants
    python tools/asked.py --dot      # the same as graphviz source
    python tools/asked.py --svg [OUT] # laid out by dot (Sugiyama), SVG to OUT or stdout


**The question this answers.**  On 2026-08-23 somebody outside the
project asked how the tree verifies that all of its code is tested, and
the answer was that nobody had ever measured it — one sentence from a
stranger produced an instrument the same afternoon.  Looking for the
mechanism that catches the *next* one found there was none, and that the
obvious one is a trap: a register of questions from outside is a list
nothing can enumerate, so nothing can gate it, so it fills once and dies.

**What is enumerable is not the questions.  It is `tools/`.**  Every
tool here exists because somebody wanted something, and that somebody is
recoverable at the moment the tool is written and almost nowhere after.
So each file carries one line saying who asked, and the suite refuses a
tool that does not.  `F169`'s rule — *a number nobody asked for is a
number nobody checks* — generalises exactly: **a tool nobody asked for
is a tool nobody runs**, and the register is what makes that visible
rather than a suspicion.

**`a session` and `unrecorded` are legal answers**, and that is the
point.  A stamp that could only say "Henri asked" would be a stamp
everybody writes and nobody means.  What the register is for is the
*shape of the distribution* — how much of this bench came from outside
pressure, how much from the person, and how much a session built because
it could.

**The verdicts**, and there is no default:

* `Henri` — he asked, and the line quotes his words or cites the
  `card:` that does.
* `outside` — somebody not on the project asked, quoted.
* `a session` — a session built it on its own initiative; the record
  says so.
* `the tree` — a document or a gate demanded it and named it.
* `unrecorded` — nobody wrote down where it came from.  The date is
  when the file was added, and `test_provenance.py` holds the count so
  it can only fall on purpose.

**And the other axis is not stamped — it is computed.**  Henri,
2026-08-24: *"I think we could have 'who-asked' and 'needed-by'.  So
that we get a graph."*  A `needed-by` line kept by hand would rot the
way every hand-kept register here has; what the tree can *derive* is
who names the tool — which tests, which documents, which other tools,
which cards.  Crossed with the stamp that gives four quadrants, and
F169 checkable from both ends:

* **asked, needed** — the bench.
* **asked, not needed** — built for somebody, now run by nothing.
* **not asked, needed** — a session's initiative that earned its place.
* **neither** — the candidate for *dead*, and the only one this file
  will call that.

*Needed* means named by a test, a document, or another tool.  A card
naming it is shown and does not count: cards are where a tool was
wanted, not where it is used.  The journal is not searched at all — it
names everything once and is history, not need.
"""

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"

#: How far into a file the stamp may hide.  Deep enough for a shebang
#: and a long opening paragraph, shallow enough that it is still the
#: first thing a reader meets.
WINDOW = 40

WHO = ("Henri", "outside", "a session", "the tree", "unrecorded")
#: `Henri` and `outside` are a *person's* ask, and a person's ask rots
#: into a paraphrase within a week.  The words are the part that keeps.
QUOTED = ("Henri", "outside")

STAMP = re.compile(
    r"^#:\s*asked-by:\s*(?P<who>Henri|outside|a session|the tree|unrecorded)"
    r"\s*,\s*(?P<date>\d{4}-\d{2}-\d{2})\s*(?P<rest>.*)$")


def tools():
    """Every script on the bench.  A glob, deliberately — a roster typed
    out by hand is a roster that forgets the file somebody just added."""
    return sorted([*TOOLS.glob("*.py"), *TOOLS.glob("*.sh")])


def stamp(path):
    """`(who, date, rest)` for one tool, or `None` if it carries none.

    Read from the first `WINDOW` lines rather than the whole file so a
    stamp quoted inside a docstring further down — this file quotes the
    grammar itself — cannot be mistaken for the file's own."""
    for line in path.read_text().splitlines()[:WINDOW]:
        found = STAMP.match(line.strip())
        if found:
            return (found.group("who"), found.group("date"),
                    found.group("rest").strip())
    return None


def register():
    """Every tool with its stamp, unstamped ones carrying `None`."""
    return {p.relative_to(ROOT).as_posix(): stamp(p) for p in tools()}


#: Where a tool can be *needed* from, and where it can only be *wanted*.
NEEDERS = {
    "test":  lambda root: root.glob("test/test_*.py"),
    "doc":   lambda root: [*root.glob("*.md"), *root.glob("doc/**/*.md"),
                           *root.glob("spec/*.md")],
    "tools": lambda root: [*root.glob("tools/*.py"), *root.glob("tools/*.sh")],
}
WANTERS = {"cards": lambda root: root.glob("board/**/*.md")}


def needed_by(name, root=ROOT):
    """`{kind: [files that name this tool]}` — the computed axis.

    The basename is what is searched for, because that is how the
    documents write a tool (`lagcheck.py`, not `tools/lagcheck.py`) —
    the same lesson `seedaudit.py`'s second harvester bug taught.  A tool
    never names itself here, and `test_provenance.py` is skipped: it
    names every tool in order to test the stamps."""
    base = pathlib.PurePosixPath(name).name
    out = {}
    for kind, files in {**NEEDERS, **WANTERS}.items():
        hits = []
        for f in sorted(files(root)):
            rel = f.relative_to(root).as_posix()
            if rel == name or rel == "test/test_provenance.py" or "/notes/" in rel:
                continue
            try:
                if base in f.read_text(encoding="utf-8", errors="ignore"):
                    hits.append(rel)
            except OSError:
                continue
        out[kind] = hits
    return out


def quadrant(stamp_, needs):
    """One of four, from the stamp and the computed needs."""
    asked = stamp_ is not None and stamp_[0] in ("Henri", "outside", "the tree")
    needed = any(needs[k] for k in NEEDERS)
    return {(True, True): "asked, needed", (True, False): "asked, not needed",
            (False, True): "not asked, needed", (False, False): "neither"}[(asked, needed)]


def graph(root=ROOT):
    """`[(name, stamp, needs, quadrant)]` for every tool."""
    rows = []
    for name, s in register().items():
        needs = needed_by(name, root)
        rows.append((name, s, needs, quadrant(s, needs)))
    return rows


def print_graph(rows):
    order = ["neither", "asked, not needed", "not asked, needed", "asked, needed"]
    for q in order:
        here = [r for r in rows if r[3] == q]
        if not here:
            continue
        print(f"\n── {q} ── {len(here)} of {len(rows)}")
        for name, s, needs, _ in sorted(here):
            who = s[0] if s else "—"
            counts = "  ".join(f"{k}:{len(needs[k])}" for k in [*NEEDERS, *WANTERS])
            print(f"  {name:<28} {who:<11} {counts}")
    dead = [r[0] for r in rows if r[3] == "neither"]
    print(f"\nasked: {len(rows)} tools; {len(dead)} asked for by nobody and named by nothing"
          + (": " + ", ".join(dead) if dead else "."))


def dot(rows):
    """Graphviz source: three layers, left to right — the files that
    *need* a tool, the tools coloured by quadrant, and the cards that
    *wanted* one (dashed).  `dot` lays it out Sugiyama-style, which is
    what the layers are for: a tool with nothing on its left is the
    picture of *needed by nothing*.  Henri, 2026-08-24: "Could the
    asked.py also create a sugiyama-layouted graph?" — it does, by
    handing this to the reference implementation rather than writing a
    second one."""
    colour = {"asked, needed": "white", "asked, not needed": "lightyellow",
              "not asked, needed": "lightblue", "neither": "lightcoral"}
    names = {r[0] for r in rows}
    needers, cards = set(), set()
    for _, _, needs, _ in rows:
        for kind in NEEDERS:
            # A tool that needs a tool stays in the tools layer — putting
            # it in both merged the two columns into one on the first draw.
            needers.update(f for f in needs[kind] if f not in names)
        cards.update(needs["cards"])
    out = ["digraph needed_by {",
           "  rankdir=LR; ranksep=1.6; nodesep=0.12; splines=true;",
           "  node [shape=box, style=filled, fontname=monospace, fontsize=9];",
           "  edge [color=gray50, arrowsize=0.6];",
           "  subgraph needers { rank=same;"]
    out += [f'    "{f}" [fillcolor=gray95];' for f in sorted(needers)]
    out += ["  }", "  subgraph tools_ { rank=same;"]
    for name, s, needs, q in rows:
        who = s[0] if s else "unstamped"
        out.append(f'    "{name}" [label="{name}\\n{who}", fillcolor="{colour[q]}"];')
    out += ["  }", "  subgraph cards { rank=same;"]
    out += [f'    "{c}" [fillcolor=gray95, shape=note];' for c in sorted(cards)]
    out.append("  }")
    for name, _, needs, _ in rows:
        for kind in NEEDERS:
            for f in needs[kind]:
                out.append(f'  "{f}" -> "{name}";')
        for f in needs["cards"]:
            out.append(f'  "{name}" -> "{f}" [style=dashed];')
    out.append("}")
    return "\n".join(out)


def svg(rows):
    """The graph laid out by `dot` — Sugiyama's layered layout, from the
    implementation everybody else's is measured against.  Refuses out
    loud without graphviz rather than drawing something worse."""
    import shutil
    import subprocess
    if shutil.which("dot") is None:
        raise SystemExit("asked: no `dot` on PATH — install graphviz, or use --dot and lay it out elsewhere")
    r = subprocess.run(["dot", "-Tsvg"], input=dot(rows), capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"asked: dot refused the graph:\n{r.stderr}")
    return r.stdout


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bare", action="store_true",
                    help="one line per tool, unsorted, for grepping")
    ap.add_argument("--graph", action="store_true",
                    help="asked-by × needed-by, four quadrants")
    ap.add_argument("--dot", action="store_true",
                    help="the graph as graphviz source on stdout")
    ap.add_argument("--svg", nargs="?", const="-", metavar="OUT",
                    help="the graph laid out by dot, as SVG to OUT (default stdout)")
    args = ap.parse_args(argv)

    if args.graph or args.dot or args.svg:
        rows = graph()
        if args.svg:
            picture = svg(rows)
            if args.svg == "-":
                sys.stdout.write(picture)
            else:
                pathlib.Path(args.svg).write_text(picture)
                print(f"asked: {len(rows)} tools drawn to {args.svg}")
        elif args.dot:
            print(dot(rows))
        else:
            print_graph(rows)
        return 0

    reg = register()
    if args.bare:
        for name, s in reg.items():
            print(f"{name}\t{s[0] if s else '—'}\t{s[1] if s else ''}")
        return 0

    missing = [n for n, s in reg.items() if s is None]
    for who in WHO:
        rows = [(n, s) for n, s in reg.items() if s and s[0] == who]
        if not rows:
            continue
        print(f"\n── {who} ── {len(rows)} of {len(reg)}")
        for name, (_, date, rest) in sorted(rows, key=lambda r: r[1][1]):
            print(f"  {date}  {name}")
            if rest:
                print(f"            {rest.lstrip('—- ')}")
    if missing:
        print(f"\n── no stamp ── {len(missing)}")
        for name in missing:
            print(f"  {name}")

    n = sum(1 for s in reg.values() if s and s[0] == "unrecorded")
    print(f"\nasked: {len(reg)} tools, {n} unrecorded, {len(missing)} unstamped.")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
