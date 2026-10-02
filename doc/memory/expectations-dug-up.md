---
name: expectations-dug-up
description: "Week 39: Henri's expectations are being dug up for vision.md, one or two per conversation and slowly; thirteen candidates from the tree, one met at his word, the rest open — and a fourteenth pre-registered 2026-10-02, reactors cutting GUI ceremony tenfold, with its baseline"
metadata:
  type: project
---

**The occasion, Henri, 2026-09-24.**  He asked for PDCA on the card,
the week and the vision, and then put it plainer: *"We need to
pre-register what we expect, and then start checking/studying whether
our expectations meeted the reality."*  The card and the week already
do it — a postcondition before building, a **Goal.** before the days.
The vision does not: its dated lines are wishes, and none says what is
expected or when it will be looked at.  Asked for his, he said he held
few he was aware of, and asked how to dig them up.

**How they were dug:** his surprises read backwards (each one breaks an
expectation), and his decisions read for what they bet on — from
`journal.md`, `journal/2026-08.md`, every shelf of the board and this
directory.  The wording of each expectation below is the session's;
the quotations are his.

**And the pace is his:** *"some of this should be resolved later..
maybe during this week, slowly as part of every conversation."*

## The list

Stated as expectations:

1. **Generality, his own, stated 2026-09-24:** gestate made general,
   around data edited while it lives, becomes *"a common platform for
   implementing small models and GUIs that stand above LLM-editable
   material, allowing both to work through small, or large, datasets
   available at each moment."*  Open — wants a date and what would show
   it wrong.
   *2026-09-26:* no date — *"I don't know by when we get there"* —
   and he wants **the bounds instead**: what stands as *achieved*.  A
   table of five tests and one witness (a tool nobody planned, built in
   a day as one file, no core change) was offered; his view was that
   **one sentence** should carry the bounds, **with expectations set
   beside it**, and that the morning was too early to decide.  Open;
   his to write, later.
   *Later the same morning*, asked whether the goal suits at all —
   *"There is no pre-existing pull on the data-based gestate, other
   than the music one can do with it"* — and then: *"I've been using
   reaper to make music lately.  Notes editor addresses the right
   thing, but maybe too loosely.  What we are doing right now is
   learning to utilise AI well.. I'm thinking this all what we've been
   doing right now is getting help to define what the project itself
   is about."*  Not settled; the sentence is still his.
   And on the reading that he explores *"a way for minds to work
   together"*: *"The "minds to work together" might also mean for
   human minds, not just human+session.  A team is forming where the
   context of that sentence changes that way."*  The vision line of
   2026-08-16 — *"We are missing a way to work with each other"* — was
   offered as a candidate for the one sentence; his to take or leave.
   Team members named in the tree go through `doc/consent.md` first.
   *2026-10-02,* after reading the reactor paper: *"finding out about
   the reactor model probably changes things here"* — "here" being, at
   his word, the vision sentence and `card:gui-is-difficult.md`.  The
   session's reading: the reactor's one notion of time is a candidate
   for the "same things" of expectation 8, which is the root of this
   one.  Still his sentence to write.
2. **The language, noted 2026-08-20** (`[[the-language-goal]]`):
   *"Tavoite lyhyellä ajalla… kieli joka kääntyy wasmiin"* — "short
   term", undated; nothing compiles to wasm five weeks on.  Open.
3. **The graph, stated 2026-09-11** (`card:graphrag-c.md`): *"Minä uskon
   että kohdat 1 ja 2 tuottavat jotakin todellista."*  Already
   pre-registered; studied at its verdict, 2026-10-12.
4. **One card at a time, decided 2026-09-23:** packages worked in
   sequence finish sooner than ones started together.  Open;
   `tools/flow.py` lead times before and after, read in about a month.

