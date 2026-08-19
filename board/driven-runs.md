# driven-runs — a driven run does not say what it ran, and I believed it four times

    status   open — the harness is built; one real driven run is left
    because  "I read stale screenshots four times and told you wrong
             things twice" — a driven window leaves photographs with no
             record of which binary made them, and `cargo build -p
             gestate-editor` does not even build the library the editor
             loads, so a run can be green about code that was never in
             the process
    asked    Claude, 2026-08-18, at Henri's ask — "Write cards for
             fixing these issues in your workflow.  Describe them in
             good detail so that next time you can fix them."
    see      tools/lagcheck.py — `driven`, `find_window`, `tap`, `chord`,
             `click_into`, `shot`, `a_copy_of`
             doc/instruments.md — where the driven window is written up
             card:interface-oracle.md — what to assert once you trust the run
             card:reviewing-by-running.md — the loop this sits inside

## The ask

From the day's kaizen, in my own words:

> I read stale screenshots four times and told you wrong things twice.
> Once I reported "it doesn't land on the line" when it did.  The
> harness has no idea what binary it ran against — and `cargo build -p
> gestate-editor` isn't even what the editor loads (`--features capi`),
> which cost two more runs.
>
> And: I ran the driven window one question at a time.  Six separate
> two-minute runs on gemba where two would have answered everything.

## Found by looking, before it was taken

**Driving the real window is the best instrument this project has.**
On 2026-08-18 it found about thirteen defects; the test suite found
none of them.  This card is not about the instrument being wrong.  It
is about the instrument being *unlabelled*, which is worse than a
weak instrument, because an unlabelled one comes back confidently
green.

Three failures, all the same morning:

**1. The `.so` was stale.**  The editor loads a C-ABI library built by
`cargo build --release -p gestate-editor --features capi`.  Without the
feature the crate builds, cargo prints success, and the editor keeps
loading the *previous* library.  Two screenshots of an old binary were
read as two defects in new code.  Nothing in the shot, the filename or
the terminal output distinguishes that case from a real defect.

**2. Screenshots outlived their run.**  `shot()` writes a PNG to a path
the caller picks.  A second run that fails early leaves the first run's
image sitting there, and the next thing to look at it is me.

**3. Six runs where two would do.**  Each driven scenario costs about
two minutes of wall time — plus, and this matters more, it costs the
machine Henri is *listening on* (`board/README.md` §"And the machine is
shared": a session running X servers and polling loops made the audio
crackle for the person at the keyboard, and it was diagnosed as
hardware first).  I asked one question per run because writing the
scenario is the expensive part and adding a second assertion to an
existing scenario feels like risk.  That is exactly backwards.

### The shape the fix should take

**A wrapper that a driven scenario cannot forget**, in the spirit of
`lagcheck.driven()` — which already exists for precisely this reason,
and whose docstring says why: *"Every tool here that opens a window
goes through this, so a fifth one cannot forget."*  Same argument, one
layer out:

* **Build what the editor loads, or refuse to start.**  Shell out to
  the real command with `--features capi`, and compare the `.so`'s
  mtime against the newest `.rs` and `.py` in the tree.  If the library
  is older than the source, that is not a warning — the run should not
  happen, because its result is not about the code in front of you.
* **A run owns a fresh directory.**  Shots, logs and the report land in
  it; the directory is named for the run, so a stale image cannot be
  picked up by the next reader.  Nothing is ever written to a path a
  previous run also used.
* **Stamp the run.**  A small header written beside the shots and
  printed at the end: commit, tree dirty or clean, the `.so`'s mtime
  and hash, the scenario's name, the environment (`GESTATE_*` variables
  actually set).  When a screenshot is quoted in a commit body or a
  card, the stamp is what makes the quote checkable.
* **Scenarios take a list of questions, not one.**  The shape that
  encourages batching is one where a scenario is *steps plus a list of
  observations*, so adding an observation is a line and not a run.

**A worked example of what a stamped run would have prevented**: the
gemba walk "cutting off" had three stacked causes, and I ran six
scenarios chasing them.  Two of those runs were against a stale `.so`.
The finding that actually cracked it came from `GESTATE_WALK_WHY=1`
printing `[walk] ended by the caret: 2 != 132` — a print statement,
not a screenshot — which suggests a fourth item:

