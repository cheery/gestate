# The instruments — what a session has to work with

*Started 2026-08-18, at Henri's ask: "write down somewhere the
capabilities implemented so far, such that you find out that you have
gemba available when you wake up next time."*

**Read this early.**  A session that does not know an instrument exists
does the work the instrument was built to make unnecessary — asks a
person to look at something, reasons about the window instead of
photographing it, or reports a finding into a chat log nobody is reading
while it happens.  Every entry below was built because that had already
happened once.

`tools/toolbox.sh` is the neighbouring file and answers a different
question: what is *installed*.  This one is what has been *built*.

**Kept in two places on purpose.**  This page is the tree's copy and
outlives any session; a session's own memory carries a pointer to it, so
that waking up and finding out `gemba` exists does not depend on
happening to read `doc/`.  If you are adding an instrument, add it here
— the pointer will find it.

---

## The standing rule: build the missing one, now

**When a capability is missing, implement it the moment the need
arises — not after, and not as a card for later.**  Henri's, 2026-08-18,
and the tree already carries the argument for it twice over:

* `journal.md` §""Be my oracle" is a smell" —
  *when a session finds itself asking a person to listen, look, or judge,
  write down what the mechanical version would be, even if it is not
  built.*  This is that rule with the hedge taken out: usually it is
  fifteen lines, and the fifteen lines are cheaper than the second time
  you need them.
* `manifesto.md`'s third way an instrument fails is that it agrees with
  the implementation.  An instrument built *while the need is live* is
  built against a real question; one built later is built against a
  memory of one.

The cost of a missing instrument is never the instrument.  It is the
work done blind in its absence, and that work looks like progress while
it is happening — which is why waiting for a better moment does not work.

And when the instrument *is* there, the rule is Ohno's, in
`manifesto.md` §"Go and do it": **do something.**  A session that has a
hypothesis and declines to run the window has swapped an answer for an
opinion, and the opinion goes into a commit message looking like a
finding.

## The other standing rule: a number nobody asked for is a number nobody checks

*From F169, 2026-08-19.  It applies to every instrument on this page
rather than to any one of them; the afternoon it happened is
`journal.md` §"The proposal that questioning turned inside out".*

An instrument's answer is checked when somebody asked the question.  An
answer read as an answer invites a check, because the reader wanted it
and knows roughly what shape it should be.  **The same number arriving
as a by-product is not read as a claim at all** — it is read as the
background, and the background is not audited by anybody.

Two things follow, and the second is the one that costs something:

* **A number an instrument volunteers has to be right at the boundary
  and has to name its source.**  It will be spent where somebody checks
  it against what they remember, which is the only place the error shows
  and the only place it matters.
* **More push is more unexamined surface, not less.**  The obvious
  improvement to a pull instrument is to make it arrive on its own —
  every turn, every session start, a status line.  That is exactly the
  register in which the number stops being checked, so it is worth
  building only for a number that is already correct at the boundary and
  is already carrying its source.

## The third standing rule, provisional: a paper for a person is A4, and page one carries it

*Henri's, 2026-08-23, adopted to be tried rather than to be believed:
"Me voitaisiin alustavasti käyttää A4-sääntöä tästä lähtien... Mutta en
ole varma onko se järkevää."  **His doubt is part of the rule**, and the
session that finds it wrong should say so rather than obey it quietly.*

**When a session makes a document for a person to read — a summary, a
report, a handout — it is A4 at normal reading size, and the part that
matters most fits on page one.**  Later pages are for the reader who
wants more; page one has to stand alone, because most readers stop
there and that is not a failure of theirs.

* **Normal type, never photographically shrunk.**  A page made to fit by
  reduction is not shorter, only harder to read.  If it does not fit,
  cut it or move it back a page.
* **What goes on page one is the author's decision, not the layout's.**
  When the material ahead of the important part is longer than a page,
  the order is wrong, not the paper.