14. **Reactors and the GUI's ceremony, his, 2026-10-02:** *"I believe
    reactors themselves would reduce the amount of ceremony we need for
    a GUI, by an order of magnitude."*  Measured on *"all GUI code, but
    mainly the notes editor"*; by when — *"we will figure it out as soon
    as we try this out for real"*: a trigger, not a date — the first
    real port of a piece of the notes editor to reactors.  **What would
    show it wrong:** the ported part under a tenth of what it replaces
    is the claim; a ratio nearer one is the claim failing.  **Baseline,
    taken before anything is ported** — code lines, non-blank and not a
    comment, Python docstrings counted:

        f() { for x in "$@"; do grep -v '^\s*$' "$x" | grep -v '^\s*#' | grep -v '^\s*//' | wc -l; done | paste -sd+ | bc; }
        f gestate/scorebox.py gestate/roll.ges gestate/hand.ges gestate/hands.ges gestate/gesture.ges gestate/grid.ges gestate/gridbox.py gestate/charts.py gestate/chart.ges   # 2776
        f gestate/gui.py gestate/gui.ges shell/panel/src/list.rs shell/panel/src/substrate.rs shell/editor/src/walk.rs                                                   # 2329
        f gestate/audioeditor.py gestate/workbench.py                                                                                                              # 3919

    The notes editor's own picture, hands and gestures are the first
    line — `scorebox.py` 1832 of it; the second is the canvas machinery
    under every GUI; the third is the host, which also holds the
    instrument and is an upper bound.  The file set is the session's,
    his to correct.  Context: `card:gui-is-difficult.md` §"Mutations,
    read — and his view of the ceremony".

Broken already — each written down with what happened:

5. **The origin, told 2026-09-01:** *"at first I thought I'd have to
   work on the code myself"* — broken; `[[discovered-not-designed]]`.
6. **People and the tree, said 2026-08-21:** *"or at least, I expect
   they want to"* — broken; `[[the-tree-meets-people-on-pull]]`.
7. **The tree's memory, said 2026-08-24:** *"This is better than
   expected"* — the lower expectation itself is unsaid.  Open.
8. **One general GUI, said 2026-09-09:** *"jokainen GUI-asia tuntuu
   vaativan samat asiat, mutta eri muodoissa"* — the root of 1.  Open.
9. **SuperCollider's itch:** recalled 2026-09-24, not pre-registered;
   met, at his word — *"we already know the result."*  What was not
   expected is the direction: Rizzo's constructs, a session's find.

Carried by vision lines, and wanting a date:

10. **Models are already good enough, vision since 2026-08-16:** *"we
    already have LLMs that can get really good work done… We are
    missing a way to work with each other."*  **Met, at his word,
    2026-09-24:** *"Opus 5.5 rolled out just recently and shows mainly
    better performance at writing text, but otherwise is not more
    powerful.  I find it good enough."*  His verdict; a session is the
    wrong judge of this one ([[the-evaluation-loop]]).  The second half
    — *a way to work with each other* — is not studied; `~/tend` is
    its second transfer.
11. **Lean at scale, vision since 2026-08-16:** *"Even at 100,000 lines
    it stays lean."*  Open; `wc -l` and one read for holdability.
12. **The stranger, vision since 2026-08-16:** open a file, hear it,
    change it, untold; and *"my friend could use it."*  Studied once, in
    part — `card:stranger-test.md`.
13. **The keeper's weight, doubted 2026-08-21:** *"I am really uncertain
    that I am up for this task."*  Partly met — `[[the-keepers-evening]]`.

**Why:** a vision line with no expectation cannot be studied, so the
top level of the loop has a Plan and nothing after it.  The card and
the week each close their own loop already.

**How to apply:** through week 39 (to 2026-09-27), bring **one or two**
of the open ones into a conversation where they fit — never the list —
and ask his two questions of it: *by when, and what would show it
wrong?*  Transcribe the answer here, dated.  **`vision.md` is his to
write**; what he settles goes there by his hand, and a line he strikes
here is struck, not argued.  When none is left open this memory has
done its job and says so.
