# reviewing-by-running — the editor runs code nobody has read yet

    status   open
    because  I tend to run the workbench along reading the commits.
             It allows me to quickly check if anything was missed.
             Tests have not catched all the bugs, but a simple visual
             check along them has done a lot.
             Also, the workbench seem to become my new working
             environment. I am retiring the gvim&vim soon.
    asked    Henri, 2026-08-17
    see      tools/sandbox.sh — the fence, and `--check`
             spec/sandbox.md, doc/hardening.md — the argument
             gestate/editor.py `_stale` — the editor rebuilds itself
             card:timer.md — whose record the fence would erase

## The ask

> Could also the running workbench instance be guarded by the new fence
> such that it works on my end?

## Found by looking, before it was taken

**The `because` is the strongest part of this card and it is not the
security one.**  `tools/sandbox.sh` exists because *"`cargo build`
executes build scripts and proc-macros as arbitrary code … and `pytest`
imports whatever is on the path"*.  Henri's reason is the same fact
arriving from the other side: he opens a session's fresh commits **in a
program that compiles and runs them**.  `editor.py::_stale` re-runs
`cargo` when the crate moves, and every save runs `clang`.  So the
thing the fence was built against is already inside the editor, and the
editor is becoming the place he works.

### It works.  Measured 2026-08-17, on his machine

A fenced X client reaches the display with four additions to
`tools/sandbox.sh`'s fence:

```
--ro-bind /tmp/.X11-unix /tmp/.X11-unix     # AFTER --tmpfs /tmp, or it is wiped
--ro-bind "$XAUTHORITY" /tmp/xauth          # the cookie lives in /run/user/1000,
--setenv  XAUTHORITY /tmp/xauth             #   which the fence does not bind
--dev-bind /dev/snd /dev/snd                # the sound card
--setenv  DISPLAY :0
```

Verified inside the fence: `xdpyinfo` answers `name of display: :0`, and
`/dev/snd` lists the cards.  Without the cookie it is *"Authorization
required, but no authorization protocol specified"*, which is the first
thing anybody trying this will hit.

Everything else the workbench needs is already there: `clang` is in the
read-only `/usr`, `/tmp` is a writable tmpfs, and the network is not
wanted.

### What it costs, and the one that decides the card

**Only `$PROJECT` is writable, and nothing else is even visible.**  A
file outside the repository cannot be opened, not merely not saved.
That is arguably a *feature* while the workbench is a tool for working
on gestate — and it is a wall the moment it is his general editor, which
the `because` says it is becoming.  **This is the question the card
turns on**, and it is asked below rather than guessed at.

**The timer's week would be erased.**  `$HOME` is a tmpfs inside the
fence, so `~/.local/state/gestate/presence.tsv` is written into nothing
and gone at exit — the strip would reset every session, silently.  Needs
the state directory bound, or `GESTATE_PRESENCE` pointed somewhere that
survives.  A concrete regression of `card:timer.md`, found before
it happened.

**X access narrows the fence, and Wayland bounds how far.**  His session
is Wayland (`XDG_SESSION_TYPE=wayland`) with XWayland behind
`DISPLAY=:0`, so a fenced process holding the X socket can watch other
**X11** clients — keys, windows — but not native Wayland ones.
`~/.ssh`, `~/.claude` and the network stay out of reach either way.  So
the fence keeps everything it was built to keep and stops being a fence
against a keylogger, for X clients only.  Worth stating in
`spec/sandbox.md` if this ships, because a fence whose limits are not
written down is a mood.

## Questions

**Q (Claude), and it decides the shape.**  When you edit a file *outside*
gestate — once vim is retired — should the fenced workbench be able to
see it?  Three answers, and they are three different cards: **gestate
only**; **the directory the window was started in**; or **a named list
of roots** that get bound.

**Henri, 2026-08-17:**

> I do not know.  This should be probably measured.  How much attack
> surface there is between "the directory you started with" and "gestate
> only".  I could always symlink the data I'm going to work, inside
> gestate.  I think "gestate only" would be sufficient then.

**So this one is still open, and it is open for a reason he named: it
wants a measurement, not an opinion.**  What that measurement is: for
each option, enumerate what becomes readable and writable on his actual
home directory — because that set *is* the attack surface, and the
difference between the two options is a list of files, not a feeling.
It is arithmetic on a directory tree, the same shape as the `git log`
half of the timer.

**But the workaround in that answer does not work, and it was checked
rather than assumed.**  A symlink inside the project is only a path
string; its target has to exist in the *fence's* namespace, and both
`/tmp` and `$HOME` are tmpfs in there.  Measured 2026-08-17: a symlink
in `$PROJECT` pointing at `/tmp/outside-probe` reads fine on the host
and is *"No such file or directory"* inside the fence.

The instinct is right and the mechanism is a **bind**, not a symlink:
`--bind ~/music "$PROJECT/data/music"` does put outside data inside the
fence at a path under the project.  Which makes that workaround a
quieter spelling of option three — so "gestate only" being sufficient
rests on a premise that is false, and the question really is still open.

**Q (Claude).**  Should the fenced run be *the* way the workbench starts
— `tools/gestate-editor` and the `.desktop` entry both going through it —
or a second command you reach for deliberately?

**Henri, 2026-08-17: the default way it starts.**  Which is the right
call and the harder one: it is the only answer that protects the case in
his `because`, since reading commits is the ordinary way he opens it and
a fence you have to remember is off exactly then.  It also means **the
fence becomes load-bearing for the editor starting at all**, so
`sandbox.sh --check` stops being a thing run before a suite and becomes
a thing the editor's own startup depends on.  That belongs in the work:
a failing fence must degrade to a named refusal, not to a window that
does not appear.

## Where it stands

Placed **at the end of the order**, at his ask on 2026-08-17, having
arrived unplaced — even though the `because` describes something he does
today.  His call, recorded here so it is not re-litigated.
