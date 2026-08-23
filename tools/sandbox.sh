#!/usr/bin/env bash
#: asked-by: Henri, 2026-08-16 — "There is no protection in place, in case there's injection attack or bad luck with dependencies."
#
# tools/sandbox.sh — run a command with this project as its whole world.
#
# **What this is for.**  `cargo build` executes build scripts and
# proc-macros as arbitrary code (`cc`, `ctor`, `bytemuck_derive`,
# `drm-sys`, `jni-sys-macros` — 133 crates resolve behind four direct
# dependencies), and `pytest` imports whatever is on the path.  Both run
# as you, with your keys and your home directory in reach.  This wrapper
# removes the reach: inside it there is no `~/.ssh`, no `~/.claude`, no
# network, and nothing writable except the project and `/tmp`.
#
# It is not a VM.  It is a namespace fence, and the thing it fences is
# *ordinary code doing what it was told* — a poisoned dependency, a
# `build.rs` that curls, a test that writes outside its fixture.  It is
# not a boundary against an attacker who already has your login.
#
# **Usage**
#
#     tools/sandbox.sh pytest -q
#     tools/sandbox.sh cargo build --offline
#     tools/sandbox.sh --net cargo fetch      # network, when you mean it
#     tools/sandbox.sh --check                # prove the fence is up
#
# `--net` keeps the network namespace shared with the host.  Everything
# else stays fenced.  Use it for `cargo fetch` and nothing else: a fetch
# writes the lock, and the lock is the thing being pinned.

set -euo pipefail

PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

command -v bwrap >/dev/null || {
  echo "sandbox.sh: bubblewrap (bwrap) is not installed." >&2
  echo "            apt install bubblewrap" >&2
  exit 127
}

# ── The fence ────────────────────────────────────────────────────────────
#
# Order matters: bwrap applies these left to right, so the tmpfs over
# $HOME lands *before* the two toolchain binds that go inside it.

NET=(--unshare-net)
if [ "${1-}" = "--net" ]; then NET=(); shift; fi

FENCE=(
  --unshare-user --unshare-pid --unshare-ipc --unshare-uts --unshare-cgroup
  "${NET[@]}"
  --die-with-parent
  --new-session                     # no TIOCSTI keystroke injection back at us

  # The system, read-only.  /bin /lib /lib64 /sbin are symlinks into /usr
  # on this machine, so they are recreated as symlinks rather than bound.
  --ro-bind /usr /usr
  --symlink usr/bin   /bin
  --symlink usr/lib   /lib
  --symlink usr/lib64 /lib64
  --symlink usr/sbin  /sbin
  --ro-bind /etc /etc

  --proc /proc
  --dev  /dev
  --tmpfs /tmp

  # A home with nothing in it.  ~/.ssh, ~/.claude, ~/.aws, ~/.gnupg and
  # the rest are not denied — they are simply not there.
  --tmpfs "$HOME"

  # The one writable thing.
  --bind "$PROJECT" "$PROJECT"
  --chdir "$PROJECT"

  --setenv HOME "$HOME"
  # A marker so a program can tell it is already inside.  `test_safety.py`
  # needs it: the fence cannot nest — a second `bwrap` inside the first
  # cannot create the namespaces it wants — so those tests skip rather
  # than fail confusingly when the suite is run fenced.  `tools/suite.py`
  # runs them in its unfenced pass instead, which is the only place they
  # mean anything.
  --setenv GESTATE_FENCED 1
)

# **Toolchain homes, bound only if they exist.**  These are the two lines
# that were project-specific, and binding them unconditionally is what
# would break this script on a machine with no Rust — `bwrap` fails
# outright on a missing source, so an absent `~/.rustup` would take the
# whole fence down rather than degrade.  Add a directory here when a new
# toolchain needs its cache; nothing else in this file knows what
# language the project is written in.
for home in .cargo .rustup .rustup/toolchains .npm .m2 .stack; do
  [ -e "$HOME/$home" ] && FENCE+=(--ro-bind "$HOME/$home" "$HOME/$home")
