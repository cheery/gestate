# Reading the log — following changes you did not make

Written 2026-08-16, the day auto mode was turned on.

**Why this page exists, precisely.**  The fence (`spec/sandbox.md`) and
the deny-list stop me *damaging* things.  Neither of them has any
opinion about whether what I did was **right**.  That gap is review, and
review is git.  Under auto mode it is the only remaining place a wrong
decision gets caught, which makes it the most valuable hour on the
roadmap.

Every example below is a real commit from this repository, most of them
from one day.  Several are commits where I was wrong, because those are
the ones worth learning to spot.

> **The one idea, if you read nothing else.**  A commit message is a
> **claim**.  The diff is the **evidence**.  Reviewing is checking one
> against the other — and the failure mode is not a lying message, it is
> an *honest* message about a diff that does something slightly else.

---

## 1. One commit

    git show 847a01c

That prints the message, then every line changed.  `-` is what left,
`+` is what arrived.

Reading order that works: **subject → body → diff → back to the body.**
The last step is the review. `847a01c` claims a directory leaked once
per process and that `atexit` now removes it; the diff should therefore
show something registered with `atexit`, and a guard so it does not
delete a directory somebody else owns.  If the diff showed only the
`atexit` and no guard, the claim would be honest and the change wrong.

Just the message, no diff:

    git show -s 847a01c

Just the names of files touched — the fastest way to see whether a
change is where it says it is:

    git show --stat 847a01c

---

## 2. A day

    git log --oneline --since="2026-08-16 00:00"

Thirty-three lines for the day this was written — the day started at
07:13 with the atlas work, and only the last sixteen are the security
work.  That distinction is itself a lesson: the first draft of this page
said "sixteen", because I had the afternoon in mind and did not run the
command.  **Run the command.**

Add `--stat` for the shape of each, or `-p` for every diff in sequence:

    git log --stat --since=yesterday
    git log -p  --since=yesterday        # long; q quits, / searches

`git log` opens a pager: **space** pages down, **q** quits, **/word**
searches, **n** repeats the search.  Append `| cat` to dump it straight
out instead.

---

## 3. Between two points

The most useful question after a day of unattended work is *"what is
different from where I left it?"*

    git diff f2f8a61..HEAD              # everything since last night
    git diff f2f8a61..HEAD --stat       # just the shape
    git diff f2f8a61..HEAD -- tools/    # just one directory

`A..B` is "what B has that A does not".  `HEAD` is where you are now,
`HEAD~1` one before it, `HEAD~5` five before.

And what has **not** been committed yet — my working notes, or your own
edits mid-thought:

    git status              # which files
    git diff                # what changed in them
    git diff --staged       # what is staged and about to be committed

---

## 4. Finding when something changed

When a line is wrong and you want the commit that made it wrong:

    git log -S "GESTATE_FENCED" --oneline        # commits adding/removing that string
    git log --oneline -- tools/sandbox.sh        # every commit touching one file
    git blame tools/leash.sh                     # who last touched each line

`git blame` prints a commit hash per line.  Feed it back to `git show`
and you have the reasoning behind that line, which in this repository is
usually several paragraphs.

---

## 5. Undoing

**Already committed** — make a new commit that reverses it:

    git revert 847a01c

This is the safe one.  It keeps the history, so the mistake and its
reversal are both visible, which is the same principle as `fixme.md`
closing entries by marking them rather than deleting them.

**Not yet committed** — throw away a file's uncommitted changes:

    git restore tools/suite.py          # that file, back to last commit
    git restore --staged tools/suite.py # unstage, keep the edit

**What not to reach for.**  `git reset --hard` discards work with no
record that it existed.  It is denied to me outright
(`.claude/settings.json`), and it should be rare for you: `revert` and
`restore` cover almost everything, and neither can lose an hour you
forgot you had.

Anything committed can be recovered even after a bad reset, via
`git reflog` — but knowing that is not a reason to use the sharp tool.

---

## 6. Reviewing *my* commits specifically

Four questions, in the order they catch things.

**a. Does the diff match the claim?**  This is the whole job.  Take
`b74fa89 the hook, corrected by the command it broke`.  Its body claims
two bugs in the hook — a regex that read `|` inside a quoted string as a
command position, and `jq -Rs` missing its `-r`.  Check it:

    git show b74fa89 -- tools/fence-hook.sh

Two substantive lines change, one per claim.  Good.

Now look at the whole thing:

    git show --stat b74fa89

**Five files.**  The subject says "the hook"; the diff also carries a
`suite.py` rewrite, a new `doc/hardening.md` section, and edits to
`.gitignore` and `.claude/settings.json`.  The *body* does mention all
of them — so this is honest, not sloppy — but the **subject undersells
what landed**, and a subject is what you will actually skim in six
months.

That is the real lesson, and it is a fair thing to hold me to: when a
commit does more than its subject says, ask why the rest was not its own
commit.  Usually the answer is that I was moving fast, which is exactly
when review earns its keep.

**b. Is a number in the message a number I could reproduce?**  This
repository's messages are full of them — *"133 crates"*, *"13/13"*,
*"5 failed, 2426 passed"*, *"before=0 after=1"*.  Every one of those is
a command you can run again.  If it does not reproduce, that is the
finding.

**c. Does it touch anything the subject did not mention?**
`git show --stat` answers this in one screen.  A commit called *"fix a
typo"* touching six files is the shape to distrust — not because it is
dishonest, but because the other five went in without their own
reasoning.

**d. Is the test able to fail?**  A test added alongside a fix should
have been *seen* failing.  `847a01c` says so explicitly — the fix was
disabled and the test reported `leaked at exit: [...]` — and where a
commit does not say that, it is a fair thing to ask me for.

---

## 7. A worked exercise, on this day

Run these in order.  Fifteen minutes, and it covers everything above.

    git log --oneline --since="2026-08-16 00:00"     # 1. the day
    git show -s 5120007                              # 2. read one claim
    git show 5120007                                 # 3. check it against the diff
    git show --stat 8ffdd78                          # 4. does it touch what it says?
    git diff f2f8a61..HEAD --stat                    # 5. the whole day's shape
    git log -S "RUNS_UNFENCED" --oneline             # 6. when did that appear?

`5120007` is a good one to start on, because it is a commit about being
wrong: five tests failed, they looked like a defect in the project, and
they were the fence.  The claim is *"the suite is green; the fence broke
them"* and the evidence is a second, unfenced pass added to
`tools/suite.py`.  Read whether you believe it.

---

## 8. What this does not give you

Git shows what changed, never what was *considered and not done*.  A
commit cannot show you the option I rejected, and the messages in this
repository try to carry that because git will not.

It also will not tell you a change is wrong when it is internally
consistent — a well-argued commit implementing the wrong thing reviews
clean.  That is not a gap review can close; it is why `roadmap.md` says
what to build before anything is built, and why the questions get
batched before an item is taken rather than after.
