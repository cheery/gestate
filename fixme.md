# fixme.md — where `gestate/` and `spec/` disagree

Read of `gestate/**.py` against `spec/*.md`.  Only **divergences from the
spec** are listed; things the spec never decided are in `spec/errata.md`, and
things `journal.md` Part I already tracks as unbuilt increments are
noted as such rather than re-litigated.

**The numbers in this ledger are addresses.**  `gestate/*.py` cites them —
fifty-six distinct `F` numbers, in comments explaining why a piece of
code is the shape it is (`declarations.py` F36, `gmachine.py` F95,
`audioextract.py` F94).  So an entry is never renumbered and never
deleted once written: **[resolved]** is what closing one looks like,
and that is why nine tenths of the ledger is resolved.  The same is
true of `spec/errata.md`'s `D` numbers.

**Each entry is a file, `fixme/F123.md`, and a citation still says
`fixme.md` F123.**  It was cut at Henri's ask on 2026-09-13, when the ledger
was 451 KB in one file and every entry added or closed changed it
whole for anything that reads files — `tools/graphrag.py` extracted it
again at every commit that touched it.  This page is the ledger's name
and its front; `fixme/` is where the entries live — the same separation
as `journal.md` and its closed months, and a card's id and its shelf.

**A new defect is a new file**: `fixme/F<n>.md`, `n` one above the
highest in `ls fixme/`, opening with its heading line —

    # F228. **[bug]** what is wrong, in one line

— and a row in the table below while it is open.  Closing one edits
that file's marker and this page's count, and nothing else.

Legend: **[bug]** wrong behaviour · **[missing]** spec'd, not built ·
**[deviates]** built differently than spec'd · **[dead]** built, unreachable ·
**[resolved]** closed since this file was written, kept for the record.

Of 228 entries, **181 are resolved**.  (Those two numbers are checked by `test_citations.py`, because the ledger's whole discipline is that a
claim does not rot, and this sentence had rotted by twenty-five entries before anybody read it.)  What is left:

