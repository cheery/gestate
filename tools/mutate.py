#!/usr/bin/env python3
#: asked-by: Henri, 2026-09-02 - after a killed batch-11 harness left a defect in `gestate/reactive.py`: "card worthy issue, or even a defect"
"""tools/mutate.py — put a defect back, run a command, restore whatever happens.

    python tools/mutate.py batch.json -- python -m pytest -q test/test_frp.py
    python tools/mutate.py batch.json --only F21a -- pytest -q test/
    python tools/mutate.py --check          is the tree clean right now?

**The instrument `card:ungated-fixes.md` has needed since batch 1 and
every batch session rebuilt by hand.**  The sweep's method is mutation —
put the repair's defect back, run the tests, read whether anything goes
red — and its one hazard is that the tree is left holding a deliberate
bug.  Nine batches restored inside a `finally`, which covers an
exception and **does not cover a signal**: on 2026-09-02 a batch-11
harness was killed mid-run and left `ticked`'s `_deref` deleted in the
working tree, where the next `git commit -a` would have taken it.

So this module's whole promise is the restore, and it is made four ways:

* the original bytes are read into memory before anything is written,
  and written back in a ``finally``;
* ``SIGINT`` and ``SIGTERM`` are handled and re-raised after restoring,
  so a `kill` restores rather than abandoning;
* ``atexit`` restores as well, for the paths neither of those catches;
* and the restore is **verified by hash**, not assumed — a file that
  does not come back byte-for-byte is a loud failure, because a quiet
  one is the whole problem.

It also refuses to start when a target file is already modified: the
sweep's rule is `git status` clean before and after every mutation
(§"Live tree or a copy"), and a harness that mutates an edited file
cannot restore it to anything meaningful.

**The spec is JSON**, one object per mutation, so a batch is a file that
can be committed beside its verdicts rather than a script that is
rewritten each time:

    [
      {"id": "F21a",
       "what": "ticked stops dereferencing the operands it inspects",
       "edits": [["gestate/reactive.py",
                  "chan_node = _deref(node.args[0])",
                  "chan_node = node.args[0]", 1]]}
    ]

Each edit is ``[path, old, new, count]`` and ``count`` is a claim: the
run refuses the mutation when ``old`` does not appear exactly that many
times, because an anchor that silently missed is a mutation that was
never applied and a green that means nothing.

Exit status is 0 when every mutation ran and the tree came back, 1 when
a mutation could not be applied, and 2 when a restore failed — which is
the one a caller must never ignore.
"""
from __future__ import annotations

import argparse
import atexit
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: complaint  world — a spec that names a file the tree does not have, or an
#: anchor that is not in it: nothing has been mutated when this is raised.


class MutateError(Exception):
    """The run refusing, with the reason."""


class Tree:
    """The files a batch touches, and their bytes as they were found."""

    def __init__(self, paths):
        self.original = {}
        for p in paths:
            path = (ROOT / p).resolve()
            if not path.is_file():
                raise MutateError(f"no such file: {p}")
            self.original[path] = path.read_bytes()
        self.digests = {p: hashlib.sha256(b).hexdigest()
                        for p, b in self.original.items()}
        self._armed = False

    def arm(self):
        """Restore on a signal, on an exception, and at exit — all three."""
        if self._armed:
            return
        self._armed = True
        atexit.register(self.restore)
        for sig in (signal.SIGINT, signal.SIGTERM):
            previous = signal.getsignal(sig)

            def handler(signum, frame, _previous=previous):
                self.restore()
                signal.signal(signum, _previous)
                os.kill(os.getpid(), signum)

            signal.signal(sig, handler)

    def apply(self, edits):
        """Write one mutation.  Returns None, or the reason it was refused.

        Nothing is written until every anchor has been checked, so a
        refusal leaves the tree exactly as it was.
        """
        staged = dict(self.original)
        for path, old, new, count in edits:
            p = (ROOT / path).resolve()
            if p not in staged:
                return f"{path} is not in this spec's file list"
            text = staged[p].decode()
            seen = text.count(old)
            if seen != count:
                return (f"anchor missed in {path}: expected {count} of "
                        f"{old[:60]!r}, found {seen}")
            staged[p] = text.replace(old, new).encode()
        for p, data in staged.items():
            if data != self.original[p]:
                p.write_bytes(data)
        return None

    def restore(self):
        """Put every file back, and check that it went back."""
        bad = []
        for p, data in self.original.items():
            try:
                if p.read_bytes() != data:
                    p.write_bytes(data)
                if hashlib.sha256(p.read_bytes()).hexdigest() != self.digests[p]:
                    bad.append(p)
            except OSError as e:
                bad.append(f"{p}: {e}")
        if bad:
            print(f"mutate: RESTORE FAILED for {bad} — the tree is holding a "
                  f"deliberate defect, do not commit", file=sys.stderr,
                  flush=True)
            return False
        return True


