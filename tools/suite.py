#: asked-by: Henri, 2026-08-16 — "Let give the test a place where it can draw itself."
"""Run the suite and let it draw itself.

    python tools/suite.py                 # fenced, the whole suite
    python tools/suite.py --gates         # the seventeen-second checks, and stop
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

**`--gates` is for the commit, not for the shift.** The set below runs
in seconds and is exactly what a working session breaks, so it is worth
running per commit rather than per shift — `card:cheap-gates.md` is the
day that argument was paid for, when the only full run of a shift died
at a gate in seventeen seconds on a breakage hours old. It draws
`test/gates.md`, a **different file** from `test/report.md`, because a
gate page and a suite page competing for one filename is how somebody
reads the tree as good on the strength of eight document checks.

**It records the fence.** `tools/sandbox.sh` is where builds and tests
belong (`spec/sandbox.md`), and a report that did not say which side of
the fence it ran on would leave the reader to guess.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "test" / "report.md"
#: **A second page, deliberately.**  A `--gates` run and a full run
#: writing one file is this board's two-writers rule in miniature: the
#: last writer wins and the reader cannot tell which ran.
GATES_PAGE = ROOT / "test" / "gates.md"

#: **The gates: seconds-long checks that a working session breaks.**
#:
#: Henri's ask, 2026-08-17: *"Put the obviously easy to fail tests first,
#: so that we catch early up."*  The occasion was three failures in one
#: day, each of them a structural check costing under five seconds and
#: each of them sitting behind twenty minutes of audio renders — the
#: atlas four minutes in, the gui roster thirteen, the citation check
#: after the full twenty-five.  Every one was a session doing ordinary
#: work: renaming a card, adding an example, changing a struct.
#:
#: These run **first and alone**, and a failure stops the run there.
#: Nothing here tests behaviour; they test that the tree still agrees
#: with itself, which is exactly the property editing the tree breaks.
#:
#: **The rule for what belongs here is the defect class, not the file.**
#: `doc/ref/` joined on 2026-08-17 for exactly that reason: it is a
#: *generated file behind its source*, the same class as the atlas, and
#: the two sat at different depths for no reason anybody had chosen —
#: the sheet failed six seconds in and the reference page twenty-four
#: minutes in, on the same evening, from the same edit to
#: `command.ges`.  The second cost a whole re-run.  The check itself is
#: a directory comparison and takes 0.17 s.
#:
#: **`test_carry.py` joined on 2026-08-19**, and it is the first entry
#: here that is about code rather than about documents — which is right,
#: because the rule is the defect class.  A `Session` field added
#: without a matching line in `workbench._carry` is a list falling
#: behind its source, exactly like the atlas behind its modules; it
#: costs 0.19 s to check and it crashed the editor in Henri's hands
#: twice in one day before anything checked it (`card:carried-state.md`).
#:
#: They are not re-listed for the long pass — it runs them again as part
#: of its own collection, which is where their five seconds are counted.
GATES = {
    "test/test_board.py":
        "the board's own contract, which a session edits every card",
    "test/test_citations.py":
        "every §\"…\" and card citation in the tree",
    "test/test_consent.py":
        "nobody quoted into this public tree who was not asked",
    "test/test_atlas.py":
        "the generated sheets against the source they describe",
    "test/test_reference.py::test_doc_ref_is_not_behind_the_libraries":
        "doc/ref/ against the libraries it is derived from",
    "test/test_complaints.py":
        "every complaint's verdict, and doc/complaints.md against it",
    "test/test_audio.py::test_every_audio_example_is_exercised_here":
        "the audio example roster",
    "test/test_gui.py::test_every_gui_example_is_exercised_here":
        "the gui example roster",
    "test/test_carry.py::test_every_field_is_carried_or_deliberately_fresh":
        "every Session field, carried across a switch or knowingly not",
    "test/test_memory.py":
        "doc/memory/, and that nothing about the person is published there",
    "test/test_rules.py":
        "the five method documents are all there, and the cap's lamp works",
    "test/test_journal.py":
        "the journal's archive, and the index that is the only way into it",
    "test/test_seedaudit.py":
        "the ten people-pieces, each present, each behind its declared gate",
    "test/test_memoryindex.py":
        "the boot index's public half against doc/memory/README.md it is generated from",
    #: **Joined 2026-08-25**, and it is the second entry here about code
    #: rather than documents — same reasoning as `test_carry.py`: the rule
    #: is the defect class.  A `pgrep -f` that matches its own command
    #: line is a check that waits for itself, and this tree paid for it
    #: once already — twelve polling shells on the machine being listened
    #: on, and the crackle they caused diagnosed as hardware first
    #: (2026-08-18).  It costs 0.8 s, it has no bearing on behaviour, and
    #: a session writing a wait loop is exactly the ordinary work that
    #: breaks it.  The gate itself came back from `~/tend`, which built it
    #: from this tree's own post-mortem.
    "test/test_selfmatch.py":
        "no pattern kill in the tree matches its own command line",
    #: **Joined 2026-08-25**, both of them found by the long pass being red
    #: for a day with nobody told: `tools/slides.py` landed on 08-24 with
    #: no `asked-by:` stamp, and `test_precommit.py` went red in the same
    #: commit that taught the hook to say `"$PY"` instead of `python3`.
    #: Two sub-second structural checks that reported twenty-five minutes
    #: late, which is `card:cheap-gates.md`'s argument arriving a second
    #: time.  Henri, 2026-08-25: *"they join the GATES."*
    #:
    #: **The two node ids rather than the file** — `test_provenance.py`
    #: costs 4.2 s, and 3.8 of those are `test_the_graph_is_a_command_and_a_picture`
    #: and `test_the_svg_is_laid_out_by_dot`, which render a picture with
    #: `dot`.  Those are not of this class: they are slow, and a session
    #: doing ordinary work does not break them.  The stamp check and the
    #: register command are 0.12 s together.
    "test/test_provenance.py::test_every_tool_says_who_asked_for_it":
        "every tool in tools/ says who asked for it",
    "test/test_provenance.py::test_the_register_is_a_command_somebody_can_run":
        "the who-asked register, against the tools it registers",
    "test/test_precommit.py":
        "the hook is installed here, parses, and runs the gates and nothing else",
}


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
# -rw renders, between these two lines, one unindented header per test
# (or per file, when pytest folds a file's repeats) and the warning
# under it indented by two, the offending line by four:
#   ===== warnings summary =====
#   test/test_x.py::test_y
#     /path/to/file.py:12: DeprecationWarning: message
#       the line
#   -- Docs: https://docs.pytest.org/...
WARNBLOCK = re.compile(r"^=+ warnings summary.*?=+\n(.*?)^-- Docs:", re.M | re.S)
# --tb=line renders each failure as: /path/to/file.py:LINE: message
FAILLINE = re.compile(r"^(/\S+?\.py):(\d+):\s*(.*)$", re.M)
FAILNAME = re.compile(r"^(?:FAILED|ERROR)\s+(\S+)(?:\s+-\s+(.*))?$", re.M)


def _rust(stream, fenced, root):
    """The Rust workspace — four crates, eighteen binaries, 344 tests.

    **Nothing ran these until 2026-08-18.**  It was found by asking why
    `view.rs`'s own tests had gone red on one commit and stayed red for
    a whole session: nothing runs them, so green was luck rather than
    evidence.  They cost **under a second** warm.

    Between the gates and the long pass, because that is what its speed
    buys: a broken crate is known in the first minute rather than the
    twenty-fifth.  Inside the fence, which is what `tools/sandbox.sh`
    was written for in the first place — `cargo` runs build scripts and
    proc-macros as arbitrary code.
    """
    if shutil.which("cargo") is None:
        # A machine with no cargo still has a Python suite worth
        # running, and says so rather than failing.  The posture
        # `doc/install.md` takes with every backend: missing ones
        # degrade politely.
        print("\nsuite.py: no cargo; the Rust crates went unchecked.")
        return 0, "", "skipped — no cargo on PATH"
    print("\n--- the Rust workspace, before the long pass ---")
    cmd = ["cargo", "test", "--workspace", "--quiet"]
    if fenced:
        cmd = [str(root / "tools" / "sandbox.sh"), *cmd]
    rc, out = stream(cmd)
    ran = sum(int(n) for n in
              re.findall(r"^test result: ok\. (\d+) passed", out, re.M))
    if rc:
        # **Not a stop.**  A red crate must not erase the page that says
        # what else is true — the Python pass is twenty-five minutes of
        # evidence and it is still worth having.
        return rc, out, "**failed**"
    return 0, out, f"{ran} passed"


def _tally(chunks):
    """pytest's totals, summed across passes rather than taken from one.

    **The bug this is shaped by.**  The first version kept only the
    final match, so a two-pass run reported the second pass alone — a
    green page for twenty-six tests while two thousand went unmentioned.
    Exactly the silently-partial report this file exists to prevent,
    reintroduced by the fix for it.
    """
    tally = {}
    for chunk in chunks:
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
    return ", ".join(parts) if parts else "(not parsed)"


def _failures(out):
    """Every failure named, by test id where pytest gave one."""
    failures = [(name, (why or "").strip()) for name, why in FAILNAME.findall(out)]
    if not failures:
        for path, line, msg in FAILLINE.findall(out):
            rel = (Path(path).relative_to(ROOT)
                   if str(path).startswith(str(ROOT)) else path)
            failures.append((f"{rel}:{line}", msg.strip()))
    return failures


def _warnings(out):
    """Every warning named, by the test that raised it and the sentence.

    **The page counted them and named none** — 2026-08-26, Henri: *"I
    ran full suite today and it had one warning, able to check that
    one?"* — and the only way to answer was to run the twenty-three
    minutes again, because `-rfE` asks pytest for failures and errors
    and the count in the totals line was all that survived.  A number
    nobody can check is a number nobody checks (`doc/instruments.md`).
    """
    found = []
    for block in WARNBLOCK.findall(out):
        head = None
        for line in block.splitlines():
            if not line.strip():
                continue
            if not line.startswith(" "):
                head = line.strip()
                found.append((head, []))
            elif not line.startswith("    ") and found:
                text = line.strip()
                if str(ROOT) in text:
                    text = text.replace(str(ROOT) + "/", "")
                found[-1][1].append(text)
    return found


def _warning_section(warnings):
    if not warnings:
        return ["## Warnings", "", "None.", ""]
    body = [f"## The {len(warnings)} warning{'s' if len(warnings) > 1 else ''}", ""]
    for head, lines in warnings:
        body.append(f"* `{head}`")
        for text in lines:
            body.append(f"  * {text}")
    return body + [""]


def _failure_section(failures):
    if not failures:
        return ["## Failures", "", "None.", ""]
    body = [f"## The {len(failures)} that did not pass", ""]
    for name, why in failures:
        body.append(f"* `{name}`")
        if why:
            body.append(f"  * {why}")
    return body + ["", "Full output is above in the terminal; this page keeps the names."]


def _rules_total():
    """The five method documents, and their cap — `spec/rules.md`."""
    import rulecount
    rows = rulecount.counts()
    return sum(n for _, n in rows if n >= 0), rulecount.CAP


def _rules_row():
    total, cap = _rules_total()
    if total > cap:
        return f"**{total:,} of {cap:,} — over by {total - cap:,}**"
    return f"{total:,} of {cap:,}, {cap - total:,} to spare"


def _rules_andon():
    """**Andon, not refusal** — Henri, 2026-08-20: *"make it light the
    andon."*

    The rules set has a size and the size is charged to every shift, so
    growth has to be *seen*.  It must not be *blocked*: a genuine
    amendment to the method is exactly the kind of change that arrives
    with a good reason and no room, and a gate that refuses it teaches
    the next session to make the method worse in smaller words.

    So this is a lamp.  It is lit where somebody is already standing —
    the commit, by way of `tools/pre-commit.sh` — and it never changes
    the exit code.  What the suite still refuses is the loss of one of
    the five, which is not growth but the cap being abandoned;
    `test/test_rules.py` holds that half.
    """
    total, cap = _rules_total()
    if total <= cap:
        return []
    return [
        "",
        "## 🔴 The rules are over their cap",
        "",
        f"**{total:,} lines against {cap:,}** — over by {total - cap:,}.",
        "",
        "This does not fail anything.  It is the andon: the method grew,",
        "and growth is a visible event rather than a forbidden one.",
        "",
        "The fat is session narration, and the honest destinations are",
        "`journal.md`, `doc/memory/`, or deletion — not the dates, not a",
        "sixth document, and not moving text from one rule into another.",
        "`spec/rules.md` names all three as cheats.  `python",
        "tools/rulecount.py` says where the lines are.",
        "",
        "If the growth is right and the cap is wrong, the cap moves —",
        "by Henri, in writing, with the date.",
    ]


def _journal_total():
    """The open journal, and its budget — `spec/rules.md` §"The journal
    rotates"."""
    import journalroll
    return journalroll.lines_now(), journalroll.BUDGET