| # | State | What |
|---|---|---|
| F5 | partly resolved | `δ(case …)` does not go through `split [ϕe]` |
| F26 | missing | `{: … :}` parses to a type constructor nothing knows about |
| F29 | partly resolved | Property tests and examples exist; golden ASTs do not |
| F32 | partly resolved | Ambiguous `Num`/`Eq`/`Ord` constraints default silently to `Int` |
| F33 | partly resolved | No superclasses, no multi-parameter classes |
| F34 | missing | No orphan-instance rule |
| F35 | missing | No specialization, no existential dictionaries |
| F38 | partly resolved | No monotone/discrete discipline and no eqtype/semilattice/fixtype checks |
| F67 | missing | Nothing enforces the "no variable starting with `d`" rule |
| F93 | deviates | A graph node's `clock` is set only on sources, not inherited |
| F100 | resolved | A constraint naming a class that does not exist is accepted |
| F95 | fixed | The fragment admits tuples; the extractor now lays them out |
| F103 | resolved | The same file's canvas builds or fails typechecking, run to run |
| F106 | resolved | The drawn piano retriggers a held key (OS autorepeat) |
| F107 | resolved | Up/Down inside a palette argument runs the command |
| F108 | resolved | `pianoStep` inserts `50` with no trailing separator |
| F109 | resolved | Opening a file joins the previous start in the gesture loop — no cancel, late switch |
| F110 | resolved | Zoom wedge: the mirror only synced after input — tell() every poll now |
| F111 | resolved | Space in `transcript`'s path box erases the proposed path |
| F116 | resolved | Every click was eaten while the command list was open |
| F117 | resolved | Tab did not complete paths in the file dialog |
| F118 | resolved | The list sat over a freshly opened file and caught the first keystrokes |
| F119 | resolved | The caret anchored the scroll — the view snapped back on every model description |
| F120 | resolved | Opening a `.wav` quit the whole editor |
| F121 | resolved | A template inserted while scrolled away appeared behind the list |
| F122 | resolved | A typed path was walked twice — `transcript ../../x` landed in `/home/` |
| F123 | resolved | A finished `open` re-runs from a different directory than its first run |
| F124 | resolved | The directory-watch tests flake under machine load — the kernel's coarse clock, not load |
| F126 | resolved | The crossfade resolved the leaving engine's nodes against the live graph |
| F127 | resolved | A literal applied to arguments answers with an instance at a function type |
| F128 | resolved | The text sniff refused `duet.ges` — the tail-drop moved the boundary instead of removing it |
| F129 | resolved | An exactly-named directory loses to a fuzzy file |
| F130 | resolved | A file you can name is a file the dialog cannot find — and Tab wiped the walk |
| F131 | resolved | An apply drops the notes it crosses — long holds die audibly, the pad most of all |
| F132 | resolved | A content box near the foot renders over the status bar |
| F133 | resolved | `what scope` draws its page outside the window when the panel is low |
| F125 | resolved | A phantom new file read as saved — no tell it was a starter wearing a borrowed name |
| F112 | resolved | The file dialog's listing sometimes lags — measured: a beat only while the model builds |
| F113 | resolved | Undo and redo cross a file switch — one history for the session |
| F114 | resolved | Copy and paste are not commands |
| F115 | resolved | A bank added by an audition could not be listened to — allocators followed the disk |
| F134 | resolved | `now : Sig Float` — the current time in seconds, to the substrate |
| F135 | partly resolved | Long features work in silence; the CLI has progress text, the statusline does not |
| F136 | missing | A tuple-pattern lambda picks the wrong instance, silently |
| F137 | missing | A zoom scales the band and not the picture in it |
| F140 | resolved | A render refused and the reason stayed in the terminal |
| F141 | resolved | `foo : int` is a legal signature and a certain mistake |
| F148 | resolved | The taskbar wore a sine; the front page wore the egg |
| F149 | resolved | The desktop icon installed correctly and did nothing when clicked |
| F150 | resolved | The first screen named a deleted button; the menu opened on `skip` |
| F151 | resolved | Typing reached nothing, and there was no word for it |
| F152 | resolved | A complaint with no place to land |
| F153 | resolved | The window taught the key only to people who no longer needed it |
| F154 | resolved | A driven harness saved into the repository |
| F155 | resolved | The one control was a glyph nobody could find |
| F156 | open | The audio backend says which definition, never which line |
| F157 | open | The type machinery's later stages let go of the span |
| F158 | open | A piece's complaints name a beat, never a line |
| F159 | open | The evaluator's runtime complaints carry no position |
| F176 | bug | The file chooser opens on the source tree, and a stranger reads it as a menu |
| F177 | fixed | The way back up is the top row; it is `[up]` now |
| F178 | bug | `[command]` opens unaided, then the list gives a newcomer nothing to do |
| F174 | bug | A driven run cannot tell its own window from one beside it |
| F179 | resolved | The desktop icon's absent file opens the starter, which sounds |
| F180 | resolved | `test_suite_runner.py` fails alone and passes in the full run — its own `sys.path` line now |
| F181 | bug | `seedaudit.py`'s piece paths are gestate's own, and a seed cannot say where its pieces are — the first instance was a slip the audit caught |
| F182 | resolved | `test_precommit.py` read the hook as prose, and passed with the gate neutered |
| F183 | resolved | The automatic audition shut its gate and said nothing, so a slow file read as a broken one |
| F184 | resolved | The housekeeping thread died under a test for nine days, and the suite called it *1 warning* |
| F185 | resolved | The browser gate skipped under the fence — Chrome is in `/opt`, which the fence did not bind — so its green had only ever been unfenced |
| F186 | resolved | An application's head loses its parentheses: `(x => x + 1) 2` comes back as `x => x + 1 2` |
| F187 | resolved | A lambda's and an instance member's parameters are not atoms — F46's third bullet, in the callers it did not reach |
| F188 | resolved | A `Box` pattern formats as the debugging placeholder `<PBox>`, which does not parse |
| F190 | open | The formatter is not idempotent: a second pass moves comments and deletes 27 of them |
| F191 | open | For nine sources — the prelude among them — the formatter's output does not parse |
| F192 | open | A written type loses its source position at instantiation: `_apply_subst_map` carries the span on `TFun` and not on `TApp` |
| F193 | resolved | `spec/syntax.md` did not list `do`, `internal` or `%`, which the tokenizer and the parser have |
| F194 | open | `memoryindex.py` writes nothing and exits 0 behind the fence, where `$HOME` is a tmpfs — and its own gate skips there |
| F189 | open | The leash reported itself off at session start against a file it had not touched, and it was on — not reproduced |

Several of these are **closed rather than pending** under
`journal.md` Part I's rule — *do not build what nothing needs*.
F33, F34 and F35 have no caller and are not scheduled; F34 is vacuous
outright, there being one compilation unit.  Recording them is the
deliverable, not implementing them.

## Where the entries came from

The ledger was one file in seven sections until the cut, and an entry's
number says which section it was written in.  A section is a reading,
not a place, so it is kept here and not as a directory:

- **1. Seminaïve ϕ/δ** — `gestate/seminaive.py` vs `spec/data.md` Part I — F1–F10
- **2. Datafun helpers** — `gestate/helpers.py` — F11–F13
- **3. Rizzo / FRP** — `gestate/reactive.py`, `gestate/gmachine.py`, `gestate/desugar.py` — F14–F22
- **4. Surface syntax** — `gestate/syntax/` vs `spec/syntax.md` — F23–F29, F44–F49
- **5. Types and classes** — `gestate/unify.py`, `infer.py`, `elaborate.py` — F30–F39
- **6. Pipeline and documentation drift** — F40–F43
- **7. Found while building the front end (2026-08-03)** — F50–F228 and `fixme/D3-D4.md`

F11 was written twice, a diagnosis in §2 and its resolution in §7;
`fixme/F11.md` keeps both.  Counted apart they made the header say 228
entries where 227 numbers stand.