def dirty(paths) -> list:
    """Which of `paths` git already sees as modified."""
    out = subprocess.run(["git", "status", "--porcelain", "--", *paths],
                         cwd=ROOT, capture_output=True, text=True)
    return [line[3:] for line in out.stdout.splitlines() if line[:2] != "??"]


def run(spec, command, only=None) -> int:
    paths = sorted({e[0] for m in spec for e in m["edits"]})
    already = dirty(paths)
    if already:
        raise MutateError(
            "these files are already modified, so a restore could not put "
            f"them back: {', '.join(already)}.  Commit or stash first — the "
            "sweep's rule is a clean tree before and after every mutation")
    tree = Tree(paths)
    tree.arm()
    failed = 0
    for m in spec:
        if only and m["id"] not in only:
            continue
        why = tree.apply(m["edits"])
        if why is not None:
            print(f"{m['id']:10s} REFUSED — {why}", flush=True)
            failed += 1
            continue
        start = time.time()
        try:
            r = subprocess.run(command, cwd=ROOT, capture_output=True,
                               text=True)
        finally:
            if not tree.restore():
                return 2
        last = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "(no output)"
        names = [l.split("::")[-1].split(" ")[0]
                 for l in r.stdout.splitlines() if l.startswith("FAILED")]
        print(f"{m['id']:10s} {time.time() - start:6.1f}s  {last}"
              f"   <- {m.get('what', '')}", flush=True)
        for n in names[:12]:
            print(f"    - {n}", flush=True)
        if len(names) > 12:
            print(f"    … and {len(names) - 12} more", flush=True)
    if not tree.restore():
        return 2
    print("mutate: every file restored and verified", flush=True)
    return 1 if failed else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("spec", nargs="?", help="JSON file of mutations")
    ap.add_argument("--only", action="append",
                    help="run only this id; repeatable")
    ap.add_argument("--check", action="store_true",
                    help="report whether the working tree is clean and exit")
    ap.add_argument("command", nargs="*",
                    help="after --, the command to run per mutation")

    # The command is split off *before* argparse sees it, because argparse
    # cannot hold an option after a positional whose `nargs` is open —
    # `mutate.py spec.json --only F8a -- pytest …`, the form this file's
    # own docstring gives, was rejected as "unrecognized arguments" the
    # first time a batch used it (`fixme.md` F196).  Everything after the
    # first bare `--` is the command, verbatim, whatever its shape.
    argv = list(sys.argv[1:] if argv is None else argv)
    command: list[str] = []
    if "--" in argv:
        cut = argv.index("--")
        argv, command = argv[:cut], argv[cut + 1:]
    args = ap.parse_args(argv)
    args.command = command

    if args.check:
        out = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                             capture_output=True, text=True).stdout.strip()
        if not out:
            print("mutate: the tree is clean")
            return 0
        print("mutate: the tree is NOT clean —\n" + out)
        return 1

    if not args.spec or not args.command:
        ap.error("give a spec and, after --, the command to run")
    try:
        spec = json.loads(Path(args.spec).read_text())
        return run(spec, args.command, set(args.only) if args.only else None)
    except MutateError as e:
        print(f"mutate: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
