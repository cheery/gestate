# summary.md — everything built, and the calendar it was built on

`journal.md` is the narrative and it is 6,948 lines long. This file is the
same span read as a **calendar**: what was built, in what order, and in how
much time. It exists because the second question has never been asked of
this project before, and the answer is short enough to fit on one page.

Every number below comes from `git log` on the tree as of the last commit
counted, `f2f8a61` — reproduce any of them with the command in the
footnote of its section.

---

## The headline

| | |
|---|---|
| First commit | **2026-08-08, 22:21** |
| Last commit counted | **2026-08-16, 09:56** |
| Elapsed | **7 days, 11 hours, 35 minutes** — nine calendar days, seven of them whole |
| Commits | **272** |
| Lines added / removed | **+224,657 / −18,534** (of which the initial import is +110,167) |
| Net authored after the import | **≈ +114,500** |

So: **a hundred thousand lines of new work, in a week and a half, by one
person.** That is **30 commits and ~14,800 changed lines per calendar day**
(added plus removed, import excluded), sustained without a day off.

> `git log --reverse --pretty='%ad' --date=iso | head -1`
> `git log --shortstat --pretty='%ad' --date=short`

---

## What exists now

| Artifact | Size |
|---|---|
| Python (`gestate/`, `test/`, `tools/`) | **90,251 lines** |
| Rust (`shell/`, `crust/`) | **26,510 lines** |
| C host (`gestate/host.c`) | 593 lines |
| Specs and docs (`spec/`, `doc/`, root `*.md`) | **36,649 lines** across 63 files |
| Test files / test functions | 110 files, **2,008 tests** |
| Example programs (`examples/*.ges`) | **104** |
| Defect register (`fixme.md`) | **141 `F` numbers** filed |
| Errata register (`spec/errata.md`) | 10 `D` numbers |
| Journal / roadmap / README | 6,948 / 852 / 241 lines |

Three languages, a compiler, a G-machine in two implementations, a CLAP
plugin, a Rust editor, a live audio host, a drawing substrate, a
documentation set, and a two-thousand-test suite. In nine days.

> `git ls-files '*.py' | xargs wc -l`

---

## The nine days

| Day | Commits | What it was |
|---|---:|---|
| **08-08** | 7 | Import. Linear envelopes (`on : [Envelope] -> Float -> Float`), `bpm`/`tempo` enabling the beat parameter, parser papercuts — multi-line lists and expression bodies. |
| **08-09** | 26 | Sliding delay lines, compiler optimisations, `gateOn`, resonances promoted to signals. **Verification work started.** CLAP plugins started end-to-end in one day: transport, knobs, keyboards, state persistence, stereo export. The dynamic-score proposal written and revised twice. |
| **08-10** | 26 | Dynamic score built and unfolded. **The crust G-machine** — "large changes, most major is the crust g-machine". Ariadne implemented; `sown`/`probe` retired. Sections, resumption paths, the silent-stall fix. Arpeggios, nightdrive, jazz. |
| **08-11** | 33 | The heaviest structural day. GUI in Rust; the G-machine *inside* the CLAP plugin; dynscore in plugins; the substrate designed, built, and shipped into the plugin. **The editor rewritten in Rust.** The lag bug found and fixed; the segfault run down to two bugs, both in the audio layer. Ran 00:03 → 23:48. |
| **08-12** | 18 | Commands, syntax colours, diagnostics. **pygame deleted.** The canvas broke as a consequence and the investigation opened — root cause found, countermeasures set. F103 first sighted. |
| **08-13** | 42 | Content boxes, and error messages moved into them. **Transcripts given a home** as the medium a defect is recorded in. Piano-key contract and smart labelling. File dialog: barrier undo, unsaved-changes warning, no stale directory views, "the dialog answered in thirteen milliseconds". Monomorphisation of `let`. |
| **08-14** | 43 | Hamburger menu, inert mode. **The crust canvas move** — the throttle, the clock floor, the payload door, "a showing canvas keeps the fast pace". Scope, spectroscope, sink, line command, folds. **F103 closed** with its reproduction, plus F124, F127, F129–F133. The canvas ask-line, box hands, multiple canvases. The notes score box. Streaming with stall detection. |
| **08-15** | **60** | The largest day in the project. **The oracles arrived.** `GESTATE_BUILD_TIME`; the day measured; and then the removal of work that did nothing — the vectoriser that cost a second, the library renamed on every keystroke, the environment rebuilt once per pushed cell, the cache that evicted the file it was caching. **The north star**: a note that follows the hand, byte-exact and heard. F137 and F138 filed with repros. `manifesto.md`, `doc/switches.md`, `rocks.md`. Jukebox, moon sonata, chopin.gif. Real World One, from a friend. Started 02:49. |
| **08-16** | 17 | Export learned to weigh itself. A refusal keeps its own sentence. **The atlas** — the project drawn on five generated A3 sheets, stamped from a clean tree, and *closed at five*. The rebuild asks what changed. (Counted to 09:56.) |

---

## The clock

The distribution of commit timestamps across the 24 hours of the day:

```
00 ▌1     06 ████████ 16      12 ████ 8       18 ███████ 14
01 █ 2    07 ████████████ 25  13 █████████ 18  19 █████████ 19
02 █▌3    08 ██████████████ 29 14 █████ 11     20 ████ 8
03 ██ 4   09 █████ 10        15 █████ 10      21 ████ 9
04 ██ 5   10 ███ 7           16 █████ 10      22 ██████ 13
05 █████ 10  11 █████ 11     17 █████████ 18  23 █████ 11
```

**There is no hour of the day without a commit in it.** Fifteen commits fall
between midnight and 05:00. Eighty fall between 05:00 and 09:00 — the
mornings are the spine of this project. Four of the nine days ran longer
than sixteen hours between first and last commit:

| Day | First → last | Span |
|---|---|---|
| 08-11 | 00:03 → 23:48 | 23h 45m |
| 08-10 | 06:21 → 23:31 | 17h 10m |
| 08-15 | 02:49 → 19:41 | 16h 52m |
| 08-09 | 09:44 → 23:16 | 13h 32m |

Those are the spans between commits, not between waking and sleeping, so
they are a floor and not a measurement. Nine days, no rest day, work
recorded in every hour of the clock.

> `git log --pretty='%ad' --date=format:'%H' | sort | uniq -c`

---

## What the calendar says about the method

The method in `manifesto.md` — *do not build what nothing needs*, and
*what is built must be able to say when it is wrong* — is visible in the
shape of the days, not only in the prose:

* **The registers grew faster than the code.** 141 `F` numbers in nine
  days is one filed defect every ninety minutes of elapsed project time.
  That is the second rule working: the things being built were saying
  when they were wrong, in writing, at addresses the source cites.
* **Deletion is a day's work here.** 08-12 deleted pygame; 08-15 spent a
  day removing work that cost time and moved nothing; 08-16 closed the
  atlas at five sheets rather than adding a sixth. Three of the nine days
  have subtraction as their headline.
* **Measurement preceded optimisation, every time.** `lagcheck`,
  `GESTATE_EDITOR_TIME`, `GESTATE_BUILD_TIME`, "the day measured", "the
  loop's stopwatch", "the stopwatch that keeps build honest" — the
  instrument was built before the thing it judged was touched.
* **The pace itself was never instrumented.** Every other cost in this
  project has an oracle. This one did not, until this file.