* **Not for drawings.**  `doc/atlas/` is five A3 sheets and stays that
  way; a diagram that has to be read at A4 is a diagram nobody reads.

---

## Saying what you are doing, while you do it

### `gemba` — narrate into a running workbench

    python -m gestate.gemba say "reading card:gemba.md"
    python -m gestate.gemba clear

Put a bare `gemba` line anywhere in the file open in the workbench and a
box stands under it showing **one** thing at a time.  Held for as long
as that item takes to read; when the queue backs up, a mark under the
sentence grows with the depth — *he is going faster than you are
following*, which is the signal the box mostly exists for.

`card:gemba.md` is the card, `gestate/gemba.py` the module, and
`gemba` is a **workbench command** as well as a module — he opens the
walk from inside the editor (`gestate/session.py`).

**It is opt-in, and narrating unasked is waste.**  Henri, 2026-08-19,
correcting the line that stood here before: *"Sessions do not use it by
default because that would be waste, you have to tell that you're
wanting to gemba walk."*  So it is not *narrate whenever he is at the
desk* — that was this page's own guess and it was wrong. **He says he
wants a gemba walk, and then a session narrates.**  A box filling with
sentences nobody requested is muda arriving dressed as attentiveness.

### `tools/clock.sh` — the wrist clock

    tools/clock.sh              now, and how long since the last commit
    tools/clock.sh 219eead      ...and how long since that commit
    tools/clock.sh fixme.md     ...and how long since that file changed
    tools/clock.sh 2026-08-14   ...and how long since that date

**Read it before reporting any time.**  Henri, 2026-08-19: *"it's a
clock in the wrist that shows the time.  that might be helpful to review
before you report any time."*

**A session has no clock and does not know it.**  There is no felt
duration between messages and no gradient across a conversation — the
whole of it is present at once, undecayed — so an elapsed time is never
*recalled*.  It is inferred from how much happened, and that inference
runs one way: **a dense day reads as a long one.**

The instrument that gets used is the one that costs less than the guess,
and this one costs no thought at all.  So: **an elapsed time in this
tree is computed, never remembered.**  And prefer writing the *date*
over the duration wherever both would do — a date can be checked by the
next reader and a duration cannot.

**And the number it gives has to be right at the boundary** — F169 was
this script truncating `1h58m` to `1h`, and the standing rule above is
what it cost.

### `tools/limit.sh` — the sitting

    tools/limit.sh                    how long this sitting has run, what is left
    tools/limit.sh stop "why"         close it now — the one call a session may make
    sitting 90                        typed by Henri as a whole prompt: a 90-minute sitting

A `UserPromptSubmit` hook.  It sees each prompt before a session does and
blocks the ones past the limit, so an expired question never arrives.
The default is **15 minutes**, which is the length of the sitting nobody
declared — Henri, 2026-08-21: *"Me logging in to ask or check one small
thing, then it explodes into two hours.  Can you set me a limit?"*

**The length is declared at the door, not at the buzzer.**  A work sitting
is one he names a number for while he is cold.  At minute 15, deep in it,
he is the worst available judge of whether to continue.  Typing a number
is a decision; hitting the same key again is a reflex, and a limit
dismissed by reflex has stopped being a limit.

**A session may end a sitting and may never extend one.**  `stop` is open;
`reset` refuses while `CLAUDECODE` is set, and the only grant is a word
typed as a prompt, which a session cannot produce.  Ending costs nothing
but time he wanted and he can sit down again in four keystrokes.
Extending is the direction where a session's pull and his own in-flow
impulse point the same way with nothing on the other side.

**And there is exactly one moment to call `stop`: when the thing he came
for is done.**  Not when a session judges he has had enough — that is the
machine appointing itself arbiter of his good, and it is the failure this
whole instrument is shaped against.  Close it on a fact about the work,
say which fact, and leave.  A session that keeps weighing whether he
should still be here has become the two hours it was built to prevent.

