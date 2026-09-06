#!/usr/bin/env python3
#: asked-by: Henri, 2026-09-06 — "Do cards for these, and implement standing
#: questions immediately, but come up with some good standing questions and
#: let me choose among them." — card:standing-questions.md
"""tools/standing.py — the question a session is asked when it opens a card

    python tools/standing.py --hook          as a PostToolUse hook on Read and Bash: stdin in, context out
    python tools/standing.py card:<name>.md  what the hook would say for that card, on demand
    python tools/standing.py --check         the lamp: 1 not installed, 2 the questions file is not usable
    python tools/standing.py --report        what the hook has been doing, from its own log
    python tools/standing.py --install       the settings.json lines to add

**What this is for.**  `doc/notes/notes-on-cues.md`, 2026-09-06: what a
session retrieves is a function of what is in its context, so *a session
cannot tell you what it knows that you did not ask about* — and the
question is the retrieval key.  The keeper's question-forming is the
bottleneck, and it cannot come from the session, so it comes from a
stored cue.  Henri's own sentence that morning: *"You know massive
amount of things, but mostly when I request them I get them.  their
acces seem to be scoped by context a lot."*

**Where the questions live: `board/standing.md`**, one section per
shelf — `## live` for a card in `board/`, `## shelved` for `later/`,
`## done`, `## refused` — and `## proposed`, which never fires.  Henri
chooses which line stands under which heading; a session proposes under
`proposed`.  A question is a `- ` line.  Nothing about the cards
changes: the type a question attaches to is the shelf, which is the one
type the board already has.

**Where it lands: in front of the session at the moment it opens the
card**, as a `PostToolUse` hook on `Read` and on `Bash` — the same
contract and the same shell parsing as `tools/backlinks.py`, and for
the same reason: the cue has to reach the context, and a perfect list
nobody reads changes nothing.  Once per card per sitting; a question
re-asked on every re-read of the same file is the noise that gets a
hook muted.

**And it is capped.**  `CAP` questions per fire, the first ones under
the heading, because the backlinks hook's own lesson (`card:backlinks-ranges.md`)
is that twenty lines train the reader to skim past.  A heading holding
more than the cap is a question nobody sees, and `--check` says so.

**Silent on everything it is not about, and silent on failure** — a
hook that raises interrupts a session over a file it was only reading,
so `--hook` prints nothing and exits 0 on any exception, with the
reason on stderr.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

#: Questions per fire.  Three is what a reader answers; the fourth is
#: the one they skip, and then the third.
CAP = 3

#: The shelf a card sits on is the type its questions attach to.
SHELVES = {
    "board": "live",
    "board/later": "shelved",
    "board/done": "done",
    "board/refused": "refused",
}

#: Files under `board/` that are not cards.
NOT_A_CARD = {"README.md", "standing.md"}

HEADING = re.compile(r"^##\s+(\w+)\s*$")
QUESTION = re.compile(r"^-\s+(.+?)\s*$")


def questions_file(root: Path = ROOT) -> Path:
    return root / "board" / "standing.md"


def parse(text: str) -> dict[str, list[str]]:
    """`{heading: [question, …]}`, in file order.  Anything before the
    first `## ` heading is prose and is not a question."""
    out: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        m = HEADING.match(line)
        if m:
            current = m.group(1).lower()
            out.setdefault(current, [])
            continue
        m = QUESTION.match(line)
        if m and current is not None:
            out[current].append(m.group(1))
    return out


def load(root: Path = ROOT) -> dict[str, list[str]]:
    return parse(questions_file(root).read_text(encoding="utf-8"))


def by_id(cite: str, root: Path = ROOT) -> str | None:
    """`card:<name>.md` → the card's path on whichever shelf holds it."""
    name = cite[len("card:"):]
    for shelf in SHELVES:
        if (root / shelf / name).is_file():
            return f"{shelf}/{name}"
    return None


def shelf_of(path: str, root: Path = ROOT) -> str | None:
    """The card's shelf as a question heading, or None when the file is
    not a card on any shelf."""
    if path.startswith("card:"):
        path = by_id(path, root) or path
    p = Path(path)
    try:
        rel = p.resolve().relative_to(root.resolve()) if p.is_absolute() else Path(path)
    except ValueError:
        return None
    rel = Path(os.path.normpath(str(rel)))
    if rel.suffix != ".md" or rel.name in NOT_A_CARD:
        return None
    return SHELVES.get(str(rel.parent))


def ask(path: str, root: Path = ROOT, sections: dict | None = None) -> list[str]:
    """The questions for one card, capped, or none."""
    shelf = shelf_of(path, root)
    if shelf is None:
        return []
    sections = sections if sections is not None else load(root)
    return list(sections.get(shelf, []))[:CAP]


# --- the log, and once-per-sitting ------------------------------------------

def log_path() -> Path:
    if os.environ.get("GESTATE_STANDING_LOG"):
        return Path(os.environ["GESTATE_STANDING_LOG"])
    state = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    return state / "gestate" / "standing.log"


def _rows(days: int | None = None) -> list[tuple[float, str, str, int]]:
    """`(when, card, session, how many asked)` per fire."""
    p = log_path()
    if not p.exists():
        return []
    since = time.time() - days * 86400 if days else 0
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        try:
            when = float(parts[0])
        except ValueError:
            continue
        if when < since:
            continue
        out.append((when, parts[1], parts[2], int(parts[3])))
    return out


def already_asked(session: str) -> set[str]:
    if not session:
        return set()
    return {card for _w, card, sess, _n in _rows() if sess == session}


