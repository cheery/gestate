"""Replay a `GESTATE_TRACE` recording against the plugin, with no DAW.

    GESTATE_TRACE=/tmp/nd.trace reaper          # record, then quit Reaper
    python test/replay_trace.py /tmp/nd.trace ~/.clap/nightdrive.clap

`spec/verification.md`'s session transcript, closing its loop.  The
plugin writes one row per `process` — what the host handed it, what the
piece made of it, how long it took — and this drives the same code with
exactly those blocks.  A fault that only happens in a DAW becomes a
fault that happens in a test.

Two things it reports, and they answer different questions:

* **What the host did** — where the transport jumped, when it stopped,
  how the block size moved.  This is the part every harness in this
  project has guessed at and got wrong.
* **What it cost, then and now** — the recorded microseconds beside the
  replayed ones.  A block that was slow in Reaper and is fast here says
  the fault is scheduling, not the code; slow in both says the opposite.
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import POINTER, c_float, c_void_p
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_export as T  # noqa: E402

FIELDS = ("steady", "frames", "has_transport", "flags", "tempo", "pos",
          "events", "notes", "engine_t", "descending", "wanted", "pending",
          "played", "dropped", "micros")


def load(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("gestate-trace"):
            continue
        parts = line.split()
        # Traces recorded before the played/dropped counters existed are
        # two columns short; read them, and report zero for what they
        # could not know.
        if len(parts) == len(FIELDS) - 2:
            parts = parts[:-1] + ["0", "0"] + parts[-1:]
        if len(parts) != len(FIELDS):
            continue
        row = {}
        for name, raw in zip(FIELDS, parts):
            row[name] = float(raw) if name == "tempo" else int(raw)
        rows.append(row)
    return rows


def channels_of(plug_raw, plugin) -> int:
    """Ask the plugin, rather than assuming — the mistake that cost this
    project a whole afternoon of false measurements."""
    class Info(ctypes.Structure):
        _fields_ = [("id", ctypes.c_uint32), ("name", ctypes.c_char * 256),
                    ("flags", ctypes.c_uint32),
                    ("channel_count", ctypes.c_uint32),
                    ("port_type", ctypes.c_char_p),
                    ("in_place_pair", ctypes.c_uint32)]

    class Ports(ctypes.Structure):
        _fields_ = [("count", ctypes.CFUNCTYPE(ctypes.c_uint32, c_void_p,
                                               ctypes.c_bool)),
                    ("get", ctypes.CFUNCTYPE(ctypes.c_bool, c_void_p,
                                             ctypes.c_uint32, ctypes.c_bool,
                                             POINTER(Info)))]

    raw = plugin.get_extension(plug_raw, b"clap.audio-ports")
    if not raw:
        return 1
    ports = ctypes.cast(raw, POINTER(Ports)).contents
    info = Info()
    if ports.get(plug_raw, 0, False, ctypes.byref(info)):
        return max(1, info.channel_count)
    return 1


def replay(trace: Path, clap: Path, rate: float = 48000.0) -> None:
    import math
    import time

    rows = load(trace)
    if not rows:
        print(f"{trace}: no rows")
        return
    frames = max(r["frames"] for r in rows)

    lib, raw, plugin = T._plugin_of(clap)
    assert plugin.init(raw), "init"
    nch = channels_of(raw, plugin)
    assert plugin.activate(raw, rate, 1, frames), "activate"
    assert plugin.start_processing(raw)

    bufs = [(c_float * frames)() for _ in range(nch)]
    arr = (POINTER(c_float) * nch)(
        *[ctypes.cast(b, POINTER(c_float)) for b in bufs])
    port = T.AudioBuffer(data32=arr, data64=None, channel_count=nch,
                         latency=0, constant_mask=0)

    # **Reset where the host reset.**  A recorded `engine_t` that goes
    # backwards is `clap_plugin.reset()` having been called — a host
    # does that when the timeline jumps, and no harness in this project
    # ever did, which is precisely why a whole class of bug was
    # invisible here and audible in Reaper.  The replay obeys the trace.
    resets = {i for i in range(1, len(rows))
              if rows[i]["engine_t"] < rows[i - 1]["engine_t"]}

    took, level = [], []
    for i, r in enumerate(rows):
        if i in resets:
            plugin.reset(raw)
        tr = None
        if r["has_transport"]:
            tr = T.Transport()
            tr.header.size = ctypes.sizeof(T.Transport)
            tr.header.type_ = 3
            tr.header.space_id = 0
            tr.flags = r["flags"]
            tr.tempo = r["tempo"]
            tr.song_pos_beats = r["pos"]
        proc = T.Process(
            steady_time=r["steady"], frames_count=r["frames"],
            transport=ctypes.pointer(tr) if tr else None,
            audio_inputs=None, audio_outputs=ctypes.pointer(port),
            audio_inputs_count=0, audio_outputs_count=1,
            in_events=None, out_events=None)
        t0 = time.perf_counter()
        assert plugin.process(raw, ctypes.byref(proc)) == 1
        took.append((time.perf_counter() - t0) * 1e6)
        flat = [x for b in bufs for x in b[:r["frames"]]]
        level.append(math.sqrt(sum(v * v for v in flat) / max(1, len(flat))))
    plugin.deactivate(raw)
    plugin.destroy(raw)

    print(f"{clap.name}: {len(rows)} blocks, {nch} channel(s), "
          f"{frames} frames max")
    print(f"  host resets replayed: {len(resets)}")

    # What the host did — the part a harness cannot invent.
    beats = [r["pos"] / (1 << 31) for r in rows]
    jumps = [(i, beats[i - 1], beats[i]) for i in range(1, len(rows))
             if abs(beats[i] - beats[i - 1]
                    - rows[i]["frames"] / rate * rows[i]["tempo"] / 60) > 0.05]
    playing = [(r["flags"] >> 4) & 1 for r in rows]
    edges = [(i, playing[i - 1], playing[i]) for i in range(1, len(rows))
             if playing[i] != playing[i - 1]]
    sizes = sorted({r["frames"] for r in rows})
    print(f"  block sizes seen: {sizes}")
    print(f"  transport edges : {len(edges)}"
          + (f"  first at block {edges[0][0]}" if edges else ""))
    print(f"  position jumps  : {len(jumps)}")
    for i, a, b in jumps[:6]:
        print(f"     block {i}: beat {a:.2f} -> {b:.2f}")

    # What it cost, in Reaper and here.
    def worst(v):
        return sorted(v)[-1], sorted(v)[len(v) * 99 // 100]
    rw, rp = worst([r["micros"] for r in rows])
    hw, hp = worst(took)
    budget = frames / rate * 1e6
    print(f"  in Reaper : worst {rw/1000:.1f} ms, 99th {rp/1000:.1f} ms")
    print(f"  replayed  : worst {hw/1000:.1f} ms, 99th {hp/1000:.1f} ms"
          f"   (budget {budget/1000:.1f} ms)")
    over = [i for i, r in enumerate(rows) if r["micros"] > budget]
    print(f"  blocks over budget in Reaper: {len(over)}")
    for i in over[:8]:
        r = rows[i]
        print(f"     block {i}: {r['micros']/1000:6.1f} ms  "
              f"descending={r['descending']} wanted={r['wanted']} "
              f"pending={r['pending']} events={r['events']}")

    # And whether the score was heard, here.
    quiet = sum(1 for v in level if v < 1e-4)
    print(f"  replayed level: mean rms {sum(level)/len(level):.4f}, "
          f"{quiet}/{len(level)} blocks silent")

    # **The gaps, named.**  "Sometimes only the drums play" is a stretch
    # of blocks where the score made no sound, and the useful question
    # is what the plugin was doing through it: descending (waiting for a
    # stream), holding notes that were not yet due (`pending`), or
    # neither — which would mean it had nothing to play at all.
    floor = max(1e-4, 0.02 * (sum(level) / len(level)))
    gaps, i = [], 0
    while i < len(level):
        if level[i] < floor:
            j = i
            while j < len(level) and level[j] < floor:
                j += 1
            gaps.append((i, j - i))
            i = j
        else:
            i += 1
    long_gaps = [g for g in gaps if g[1] * frames / rate > 0.15]
    print(f"  silent stretches over 150 ms: {len(long_gaps)}")
    for start, n in long_gaps[:8]:
        window = rows[start:start + n]
        desc = sum(r["descending"] for r in window)
        pend = max(r["pending"] for r in window)
        beat = window[0]["pos"] / (1 << 31)
        played = sum(r["played"] for r in window)
        dropped = sum(r["dropped"] for r in window)
        print(f"     block {start:4d}  {n * frames / rate * 1000:6.0f} ms "
              f"from beat {beat:7.2f}   descending {desc}/{n}, "
              f"pending {pend}, played {played}, dropped {dropped}")
    tot_p = sum(r["played"] for r in rows)
    tot_d = sum(r["dropped"] for r in rows)
    print(f"  notes performed {tot_p}, dropped {tot_d}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    rate = float(sys.argv[3]) if len(sys.argv) > 3 else 48000.0
    replay(Path(sys.argv[1]), Path(sys.argv[2]), rate)