* **Prefer a machine-readable trace to a photograph** where one is
  available.  The shot proves what a person sees; the trace says why.
  A run should collect both, and the stamp should say which env
  variables were on so a trace can be reproduced.

## The postcondition

*A first draft, for Henri to correct:*

**A claim about what the window did can be checked by somebody who was
not there, from what the run left behind.**

## Questions

**Where does this live — a new tool, or grown into `tools/lagcheck.py`?**
`lagcheck.py` is named for the thing it was built to measure and now
holds the whole driven-window vocabulary, which is already a small lie
in the filename.  Growing it is cheaper; splitting it (`tools/driven.py`
for the harness, `lagcheck` for the latency scenario that named it)
would be honest.  Not worth asking Henri — pick one when taking the
card, and say which in the journal.

**Should the build-freshness check refuse, or warn?**  `fixme.md`
F113's rule is that a warning is better than a gate when a person is at
the keyboard and knows what they are doing.  But nobody is at the
keyboard during a driven run, and the reader of the result is the one
who gets misled.  Leaning refuse: the person this protects is a session
reading its own output an hour later, and that reader never sees a
warning it printed at the start.

## Built — 2026-08-19

**`tools/driven.py`**, and the split the card offered.  `lagcheck.py`
was named for one latency scenario while holding the vocabulary every
driven tool imported, so the vocabulary moved and `lagcheck` re-exports
it — *"splitting it would be honest"*, and on the day the board's own
§"The order" was renamed §"The priority" for the same reason, honest won.
`dialoglag.py`, `dragcheck.py` and `measure_editor.py` now import from
`driven`; `dragcheck` lost a duplicated `ctypes` block and
`measure_editor` two duplicated pointer helpers, so the display is
opened in one place instead of three.

**Refuse, not warn** — the card's second question, answered as it leaned.

* **The stale-library check is not the one the card predicted.**
  `gestate/editor.py::_stale` already rebuilds when the crate moves, so
  a stale load heals itself and has since 2026-08-17 — *before* the
  morning this card is about.  What does not heal is that there are
  **two** places the library can live: the editor loads
  `shell/editor/target/release/`, and `cargo build -p gestate-editor
  --features capi` run from the workspace root writes `target/release/`.
  Measured on 2026-08-19: both existed, different md5s, five days apart.
  So `Run` refuses when *a different copy is newer than the loaded one*,
  and prints the command that builds the right one.
* **A run owns a fresh directory** under `test/driven/`, named for
  itself, never reused, gitignored.
* **The stamp** — commit, tree, the loaded library's mtime and md5, the
  `GESTATE_*` environment actually set, wall time — written beside the
  shots, and written **even when the scenario raises**, since a run that
  died is exactly the one somebody reads later.
* **Observations are a list.**  `run.observe(question, answer)` is a
  line, so a second question costs a line rather than another two
  minutes of the machine Henri is listening on.
* **And `run.note()` for a trace**, because the finding that cracked the
  gemba walk was `[walk] ended by the caret: 2 != 132` — a print
  statement, not a screenshot.

**F170, found by building it.**  `find_window` shells out to `xdotool`,
which is not installed here and appeared nowhere in the tree except the
two lines calling it — so the search returned `None` after thirty
seconds and every caller reads that as *the editor never opened a
window*.  An undeclared dependency makes an instrument come back
confidently **red**, which is the mirror of this card's own subject.
`Run` now refuses by name, and `tools/toolbox.sh` gained `xdotool` and
`imagemagick` rows.

**Ten tests in `test/test_driven.py`**, none of which needs a display —
deliberately, because the bookkeeping is the part that was missing and a
harness whose bookkeeping cannot be tested is the same problem as the
runs it labels.

## What is left

**One real driven run**, once `xdotool` is installed — the whole point
of `test_what_a_person_would_do`, and until it happens this card has
built a harness that has never driven a window.  The bookkeeping is
tested; the driving is not, and the card does not close on the half that
was already working.
