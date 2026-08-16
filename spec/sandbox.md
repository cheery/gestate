# sandbox.md — what an unattended run is allowed to reach

Companion to `manifesto.md`.  Rule 2 there says a thing that is built
must be able to say when it is wrong.  This file applies it to the
machine: **a sandbox that has not proved its own fence is a mood**, and
the proof is `tools/sandbox.sh --check`.

Written 2026-08-16, when the question "can an agent run here unattended"
was first asked seriously.

---

## The two threats, which are not the same

They get conflated, and the countermeasures are completely different.

**A. Dependency code executes.**  `cargo build` runs build scripts and
proc-macros as arbitrary code at compile time — `cc`, `ctor`,
`bytemuck_derive`, `drm-sys`, `jni-sys-macros` are all in the set, and
**133 crates** resolve behind the four direct dependencies
`shell/editor` and `shell/panel` declare.  `pytest` imports whatever is
importable.  None of this needs an attacker who knows the project
exists; one bad patch release upstream is enough.

*Countered by:* the lockfile, now tracked (`.gitignore`, and the comment
there explaining which rule expired and when), and the fence below.

**B. The agent is steered.**  Text the agent reads — a file from a
friend, a dependency's README, a web page — contains instructions, and
the agent follows them.  `incoming.txt` is the live example: fifty lines
of outside material sitting untracked in the working tree.

*Countered by:* the permission deny-list in `.claude/settings.json`, the
GitHub branch protection on `main`, and the reading rule below.  **Not**
countered by the fence — a steered agent inside the fence still has the
project, which is the thing worth protecting.

The fence is for A.  The deny-list and branch protection are for B.
Neither substitutes for the other.

---

## The fence

`tools/sandbox.sh` runs a command with the project as its whole world:
`$HOME` is an empty tmpfs, so `~/.ssh`, `~/.claude`, `~/.aws` and
`~/.gnupg` are not denied — they are *not there*.  `/usr` is read-only,
there is no network, and the only writable paths are the project and
`/tmp`.

    tools/sandbox.sh pytest -q
    tools/sandbox.sh cargo build --offline
    tools/sandbox.sh --net cargo fetch    # network, only when you mean it
    tools/sandbox.sh --check              # prove the fence before trusting it

### It does not work out of the box on Ubuntu 24.04, and the way it fails is the point

`kernel.apparmor_restrict_unprivileged_userns = 1` blocks unprivileged
user namespaces.  Every unprivileged sandbox needs one.  The two
candidates fail differently, and the difference is the lesson:

| | how it fails |
|---|---|
| `bwrap` | **loudly** — `setting up uid map: Permission denied`, nothing runs |
| `systemd-run --user` | **silently** — the unit starts, `ProtectHome=tmpfs`, `PrivateNetwork=yes` and `ProtectSystem=strict` are all *accepted*, none are *applied*, and the command runs with the SSH key readable and the network up |

The second was measured, not assumed.  A probe that only asked "does
systemd accept this property" returned eight of eight supported and
proved nothing whatsoever.  Reading the key inside the supposed fence is
what settled it.

So: **bubblewrap, and `--check` before trusting it.**  Enable it with
`tools/apparmor-bwrap.profile` — one binary granted `userns`, narrower
than turning the sysctl off system-wide or making `bwrap` setuid:

    sudo install -m 644 tools/apparmor-bwrap.profile /etc/apparmor.d/bwrap
    sudo apparmor_parser -r /etc/apparmor.d/bwrap
    tools/sandbox.sh --check

`--check` runs thirteen probes and exits non-zero if any disagrees.
Until it prints *the fence is up*, there is no fence.

Two of the thirteen are worth naming, because the obvious versions of
them are wrong:

* **`$HOME` is writable, and must be.**  It is an ephemeral tmpfs —
  cargo, pytest and git all write to a home directory, and a read-only
  one breaks them.  The property that matters is not that it cannot be
  written but that it is *not the real home* (checked by the absence of
  `.bashrc`) and that writes to it *do not survive* (checked by writing
  a sentinel inside and looking for it **outside**).  The first draft of
  this check asserted `$HOME` was unwritable, which the fence correctly
  failed.
* **The escape probe runs outside the sandbox.**  A sandbox cannot be
  trusted to grade its own escape; the only honest place to look for a
  leaked file is the filesystem it would have leaked into.

---

## The reading rule

**Untrusted content does not enter an unattended run.**

Content is untrusted when it did not come from this repository's history:
a file from a friend, a downloaded example, a pasted table, anything in
`incoming.txt`.  Such a file is read *interactively*, with a person
present, and what survives the reading is committed in the person's own
words.  It is never left in the working tree for an automode run to pick
up.

The pre-flight, which is the whole enforcement:

    git status --porcelain      # must be empty before an unattended run

An automode run starts from a clean tree.  If that command prints
anything, the run does not start until the output is either committed or
removed.  This is deliberately cruder than a rule about *which* files are
dangerous — a rule that requires judgement about each file is a rule that
fails on the day judgement is tired, which is exactly the day automode is
being used.

---

## What the deny-list covers, and what it does not

`.claude/settings.json` denies fifty patterns: `git push`, `git reset
--hard`, `git clean`, history rewriting, every package installer, `curl`
and `wget`, `sudo`, `ssh`, and reads of `~/.ssh`, `~/.aws`, `~/.gnupg`
and `~/.claude`.  It also denies edits to `./.claude/**` and
`./.gitignore` — **an agent that can edit its own leash does not have
one.**

What it is: defence in depth, and a statement of intent that is cheap to
audit because it is one file in the tree.

What it is not: a boundary.  Shell patterns can be evaded by anything
that composes a command a different way, and the list is prefix-matched.
The two controls that actually hold are outside the agent's reach
entirely:

* **Branch protection on `main`** — force-push and deletion blocked at
  GitHub.  The canonical history survives anything that happens locally.
  This is the one that matters most, and it is the reason the answer to
  "what is the worst case" is *lose a working tree*, not *lose the work*.
* **The fence**, once `--check` passes — because a build script cannot
  read a key that is not mounted.

---

## Status, 2026-08-16

| | |
|---|---|
| `Cargo.lock` tracked | **done** |
| Branch protection on `main` | **done** |
| SSH key passphrase | **done** |
| Deny-list, `.claude/settings.json` | **done** |
| `tools/sandbox.sh` written, `--check` written | **done** |
| AppArmor profile installed, `--check` passing | **done** — thirteen of thirteen, *the fence is up* |
| `postfix` narrowed to `loopback-only` | **done** — port 25 no longer binds a public interface |
| `ufw` actually running | **open** — see below |
| Full-disk encryption | **waits on the machine switch** — it wants a fresh install, and retrofitting LUKS is the one item here that a new laptop genuinely buys |

### One measurement that was made twice, and got it wrong the first time

`systemctl is-enabled ufw` returns `enabled`.  That reports whether the
**unit starts at boot**, not whether the **firewall is up**; `ufw status
verbose` reported `passiivinen` — inactive — and had all along.  A
finding of "port 25 is exposed" was raised, then withdrawn on the
strength of the wrong command, then reinstated when the right one was
run.  The withdrawal was the error, and it is recorded here rather than
deleted for the same reason `fixme.md` entries are closed by marking
them: **a check that answers a neighbouring question is worse than no
check, because it carries the confidence of one that answered this
one.**

Remaining externally-bound listener: `kdeconnectd` on 1716/1717.
