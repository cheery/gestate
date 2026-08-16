# Hardening a machine for gestate

Companion to `doc/install.md`, which gets the project *running*.  This
gets it running **safely enough to leave an agent alone with it**, and
it is written as a checklist because it will be followed on a day when
nobody wants to think.

`spec/sandbox.md` is the reasoning — the threat model, what the fence is
for and what it is not for.  This page is only the order of operations
and the commands, each with the check that proves it took.

Established 2026-08-16, on Ubuntu 24.04.

> **Read this before installing the OS, not after.**  Step 0 cannot be
> done later without reinstalling, and it is the one item on this page
> that a new machine genuinely buys.

---

## The rule this page follows

**Every step has a verification, and the verification is a different
command from the one that did the work.**  Three times in one afternoon
a step looked done and was not:

| what was run | what it actually answered |
|---|---|
| `systemctl is-enabled ufw` → `enabled` | whether the *unit starts at boot* — **not** whether the firewall is up.  `ufw status verbose` said `inactive`, and had all along. |
| `systemd-run --user -p ProtectHome=tmpfs …` → starts fine | whether systemd *parsed* the property.  It applied none of them; the SSH key was readable inside the "sandbox". |
| `apt remove kdeconnect` | closes port 1717.  Port 1716 belongs to **GSConnect**, a different program with a similar name, and stays open. |

A check that answers a neighbouring question is worse than no check,
because it carries the confidence of one that answered this one.

---

## 0 — At OS install.  Cannot be retrofitted.

Ubuntu installer → *Advanced features* → **Use LVM and encryption** (LUKS).

Everything else on this page can be done on a running machine.  This one
cannot, and without it every other control is defeated by picking the
laptop up.

```sh
lsblk -o NAME,FSTYPE | grep crypt        # must print a crypto_LUKS line
```

---

## 1 — Before the repo can be cloned

**An ed25519 key, with a passphrase.**  The passphrase is the half that
matters: an unencrypted disk plus a bare key is push access for whoever
holds the machine.

```sh
ssh-keygen -t ed25519 -C "henri.tuhola@gmail.com"     # do not leave it empty
ssh-add ~/.ssh/id_ed25519                              # once per session
```

Add the public half at <https://github.com/settings/keys>, then:

```sh
ssh -T git@github.com                                  # "Hi cheery!"
grep -c ENCRYPTED ~/.ssh/id_ed25519                    # must print 1
```

Then `doc/install.md`, plus two packages it does not need but this page
does:

```sh
sudo apt install bubblewrap ufw
```

---

## 2 — The machine

### 2.1 Firewall on, default deny

```sh
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw enable
```

```sh
sudo ufw status verbose            # "Status: active", "deny (incoming)"
```

Not `systemctl is-enabled ufw`.  See the table above.

### 2.2 Nothing bound to a public interface

```sh
ss -tlnp | grep -vE '127\.0\.0\.|\[::1\]'
```

Anything that prints here is reachable from whatever network you join.
The two seen on the old machine, and their fixes:

```sh
# postfix, port 25 — a dev laptop does not need to accept mail
sudo postconf -e 'inet_interfaces = loopback-only' && sudo systemctl restart postfix

# kdeconnect (1717) and GSConnect (1716) — TWO programs, remove both
sudo apt remove --purge kdeconnect nautilus-kdeconnect
gnome-extensions disable   gsconnect@andyholmes.github.io
gnome-extensions uninstall gsconnect@andyholmes.github.io
```

Simplest of all: do not install them on the new machine.

### 2.2b Remove the allow rules for anything you removed

A rule opened for a program that is now gone outlives it, and `ufw
status verbose` is the only place it shows — `ss` cannot see it, because
nothing is listening.  It costs nothing today and everything the day
another program binds the same range.

```sh
sudo ufw status numbered
sudo ufw delete allow 1714:1764/tcp        # by spec, not by number
sudo ufw delete allow 1714:1764/udp
```

