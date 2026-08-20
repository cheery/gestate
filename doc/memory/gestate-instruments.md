---
name: gestate-instruments
description: "doc/instruments.md lists every capability a session has (gemba, andon, window driving, the generated pages) — read it early, and build a missing one the moment the need arises"
metadata: 
  node_type: memory
  type: project
  originSessionId: be127235-dfd4-4452-b39a-95cc015e2186
  modified: 2026-08-18T04:43:51.627Z
---

**`doc/instruments.md` is the list of what a session can already do**, written
2026-08-18 at Henri's ask: *"write down somewhere the capabilities implemented
so far, such that you find out that you have gemba available when you wake up
next time."*  Read it before deciding you have to do something the hard way.

The ones easiest to forget you have:

- **`python -m gestate.gemba`** — narrate into a running workbench.
  **Only when Henri has said his window is open and subscribed** (his rule,
  2026-08-18: *"do not use it unless I tell I have it open, it's waste if I
  don't do that"*).  And **sparingly** — one box, paced to the reader, so a
  session that says everything says nothing.  `at <path> <line> "…"` takes
  him to the place; `say "…"` narrates without moving him.
  He subscribes with `Ctrl-K` `gemba`; a bare `gemba` line pins the box in one
  place instead.  The alternative it replaced is him reading commit messages
  afterwards.
- **`tools/lagcheck.py`** — drive and photograph the real window
  (`driven`, `find_window`, `tap`, `chord`, `shot`).  This keeps finding what
  tests do not; see [[gestate-testing-standard]].
- **`tools/andon.sh`** — ring him, capped at three ([[gestate-andon]]).
- The generated pages that are suite gates: `gestate.complaints`,
  `gestate.reference`, `gestate.atlas` ([[gestate-atlas]]).
- **`python tools/suite.py --gates`** — the eight structural gates, fenced,
  then stop.  **12s**, writes `test/gates.md` (never `test/report.md`).  Built
  2026-08-19, `card:cheap-gates.md`.  `tools/pre-commit.sh --install` runs them
  at every commit and **is installed in Henri's checkout**; hooks are untracked
  so a fresh clone needs the install.  It caught four things in its first hour,
  all in a session's own new prose.  The full 25-minute pass is unchanged:
  still one per shift, tree frozen.
- **`tools/driven.py`** — the driven-window harness (moved out of
  `lagcheck.py` 2026-08-19).  `Run(name)` refuses if a *different*
  `libgestate_editor.so` is newer than the loaded one (`cargo build` from
  the workspace root writes `target/release/`, the editor loads
  `shell/editor/target/release/` — this cost four wrong readings), gives
  each run a fresh dir under `test/driven/`, and stamps commit + library
  md5 + the child's environment + `observe()` answers.  **`tools/toolbox.sh`
  is the record of what the bench needs** — F170 was `xdotool` missing and
  named nowhere, so `find_window` returned `None` and that read as *the
  editor never opened a window*.  Drive on `Xvfb :99`, never Henri's screen.
- **`tools/blind.py`** — the judging sheet for a blind multi-arm run
  (`--batch N arm1 arm2 arm3`).  Built 2026-08-19 because the *sheet* is
  what failed the first comparison, not the experiment.
- **`tools/clock.sh`** — the wrist clock ([[gestate-editor-latency]] neighbours
  it in spirit).  Read it before stating any elapsed time.

**And the second standing rule, learned 2026-08-19 (F169): a number nobody
asked for is a number nobody checks.**  `clock.sh` printed `1h` for 1h58m; the
line arrived as a by-product of an unrelated command and **Henri retracted a
true statement against it** — he had said "about two hours" and was right to
within two minutes.  An answer somebody asked for invites a check; the same
number arriving as background does not.  So: an instrument's volunteered number
must be right at the boundary and must name its source, and **more push is more
unexamined surface, not less** — which is why his own proposal that day (inject
the board, the clock and the last commit into every context) was questioned into
a journal entry rather than built.  It is not a session-only failing; the author
had a correct memory and overrode it.

**Why:** an instrument you do not know about costs the work you do blind in its
absence, and that work looks like progress while it is happening.

**How to apply:** read `doc/instruments.md` early in a session — and when a
capability is *missing*, **build it immediately, the moment the need arises**,
rather than filing a card.  Henri's rule, same day.  An instrument built while
the need is live is built against a real question; one built later is built
against a memory of one, which is `manifesto.md`'s third way an instrument
fails.  The page's last section lists what is not built yet, with `shot <path>`
in the gemba channel named as the next one.
