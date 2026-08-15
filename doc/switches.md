# Switches — every `GESTATE_*` the program reads

**Most of these are not settings.**  They are how the program is asked
where its time went, or made to do the slow thing on purpose so a
measurement means something.  Nothing here needs to be set to use
gestate; the defaults are what the project runs and what its numbers
were taken with.

The rule they follow: a cache has an off switch, and an instrument has
an on switch.  Nothing else is optional
(`manifesto.md`, "what visible costs").

---

## Where a rebuild's time goes

    GESTATE_BUILD_TIME=1 python -m gestate.workbench examples/audio/quartet.ges

One block per rebuild, on stderr:

    [build] apply quartet.ges 2.24s
                   front end    1.40s  ×2
                       score    0.27s
                   substrate    0.24s
                        midi    0.14s
                     extract    0.04s  ×2
                       holes    0.02s

* A phase reports its **own** time — a phase inside another is counted
  once, as itself, and its caller's number excludes it.
* `‖` marks a phase that ran while another thread was in one too.  It
  is a claim about the clock and about who called whom, not about
  thread identity: `pipeline._deep_stack` hands the front end to a
  worker and *waits*, which is another thread and is not concurrency.
* `clang` appears **only when the compiler ran**.  A hit in the
  compiled-object store is meant to cost nothing, so a phase reading
  0.05 s would leave you guessing which it was.

**To measure a build honestly, turn the object store off** — otherwise
the second run of anything is a file copy and `clang` never appears at
all:

    GESTATE_BUILD_TIME=1 GESTATE_SO_CACHE=0 python -m gestate.workbench …

## Where a frame's time goes

    GESTATE_EDITOR_TIME=1 python -m gestate.workbench file.ges

The window's own stopwatch: paint, copy, present, resize, the gap
between frames, and the number that matters — **key to pixels**, from
the event that changed something to the `present` that showed it.

* `GESTATE_EDITOR_STRESS=1` never lets the picture go clean, so the
  platform's half can be measured with no hand on the keyboard.
* `GESTATE_EDITOR_KEYS=1` prints what the X server said about
  detectable autorepeat, which is the difference between a held key and
  a hundred presses.
* `GESTATE_LOOP_TIME=1` is the *model's* half of the same question —
  `[loop]` lines every five seconds: what a pass spends answering
  gestures, deriving the furniture and walking the canvas, and how far
  apart canvas frames actually land.
* `GESTATE_CANVAS_SHARE=<fraction>` (default `1.0`) overrides how much
  of the loop a watched canvas may have.  For measuring: the default
  was itself chosen by measurement, and lowering it is how that was
  checked.

`tools/lagcheck.py` and `tools/dialoglag.py` drive the real window
through XTEST and read the answer off the screen; they are the other
half of this and need no switch.

## Caches, and turning them off

Each is a cache in the strict sense: nothing in it is authoritative, a
miss only costs time, and a stale one is impossible because the key is
the whole input.

| switch | turns off | what a miss costs |
|---|---|---|
| `GESTATE_STACK_CACHE=0` | the pickled library front on disk | one library front end |
| `GESTATE_SO_CACHE=0` | the content-addressed `.so` store | one `clang` run — seconds on a large piece |
| `GESTATE_SCORE_CACHE=0` | the laid-out score on disk | one interpreter pass over the piece — five seconds for `quartet.ges` |

`GESTATE_STACK_CACHE=0` turns off the *disk* half only; the in-memory
one has no reason to be optional.

## Choosing a path rather than measuring one

`GESTATE_SIDE_THREAD=1` puts back the thread that used to compile the
canvas, the score and the `FromMIDI` interpreter while `Live.start` ran
`clang`.  It is off because the overlap was measured and lost — with
`clang` forced to run, `quartet.ges` started in 8.50/9.44/11.82 s
threaded against 6.75/7.48/7.33 s inline, because two Python threads
cannot run Python at the same time.

**The switch is kept because that was one machine** — a four-core
fanless laptop.  More cores or slower storage may answer differently,
and re-measuring should not mean re-implementing.  If you try it, do it
with `GESTATE_SO_CACHE=0` and alternate the runs: without the first,
`clang` never runs and the comparison measures nothing.

## Tests

`GESTATE_TEST_AUDIO=1` puts back the sound-card fallback the suite
removes.  Without it a test that reaches a real device is an error
naming the test that did — a suite that plays `duet.ges` out loud is a
suite nobody runs twice.  Set it when checking by ear that the live
path still makes a sound.

## The plugin

* `GESTATE_TRACE=<path>` records a session transcript from the next
  `activate`: every `process` call as the host presented it, written at
  `deactivate`, allocating nothing while audio runs.  It is the working
  oracle for "what did the DAW actually do to us"
  (`journal.md` §"The day the transcripts earned their keep").
* `GESTATE_GRAPH_DIR` is plumbing rather than a knob:
  `gestate.export` points it at the graph it just wrote before invoking
  cargo, and the plugin's `build.rs` reads it.

## At build time, not run time

`-DGESTATE_ALSA` is a compiler define, not an environment variable: it
is what gives `gestate/host.c` a device to open.  Without it the C host
still renders — `test_audiohost.py` fills blocks from one on every
machine — it simply has nowhere to send them.

---

## How to measure so the number means something

Learned the hard way, each of these more than once:

1. **Caches off for the thing under test**, on for everything else.  A
   run that skipped the work is not a fast run.
2. **Alternate the runs.**  A busy machine drifts, and A-then-B blames
   the drift on B.
3. **One start per process** when what you are timing includes imports
   and first-call costs; the second start in a process is a different
   measurement and worth taking separately.
4. **Say which machine.**  `spec/performance.md` records the one the
   editor's baselines came from, and every number in this file came
   from the same fanless laptop.
5. **Distrust the first surprising number**, including from these
   instruments.  `GESTATE_BUILD_TIME` reported a phase at 7.8 s that
   was really 0.24 s plus double counting, and it was believed for
   about an hour (`manifesto.md`, "the three ways an instrument
   fails").
