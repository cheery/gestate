"""Run the suite and let it draw itself.

    python tools/suite.py                 # fenced, the whole suite
    python tools/suite.py -m "not golden" # the fast half
    python tools/suite.py --unfenced      # when you mean to

**Why this exists.** A run that lives only in terminal scrollback has
said nothing by tomorrow. This one leaves `test/report.md` behind: what
ran, when, against which commit, whether the tree was clean, whether it
was fenced, and every failure named with its line. Extra arguments are
passed through to pytest.

**Why the report is not committed.** `pytest.ini` says it plainly — a
golden test re-renders through the interpreter and compares sample for
sample, and *"bit-exactness through `sin` and `exp` holds where the
buffer was made and nowhere else"*. A report is therefore a claim about
one machine at one commit. Committed, it would be read on a second
machine as though it meant something there, which is the exact drift
`doc/atlas/*.png` is kept out of the tree to avoid. So `test/report.md`
is generated, gitignored, and regenerated in about the time the suite
takes.

**It records the fence.** `tools/sandbox.sh` is where builds and tests
belong (`spec/sandbox.md`), and a report that did not say which side of
the fence it ran on would leave the reader to guess.
"""

import argparse
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "test" / "report.md"


def _run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, **kw)


def _commit():
    r = _run(["git", "log", "-1", "--format=%h %s"])
    return r.stdout.strip() or "(no commit)"


def _tree():
    r = _run(["git", "status", "--porcelain"])
    lines = [l for l in r.stdout.splitlines() if l.strip()]
    if not lines:
        return "clean"
    return f"{len(lines)} file(s) modified or untracked"


def _fence_state():
    """Ask the fence whether it is up, rather than assuming it."""
    r = _run([str(ROOT / "tools" / "sandbox.sh"), "--check"])
    ok = r.returncode == 0
    n = len(re.findall(r"[✓✗]", r.stdout))
    return ok, f"{n}/{n} — the fence is up" if ok else "FENCE INCOMPLETE"


# **Tests the fence cannot host, and why each one.**
#
# These run **outside** the fence, in a second pass, and the report names
# them.  Quietly deselecting them would produce a green page that had not
# run them, which is the exact failure this file exists to prevent.
#
# Both reasons are properties of the fence working correctly, not gaps to
# close later.  Adding a file here needs a reason of that kind; "it fails
# inside" is not one on its own, because a test failing inside the fence
# is usually the fence catching something.
RUNS_UNFENCED = {
    # X11 has no isolation between clients: a sandboxed process holding
    # the socket can read every keystroke and pixel of the session, so
    # binding it would undo most of what the fence is for.  Found by
    # fencing the whole suite — five failures reading "the window never
    # said which argument it is on", all eight passing unfenced.
    "test/test_editor_abi.py": "needs a window; no X11 socket inside the fence",
    # A bwrap cannot nest, so every probe in here would fail for the
    # wrong reason.  The file skips itself on GESTATE_FENCED; this entry
    # is what makes it actually run somewhere.
    "test/test_safety.py": "checks the fence from outside; a fence cannot nest",
}