def _journal_row():
    total, budget = _journal_total()
    import journalroll
    if journalroll.due():
        return f"**{total:,} of {budget:,} — rotation due**"
    return f"{total:,} of {budget:,}, {budget - total:,} to spare"


def _journal_andon():
    """**Andon, not refusal, and its meaning is *rotate*** — Henri,
    2026-08-21: the lamp says *"rotation is due," not "stop writing."*

    The journal is the one document in this tree that is supposed to
    grow without limit, so nothing may ever fail for its size.  What has
    a limit is how much of it a session pays for on every `grep`, and
    the fix for that is not writing less — it is moving the closed
    months out to `journal/` where nobody reads them by accident.

    So the lamp is lit where somebody is already standing, the same
    place as the cap's: `test/gates.md` and every commit through the
    hook.  It never changes the exit code.  `test/test_journal.py` holds
    the half that *is* refused, which is the index having fallen behind
    the archive.
    """
    import journalroll
    reasons = journalroll.due()
    if not reasons:
        return []
    total, budget = _journal_total()
    return [
        "",
        "## 🔴 The journal's rotation is due",
        "",
        *(f"* {r}." for r in reasons),
        "",
        "This does not fail anything, and it does not mean write less —",
        f"{total:,} lines of past tense is the project working.  It means the",
        "closed months should be out of the file every session greps, in",
        "`journal/`, behind one index line each.",
        "",
        "The act is the fire's, not the gate's: skim the closing month once,",
        "promote the two or three lines that pass the earning test up into the",
        "method files, write the index line, close the file.  Nothing is",
        "rewritten — git already remembers, and a journal that is retroactively",
        "edited becomes a second source of truth about the past.",
        "",
        "    python tools/journalroll.py --roll --themes \"…\"",
        "",
        "`spec/rules.md` §\"The journal rotates\" is the contract; `python",
        "tools/journalroll.py` says where the lines are.",
    ]


