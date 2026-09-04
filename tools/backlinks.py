#!/usr/bin/env python3
#: asked-by: Henri, 2026-09-04 — "Lets open the card for backlink tool, I think it's something you could actually use, and there's a because for it already, in your words." — card:backlinks.md
"""tools/backlinks.py — who cites this?

    python tools/backlinks.py PATH               every place that cites a file
    python tools/backlinks.py card:<name>.md     … a card, by its id
    python tools/backlinks.py F123               … a defect
    python tools/backlinks.py [[name]]           … a memory (the bare name works too)
    python tools/backlinks.py --hook             as a PostToolUse hook on Read: stdin in, context out
    python tools/backlinks.py --time PATH        the walk's cost, cold and warm
    python tools/backlinks.py --check            the lamp: 1 not installed, 2 the cut has become noise
    python tools/backlinks.py --report           what the hook has been doing, from its own log
    python tools/backlinks.py --install          the settings.json lines to add

**What this answers.**  Every citation in this tree runs one way: the
citing file knows its target, the target knows nothing.  A session
reading `gestate/host.c` cannot see that `card:unseen-flare.md` and a
memory lean on it; a session reading a memory cannot see the three
places that apply it.  This is the inverse index — the same walk
`test/test_citations.py` makes, with the pairs turned around.

**Five kinds of citer**, and nothing about how anything is cited
changes:

    file.md §"a passage"    resolved as test_citations resolves it
    card:<name>.md          a card, by id, on whatever shelf
    [[name]]                a memory body in doc/memory/
    F123                    a defect in fixme.md
    tools/asked.py          any file in the tree named by path, or by a
                            bare basename when only one file has it

**Why a hook and not a generated block.**  `card:backlinks.md` §"Q1,
reasoned": the failure the card names happens while reading source and
spec — the thing a session *was* reading when it did not know a memory
existed — and a generated foot cannot go into a `.py`.  A hook on the
reader's `Read` reaches every file, is never stale, and rewrites
nothing; a foot would have been rewritten in a quarter of all commits.
What the hook gives up is every reader that is not a Claude Code
session, and that is the trigger for building the foot over this same
command.

**The budget is a tenth of a second per read**, because it runs on
every one.  A cold walk over the tree costs more than that, so the
index is cached under `$XDG_CACHE_HOME` keyed by each file's size and
mtime, and a warm run rescans only what changed.  `--time` prints both
numbers; the test holds the warm one.

**Not all citations are equal**, Henri's words on the day it fired, so
the rows come ranked and grouped: what is currently wanted or known
first (live cards, memory), then the standing documents, then code and
tests that name the file, then shelved cards, the defect ledger, and
history last.  Within a group a card's own `see` line and an explicit
citation — a passage, a `card:` id, a `[[memory]]` — outrank a file
named in passing.  The cut at twenty falls on history first, which is
where the noise is.  `TIERS` is the table, and it is his to change.

**The hook watches itself.**  Every fire appends one line to
`~/.local/state/gestate/backlinks.log` — epoch, file, citers, shown —
and `--report` reads it.  `--check` trips when, over the last fortnight,
a third or more of the fires were cut at twenty and there were at least
thirty of them: that is the noise the card warned about arriving, and
the lamp names `card:backlinks-ranges.md`, the fix already designed.
The three numbers are the session's, picked 2026-09-04, and nobody has
checked them.

**Never fatal in the hook.**  A hook that dies takes the desk with it,
so `--hook` prints nothing and exits 0 on any failure, with the reason
on stderr where Claude Code's debug log keeps it.

**Install.**  `.claude/settings.json` is behind the leash, which a
session may not edit, so the install is Henri's: `--install` prints the
lines, `--check` says whether they are there, and `tools/pre-commit.sh`
prints the state as a lamp that never refuses a commit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: The same walk `test/test_citations.py` makes, plus the shell, C and
#: config files that carry citations in comments.  `.claude` is skipped
#: for the reason that file gives: a subagent worktree lives inside it.
CITERS = {".py", ".rs", ".md", ".ges", ".sh", ".c", ".h", ".toml", ".txt"}
SKIP = {"target", ".venv", "__pycache__", ".git", "node_modules", ".claude",
        ".pytest_cache", ".mypy_cache", "dist", "build"}
SHELVES = ("board", "board/done", "board/later")

SEC = re.compile(r"`?([\w./-]+\.md)`?\s*§\"([^\"]+)\"")
CARD = re.compile(r"`?card:([\w-]+\.md)`?")
WIKI = re.compile(r"\[\[([\w-]+)\]\]")
FNUM = re.compile(r"(?<![\w.])F(\d{1,3})\b")
DEFINES = re.compile(r"^###\s+F\d{1,3}\.")
#: A file named by path, or by a bare basename.  The look-behind keeps
#: `a.b.py` from yielding `b.py`, and a URL's host from yielding `.md`.
MENTION = re.compile(
    r"(?<![\w./@-])((?:[\w-]+/)*[\w-]+\.(?:py|sh|rs|md|c|h|ges|json|toml|txt|html|js|css))\b")

TEXT_CUT = 100
HOOK_CUT = 20

#: The lamp's three numbers — window, floor, and the share of fires cut
#: at HOOK_CUT that means the twenty lines have become noise.
LAMP_DAYS = 14
LAMP_MIN_FIRES = 30
LAMP_CUT_SHARE = 1 / 3

#: Where a citer stands, by what it is.  Lower comes first.  The order
#: is what a reader of the *target* most wants to know: what currently
#: leans on it, then what defines the tree, then code, then the past.
TIERS = (
    (0, "cards and memory", lambda r: (r.startswith("board/") and not r.startswith(("board/done/", "board/later/")))
                                      or r.startswith("doc/memory/")),
    (3, "shelved cards",    lambda r: r.startswith(("board/done/", "board/later/"))),
    (4, "the ledger",       lambda r: r == "fixme.md"),
    (5, "history",          lambda r: r == "journal.md" or r.startswith("journal/")),
    (2, "code and tests",   lambda r: r.startswith(("test/", "gestate/", "tools/", "shell/", "examples/"))
                                      or r.endswith((".py", ".rs", ".c", ".h", ".sh", ".ges"))),
    (1, "documents",        lambda r: True),
)
#: A card's header block — `status`, `because`, `asked`, `see` — where a
#: citation is a deliberate pointer and not a mention.
HEADER_LINES = 20


# --- the tree ---------------------------------------------------------------

def files(root: Path) -> dict[str, os.stat_result]:
    """Every file under ROOT that is not in a skipped directory, as
    `{tree-relative path: stat}` — one pass, and the stat kept, because
    the walk is the whole warm cost and doing it twice put the hook over
    its budget."""
    out: dict[str, os.stat_result] = {}
    base = str(root)

    def walk(dirpath: str) -> None:
        try:
            entries = sorted(os.scandir(dirpath), key=lambda e: e.name)
        except OSError:
            return
        for e in entries:
            if e.is_dir(follow_symlinks=False):
                if e.name not in SKIP:
                    walk(e.path)
            elif e.is_file(follow_symlinks=False):
                try:
                    out[os.path.relpath(e.path, base).replace(os.sep, "/")] = e.stat()
                except OSError:
                    pass
    walk(base)
    return out


class Tree:
    """The files, and how a token resolves to one of them."""

    def __init__(self, root: Path):
        self.root = root
        self.stat = files(root)
        self.rel = set(self.stat)
        by_name: dict[str, list[str]] = {}
        for r in self.rel:
            by_name.setdefault(r.rsplit("/", 1)[-1], []).append(r)
        #: A bare basename resolves only when it is unique in the tree.
        #: `README.md` is not, so a mention of it cites nothing — which
        #: is the honest answer, since the reader could not tell either.
        self.unique = {n: rs[0] for n, rs in by_name.items() if len(rs) == 1}

    def resolve(self, token: str, here: str) -> str | None:
        """A path token to the tree-relative path it names, or None."""
        if "/" in token:
            base = here.rsplit("/", 1)[0] if "/" in here else ""
            for cand in (token, f"{base}/{token}" if base else token):
                cand = os.path.normpath(cand)
                if cand in self.rel:
                    return cand
            return None
        return self.unique.get(token)

    def resolve_section(self, target: str, here: str) -> str | None:
        """`file.md §"…"` — the order `test_citations.py` tries."""
        base = here.rsplit("/", 1)[0] if "/" in here else ""
        for cand in (f"{base}/{target}" if base else target, target,
                     f"spec/{target}", f"doc/{target}"):
            cand = os.path.normpath(cand)
            if cand in self.rel:
                return cand
        return None


def keys_for(tree: Tree, target: str) -> tuple[str, list[str], set[str]]:
    """What a person typed, to (a display name, the index keys it answers
    to, the files that *are* the target and so cannot cite it).

    The third is not the first: a card asked for by id is displayed as
    the id and lives on one of three shelves, and the first version
    counted a card naming its own id as its own citer."""
    t = target.strip()
    if t.startswith("card:"):
        own = {f"{shelf}/{t[5:]}" for shelf in SHELVES}
        return t, [t], own & tree.rel
    if re.fullmatch(r"F\d{1,3}", t):
        return t, [t], set()
    m = re.fullmatch(r"\[\[([\w-]+)\]\]", t)
    if m:
        t = m.group(1)
    if "/" not in t and not t.endswith(".md") and f"doc/memory/{t}.md" in tree.rel:
        rel = f"doc/memory/{t}.md"
        return rel, [f"mem:{t}", rel], {rel}
    # A path, absolute or relative to ROOT or to the working directory.
    p = Path(t)
    if not p.is_absolute():
        for cand in (tree.root / t, Path.cwd() / t):
            if cand.exists():
                p = cand
                break
    try:
        rel = p.resolve().relative_to(tree.root.resolve()).as_posix()
    except ValueError:
        return t, [], set()
    keys = [rel]
    parts = rel.split("/")
    if len(parts) >= 2 and "/".join(parts[:-1]) in SHELVES and parts[-1] != "README.md":
        keys.append(f"card:{parts[-1]}")
    if len(parts) == 3 and parts[:2] == ["doc", "memory"] and parts[2] != "README.md":
        keys.append(f"mem:{parts[2][:-3]}")
    return rel, keys, {rel}


# --- the index --------------------------------------------------------------

def scan(tree: Tree, rel: str, text: str) -> list[list]:
    """`[line, key, text]` for every citation in one file."""
    out = []
    seen = set()
    for n, line in enumerate(text.splitlines(), 1):
        #: (key, explicit) — a passage, an id, a wiki link or a defect
        #: number is a citation somebody wrote on purpose; a file named
        #: in passing is not, and ranks below it.
        hits: list[tuple[str, bool]] = []
        for target, _section in SEC.findall(line):
            r = tree.resolve_section(target, rel)
            if r:
                hits.append((r, True))
        hits += [(f"card:{c}", True) for c in CARD.findall(line)]
        hits += [(f"mem:{w}", True) for w in WIKI.findall(line)]
        #: `fixme.md`'s own `### F25.` heading is the entry, not a citer
        #: of it — the one line that defines a defect rather than leans
        #: on it.
        if not (rel == "fixme.md" and DEFINES.match(line)):
            hits += [(f"F{f}", True) for f in FNUM.findall(line)]
        for tok in MENTION.findall(line):
            r = tree.resolve(tok, rel)
            if r:
                hits.append((r, False))
        for key, explicit in hits:
            if key == rel or (n, key) in seen:
                continue
            seen.add((n, key))
            out.append([n, key, " ".join(line.split())[:TEXT_CUT], explicit])
    return out


def cache_path(root: Path) -> Path:
    if os.environ.get("GESTATE_BACKLINKS_CACHE"):
        return Path(os.environ["GESTATE_BACKLINKS_CACHE"])
    home = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    tag = hashlib.sha1(str(root).encode()).hexdigest()[:12]
    return home / "gestate" / f"backlinks-v2-{tag}.json"


def index(tree: Tree, use_cache: bool = True) -> dict:
    """`{rel: {"m": mtime_ns, "s": size, "c": [[line, key, text, explicit], …]}}`,
    rescanning only what moved since the cache was written."""
    cp = cache_path(tree.root)
    old: dict = {}
    if use_cache and cp.exists():
        try:
            old = json.loads(cp.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            old = {}
    new: dict = {}
    for rel, st in tree.stat.items():
        if os.path.splitext(rel)[1] not in CITERS:
            continue
        had = old.get(rel)
        if had and had.get("m") == st.st_mtime_ns and had.get("s") == st.st_size:
            new[rel] = had
            continue
        try:
            text = (tree.root / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        new[rel] = {"m": st.st_mtime_ns, "s": st.st_size, "c": scan(tree, rel, text)}
    if use_cache and new != old:
        try:
            cp.parent.mkdir(parents=True, exist_ok=True)
            tmp = cp.with_suffix(".tmp")
            tmp.write_text(json.dumps(new), encoding="utf-8")
            os.replace(tmp, cp)
        except OSError:
            pass
    return new


def citers(tree: Tree, target: str, use_cache: bool = True):
    """(display name, [(citing file, line, text)…]) for one target."""
    name, keys, own = keys_for(tree, target)
    if not keys:
        return name, []
    want = set(keys)
    found: dict[tuple[str, int], tuple[str, bool]] = {}
    for rel, entry in index(tree, use_cache).items():
        if rel in own:
            continue
        for line, key, text, explicit in entry["c"]:
            #: One line, one row — a card named by id and by its basename
            #: on the same line answers to two keys and is one citation,
            #: and it is explicit if either spelling was.
            if key in want:
                had = found.get((rel, line))
                found[(rel, line)] = (text, explicit or (had[1] if had else False))
    rows = [(rel, line, text, explicit) for (rel, line), (text, explicit) in found.items()]
    rows.sort(key=rank)
    return name, [(rel, line, text) for rel, line, text, _e in rows]


def tier(rel: str) -> tuple[int, str]:
    for order, label, fits in TIERS:
        if fits(rel):
            return order, label
    return 1, "documents"                                  # pragma: no cover


def rank(row) -> tuple:
    """Where a citation sorts: its tier, then a card's header block, then
    an explicit citation over a mention, then the file and the line."""
    rel, line, _text, explicit = row
    order, _label = tier(rel)
    header = 0 if (rel.startswith("board/") and line <= HEADER_LINES) else 1
    return (order, header, 0 if explicit else 1, rel, line)


# --- the four ways it is used ------------------------------------------------

def grouped(rows) -> list[str]:
    """The rows as lines, each tier under its label, in rank order."""
    out = []
    last = None
    for rel, line, text in rows:
        _order, label = tier(rel)
        if label != last:
            out.append(f"{label}:")
            last = label
        out.append(f"  {rel}:{line}  {text}")
    return out


def report(name: str, rows) -> str:
    if not rows:
        return f"{name} — cited by nothing"
    n = len(rows)
    head = f"{name} — cited by {n} place{'s' if n != 1 else ''}"
    return "\n".join([head, *grouped(rows)])


def log_path() -> Path:
    if os.environ.get("GESTATE_BACKLINKS_LOG"):
        return Path(os.environ["GESTATE_BACKLINKS_LOG"])
    return Path.home() / ".local" / "state" / "gestate" / "backlinks.log"


def note(rel: str, total: int, shown: int) -> None:
    """One line per fire, never fatal — the same shape as the sitting
    log, and for the same reason: a number a session picked (twenty)
    that nobody has checked needs the denominator kept somewhere."""
    try:
        lp = log_path()
        lp.parent.mkdir(parents=True, exist_ok=True)
        with lp.open("a", encoding="utf-8") as f:
            f.write(f"{int(time.time())}\t{rel}\t{total}\t{shown}\n")
    except OSError:
        pass


def fires(days: int = LAMP_DAYS, now: float | None = None) -> list[tuple[int, str, int, int]]:
    """The log's lines from the last `days`, parsed."""
    lp = log_path()
    if not lp.exists():
        return []
    since = (now if now is not None else time.time()) - days * 86400
    out = []
    try:
        for ln in lp.read_text(encoding="utf-8").splitlines():
            parts = ln.split("\t")
            if len(parts) != 4:
                continue
            try:
                when, total, shown = int(parts[0]), int(parts[2]), int(parts[3])
            except ValueError:
                continue
            if when >= since:
                out.append((when, parts[1], total, shown))
    except OSError:
        return []
    return out


