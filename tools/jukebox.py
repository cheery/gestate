#: asked-by: a session, 2026-08-15 — "nothing else here listens to the library"; the commit body is the whole record
"""Play every example, ten seconds each, and say what is playing.

    python tools/jukebox.py                    # the whole tree
    python tools/jukebox.py examples/audio     # one shelf of it
    python tools/jukebox.py --seconds 4        # a faster pass

**What it is for.**  Nothing else here listens to the *library*.  The
goldens hold a handful of files to the sample, `--report` hears a mix's
peak and RMS, and `test_playedsound.py` hears which note came out — but
a change to `synth.ges` touches forty-six pieces and no test plays them.
Ten seconds each is twelve minutes for the tree, which is a coffee, and
it is the only way to notice that something *sounds* wrong rather than
merely different from a recording.

**A track that refuses does not stop the record.**  A file with no
`sound` is skipped by name, a file that will not compile says its first
line and the next one starts.  A jukebox that halted on a bad track
would be a test runner, and there is one of those already.

Each track is its own process, which is not tidiness: the sound card is
held by whoever is playing, and `journal.md`'s two-stop teardown is
about exactly the crash that follows from getting that wrong.  A dead
subprocess cannot hold a device.

**Ctrl-C skips**; twice within a second quits.  That is the control a
jukebox has, and the reason the loop reads the clock rather than
counting interrupts.
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
import time
from gestate.notes import read

ROOT = pathlib.Path(__file__).resolve().parents[1]


def playable(path: pathlib.Path) -> str | None:
    """Why this file is not a track, or `None` when it is one.

    Asked of the *text*, with the compiler's own question — a canvas or
    a Datafun example is not a broken synth, and saying "no `sound`" is
    the difference between a shelf and a fault report.
    """
    sys.path.insert(0, str(ROOT))
    from gestate.audio import has_sound

    try:
        source = read(path)
    except OSError as exc:                              # noqa: BLE001
        return f"unreadable ({exc.strerror})"
    if not has_sound(source):
        return "no `sound` — not an instrument"
    return None


def tracks(where: list) -> list:
    """Every `.ges` under the given roots, in reading order."""
    found: list = []
    for one in where:
        here = pathlib.Path(one)
        if not here.is_absolute():
            here = ROOT / here
        if here.is_file():
            found.append(here)
        else:
            found += sorted(here.rglob("*.ges"))
    return found


def play(path: pathlib.Path, seconds: float, rate: int | None) -> str:
    """One track, in its own process.  Answers what to print after it."""
    argv = [sys.executable, "-m", "gestate.audioperform", str(path),
            "--seconds", str(seconds)]
    if rate is not None:
        argv += ["--rate", str(rate)]
    try:
        done = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                              timeout=seconds + 120)
    except subprocess.TimeoutExpired:
        return "gave up waiting — it never reached the sound card"
    if done.returncode == 0:
        return ""
    said = (done.stderr or done.stdout or "").strip().splitlines()
    return said[0] if said else f"refused (exit {done.returncode})"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("where", nargs="*", default=["examples"],
                    help="files or directories (default: examples)")
    ap.add_argument("--seconds", type=float, default=10.0,
                    help="how long each track gets (default: 10)")
    ap.add_argument("--rate", type=int, default=None,
                    help="sample rate, when a slow machine wants one")
    args = ap.parse_args(argv)

    listing = tracks(args.where or ["examples"])
    if not listing:
        print("nothing to play", file=sys.stderr)
        return 1

    width = max(len(str(p.relative_to(ROOT))) for p in listing)
    played = skipped = refused = 0
    last_interrupt = 0.0
    began = time.monotonic()

    for n, path in enumerate(listing, start=1):
        name = str(path.relative_to(ROOT))
        why = playable(path)
        if why is not None:
            print(f"[{n:3d}/{len(listing)}] {name:<{width}}  — {why}",
                  flush=True)
            skipped += 1
            continue
        # Said *before* it plays, and flushed: the whole point is
        # knowing what you are hearing while you hear it.
        print(f"[{n:3d}/{len(listing)}] {name:<{width}}", end="", flush=True)
        started = time.monotonic()
        try:
            said = play(path, args.seconds, args.rate)
        except KeyboardInterrupt:
            now = time.monotonic()
            print("  — skipped", flush=True)
            if now - last_interrupt < 1.0:
                print("\nstopped.", flush=True)
                return 0
            last_interrupt = now
            continue
        took = time.monotonic() - started
        if said:
            print(f"\n{'':>{width + 11}}refused: {said}", flush=True)
            refused += 1
        else:
            # Silence on success: the name is already on the line and a
            # duration beside a fixed budget reads as the *sound's*
            # length, which it is not — it is the build plus the sound.
            # Said only when the build was long enough to be the reason
            # you are still waiting.
            slow = took - args.seconds
            print(f"  — {took:.0f}s ({slow:.0f}s of it building)" if slow > 3
                  else "", flush=True)
            played += 1

    took = time.monotonic() - began
    how_long = (f"{took / 60:.0f} minutes" if took >= 90
                else f"{took:.0f} seconds")
    print(f"\n{played} played, {skipped} not instruments, {refused} refused "
          f"— {how_long}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nstopped.")