def _arrivals_row():
    """The number *question it into existence* is measured by —
    `tools/arrivals.py`.  A row, never a refusal: the rule is critical
    *if it works*, Henri 2026-08-18, and this is where it shows."""
    import arrivals
    return f"{arrivals.week()} in the last seven days"


def _draw_gates(rc, out, started, wall, fence_row, gates):
    """`test/gates.md` — and it says what it is not.

    **The whole risk of a cheap check is that it reads like an
    expensive one.**  A green page headed by eight passing document
    checks is a true page and an untrue impression, so the title, the
    first paragraph and the totals line each say that the suite did not
    run.  Three times, on purpose: a reader skimming for the bold number
    at the bottom must not be able to miss it.
    """
    body = [
        "# test/gates.md — the gates, and nothing else",
        "",
        "Generated by `tools/suite.py --gates`.  **This is not a suite run",
        "and says nothing about whether gestate works.**  These are the",
        "seconds-long structural checks that a working session breaks — that",
        "the tree still agrees with itself, not that any of it behaves.",
        "`test/report.md` is the page that answers the other question; this",
        "run deliberately does not touch it.",
        "",
        "| | |",
        "|---|---|",
        f"| Ran | {started:%Y-%m-%d %H:%M:%S} |",
        f"| Commit | `{_commit()}` |",
        f"| Tree | {_tree()} |",
        f"| Fence | {fence_row} |",
        f"| Gates | {len(gates)} of them |",
        f"| Rules | {_rules_row()} |",
        f"| Journal | {_journal_row()} |",
        f"| Cards minted | {_arrivals_row()} |",
        f"| Wall | {int(wall)}s |",
        f"| Exit | {rc} |",
        "",
        "## Totals",
        "",
        f"**{_tally([out])}** — *the gates alone; the suite did not run.*",
        "",
        *_failure_section(_failures(out)),
        *_rules_andon(),
        *_journal_andon(),
    ]
    GATES_PAGE.parent.mkdir(parents=True, exist_ok=True)
    GATES_PAGE.write_text("\n".join(body) + "\n")
    print(f"\nsuite.py: the gates only — drawn to {GATES_PAGE.relative_to(ROOT)}")
    for line in _rules_andon() + _journal_andon():
        print(line)
    return rc


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--unfenced", action="store_true")
    ap.add_argument("--gates", action="store_true")
    ap.add_argument("-h", "--help", action="store_true")
    args, passthrough = ap.parse_known_args()

    if args.help:
        print(__doc__)
        return 0

    pytest_cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:randomly",
                  "--tb=line", "-rfEw", *passthrough]

    # **The word that unlocks a whole-suite run** — `test/conftest.py`
    # refuses one that did not come through here, because a full run that
    # leaves no report behind is the silently-partial page this file
    # exists to prevent.  Set in the environment rather than passed as an
    # argument so it survives the hop through `sandbox.sh` into the
    # fence, which keeps the environment it is given.
    os.environ["GESTATE_SUITE"] = "1"

    fenced = not args.unfenced
    fence_ok, fence_note = (None, "not asked")
    window_tests = []
    cmd = pytest_cmd
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
    fence_row = ("`tools/sandbox.sh` — " + fence_note if fenced
                 else "**unfenced** (--unfenced)")

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

    # **The gates first.**  A structural check that fails is nearly always
    # a session having edited the tree, and finding that out in eight
    # seconds rather than in thirteen minutes is the whole of this.  A
    # failure stops the run: the long pass would be testing a tree
    # somebody is about to change anyway.
    gates = [g for g in GATES if (ROOT / g.split("::")[0]).exists()]
    print(f"--- the gates ({len(gates)}), "
          + ("and nothing else ---" if args.gates else "before anything slow ---"))
    gate_cmd = ([str(ROOT / "tools" / "sandbox.sh"), *pytest_cmd, *gates]
                if fenced else [*pytest_cmd, *gates])
    grc, out = stream(gate_cmd)

    # **The whole of `--gates`.**  Everything above it is shared with a
    # full run — the same fence proof, the same eight paths, the same
    # streaming — which is the point: a mode that ran a hand-copied list
    # would drift from the real one the day the list grew, and that
    # drift is what `card:cheap-gates.md` records a session doing by
    # hand, from memory, on the days it could not spare twenty-five
    # minutes.
    if args.gates:
        return _draw_gates(grc, out, started, time.monotonic() - t0,
                           fence_row, gates)

    stopped = ""
    if grc:
        # **Counted here, because nothing else ran.**  On the happy path
        # the gates are left out of `passes` — the long pass collects
        # them again and would count them twice.
        passes = [out]
        rc = grc
        stopped = ("a gate failed, so the long pass never started; "
                   "fix it and run again")
        print("\nsuite.py: " + stopped)
        window_note = "none — stopped at the gates"
        rust_note = "not run — stopped at the gates"
        window_tests = []
    else:
        rrc, rout, rust_note = _rust(stream, fenced, ROOT)
        out += "\n" + rout
        rc, main_out = stream(cmd)
        out += "\n" + main_out
        passes = [main_out]
        rc = rc or rrc

    # Second pass, unfenced, for the window tests the fence cannot host.
    if not stopped:
        window_note = "none"
    if not stopped and fenced and window_tests:
        print(f"\n--- second pass, OUTSIDE the fence: {' '.join(window_tests)} ---")
        wrc, wout = stream([*pytest_cmd, *window_tests])
        out += "\n" + wout
        passes.append(wout)
        rc = rc or wrc
        window_note = "; ".join(f"{w} ({RUNS_UNFENCED[w]})" for w in window_tests)

    wall = time.monotonic() - t0

    totals = _tally(passes)
    failures = _failures(out)

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
        f"| Fence | {fence_row} |",
        f"| Command | `{' '.join(pytest_cmd[1:])}` |",
        f"| Ran outside the fence | {window_note} |",
        f"| Rust workspace | {rust_note} |",
        f"| Wall | {mins}m {secs}s |",
        f"| Exit | {rc} |",
        *([f"| Stopped | {stopped} |"] if stopped else []),
        "",
        "## Totals",
        "",
        f"**{totals}**" + (
            "  — *the gates alone; the suite never started.*" if stopped else ""),
        "",
    ]

    body += _failure_section(failures)
    body += _warning_section(_warnings(out))

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(body) + "\n")
    print(f"\nsuite.py: drawn to {REPORT.relative_to(ROOT)}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