def lamp(days: int = LAMP_DAYS, now: float | None = None) -> tuple[bool, str]:
    """(tripped, the line to print).  Trips when the cut has become the
    rule: at least LAMP_MIN_FIRES fires in the window and LAMP_CUT_SHARE
    of them cut at HOOK_CUT."""
    rows = fires(days, now)
    if not rows:
        return False, f"backlinks: no fires logged in {days} days"
    cut = sum(1 for _w, _r, total, shown in rows if total > shown)
    share = cut / len(rows)
    line = (f"backlinks: {len(rows)} fires in {days} days, {cut} cut at {HOOK_CUT} "
            f"({share:.0%})")
    if len(rows) >= LAMP_MIN_FIRES and share >= LAMP_CUT_SHARE:
        return True, (line + " — the twenty lines have become noise; the fix is "
                      "designed in card:backlinks-ranges.md, and this is its trigger")
    return False, line


def report_fires(days: int = LAMP_DAYS) -> str:
    rows = fires(days)
    _tripped, head = lamp(days)
    if not rows:
        return head
    by_file: dict[str, list[int]] = {}
    for _w, rel, total, _shown in rows:
        by_file.setdefault(rel, []).append(total)
    top = sorted(by_file.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:8]
    lines = [head, "  most read, with their citer counts:"]
    lines += [f"    {rel}  ×{len(ts)}, {max(ts)} citers" for rel, ts in top]
    return "\n".join(lines)