**By spec, not by number.**  Deleting rule 3 renumbers everything below
it, so `delete 3` then `delete 4` removes the wrong rule.  If you must
use numbers, work from the highest down.

The check that catches this is not `ss` — it is reading `ufw status`
and asking *what is each of these still for?*  On the old machine the
answer for two of them was "a program I removed an hour ago".

### 2.3 Let bubblewrap create user namespaces

Ubuntu 24.04 sets `kernel.apparmor_restrict_unprivileged_userns = 1`,
which blocks every unprivileged sandbox.  Grant it to one binary:

```sh
sudo install -m 644 tools/apparmor-bwrap.profile /etc/apparmor.d/bwrap
sudo apparmor_parser -r /etc/apparmor.d/bwrap
```

Narrower than `sysctl kernel.apparmor_restrict_unprivileged_userns=0`
(every binary) or `chmod u+s /usr/bin/bwrap` (setuid root).

---

## 3 — The project

```sh
tools/sandbox.sh --check           # must end: "the fence is up."
```

Thirteen probes; exit non-zero if any disagrees.  **Until it says that,
there is no fence** — and the failure it caught first was its own bad
assumption, not the fence's, so read what it prints rather than the
exit code alone.

Then prove the fence is *usable*, which is a separate question from
whether it is tight:

```sh
tools/sandbox.sh python3 -m gestate.typecheck examples/closure.ges
tools/sandbox.sh pytest -q
```

`cargo` inside the fence has no network by design.  `--offline` is set
for you; when the lockfile genuinely needs refreshing, that is the one
job for `tools/sandbox.sh --net cargo fetch`.

---

## Making the fence automatic

`tools/sandbox.sh` on its own is opt-in, and a protection you have to
remember is one you will forget on the day it matters.
`tools/fence-hook.sh` is a `PreToolUse` hook that rewrites builds and
tests to run inside it.  Add to `.claude/settings.json`:

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        { "type": "command", "command": "/ABSOLUTE/PATH/TO/tools/fence-hook.sh" }
      ]
    }
  ]
}
```

**The path has to be absolute, and it is the one line that differs per
machine.**  Try `$CLAUDE_PROJECT_DIR/tools/fence-hook.sh` first; if the
hook does not fire, substitute the real path.  The script finds the
project from its own location, so nothing else needs changing.

It wraps `pytest`, `python -m pytest`, and `cargo build|test|check|
clippy|bench`.  It deliberately does **not** wrap anything that opens a
window (the fence binds no X11 socket, so those do not fail safely, they
just fail) or `cargo fetch` (which wants the network the fence removes).
`NOFENCE=1 <command>` opts out for one call.

Check it fires, rather than assuming:

```sh
echo '{"tool_input":{"command":"pytest -q"}}' | tools/fence-hook.sh
```

It should print JSON whose `updatedInput.command` begins with
`tools/sandbox.sh`.  If the hook is installed but nothing changes in a
real session, open `/hooks` once — the settings watcher only watches
directories that had a settings file when the session started.

## What does not need doing again

These live in the repository or at GitHub and arrive with the clone:

* **Branch protection on `main`** — force-push and deletion blocked, at
  GitHub.  It is the reason the worst case is *lose a working tree*, not
  *lose the work*, and it is per-repository, not per-machine.
* **`Cargo.lock`, tracked** — 133 crates pinned, so `cargo build` cannot
  resolve a fresh patch release and run its build script.  `.gitignore`
  carries the note about which rule expired and when.
* **`.claude/settings.json`** — the deny-list, including
  `Edit(./.claude/**)`, because an agent that can edit its own leash
  does not have one.

---

## Housekeeping that is not security but bites the same way

```sh
du -sh ~/.cache/* | sort -rh | head       # pip's HTTP cache reached 12 GB
pip cache purge
df -h /                                    # a build needs room to fail in
```

---

## The order, on one line

**LUKS at install → key with passphrase → clone → ufw → close listeners
→ AppArmor profile → `--check` says the fence is up.**