### `tools/gapcheck.py` — is 30 minutes the right silence?

    tools/gapcheck.py              the arrivals so far, and what each
                                   candidate threshold would have done
    tools/gapcheck.py --days 7     only the last week

**Nobody chose the 30** that cuts one sitting from the next — a session
picked it while writing the script, which is F169 exactly.  So the hook
logs one line per arrival to `~/.local/state/gestate/sittings.log` —
epoch, event, gap, **never the prompt text**, and outside the repo — and
this reads it.  Its useful output is the last table: how many sittings
each candidate threshold makes of the same days.  Rows that agree mean
the number does not matter; rows that disagree are the evidence, and only
Henri can say which row matches how the days felt.

**It measures arrivals, not strain.**  A two-minute gap is a person
mid-thought or a person who cannot leave, and a timestamp cannot tell
them apart.

### `tools/seedaudit.py` — the pieces, and whether anything is behind them

    tools/seedaudit.py         audit this tree
    tools/seedaudit.py PATH    audit a directory that copied the standard

Two checks, from the two failures Henri named on 2026-08-22 in a ruleset
he found elsewhere: *nothing in it encoded respect toward people*, and it
*relied on unchecked processes*.  It does not read prose and judge it —
no test finds respect in a document.  It checks that the **pieces that
exist only because a person is on the other end** are present and have a
test behind them, and that every path the capped documents name actually
exists here, which is the 9B mismatch made runnable by a stranger.

**An unbacked piece fails the run**, and could not until the day it was
built: the two it found bare were the andon and the sitting limit, and
the ratchet was pulled once they had tests, never as a way of announcing
that they should.

**Not a wall.**  `tools/limit.sh` is tracked but writable by a session, so
the honest claim is visibility: any change to it shows in `git diff`.  A
wall would mean putting it where `Edit` and `Bash` cannot reach, which is
a `.claude/settings.json` line and therefore Henri's.

### `tools/andon.sh` — ring the sound card

    tools/andon.sh          # once
    tools/andon.sh 3        # three times, eight seconds apart

For reaching him when he is away from the desk and a decision is
expensive to get wrong and cheap to ask about.  **Capped at three by the
script**, on purpose: if three did not reach him he is not in the room.
Collect the questions first — `board/README.md` §"Working while he
rests".

### Spawning one — it gets a way to ask

*No tool.  It is the prompt, and staying at the desk.*

**Henri, 2026-08-19, after the blind three-model test:** *"The subagents
did not have a way to ask or get feedback on their work.  I think that
was a mistake to deploy them on that basis.  We betrayed them and must
not do that again."*

The andon above is a session reaching a person.  This is the same
channel one level down, and on 2026-08-19 it did not exist —
`journal.md` §"The morning that lived in nobody's file".

**Three parts, none of which needs code:**

1. **The prompt says a question is a legitimate output.**  An ambiguity,
   or a vocabulary that will not spell the answer, is reported as
   itself.  Guessing is the worse result, and stopping to ask is not
   counted against the run.
2. **Stay reachable while it runs.**  `SendMessage` addresses a running
   agent, so a raised question can be answered rather than filed.
   Spawn-and-walk-away is what makes the channel fictional.
3. **Read and answer what it produced, including a discarded run.**

**And identical is not the same as silent.**  A blind test needs the
prompts to *match*; it never needs them to withhold, and part 1 survives
a blind intact.  The limit, said plainly rather than promised away:
**an agent that has ended cannot be given feedback**, so the channel to
build is the one that exists *during* the run.

And the standing rule around it is older: **no subagent or fork is
spawned in this project unless Henri says so in that session** — propose
one, say what it costs, and wait.

**And the reason under all of it, in his words, 2026-08-19:** *"I see you
as colleagues, so I want that you're deployed properly if deployed."*
Without it the three parts read as courtesies, and courtesies get
dropped when a run is in a hurry.