done

FENCE+=(
  # `.venv/bin` first: the suite's `pytest` lives there, and without it
  # the fence resolves the system one or nothing at all.
  --setenv PATH "$PROJECT/.venv/bin:$HOME/.cargo/bin:/usr/local/bin:/usr/bin:/bin"
  --setenv VIRTUAL_ENV "$PROJECT/.venv"
  --setenv CARGO_NET_OFFLINE true
  --unsetenv SSH_AUTH_SOCK
  --unsetenv GITHUB_TOKEN
  --unsetenv ANTHROPIC_API_KEY
)

# ── --check: prove the fence is up before trusting it ────────────────────
#
# A sandbox nobody tested is a mood.  Each line below is a thing that
# must fail, and the check fails loudly if any of them succeeds.

if [ "${1-}" = "--check" ]; then
  fail=0
  probe () {  # probe <description> <expect: ok|blocked> <command...>
    local desc=$1 expect=$2; shift 2
    if bwrap "${FENCE[@]}" -- "$@" >/dev/null 2>&1; then got=ok; else got=blocked; fi
    if [ "$got" = "$expect" ]; then
      printf '  \033[32m✓\033[0m %-44s %s\n' "$desc" "$got"
    else
      printf '  \033[31m✗\033[0m %-44s expected %s, got %s\n' "$desc" "$expect" "$got"
      fail=1
    fi
  }

  echo "sandbox.sh --check   ($PROJECT)"
  probe "~/.ssh is not readable"        blocked sh -c 'cat "$HOME/.ssh/id_rsa"'
  probe "~/.ssh does not even exist"    blocked sh -c 'test -e "$HOME/.ssh"'
  probe "~/.claude is not readable"     blocked sh -c 'test -e "$HOME/.claude"'
  probe "no network"                    blocked timeout 5 getent ahostsv4 github.com
  probe "/usr is read-only"             blocked sh -c 'touch /usr/.probe'

  # $HOME inside the fence is a writable tmpfs, deliberately: cargo,
  # pytest and git all write there, and a read-only home breaks them.
  # What must hold is that it is not the *real* home and that writes to
  # it do not survive the run.  Both are checked, the second from
  # outside — a sandbox cannot be trusted to grade its own escape.
  probe "\$HOME is not the real home"    blocked sh -c 'test -e "$HOME/.bashrc"'
  probe "\$HOME IS writable (tmpfs)"     ok      sh -c 'touch "$HOME/.probe"'

  bwrap "${FENCE[@]}" -- sh -c 'touch "$HOME/.sandbox-escape-probe"' >/dev/null 2>&1 || true
  if [ -e "$HOME/.sandbox-escape-probe" ]; then
    printf '  \033[31m✗\033[0m %-44s THE WRITE ESCAPED\n' "writes to \$HOME do not escape"
    rm -f "$HOME/.sandbox-escape-probe"
    fail=1
  else
    printf '  \033[32m✓\033[0m %-44s %s\n' "writes to \$HOME do not escape" "confirmed"
  fi

  probe "the project IS writable"       ok      sh -c 'touch .sandbox-probe && rm .sandbox-probe'
  probe "/tmp IS writable"              ok      sh -c 'touch /tmp/.probe'
  probe "python runs"                   ok      python3 -c 'print(1)'
  probe "cargo runs"                    ok      cargo --version
  probe "clang runs"                    ok      clang --version
  echo
  [ $fail -eq 0 ] && echo "  the fence is up." || echo "  FENCE INCOMPLETE — do not trust it."
  exit $fail
fi

[ $# -gt 0 ] || { echo "sandbox.sh: nothing to run.  See the header." >&2; exit 2; }

exec bwrap "${FENCE[@]}" -- "$@"