def note(card: str, session: str, n: int) -> None:
    p = log_path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(f"{time.time():.0f}\t{card}\t{session}\t{n}\n")
    except OSError as e:
        print(f"standing: could not log: {e!r}", file=sys.stderr)


# --- the hook -----------------------------------------------------------------

def _rel(path: str, root: Path) -> str:
    p = Path(path)
    if p.is_absolute():
        return str(p.resolve().relative_to(root.resolve()))
    return os.path.normpath(path)


def _for_paths(paths: list[str], session: str, root: Path) -> str:
    if not paths:
        return ""
    sections = load(root)
    asked_before = already_asked(session)
    blocks = []
    for path in paths:
        qs = ask(path, root, sections)
        if not qs:
            continue
        rel = _rel(path, root)
        if rel in asked_before:
            continue
        asked_before.add(rel)
        note(rel, session, len(qs))
        shelf = shelf_of(path, root)
        lines = [f"standing questions for a {shelf} card, {rel} (tools/standing.py):"]
        lines += [f"  - {q}" for q in qs]
        blocks.append("\n".join(lines))
    if not blocks:
        return ""
    return json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "\n\n".join(blocks)}})


def hook(stdin: str, root: Path = ROOT) -> str:
    """The PostToolUse contract: JSON in, JSON out, or nothing."""
    try:
        payload = json.loads(stdin or "{}")
        tool = payload.get("tool_name", "Read")
        args = payload.get("tool_input") or {}
        session = str(payload.get("session_id") or "")
        if tool == "Bash":
            import backlinks  # the same shell parsing, one place
            return _for_paths(backlinks.read_targets(args.get("command") or "", root),
                              session, root)
        if tool != "Read":
            return ""
        path = args.get("file_path")
        if not path:
            return ""
        return _for_paths([str(path)], session, root)
    except Exception as e:                                # noqa: BLE001
        print(f"standing --hook: {e!r}", file=sys.stderr)
        return ""


# --- the lamp, the report, the install ----------------------------------------

INSTALL = """\
    "PostToolUse": [
      {
        "matcher": "Read|Bash",
        "hooks": [
          { "type": "command", "command": "~/gestate/tools/standing.py --hook", "timeout": 5 }
        ]
      }
    ]"""


def installed(settings: Path | None = None) -> bool:
    settings = settings or ROOT / ".claude" / "settings.json"
    try:
        conf = json.loads(settings.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    for entry in (conf.get("hooks") or {}).get("PostToolUse", []):
        if "Read" not in (entry.get("matcher") or ""):
            continue
        for h in entry.get("hooks", []):
            cmd = h.get("command", "")
            if "standing.py" in cmd and "--hook" in cmd:
                return True
    return False


def check(root: Path = ROOT, settings: Path | None = None) -> tuple[int, str]:
    """`(exit code, one line)`.  1: the hook is not installed.  2: the
    questions file is missing, has no heading a shelf answers to, or a
    heading holds more than the cap — a question nobody sees."""
    try:
        sections = load(root)
    except OSError:
        return 2, "standing: board/standing.md is missing"
    firing = {h: qs for h, qs in sections.items() if h in SHELVES.values()}
    over = [f"{h} holds {len(qs)}" for h, qs in firing.items() if len(qs) > CAP]
    if over:
        return 2, f"standing: over the cap of {CAP} — " + "; ".join(over) + " — the rest are never asked"
    live = sum(len(qs) for qs in firing.values())
    if not installed(settings):
        return 1, "standing: the hook is not installed — python tools/standing.py --install"
    if live == 0:
        return 0, "standing: installed; no question chosen yet, so it fires on nothing"
    rows = _rows(14)
    return 0, (f"standing: installed; {live} question{'s' if live != 1 else ''} standing, "
               f"{len(rows)} fire{'s' if len(rows) != 1 else ''} in 14 days")


def report(days: int = 14) -> str:
    rows = _rows(days)
    if not rows:
        return f"standing: no fires in {days} days"
    by_card: dict[str, int] = {}
    for _w, card, _s, _n in rows:
        by_card[card] = by_card.get(card, 0) + 1
    sittings = len({s for _w, _c, s, _n in rows if s})
    lines = [f"standing: {len(rows)} fires in {days} days, over {sittings} sittings"]
    for card, n in sorted(by_card.items(), key=lambda kv: -kv[1])[:10]:
        lines.append(f"    {card}  ×{n}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("card", nargs="?", help="a card path: what the hook would say")
    ap.add_argument("--hook", action="store_true", help="PostToolUse hook on Read and Bash")
    ap.add_argument("--check", action="store_true", help="the lamp")
    ap.add_argument("--report", action="store_true", help="the fires, from the log")
    ap.add_argument("--install", action="store_true", help="the settings.json lines to add")
    ap.add_argument("--days", type=int, default=14)
    a = ap.parse_args(argv)
    if a.hook:
        out = hook(sys.stdin.read())
        if out:
            print(out)
        return 0
    if a.install:
        print("add to .claude/settings.json under \"hooks\":\n" + INSTALL)
        return 0
    if a.check:
        code, line = check()
        print(line)
        return code
    if a.report:
        print(report(a.days))
        return 0
    if a.card:
        if a.card.startswith("card:"):
            a.card = by_id(a.card) or a.card
        qs = ask(a.card)
        if not qs:
            print(f"standing: nothing for {a.card} — not a card on a shelf, or no question under its heading")
            return 0
        print(f"standing questions for a {shelf_of(a.card)} card, {a.card}:")
        for q in qs:
            print(f"  - {q}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