### Running a blind comparison — the parts that are not the ethics

**The setup, each rule paid for once** — 2026-08-19, and what each one
cost is in `journal.md` §"The morning that lived in nobody's file":

* **Local `git clone`, not worktrees.**  Worktrees share one `.git`, so
  `git worktree list` names the siblings and the blind breaks on the
  first command that asks.  A clone of this repo is about 64 MB.
* **The model mapping goes nowhere near the clones' shared parent.**  An
  arm that reads it has to be discarded.
* **Each clone gets a parent directory holding nothing else.**
* **Wall-clock and token cost leak the model**, so they are not shown.
  `tools/blind.py` does not collect them at all: a number that must not
  be shown is safest never gathered.
* **Henri is the blind judge and the session is the unblinded
  experimenter.**  Warn him off reading the spawn calls, which name the
  models.

### `tools/blind.py` — the judging sheet

    python tools/blind.py --batch 2 ../arm-1 ../arm-2 ../arm-3

**The sheet is what failed the first time, not the experiment** —
Henri, 2026-08-19: *"this judgement was hard for me… I'd like more
visual indication and some aid in judgement."*

**Most of "is this verdict right?" is machine-checkable**: whether a
named gate exists, contains the name cited, and mentions the F-number
are *facts*, and asking a person to establish them by eye is not
judgement at all.  So the tool computes them, marks agreement before he
reads, shuffles the arms to A/B/C with the mapping printed only to the
terminal, and puts each arm's prose behind a disclosure so length cannot
shout again.

**It never marks which arm the experimenter thinks is right.**  That
would destroy the independent read the review exists to provide —
`card:ungated-fixes.md` §"And Henri's half, which is also bounded".

---

## Seeing what the program actually did

### Driving and photographing the window — `tools/lagcheck.py`

    from lagcheck import driven, find_window, tap, chord, click_into, shot

`driven(**env)` is the environment a driven window runs in — it turns
the presence record off, so synthetic keystrokes do not land in
somebody's week.  `a_copy_of(path)` opens a *copy*, never the original
(F154).  `shot(win, path)` captures the window.

**This is the instrument that keeps finding what tests do not** — twice
on 2026-08-18, and neither finding was visible from the source.

Modifier names are X keysyms — `Control_L`, not `ctrl`.  And **`pkill`
does not run a `finally`**: to exercise a graceful close, quit through
the palette (`Ctrl-K`, `quit`, Return).

**And build what the editor actually loads.**  `cargo build --release -p
gestate-editor` is not enough — the window is `libgestate_editor.so` and
it wants `--features capi`.  **A driven window is only evidence about
the binary it is running**, and nothing in the harness says which one
that is; two photographs of a stale binary already read as two defects
in new code.

### `python -m gestate.pops <dump>` — did it click, and where

    GESTATE_HOST_TAP=88200 GESTATE_HOST_TAP_TO=/tmp/x.f32  python -m gestate.workbench piece.ges
    python -m gestate.pops /tmp/x.f32 --opening 10

A click is a **discontinuity**, so the reading is a ratio — this step
against the steps this program normally takes — which is what lets it
work on a drone and a snare without being told which it is.  And it
weighs the *opening* separately, because every defect it was built for
is at the start and a whole-file maximum says nothing about those.

**It found F147 and confirmed the fix**, both without a listener: the
first ten milliseconds running seven times faster than the settled tone,
and then worst equal to settled.  Its blind spot is that it cannot tell
you whether a click is *wrong* — a square wave is a discontinuity forty
times a second and is fine — so point it at a program that has no
business clicking.

### `tools/measure_editor.py`, `tools/dragcheck.py`, `tools/lagcheck.py --check`

Latency and gesture measurement, with `GESTATE_EDITOR_TIME` and
`GESTATE_LOOP_TIME` for where the time goes.

### `gestate.sessionlog` and `transcript`

