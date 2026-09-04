#!/usr/bin/env python3
#: asked-by: Henri, 2026-09-04 — "Lets open the card for backlink tool, I think it's something you could actually use, and there's a because for it already, in your words." — card:backlinks.md
"""tools/backlinks.py — who cites this?

    python tools/backlinks.py PATH               every place that cites a file
    python tools/backlinks.py card:<name>.md     … a card, by its id
    python tools/backlinks.py F123               … a defect
    python tools/backlinks.py [[name]]           … a memory (the bare name works too)
    python tools/backlinks.py --hook             as a PostToolUse hook on Read and Bash: stdin in, context out
    python tools/backlinks.py --time PATH        the walk's cost, cold and warm
    python tools/backlinks.py --check            the lamp: 1 not installed, 2 the cut has become noise
    python tools/backlinks.py --report           what the hook has been doing, from its own log
    python tools/backlinks.py --earned           whether the answer changed what the reader did next
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

**The hook watches itself, and it is asked to earn its place.**  Every
fire appends one line to `~/.local/state/gestate/backlinks.log` —
epoch, file, citers, shown, the sitting, and the paths it put in front
of the reader.  `--report` says what it has been doing; **`--earned`
says whether it mattered**: a *follow* is a fire on a file an earlier
fire in the same sitting offered and the reader had not already opened,
which is entirely inside the log because a follow is another fire.  A
follow is correlation and `earned`'s docstring says what it cannot rule
out; the honest floor is zero, and zero over a real number of fires
means the tool is decoration with a context bill.  Henri asked for that
number on 2026-09-04 — *"I think the new 'cited by' reading tool needs
a number that verifies whether it earns its place"* — and picked this
reading of it the same day.  `--check` trips when, over the last fortnight,
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
SHELVES = ("board", "board/done", "board/later", "board/refused")
#: The shelves a card is no longer worked on — every one of them ranks
#: below the live board, because a reader of a target wants to know what
#: currently leans on it before what once did.
SHELVED = ("board/done/", "board/later/", "board/refused/")

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
    (0, "cards and memory", lambda r: (r.startswith("board/") and not r.startswith(SHELVED))
                                      or r.startswith("doc/memory/")),
    (3, "shelved cards",    lambda r: r.startswith(SHELVED)),
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


def note(rel: str, total: int, shown: int, session: str = "",
         offered=()) -> None:
    """One line per fire, never fatal — the same shape as the sitting
    log, and for the same reason: a number a session picked (twenty)
    that nobody has checked needs the denominator kept somewhere.

    **Six fields since 2026-09-04**, and the last two are what make
    `earned` possible: the sitting this fire happened in, and the paths
    the answer put in front of the reader.  A follow is *another fire*
    — the reader opening one of those paths — so the whole measurement
    lives in this file and needs nothing else.

    Four-field lines from before that day still parse; they simply
    cannot take part in the follow count, and `earned` says how many it
    had to leave out rather than quietly dividing by a smaller number.

    A path never contains a tab or a comma, so the offer list is joined
    with commas and the record stays one line.
    """
    try:
        lp = log_path()
        lp.parent.mkdir(parents=True, exist_ok=True)
        names = ",".join(sorted({r for r in offered if "," not in r}))
        with lp.open("a", encoding="utf-8") as f:
            f.write(f"{int(time.time())}\t{rel}\t{total}\t{shown}\t"
                    f"{session}\t{names}\n")
    except OSError:
        pass


def fires(days: int = LAMP_DAYS, now: float | None = None) -> list[tuple[int, str, int, int]]:
    """The log's lines from the last `days`, parsed — `(when, file,
    total, shown)`, which is what the lamp and the report read."""
    return [(w, rel, total, shown) for w, rel, total, shown, _s, _o
            in _rows(days, now)]


def _rows(days: int = LAMP_DAYS, now: float | None = None) -> list:
    """Every field, including the two `earned` needs — `(when, file,
    total, shown, session, offered)`.  A pre-2026-09-04 line has an
    empty session and no offers and is kept, because it is still a fire
    and still counts in the denominator the cut share is read against.
    """
    lp = log_path()
    if not lp.exists():
        return []
    since = (now if now is not None else time.time()) - days * 86400
    out = []
    try:
        for ln in lp.read_text(encoding="utf-8").splitlines():
            parts = ln.split("\t")
            if len(parts) < 4:
                continue
            try:
                when, total, shown = int(parts[0]), int(parts[2]), int(parts[3])
            except ValueError:
                continue
            if when < since:
                continue
            session = parts[4] if len(parts) > 4 else ""
            offered = [r for r in (parts[5].split(",") if len(parts) > 5 else [])
                       if r]
            out.append((when, parts[1], total, shown, session, offered))
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
    #: **The second cause, and it is named apart from the first** — one
    #: lamp lighting for two reasons with one sentence is how an andon
    #: gets muted.  This one says the tool has not earned its place: no
    #: reading it offered was ever opened.  The answer is to take the
    #: hook out, or to say why not; it is not a nudge.
    g = earned(days, now)
    if g["fires"] >= LAMP_MIN_FIRES and g["follows"] == 0:
        return True, (line + f" — and none of {g['fires']} fires was followed: "
                      "nothing the tool offered was opened.  `--earned` has the "
                      "numbers; card:backlinks.md asked for this one, and zero "
                      "is the answer that takes the hook out")
    if g["fires"]:
        line += f"; {g['follows']} of {g['fires']} followed"
    return False, line


def earned(days: int = LAMP_DAYS, now: float | None = None) -> dict:
    """Did the answer change what the reader did next?

    **The number `card:backlinks.md` left open**, asked for by Henri on
    2026-09-04 — *"the new 'cited by' reading tool needs a number that
    verifies whether it earns its place"* — and this is it: a **follow**
    is a fire on a file that an *earlier fire in the same sitting* put
    in front of the reader and that the reader had not already opened.
    The reader was shown a name they had no other route to from what
    they were reading, and then they opened it.

    It is entirely inside the log, because a follow is another fire.

    **What it is not, said plainly.**  A follow is *correlation*.  The
    session may have been going to that file anyway — from the task,
    from a grep, from having read it in an earlier sitting.  Nothing
    here rules that out and no number in this log can.  What the log
    does establish is the direction and the order: the name was offered
    before it was opened, and it was offered by the one instrument that
    shows a target its citers.

    **The honest floor is zero.**  A rate of zero over a real number of
    fires means the tool is decoration with a context bill, and that is
    a decision rather than a nudge.  A rate above zero is something no
    other route delivered, and what it is worth is the reader's to say
    — which is why nothing here picks a threshold (`fixme.md` F169: a
    number nobody asked for is a number nobody checks).

    Returns the counts, and `blind` for the fires too old to carry a
    sitting id, so the denominator is never quietly the smaller one.
    """
    rows = sorted(_rows(days, now), key=lambda r: r[0])
    blind = sum(1 for r in rows if not r[4])
    sittings: dict[str, list] = {}
    for row in rows:
        if row[4]:
            sittings.setdefault(row[4], []).append(row)
    fires_seen = follows = 0
    offers: set[str] = set()
    taken: set[str] = set()
    lag: list[int] = []
    for rows_of in sittings.values():
        #: When each name was first put in front of this sitting, and
        #: which files this sitting had already opened.  A name offered
        #: *after* it was read is not an offer that led anywhere.
        first_offer: dict[str, int] = {}
        read: set[str] = set()
        for when, rel, _total, _shown, _s, offered in rows_of:
            fires_seen += 1
            if rel in first_offer and rel not in read:
                follows += 1
                taken.add(rel)
                lag.append(when - first_offer[rel])
            read.add(rel)
            for name in offered:
                if name not in read and name not in first_offer:
                    first_offer[name] = when
                    offers.add(name)
    return {"days": days, "fires": fires_seen, "blind": blind,
            "follows": follows, "offered": len(offers), "taken": len(taken),
            "lag": lag}


def report_earned(days: int = LAMP_DAYS) -> str:
    g = earned(days)
    if not g["fires"]:
        return (f"backlinks: no fires with a sitting id in {days} days"
                + (f" ({g['blind']} older ones cannot be followed)"
                   if g["blind"] else ""))
    rate = g["follows"] / g["fires"]
    lines = [f"backlinks --earned, {days} days: {g['follows']} of "
             f"{g['fires']} fires were followed ({rate:.0%})"]
    if g["offered"]:
        lines.append(f"  names offered: {g['offered']}, opened after being "
                     f"offered: {g['taken']}")
    if g["lag"]:
        mid = sorted(g["lag"])[len(g["lag"]) // 2]
        lines.append(f"  median time from offer to opening: {mid}s")
    if g["blind"]:
        lines.append(f"  {g['blind']} fires predate the sitting id and are "
                     "not in the numbers above")
    lines.append("  a follow is correlation, not cause — the docstring says "
                 "what it cannot rule out")
    return "\n".join(lines)


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


#: Shell commands that read a file's *content*.  `pytest`, `python` and
#: `ls` name paths and do not read them, and answering for those would
#: spend a reader's attention on a citer list they never asked to see.
READERS = {"cat", "sed", "head", "tail", "less", "more", "nl", "bat",
           "grep", "rg", "awk", "ug", "ugrep"}

#: Flags that turn a reader into something else.  `sed -i` edits, and a
#: recursive grep is a *search* over the tree rather than a read of a
#: file — its operand is a directory and its hits are the answer.
NOT_READING = {"-i", "--in-place", "-r", "-R", "--recursive", "-l",
               "--files-with-matches"}

#: How many files one command may be answered for.  A command naming a
#: dozen is a sweep, and a dozen citer lists at once is the noise the
#: cut at twenty was invented to stop.
BASH_CUT = 3


def read_targets(command: str, root: Path = ROOT) -> list[str]:
    """The tree files a shell command actually *reads*, in order.

    **Narrow on purpose.**  The `Read` hook has one unambiguous
    argument; a shell command has a grammar.  So this accepts only a
    segment whose verb is in `READERS`, and within it only tokens that
    **resolve to a file that exists inside the tree** — which is what
    keeps `sed -n '1,40p' doc/x.md` from offering `1,40p`, and
    `grep -n "foo" tools/y.py` from offering `foo`, with no per-command
    flag table to keep in step with seven tools.
    """
    import shlex

    try:
        words = shlex.split(command, comments=True)
    except ValueError:                                    # unbalanced quotes
        return []
    out: list[str] = []
    seen: set[str] = set()
    segment: list[str] = []
    for word in [*words, ";"]:
        if word in (";", "&&", "||", "|", "&"):
            _targets_of(segment, root, out, seen)
            segment = []
        else:
            segment.append(word)
    return out


def _targets_of(segment: list[str], root: Path, out: list, seen: set) -> None:
    while segment and "=" in segment[0] and not segment[0].startswith("-"):
        segment = segment[1:]                             # FOO=bar cat x
    if not segment or Path(segment[0]).name not in READERS:
        return
    if any(w in NOT_READING for w in segment[1:]):
        return
    skip = False
    for word in segment[1:]:
        if word.startswith(">") or word in ("2>", "1>"):
            skip = True                                   # a redirect target
            continue
        if skip:
            skip = False
            continue
        if word.startswith("-"):
            continue
        try:
            p = (root / word).resolve() if not Path(word).is_absolute() else Path(word).resolve()
            rel = str(p.relative_to(root.resolve()))
        except (ValueError, OSError):
            continue
        if p.is_file() and rel not in seen:
            seen.add(rel)
            out.append(rel)


def already_answered(session: str, days: int = LAMP_DAYS) -> set[str]:
    """Files this sitting has already been given the citers for.

    **A repeat is not worth its context.**  One file was read four times
    in the sitting of 2026-09-04 and paid for the same twenty lines each
    time — and a repeat can never be a *follow* anyway, because the file
    had already been opened, so it was inflating the denominator of the
    one number the tool is judged on.  Shell reads repeat far more than
    `Read` calls do, which is why this arrives with the Bash matcher.
    """
    if not session:
        return set()
    return {rel for _w, rel, _t, _s, sess, _o in _rows(days) if sess == session}


def hook(stdin: str, root: Path = ROOT) -> str:
    """The PostToolUse contract: JSON in, JSON out, or nothing.

    Two matchers over one answer.  `Read` names its file outright;
    `Bash` is parsed for the files it actually reads, because this
    environment tells a session to prefer the shell and the rule asking
    it not to lost to that instruction on 2026-09-04 and again on
    2026-09-05.  A hook does not depend on which instruction won.
    """
    try:
        payload = json.loads(stdin or "{}")
        tool = payload.get("tool_name", "Read")
        args = payload.get("tool_input") or {}
        session = str(payload.get("session_id") or "")
        if tool == "Bash":
            return _for_paths(read_targets(args.get("command") or "", root),
                              session, root)
        if tool != "Read":
            return ""
        path = args.get("file_path")
        if not path:
            return ""
        p = Path(path)
        try:
            p.resolve().relative_to(root.resolve())
        except ValueError:
            return ""
        return _for_paths([str(p)], session, root)
    except Exception as e:                                # noqa: BLE001
        print(f"backlinks --hook: {e!r}", file=sys.stderr)
        return ""


def _for_paths(paths: list[str], session: str, root: Path) -> str:
    """One answer for however many files the reader just opened."""
    if not paths:
        return ""
    done = already_answered(session)
    tree = Tree(root)
    blocks: list[str] = []
    for path in paths[:BASH_CUT]:
        name, rows = citers(tree, path)
        if not rows or name in done:
            continue
        done.add(name)
        shown = rows[:HOOK_CUT]
        # The sitting, and what was actually put in front of the reader
        # — the two fields `earned` needs.  `session_id` is the harness's
        # own; when it is absent the fire still counts as a fire and
        # simply cannot take part in a follow.
        note(name, len(rows), len(shown), session,
             {rel for rel, _line, _text in shown})
        lines = [f"{name} is cited by {len(rows)} place{'s' if len(rows) != 1 else ''} "
                 f"(tools/backlinks.py):"]
        lines += grouped(shown)
        if len(rows) > HOOK_CUT:
            lines.append(f"  … and {len(rows) - HOOK_CUT} more: "
                         f"python tools/backlinks.py {name}")
        blocks.append("\n".join(lines))
    if not blocks:
        return ""
    return json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "\n\n".join(blocks)}})


INSTALL = """\
    "PostToolUse": [
      {
        "matcher": "Read|Bash",
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
        #: Either matcher counts as installed.  `Read` alone was the
        #: 2026-09-04 install and still works; `Read|Bash` is what a
        #: shell-reading session needs, and a checkout with only the
        #: first is not broken, it is narrower.
        if "Read" not in (entry.get("matcher") or ""):
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
    ap.add_argument("--earned", action="store_true",
                    help="did the answer change what the reader did next")
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
    elif a.earned:
        print(report_earned(a.days))
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