# pytest -q prints, at the end, a line like:
#   3 failed, 2008 passed, 41 skipped, 2 warnings in 251.03s
TOTALS = re.compile(
    r"^(?:=+\s*)?((?:\d+ (?:passed|failed|error|errors|skipped|xfailed|xpassed|deselected|warnings?)"
    r"(?:, )?)+)(?: in [\d.]+s)?",
    re.M,
)
# --tb=line renders each failure as: /path/to/file.py:LINE: message
FAILLINE = re.compile(r"^(/\S+?\.py):(\d+):\s*(.*)$", re.M)
FAILNAME = re.compile(r"^(?:FAILED|ERROR)\s+(\S+)(?:\s+-\s+(.*))?$", re.M)


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--unfenced", action="store_true")
    ap.add_argument("-h", "--help", action="store_true")
    args, passthrough = ap.parse_known_args()

    if args.help:
        print(__doc__)
        return 0

    pytest_cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:randomly",
                  "--tb=line", "-rfE", *passthrough]

    fenced = not args.unfenced
    fence_ok, fence_note = (None, "not asked")
    if fenced:
        fence_ok, fence_note = _fence_state()
        if not fence_ok:
            print("suite.py: the fence did not come up; refusing to claim it did.",
                  file=sys.stderr)
            print("          run tools/sandbox.sh --check, or pass --unfenced.",
                  file=sys.stderr)
            return 2
        # Held out of the fenced pass and run separately below.  Only the
        # ones that actually exist, so this list may name a file a future
        # project does not have.
        window_tests = [w for w in RUNS_UNFENCED if (ROOT / w).exists()]
        cmd = [str(ROOT / "tools" / "sandbox.sh"), *pytest_cmd,
               *[f"--ignore={w}" for w in window_tests]]
    else:
        window_tests = []
        cmd = pytest_cmd

    started = datetime.now()
    t0 = time.monotonic()

    # **Stream, do not capture-then-print.**  The first version used
    # `subprocess.run(..., stdout=PIPE)` and wrote the output at the end,
    # which meant a run that takes minutes produced zero bytes for
    # minutes — indistinguishable from a hang, and it cost a real
    # investigation to establish that a healthy run at 91% CPU was in
    # fact healthy.  `os.read` returns as soon as anything is available,
    # so pytest's progress dots arrive as they are printed rather than
    # waiting for a full line.
    def stream(argv):
        p = subprocess.Popen(argv, cwd=ROOT,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        buf = []
        while True:
            data = os.read(p.stdout.fileno(), 4096)
            if not data:
                break
            t = data.decode("utf-8", errors="replace")
            sys.stdout.write(t)
            sys.stdout.flush()
            buf.append(t)
        p.wait()
        return p.returncode, "".join(buf)

    rc, out = stream(cmd)
    passes = [out]

    # Second pass, unfenced, for the window tests the fence cannot host.
    window_note = "none"
    if fenced and window_tests:
        print(f"\n--- second pass, OUTSIDE the fence: {' '.join(window_tests)} ---")
        wrc, wout = stream([*pytest_cmd, *window_tests])
        out += "\n" + wout
        passes.append(wout)
        rc = rc or wrc
        window_note = "; ".join(f"{w} ({RUNS_UNFENCED[w]})" for w in window_tests)

    wall = time.monotonic() - t0

    # **Totals are summed across passes, not taken from the last one.**
    # The first version kept only the final match, so a two-pass run
    # reported the second pass alone — a green page for twenty-six tests
    # while two thousand went unmentioned.  Exactly the silently-partial
    # report this file exists to prevent, reintroduced by the fix for it.
    tally = {}
    for chunk in passes:
        last = None
        for m in TOTALS.finditer(chunk):
            last = m.group(1)
        if last:
            for n, word in re.findall(r"(\d+) (\w+)", last):
                tally[word] = tally.get(word, 0) + int(n)
    order = ["failed", "error", "errors", "passed", "skipped",
             "xfailed", "xpassed", "deselected", "warnings", "warning"]
    parts = [f"{tally[w]} {w}" for w in order if w in tally]
    parts += [f"{v} {k}" for k, v in tally.items() if k not in order]
    totals = ", ".join(parts) if parts else "(not parsed)"

    failures = []
    for name, why in FAILNAME.findall(out):
        failures.append((name, (why or "").strip()))
    if not failures:
        for path, line, msg in FAILLINE.findall(out):
            rel = Path(path).relative_to(ROOT) if str(path).startswith(str(ROOT)) else path
            failures.append((f"{rel}:{line}", msg.strip()))

    mins, secs = divmod(int(wall), 60)
    body = [
        "# test/report.md — the suite, as it last ran",
        "",
        "Generated by `tools/suite.py`.  **Not committed**, and `pytest.ini`",
        "says why: a golden test is bit-exact *where the buffer was made and",
        "nowhere else*, so this is a claim about one machine at one commit.",
        "Regenerate it rather than read an old one.",
        "",
        "| | |",
        "|---|---|",
        f"| Ran | {started:%Y-%m-%d %H:%M:%S} |",
        f"| Commit | `{_commit()}` |",
        f"| Tree | {_tree()} |",
        f"| Fence | {'`tools/sandbox.sh` — ' + fence_note if fenced else '**unfenced** (--unfenced)'} |",
        f"| Command | `{' '.join(pytest_cmd[1:])}` |",
        f"| Ran outside the fence | {window_note} |",
        f"| Wall | {mins}m {secs}s |",
        f"| Exit | {rc} |",
        "",
        "## Totals",
        "",
        f"**{totals}**",
        "",
    ]

    if failures:
        body += [f"## The {len(failures)} that did not pass", ""]
        for name, why in failures:
            body.append(f"* `{name}`")
            if why:
                body.append(f"  * {why}")
        body += ["", "Full output is above in the terminal; this page keeps the names."]
    else:
        body += ["## Failures", "", "None.", ""]

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(body) + "\n")
    print(f"\nsuite.py: drawn to {REPORT.relative_to(ROOT)}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