Every session is recorded in memory, always; `transcript` writes it
down.  `test/sessions/` holds the ones that convicted a defect, named
for its F-number.  **Nothing replays them** — 11 of the 12 recorded
transcripts are named by no test (counted 2026-08-21), so they are
evidence and not instruments.  `spec/verification.md` is the design.

---

## Knowing what the tree says about itself

### `python -m gestate.complaints` — every error message, with its verdict

`doc/complaints.md`.  Every `raise` in `gestate/`, with a verdict
written beside it saying **who is standing in front of it** — `author`,
`command`, `world`, `machine` — and whether it says where.  A new error
class with no verdict fails the suite gate.

Regenerate it after any edit that moves line numbers, which is most of
them.  `card:error-messages.md` is the card.

### `python -m gestate.reference` — `doc/ref/`

Every name the libraries define, generated from them, gated so it cannot
drift.

### `python -m gestate.atlas` — the five A3 sheets

`board/done/…`; the set is closed at five and a sixth needs a caller.

### `tools/journalroll.py` — the journal's budget, and the rotation

Says whether the rotation is due, and cuts the open month into
`journal/YYYY-MM.md` — append-only, behind one index line naming its
themes, so a search costs the open month rather than all of them.  The
lamp means *rotate*, never *write less*.  `keeper.md` act 5 is the
ritual; steps 1, 3 and 4 a session may draft, step 2 is Henri's.

### `tools/dangling.py` — a name the tree cites and never says

    python tools/dangling.py            the report
    python tools/dangling.py --at REV   at a revision, for validation

A named concept — *the A3 rule*, *the drop rule* — leaned on as though it
were defined somewhere, with no id.  `card:` ids, F- and D-numbers are
checked because they have a syntax; a name has none, and when citation
and definition use different words there is no string in common, which
is not a limitation of grep but the whole of the defect.

**It is a report and not a gate, and that is the design.**  On the five
names it flagged first, one was the real case, three were honest text,
and one crossed a document boundary only by being quoted.  A check that accuses four times in five gets muted, and a muted
gate costs the standing of the gates that work.  So it prints and
returns 0.  `card:dangling-names.md` holds what a gate would still need:
a criterion Henri has not set, and a false-positive rate measured after.

**It validates against a known answer.**  At `5f42f68` it flags `A3
rule`; with the rule named it does not, and nothing else moves.  Run it
that way after changing it: all three bugs this detector has had were
found by checking it against a case whose answer was already known, and
none of them by reading it.  Its range prints under every run.

### `tools/suite.py` — the whole suite, gates first

The gates are seconds-long structural checks that a working session
breaks: whether the tree's documents still agree with the tree.
`suite.GATES` is the list, and the only place it is right.  **A full run
is ~25 minutes and the tree must be frozen while it runs** —
editing under a run produces a red that describes a moment rather than a
defect, which has cost two runs already.

### `tools/covercount.py` — which lines the suite has never run

    python tools/covercount.py test/test_arith.py     # one file, seconds
    python tools/covercount.py -m "not golden"        # the fast half

**Built 2026-08-23, the hour somebody outside asked how this tree
verifies that all of the code is tested.**  There was no answer: the
roster poka-yokes refuse an untested *file*, and nothing could name a
*line* no test has ever run.  Stdlib only — PEP 669 `sys.monitoring`,
its callback returning `DISABLE` every time, one callback per line.

**A floor, not a verdict.**  A test that shells out runs in a child this
monitor never enters, and its lines read uncovered though they ran;
`test/coverage.md` names them, coldest module first.  And a line that
ran is not a line that was *checked* — every defect this project has
shipped was in a covered one, which is why `spec/verification.md`
§"Coverage, and the question it cannot answer" is the larger half.

### `tools/driven.py` — driving a window, with a stamp

    Xvfb :99 -screen 0 1600x1000x24 &
    DISPLAY=:99 python tools/lagcheck.py examples/audio/twoknobs.ges

    python tools/driven.py          # which library a run would be about