def hook(stdin: str, root: Path = ROOT) -> str:
    """The PostToolUse contract: JSON in, JSON out, or nothing."""
    try:
        payload = json.loads(stdin or "{}")
        if payload.get("tool_name", "Read") != "Read":
            return ""
        path = (payload.get("tool_input") or {}).get("file_path")
        if not path:
            return ""
        p = Path(path)
        try:
            p.resolve().relative_to(root.resolve())
        except ValueError:
            return ""
        tree = Tree(root)
        name, rows = citers(tree, str(p))
        if not rows:
            return ""
        shown = rows[:HOOK_CUT]
        note(name, len(rows), len(shown))
        lines = [f"{name} is cited by {len(rows)} place{'s' if len(rows) != 1 else ''} "
                 f"(tools/backlinks.py):"]
        lines += grouped(shown)
        if len(rows) > HOOK_CUT:
            lines.append(f"  … and {len(rows) - HOOK_CUT} more: "
                         f"python tools/backlinks.py {name}")
        return json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "\n".join(lines)}})
    except Exception as e:                                # noqa: BLE001
        print(f"backlinks --hook: {e!r}", file=sys.stderr)
        return ""


INSTALL = """\
    "PostToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          { "type": "command", "command": "~/gestate/tools/backlinks.py --hook", "timeout": 5 }
        ]
      }
    ]"""


