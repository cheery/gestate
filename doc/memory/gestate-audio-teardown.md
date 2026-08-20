---
name: gestate-audio-teardown
description: "Why gestate segfaulted on quit when another program held the sound card, and the two-stop teardown that fixed it"
metadata: 
  node_type: memory
  type: project
  originSessionId: 753ff05e-7489-4e11-b1c1-e5c873af5781
  modified: 2026-08-11T16:57:47.580Z
---

**Symptom:** `python -m gestate.workbench` core-dumps on quit whenever
REAPER (or anything) holds the ALSA card. 8 of 10 quits crashed; a plain
`Workbench.start()` / `stop()` with no editor crashed too, which is how
we knew it was not the new editor wiring.

Two causes, both in the audio layer, both fixed 2026-08-11:

1. **`Workbench.stop` freed the workspace whether or not the thread had
   stopped.** It called `host.close()` right after `join(timeout)` and
   only *then* said "closing now may crash". That is not a risk of a
   crash, it is the crash. It now frees only when the thread is really
   gone; otherwise it leaves the workspace alone and says so. Leaking
   until the process ends is the cheaper of the two.

2. **The device loop could only exit on `h->stop && h->gain <= 0.0`** —
   it waits for the fade-out to *arrive*, which is what keeps a quit
   from popping. That premise fails when the card is held: `writei`
   blocks, the fade never advances, the loop never leaves.

So `gestate/host.c` now has **two stops**. `stop` is the polite one.
`halt` (`gestate_host_halt`) does not negotiate: it breaks the loop
unconditionally, `snd_pcm_drop`s instead of `snd_pcm_drain`s (drain on a
held card waits forever), and — crucially — **a flag alone cannot reach a
thread blocked inside `snd_pcm_writei`**, so `gestate_host_unblock` calls
`snd_pcm_drop` *from the stopping thread* to end the wait. A click on the
way out is the right trade against a core file. `Workbench.stop`
escalates: join, halt, join again.

**Also:** `workbench.run` used to call `bench.start()` on the way in.
That compiles with `clang` (seconds) and then asks for the card, so a
busy card left a window open that answered nothing. It starts on its own
thread now, with a `quitting` event so a close mid-start still gets the
device stopped by whoever started it.

**How to test it:** quit through the editor's own `quit` command at
varying delays (0.6 s … 6 s) and check exit codes — SIGTERM skips
`finally` entirely and proves nothing. Crash reports land in
`/var/crash/*.crash`; `apport-unpack` then `gdb -batch -ex "thread apply
all bt"`. apport **deduplicates**, so a stale report can look like a
fresh one — check its timestamp.

See [[gestate-editor-latency]] for the XTEST harness these tests drive
the window with.
