#: asked-by: Henri, 2026-08-23 — "tätä varten voi tehdä kortin ... tee siitä portti kun suite on ajettu"
"""Who asked for each tool on this bench — and which nobody can say.

    python tools/asked.py            # the register, grouped by who asked
    python tools/asked.py --bare     # one line per tool, for grepping


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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bare", action="store_true",
                    help="one line per tool, unsorted, for grepping")
    args = ap.parse_args(argv)

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