def installed(settings: Path = ROOT / ".claude" / "settings.json") -> bool:
    try:
        conf = json.loads(settings.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    for entry in (conf.get("hooks") or {}).get("PostToolUse", []):
        if entry.get("matcher") not in ("Read", "^Read$"):
            continue
        for h in entry.get("hooks", []):
            cmd = h.get("command", "")
            if "backlinks.py" in cmd and "--hook" in cmd:
                return True
    return False


def timed(tree: Tree, target: str) -> tuple[float, float]:
    """Cold (cache dropped) and warm, in seconds."""
    cp = cache_path(tree.root)
    if cp.exists():
        cp.unlink()
    t0 = time.perf_counter()
    citers(tree, target)
    cold = time.perf_counter() - t0
    t0 = time.perf_counter()
    citers(Tree(tree.root), target)
    warm = time.perf_counter() - t0
    return cold, warm


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="who cites this?")
    ap.add_argument("target", nargs="?", help="a path, card:<name>.md, F123, or [[name]]")
    ap.add_argument("--hook", action="store_true", help="PostToolUse hook on Read")
    ap.add_argument("--time", action="store_true", help="cold and warm cost of the walk")
    ap.add_argument("--check", action="store_true", help="exit 1 if the hook is not installed")
    ap.add_argument("--install", action="store_true", help="print the settings.json lines")
    ap.add_argument("--report", action="store_true", help="what the hook has been doing")
    ap.add_argument("--days", type=int, default=LAMP_DAYS, help="the report's window")
    ap.add_argument("--no-cache", action="store_true", help="walk the whole tree")
    a = ap.parse_args(argv)

    if a.hook:
        out = hook(sys.stdin.read())
        if out:
            print(out)
        return 0
    if a.install:
        print("add to .claude/settings.json under \"hooks\":\n" + INSTALL)
        return 0
    if a.report:
        print(report_fires(a.days))
        return 0
    if a.check:
        if not installed():
            print("backlinks: the Read hook is not installed — python tools/backlinks.py --install")
            return 1
        tripped, line = lamp(a.days)
        print("backlinks: the Read hook is installed; " + line[len("backlinks: "):])
        return 2 if tripped else 0
    if not a.target:
        ap.print_usage()
        return 2
    tree = Tree(ROOT)
    if a.time:
        cold, warm = timed(tree, a.target)
        print(f"cold {cold * 1000:.0f} ms, warm {warm * 1000:.0f} ms, "
              f"{sum(1 for r in tree.rel if os.path.splitext(r)[1] in CITERS)} files")
        return 0
    name, rows = citers(tree, a.target, use_cache=not a.no_cache)
    print(report(name, rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
