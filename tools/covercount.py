"""Which lines of `gestate/` the suite actually ran — and which it never did.

    python tools/covercount.py test/test_arith.py     # one file, seconds
    python tools/covercount.py -m "not golden"        # the fast half
    python tools/covercount.py                        # everything

**Fenced, deselect the two the fence cannot host.**  `tools/suite.py`
runs `test_editor_abi.py` and `test_safety.py` outside the fence — one
needs an X11 socket, the other checks a fence from outside and a fence
cannot nest.  Inside `tools/sandbox.sh` they fail rather than skip, and
five reds that describe the fence are five reds nobody should read:

    tools/sandbox.sh python tools/covercount.py -m "not golden" \\
        --ignore=test/test_editor_abi.py --ignore=test/test_safety.py

**Why this exists.**  On 2026-08-23 somebody asked Henri *"miten
verifioit että kaikki koodi on testattua?"* and the tree had no answer:
3,065 passing tests, roster poka-yokes that refuse an untested *file*,
differential oracles, committed goldens — and no way at all to name a
line no test has ever reached.  `doc/instruments.md`'s first rule is
that a missing capability is built the moment the need arises.  This is
that build.

**No new dependency.**  `requirements.txt` says the compiler needs
nothing, and coverage.py would have been the first tool to break that
for a measurement.  PEP 669 (`sys.monitoring`, CPython 3.12) does the
same job from the standard library, and does it nearly free: the
callback returns `DISABLE` every time, so each line of `gestate/` costs
exactly one callback for the whole run and never fires again.  A full
suite under this is minutes slower, not hours.

**What it cannot see, stated.**  A test that shells out — `subprocess`
to `python -m gestate.audioperform`, and this tree does that often —
runs in a child interpreter this monitor never entered.  Those lines
come back *uncovered* though they ran.  So a low number here is a
question, not a verdict, and the page names the shelling-out tests so
the reader knows which way the error points.  The number is a floor.

**And what a high number would not mean.**  Every defect this project
has actually shipped — nine in stage 10, twelve in the editor session,
six the session after — was in a line the suite *did* execute, with the
wrong thing believed about it.  Coverage answers "was this line ever
run", never "was it ever checked".  `spec/verification.md` is the
document about the second question; this tool is only about the first.
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "gestate"
PAGE = ROOT / "test" / "coverage.md"

MON = sys.monitoring
TOOL = MON.COVERAGE_ID

#: Lines seen, per absolute filename.  A `set` because the question is
#: "ever", not "how often" — a hit count would be a number nobody checks.
SEEN: dict[str, set[int]] = {}
#: Filename → is it ours.  Resolved once per code object's file, because
#: the callback runs before `DISABLE` retires each location and a path
#: comparison per line is the only cost this design has.
OURS: dict[str, bool] = {}


def _line(code, lineno):
    """Record and retire.  Returns `DISABLE` unconditionally: this
    location has now answered its only question and never needs to fire
    again, which is what keeps the overhead at one callback per line."""
    f = code.co_filename
    ours = OURS.get(f)
    if ours is None:
        ours = OURS[f] = f.startswith(str(PACKAGE))
    if ours:
        SEEN.setdefault(f, set()).add(lineno)
    return MON.DISABLE


def executable(path: Path) -> set[int]:
    """The lines `sys.monitoring` *could* report for this file.

    Compiled, then walked: a module's code object holds its functions
    and classes as nested constants, and `co_lines()` on each is exactly
    the table the interpreter fires LINE events from.  Anything else —
    counting non-blank non-comment lines, say — would disagree with the
    numerator and make the ratio a fiction."""
    try:
        code = compile(path.read_text(), str(path), "exec")
    except SyntaxError:
        return set()
    lines, stack = set(), [code]
    while stack:
        c = stack.pop()
        # `ln > 0`: a module's code object reports its `RESUME` at line
        # **zero**, which is not a line and can never be covered.  Left
        # in, it inflates the denominator by one per module and reports
        # a shortfall no test could close — found by
        # `test_covercount.py` on the day the tool was written.
        lines.update(ln for _, _, ln in c.co_lines() if ln)
        stack.extend(k for k in c.co_consts if hasattr(k, "co_lines"))
    return lines


def shells_out() -> list[str]:
    """Test files that start a child interpreter — the blind spot, named."""
    out = []
    for p in sorted((ROOT / "test").rglob("test_*.py")):
        t = p.read_text()
        if "sys.executable" in t or "subprocess.run" in t:
            out.append(p.relative_to(ROOT).as_posix())
    return out


def draw(rows, total_ex, total_hit, argv, wall, rc, blind):
    n = len(rows)
    pct = 100.0 * total_hit / total_ex if total_ex else 0.0
    L = [
        "# test/coverage.md — the lines the suite reached",
        "",
        "Generated by `tools/covercount.py`.  **A floor, not a verdict.**",
        "A test that shells out to `python -m gestate...` runs in a child",
        "this monitor never entered, so its lines are reported uncovered",
        "though they ran; the blind spot is named at the foot of this page.",
        "And a covered line is one that *ran*, never one that was *checked* —",
        "every defect this project has shipped was in a covered line.",
        "",
        "| | |",
        "|---|---|",
        f"| Ran | {datetime.now():%Y-%m-%d %H:%M:%S} |",
        f"| Command | `python tools/covercount.py {' '.join(argv)}` |",
        f"| Modules | {n} |",
        f"| Lines reached | {total_hit:,} of {total_ex:,} — {pct:.1f}% |",
        f"| Wall | {wall:.0f}s |",
        f"| Exit | {rc} |",
        "",
        "## By module, coldest first",
        "",
        "| module | reached | of | % |",
        "|---|---:|---:|---:|",
    ]
    for name, hit, ex in rows:
        p = 100.0 * hit / ex if ex else 0.0
        L.append(f"| `{name}` | {hit} | {ex} | {p:.0f}% |")
    L += [
        "",
        "## The blind spot",
        "",
        f"{len(blind)} test file(s) start a child interpreter, whose lines",
        "this run could not see:",
        "",
    ] + [f"* `{b}`" for b in blind] + [""]
    PAGE.write_text("\n".join(L))


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--help", action="help")
    args, rest = ap.parse_known_args()

    # `python tools/...` puts `tools/` on the path, not the root; pytest
    # adds the rootdir only when it is the one being run as `-m`.
    sys.path.insert(0, str(ROOT))
    import pytest

    MON.use_tool_id(TOOL, "gestate-covercount")
    MON.register_callback(TOOL, MON.events.LINE, _line)
    MON.set_events(TOOL, MON.events.LINE)
    started = time.time()
    try:
        rc = pytest.main(rest or ["test/"])
    finally:
        MON.set_events(TOOL, 0)
        MON.free_tool_id(TOOL)
    wall = time.time() - started

    rows, total_ex, total_hit = [], 0, 0
    for path in sorted(PACKAGE.glob("*.py")):
        ex = executable(path)
        if not ex:
            continue
        hit = len(SEEN.get(str(path), set()) & ex)
        rows.append((path.relative_to(ROOT).as_posix(), hit, len(ex)))
        total_ex += len(ex)
        total_hit += hit
    rows.sort(key=lambda r: (r[1] / r[2] if r[2] else 0, r[0]))

    blind = shells_out()
    draw(rows, total_ex, total_hit, rest, wall, int(rc), blind)
    pct = 100.0 * total_hit / total_ex if total_ex else 0.0
    print(f"\ncovercount: {total_hit:,} of {total_ex:,} lines "
          f"in gestate/ — {pct:.1f}% — drawn to {PAGE.relative_to(ROOT)}")
    print(f"covercount: a floor — {len(blind)} test file(s) shell out and "
          f"were not seen from inside.")
    return int(rc)


if __name__ == "__main__":
    sys.exit(main())
