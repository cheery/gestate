#!/usr/bin/env python3
#: asked-by: Henri, 2026-08-24 — "build it, spend the twenty lines." — 19 of 53 memories in the tree reached no session at boot
"""tools/memoryindex.py — the private index's public half, generated from the tree.

    python tools/memoryindex.py            rewrite the block in ~/.claude/…/memory/MEMORY.md
    python tools/memoryindex.py --check    exit 1 if that block is behind doc/memory/README.md
    python tools/memoryindex.py --print    the block, to stdout
    python tools/memoryindex.py PATH …     another index file (tests)

**What this fixes.**  The private `MEMORY.md` is what every session
reads before it asks for anything — the only half of the boot surface
`tools/seedaudit.py` cannot see, because it lives outside the tree,
unversioned, on one machine, written by sessions.  On 2026-08-24 it was
measured against `doc/memory/`: **19 of the 53 memories in the tree
were hooked by nothing at boot**, among them the ones the week's trials
were about.  Whether the hooks were never added or were lost cannot be
known, because the file has no history.  `~/audit-a4.pdf` is the sheet.

**The shape.**  `doc/memory/README.md` §"The index" is already the full
list, versioned and gated by `test/test_memory.py`.  So the public half
of the private index becomes a *view* of it: the lines between the two
markers below are written by this tool from that README, with the
paths made absolute, and nothing else in the file is touched.  The
private section — the nine about the person, Henri's 2026-08-21 call —
is kept by hand and this tool never reads it.  Same move as the atlas
and `doc/method.md`'s piece table: a generated block, and a gate that
refuses the page when it is behind its source.

**Where a hook goes now.**  Into `doc/memory/README.md`, beside the
body.  A hook added by hand inside the generated block is removed at
the next run — correct, and it will surprise the session that did it,
which is why the opening marker says so.
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
README = ROOT / "doc" / "memory" / "README.md"
DEFAULT = pathlib.Path.home() / ".claude" / "projects" / "-home-cheery-gestate" / "memory" / "MEMORY.md"

OPEN = "<!-- memoryindex: generated from doc/memory/README.md by tools/memoryindex.py — add hooks THERE, not here -->"
CLOSE = "<!-- /memoryindex -->"
HOOK = re.compile(r"^- \[([^\]]+)\]\(([\w.-]+\.md)\)(.*)$")


def hooks(readme=README):
    """(title, file, rest) for every index line in the tree's README."""
    text = readme.read_text(encoding="utf-8")
    body = text[text.index("## The index"):]
    out = []
    for line in body.splitlines():
        m = HOOK.match(line)
        if m:
            out.append(m.groups())
    return out


def block(readme=README, root=ROOT):
    lines = [OPEN]
    for title, name, rest in hooks(readme):
        lines.append(f"- [{title}]({root / 'doc' / 'memory' / name}){rest}")
    lines.append(CLOSE)
    return "\n".join(lines)


def apply(text, new):
    """The index with its generated block replaced, or inserted under the
    tree heading the first time."""
    if OPEN in text and CLOSE in text:
        a, b = text.index(OPEN), text.index(CLOSE) + len(CLOSE)
        return text[:a] + new + text[b:]
    heading = "## In the tree — doc/memory/"
    if heading not in text:
        raise SystemExit(f"memoryindex: no generated block and no '{heading}' heading to put one under")
    # First run: the hand-written hooks under the heading are what the
    # block replaces — every one of them is in the README already.
    start = text.index(heading) + len(heading)
    nxt = text.find("\n## ", start)
    tail = text[nxt:] if nxt != -1 else ""
    return text[:start] + "\n\n" + new + "\n" + tail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=DEFAULT, type=pathlib.Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--print", action="store_true")
    args = ap.parse_args()
    new = block()
    if args.print:
        print(new)
        return 0
    if not args.path.is_file():
        print(f"memoryindex: no index at {args.path} — nothing to do here", file=sys.stderr)
        return 0
    old = args.path.read_text(encoding="utf-8")
    want = apply(old, new)
    if args.check:
        if want == old:
            print(f"memoryindex: in step with doc/memory/README.md ({len(hooks())} hooks)")
            return 0
        print("memoryindex: the private index is behind doc/memory/README.md — run tools/memoryindex.py")
        return 1
    args.path.write_text(want, encoding="utf-8")
    print(f"memoryindex: wrote {len(hooks())} hooks into {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