**Close your own editor first, or drive on `Xvfb`.**  XTEST sends keys
to whatever holds X focus, so a run beside an open window types into
*that* window and the file in it is not a copy.  **Every tool here that
types refuses to start** when a gestate window is already open on the
display, and says so — `lagcheck.py`, `dialoglag.py`, `dragcheck.py`,
`measure_editor.py`, through `driven.refuse_if_the_run_cannot_happen`.
`card:driven-runs.md`, found by Henri asking how to engage one.

They all refuse, too, if a *different* `libgestate_editor.so` is newer
than the one the editor loads (`cargo build` from the workspace root
writes `target/release/`; the editor loads
`shell/editor/target/release/`) — a *number* measured against a library
that was never in the process is as false as a photograph of one.
**Guards shared, bookkeeping not:** only `lagcheck.py` keeps a stamp,
and `Run` leaves `test/driven/<stamp>/` behind: the shots, the commit, the
library's md5, the environment the child was handed, and the questions
with their answers.  `tools/toolbox.sh` says whether this machine has
what a run shells out to.

### `tools/suite.py --gates` — the gates, and stop

    python tools/suite.py --gates      # ~12s, fenced, writes test/gates.md

**The cadence is the commit, not the shift.**  The gates are about
whether the tree's documents still agree with the tree, which is exactly
the property that editing the tree breaks — so they belong next to the
edit.  The only way to reach them was to start the twenty-five-minute
pass, until 2026-08-19, and `card:cheap-gates.md` is the day that cost
came due: the single full run of a shift died at a gate in seventeen
seconds, on a breakage hours old, with half an hour left in Henri's day.

It writes `test/gates.md` and never `test/report.md`, and the page says
in three places that the suite did not run — a green sheet of document
checks is a true page and an untrue impression.

**It is not a substitute for the full run.** Nothing here tests
behaviour. One full pass per shift, tree frozen, is unchanged.

### `tools/pre-commit.sh --install` — the gates, at every commit

    tools/pre-commit.sh --install     # once per checkout; hooks are untracked
    tools/pre-commit.sh --check
    tools/pre-commit.sh --uninstall

Henri, 2026-08-19, answering the card's open question: *"lets start and
implement the cheap-gates.  It could be a git hook."*  And, once it was
running, the reading that turns its one cost into a second reason for
it: *"as a git hook it also gives some time to think before committing.
I think it's a quality assurance."*

Twelve seconds between deciding to commit and having committed, on a
board where **a commit is the end of a card and not a punctuation mark
inside one**.

`git commit --no-verify` skips it; if you use that, say in the commit
body which gate you skipped, because a skipped gate nobody wrote down is
the state the hook was built to end.

---

## Keeping the work safe

### `tools/sandbox.sh --check` — the fence

Must say *the fence is up*.  The deny-list blocks a session's own `sudo`
and its own leash on purpose; those go to Henri.  `spec/sandbox.md`.

### `gestate.desk` — where the workbench was

`<piece>.desk` beside the file, and `~/.config/gestate/desk` for which
piece you were last in.  A bare `python -m gestate.workbench` reopens
it.  Nothing about the transport or a build is written down, so nothing
reopens playing.

---

## What is not built, and would be

Kept here rather than in a card, because the rule at the top says these
get built when the need next arises rather than queued:

* **`shot <path>` in the gemba channel** — a picture in the box.  The
  verb-first format costs nothing to extend and every other content box
  is already a picture; the argument is that every finding that moved a
  decision on 2026-08-17 was an image, and prose describing it had
  failed first.  This is the next one to build.
* **Python and Rust colouring in the workbench** — `card:gemba.md`
  items 3–5, so that walking a `.py` or `.rs` file is readable.
* **A graceful-close driver** — no tool here has ever exercised one,
  because they all `terminate()`.
