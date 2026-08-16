#!/usr/bin/env bash
#
# toolbox.sh — the bench tools: what is here, and what is missing.
#
# **Not the install.**  `README.md` and `doc/install.md` say what gestate
# needs to *run*; nothing in this file is required to build a program,
# hear one, or pass the suite.  What is here is the other half — the
# tools that let a claim about the window be *checked* rather than
# reasoned about.  The editor is a real window on a real display, and
# without these the only way to see what it drew is to ask the person
# using it for a screenshot.
#
#     tools/toolbox.sh              # say what is here and what is not
#     tools/toolbox.sh --install    # fetch what is not
#
# Reports and installs are the same list read twice, so a machine that
# says it is ready is ready for the reason it printed.  Exits non-zero
# when something is missing, which makes the report usable as a gate.

set -euo pipefail

here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)

# The interpreter the suite runs under, which is where pip must put
# things — a `pip install` that lands in the system Python is a package
# the tests cannot import, and it looks exactly like a successful one.
if [ -n "${VIRTUAL_ENV:-}" ]; then
    py="$VIRTUAL_ENV/bin/python"
elif [ -x "$here/.venv/bin/python" ]; then
    py="$here/.venv/bin/python"
else
    py=$(command -v python3 || true)
fi

install=0
case "${1:-}" in
    "")            ;;
    --install|-i)  install=1 ;;
    --help|-h)     awk 'NR>2 && /^#/ { sub(/^# ?/, ""); print; next }
                        NR>2 { exit }' "${BASH_SOURCE[0]}"
                   exit 0 ;;
    *)             echo "toolbox: unknown argument \`$1\`" >&2; exit 2 ;;
esac

# apt wants root; everything else does not.  `sudo` is named out loud
# rather than assumed, because a script that silently escalates is a
# script nobody reads twice.
as_root() {
    if [ "$(id -u)" = 0 ]; then "$@"
    elif command -v sudo >/dev/null; then echo "  sudo $*"; sudo "$@"
    else
        echo "  cannot install without root; run this yourself:" >&2
        echo "    sudo $*" >&2
        return 1
    fi
}

# Colour when a person is reading, plain when something else is.
if [ -t 1 ]; then ok=$'\033[32m'; no=$'\033[33m'; off=$'\033[0m'
else ok=; no=; off=; fi

missing=0
report() {  # report <name> <have?> <what it buys> <how to get it>
    local name=$1 have=$2 buys=$3 how=$4
    if [ "$have" = yes ]; then
        printf '  %s✓%s %-14s %s\n' "$ok" "$off" "$name" "$buys"
        return 0
    fi
    printf '  %s·%s %-14s %s\n' "$no" "$off" "$name" "$buys"
    printf '    %-14s → %s\n' "" "$how"
    missing=$((missing + 1))
    return 1
}

have_py() { "$py" -c "import $1" >/dev/null 2>&1 && echo yes || echo no; }
have_bin() { command -v "$1" >/dev/null 2>&1 && echo yes || echo no; }

echo "the bench, at $here"
echo "python: ${py:-none found}"
echo

# ── A display of the tests' own ──────────────────────────────────────
#
# `test/test_editor_abi.py` opens real windows, because the boundary
# between a Rust-owned rope and a Python orchestrator is what there is
# to test and a fake window tests the fake.  On a workstation those
# windows arrive over whatever you are typing into.  With Xvfb the
# suite gets a display nobody is using:
#
#     xvfb-run -a python -m pytest test/test_editor_abi.py
#
# `DISPLAY=:0` still works and is still what you want when the point is
# to *watch* — `tools/lagcheck.py` measures a real one.
if ! report xvfb "$(have_bin Xvfb)" \
        "a display of the tests' own, so windows stop landing on yours" \
        "apt install xvfb" && [ "$install" = 1 ]; then
    as_root apt-get install -y xvfb
fi

# ── Pressing keys, and looking at what came back ─────────────────────
#
# XTEST synthesises a keystroke the window cannot tell from a hand's;
# `tools/lagcheck.py` reaches it through hand-written `ctypes` today,
# which is fine for two calls and thin for a session.  The half that is
# missing entirely is *reading the window back*: `XGetImage` over the
# editor's own window turns "the panel sits at the top" from something
# argued into something seen.  F121's placement rule, the palette's
# prompt, the score box's ink — every one of those is currently checked
# by reasoning about the code that draws it.
if ! report python-xlib "$(have_py Xlib)" \
        "XTEST keys, and reading the window's pixels back" \
        "pip install python-xlib" && [ "$install" = 1 ]; then
    "$py" -m pip install python-xlib
fi

# ── Holding an image still ───────────────────────────────────────────
#
# What a capture is saved and compared as.  Nothing in `gestate/` or
# `test/` imports it and nothing should start: it belongs to the bench,
# beside the measuring scripts, the same way numpy is welcome in a
# scratch measurement and not in the repository (`requirements.txt`
# says so, and means it).
if ! report pillow "$(have_py PIL)" \
        "saving and cropping what was captured (bench only, never imported)" \
        "pip install pillow" && [ "$install" = 1 ]; then
    "$py" -m pip install pillow
fi

# ── Looking at the atlas ─────────────────────────────────────────────
#
# `python -m gestate.atlas` draws the project on an A3 sheet, and an
# `.svg` is a file many readers cannot open — a terminal, a diff, an
# assistant reading over your shoulder.  With this, the same command
# leaves a `.png` beside it in about a second.
#
# **The `.svg` is the artefact and this is a convenience**: the atlas
# is written and checked without it, and `gestate/atlas.py` falls back
# to `rsvg-convert`, `resvg` or Inkscape if one of those is what this
# machine has.  Inkscape does the job at two and a half seconds a call,
# being a whole editor asked to convert a file; `cairosvg` is a pip
# install into the interpreter the suite already runs under, and
# renders this sheet identically.
if ! report cairosvg "$(have_py cairosvg)" \
        "the atlas as a .png, so it can be looked at anywhere" \
        "pip install cairosvg" && [ "$install" = 1 ]; then
    "$py" -m pip install cairosvg
fi

echo
if [ "$missing" = 0 ]; then
    echo "the bench is ready."
    exit 0
fi
if [ "$install" = 1 ]; then
    echo "installed; run \`tools/toolbox.sh\` again to see it."
    exit 0
fi
echo "$missing missing — \`tools/toolbox.sh --install\` fetches them."
exit 1
