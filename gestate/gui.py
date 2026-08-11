"""Run a gestate GUI program — the reactive half, on a screen.

The same shape as `gestate/midi.py`, deliberately:

    music                          GUI
    ────────────────────────────   ────────────────────────────────
    `music.ges`, prepended         `gui.ges`, prepended
    program gives `score`, `bpm`   program gives `substrate : Sig Sub`
    `perform` — pure, tested       `scenes` — pure, tested
    `write` — needs `mido`         `run` — needs `pygame`

`scenes(source, events)` is the whole backend as far as correctness goes: it
feeds a list of events in and hands back the picture after each one.  It
imports nothing outside gestate, so the tests never open a window.  `run` is
a pygame event loop wrapped around it.

    python -m gestate.gui examples/gui/bounce.ges
    python -m gestate.gui examples/gui/bounce.ges --frames 3   # no window
"""

from __future__ import annotations

import sys
from pathlib import Path

from .gmachine import NChan, NCon, NInd, NNum
from .pipeline import compile as _compile
from .reactive import init_program, react

#: `signal.ges` first: the vocabulary both reactive backends share.
_SIGNAL = (Path(__file__).with_name("signal.ges")).read_text()
_GUI = _SIGNAL + "\n" + (Path(__file__).with_name("gui.ges")).read_text()

#: The program supplies `substrate`; `main` is ours, as in the MIDI
#: backend.  See `_entry`.


def _preludes(source: str) -> str:
    """What to compile this program against — `audio.preludes` decides.

    Asked rather than assumed, because a file that draws *and* sounds is
    one program and has to be compiled with one constructor numbering.  A
    canvas alone still gets exactly what it always got.

    **And `music.ges` when the file plays a piece**, which is the same
    choice `audioscore.assemble_performance` makes and has to be the same
    one: a program that draws *and* has a `score` is one program, and this
    half of it was compiled without the vocabulary the other half is
    written in — `Unknown global '||'` from a canvas, about a line in the
    piece.
    """
    from .audio import preludes
    from .audioperform import has_score

    head = preludes(source)
    if has_score(source):
        head += "\n" + (Path(__file__).with_name("music.ges")).read_text()
    return head


def _program(source: str) -> str:
    """The author's text with its `voices` banks expanded.

    **The same rewrite `audio.assemble` does**, and for the same reason it
    is done in one place there: `voices lead 4 sineVoice : Sig Float` is
    not gestate syntax, so a reader that parses the raw text fails on it —
    which the canvas did, with `expected pattern, got ':'` at a line the
    author would have to count the preludes to find.

    It went unnoticed because it takes a file with *both* a bank and a
    substrate to reach: the audio half went through `assemble` and drew its
    banks correctly while the canvas half of the same file refused to
    build at all.

    **And `internal` is enforced here**, for the same reason `assemble`
    enforces it there: this is the last line at which the author's text is
    still a file of its own.  A canvas that reaches into `gui.ges`'s
    machinery is the same mistake a synth makes reaching into
    `synth.ges`'s, and a file that does both should hear about it once.
    """
    from .audiovoices import expand
    from .internals import enforce

    written = expand(source, _preludes(source))
    enforce(source, text=written)
    return written


def _drawn(source: str) -> str:
    """Which declaration the canvas draws.  There is one, and it is
    `substrate`.

    **`scene : Sig Scene` is gone**, along with `Shape`, `Scene` and the
    `still` that wrapped one.  It was the older spelling and the host used
    to lift it, which meant two entry points, two things that could be
    declared, and a rule about what happened when a file had both.  A
    `Sub` does everything a `Scene` did — `rect` and `circle` are what a
    `Shape` was — so the second spelling bought a program nothing and cost
    every reader the question of which one they were looking at.

    A program still carrying a `scene` is told so by name rather than
    compiled into something that draws nothing.
    """
    from .audio import _authored

    names = _authored(source)[1]
    if "substrate" in names:
        return "substrate"
    if "scene" in names:
        raise GuiError(
            "this program declares a `scene`, which the canvas no longer "
            "draws.  Rename it `substrate` and build it from `rect`, "
            "`circle`, `over`, `row` and `column` — a `Sub` is what a "
            "`Scene` was, with an extent and somewhere to attach a "
            "channel")
    return "substrate"


def _entry(source: str, rate: int) -> str:
    """`main = substrate`, and the sample rate when the file also sounds.

    A program that draws *and* sounds is compiled with `audio.ges` and
    `synth.ges` in front of it, and those are written in terms of
    `sampleRate` — which the *audio* renderer supplies, because the rate is
    the renderer's business and not the program's.  Drawing needs the same
    answer: every definition in the file has to type-check to compile any
    of it, and a scene may perfectly well be drawn from something defined
    in terms of `sampleRate`.

    So the canvas is told the rate its synth is playing at.  Two different
    answers here and in `audio._entry` would be two programs again — the
    thing this whole assembly exists to prevent.
    """
    from .audio import has_sound

    # `constSig` over *this* clock — see `audio._entry`, which gives one
    # over `ticks`.  A constant is constant over whatever is asking.
    entry = ("\nconstSig : a -> Sig a\n"
             "constSig v = mapSig (n => v) events\n")
    # `_drawn` raises on a leftover `scene`; the answer is otherwise always
    # `substrate`, and it is called for the refusal rather than the choice.
    _drawn(source)
    entry += "\nmain : Sig Sub\nmain = substrate\n"
    if not has_sound(source):
        return entry
    return f"\nsampleRate : Float\nsampleRate = {float(rate)}\n" + entry


def assembled(source: str, rate: int = 0) -> str:
    """The whole program the canvas compiles — **shadowed like the other
    two halves.**

    `audio.assemble` and `audioscore.assemble_performance` both put the
    author's text through `prelude.shadow_libraries`, so a program may
    name whatever it likes and the library definition it hides steps
    aside.  This assembly did not, and nothing noticed for as long as no
    file both drew *and* played: a canvas alone never sees `music.ges`,
    and a piece alone never comes through here.

    `lantern.ges` is the first file that does both, and it called one of
    its definitions `bar` — which `music.ges` also defines.  The audio
    half compiled it; the canvas half refused with *"Duplicate type
    signature for 'bar'"*, about a name the author had every right to.
    The three assemblies have to make the same promises about the
    author's namespace, because they are three readings of one file.
    """
    from .audio import DEFAULT_RATE
    from .prelude import shadow_libraries
    from .syntax import note_seam

    head = _preludes(source)
    written = _program(source)
    tail = _entry(source, rate or DEFAULT_RATE)
    shadowed = shadow_libraries(head, written)
    out = shadowed + "\n" + written + "\n" + tail
    # Only an unshadowed head can stand alone — see `audio.assemble`.
    if shadowed is head:
        note_seam(out, len(shadowed) + 1)
    return out


class GuiError(Exception):
    pass


# ── Reading the heap ────────────────────────────────────────────────────────


def _force(node, state):
    """Evaluate a heap node to weak head normal form."""
    from .gmachine import run

    while isinstance(node, NInd):
        if node.target is None:
            raise GuiError("null indirection while reading a scene")
        node = node.target
    if isinstance(node, (NNum, NCon)):
        return node
    saved_code, saved_stack, saved_dump = state.code, state.stack, state.dump
    try:
        state.code = [__import__("gestate.gmachine", fromlist=["Unwind"]).Unwind()]
        state.stack = [node]
        state.dump = []
        run(state)
        return state.stack[0]
    finally:
        state.code, state.stack, state.dump = saved_code, saved_stack, saved_dump


def _int(node, state) -> int:
    node = _force(node, state)
    if not isinstance(node, NNum):
        raise GuiError(f"expected a number, got {type(node).__name__}")
    return node.n


def _list(node, state) -> list:
    """A cons-list as a Python list, forcing the spine cell by cell."""
    cons_tag = state.cons["Cons"].tag
    nil_tag = state.cons["Nil"].tag
    out = []
    node = _force(node, state)
    while True:
        if not isinstance(node, NCon):
            raise GuiError(f"expected a list cell, got {type(node).__name__}")
        if node.tag == nil_tag:
            return out
        if node.tag != cons_tag:
            raise GuiError(f"expected a list cell, got tag {node.tag}")
        out.append(node.args[0])
        node = _force(node.args[1], state)


def _colour(node, state) -> tuple[int, int, int]:
    node = _force(node, state)
    if not isinstance(node, NCon) or len(node.args) != 3:
        raise GuiError("expected an RGB colour")
    r, g, b = (max(0, min(255, _int(a, state))) for a in node.args)
    return r, g, b


def _extent(node, state) -> tuple[int, int]:
    """How much room a substrate occupies, in pixels.

    **Declared, never measured.**  A leaf's extent is the number it was
    built with and a combinator's is a rule over its children's — nothing
    here looks at what got painted.  Inferring it from the drawing instead
    would give `Gap` no size at all (it draws nothing and is *entirely*
    size), and would make a layout shift when a colour changed to the
    background colour.

    It is also what makes layout possible: arranging two things requires
    knowing how big they are *before* placing them, which a walk that only
    drew could not know until afterwards.
    """
    node = _force(node, state)
    if not isinstance(node, NCon):
        raise GuiError(f"expected a substrate, got {type(node).__name__}")
    tag, cons = node.tag, state.cons
    args = node.args

    if tag == cons["Rect"].tag:
        return _int(args[0], state), _int(args[1], state)
    if tag == cons["Circle"].tag:
        r = _int(args[0], state)
        return 2 * r, 2 * r
    if tag == cons["Gap"].tag:
        return _int(args[0], state), _int(args[1], state)
    if tag == cons["Over"].tag:
        aw, ah = _extent(args[0], state)
        bw, bh = _extent(args[1], state)
        return max(aw, bw), max(ah, bh)
    if tag == cons["Row"].tag:
        aw, ah = _extent(args[0], state)
        bw, bh = _extent(args[1], state)
        return aw + bw, max(ah, bh)
    if tag == cons["Column"].tag:
        aw, ah = _extent(args[0], state)
        bw, bh = _extent(args[1], state)
        return max(aw, bw), ah + bh
    if tag == cons["Shift"].tag:
        # **Layout-neutral, and this is where that is decided.**  The
        # extent is the child's *unmoved*, so a handle sliding inside a
        # fader does not resize the fader and does not shuffle whatever is
        # in the row beside it.  A `moveXY` that grew the extent would make
        # every animation relayout the window.
        return _extent(args[2], state)
    if tag == cons["Sized"].tag:
        return _int(args[0], state), _int(args[1], state)
    if tag == cons["Pad"].tag:
        n = _int(args[0], state)
        w, h = _extent(args[1], state)
        return w + 2 * n, h + 2 * n
    if tag in (cons["TouchX"].tag, cons["TouchY"].tag):
        return _extent(args[1], state)
    raise GuiError(f"unknown substrate tag {tag}")


def _walk(node, state, cx: int, cy: int, out: list, hits: list) -> None:
    """Draw a `Sub` and record what listens, in one descent.

    `cx, cy` is where this element's **centre** goes.  Every element is
    placed by its centre and every combinator lines its children up by
    theirs, so there is no alignment argument anywhere — one agreed point
    on each thing and the arranging has nothing left to decide.

    **Painter's order, left to right.**  `over a b` is `a` and then `b`, so
    `b` is on top — the order is in the program rather than in the file,
    because composition is the thing you are meant to be able to read.

    The position is accumulated on the way down, and this is the whole
    reason `Sub` is data rather than a function: the host walks the tree to
    draw it anyway, so an attachment's region falls out of the same
    descent.  An element that hid its structure would have to be handed the
    events instead, and every combinator would have to transform them on
    the way in.

    `hits` comes out **innermost first**, because an attachment is recorded
    after the subtree it wraps — which is also the order a press wants: the
    deepest attachment containing a point is the one that gets it.
    """
    node = _force(node, state)
    if not isinstance(node, NCon):
        raise GuiError(f"expected a substrate, got {type(node).__name__}")

    tag, cons = node.tag, state.cons
    args = node.args

    if tag == cons["Rect"].tag:
        w, h = _int(args[0], state), _int(args[1], state)
        out.append(("rect", cx - w // 2, cy - h // 2, w, h,
                    _colour(args[2], state)))
        return
    if tag == cons["Circle"].tag:
        out.append(("dot", cx, cy, _int(args[0], state),
                    _colour(args[1], state)))
        return
    if tag == cons["Gap"].tag:
        return                              # room, and nothing in it
    if tag == cons["Over"].tag:
        _walk(args[0], state, cx, cy, out, hits)
        _walk(args[1], state, cx, cy, out, hits)
        return
    if tag == cons["Row"].tag:
        aw, _ah = _extent(args[0], state)
        bw, _bh = _extent(args[1], state)
        left = cx - (aw + bw) // 2
        _walk(args[0], state, left + aw // 2, cy, out, hits)
        _walk(args[1], state, left + aw + bw // 2, cy, out, hits)
        return
    if tag == cons["Column"].tag:
        _aw, ah = _extent(args[0], state)
        _bw, bh = _extent(args[1], state)
        top = cy - (ah + bh) // 2
        _walk(args[0], state, cx, top + ah // 2, out, hits)
        _walk(args[1], state, cx, top + ah + bh // 2, out, hits)
        return
    if tag == cons["Shift"].tag:
        _walk(args[2], state,
              cx + _int(args[0], state), cy + _int(args[1], state), out, hits)
        return
    if tag == cons["Sized"].tag:
        # The child keeps its own size and is centred in the declared box.
        # Nothing here scales a picture: this says how much room to
        # reserve, which is a different question from how big to draw.
        _walk(args[2], state, cx, cy, out, hits)
        return
    if tag == cons["Pad"].tag:
        _walk(args[1], state, cx, cy, out, hits)
        return
    if tag in (cons["TouchX"].tag, cons["TouchY"].tag):
        # **The region is the extent, not the drawing.**  It used to be the
        # bounding box of whatever the subtree painted, which made an
        # element's sensitive area depend on what it happened to be showing
        # — a fader whose handle sat at the top answered presses only near
        # the top, and got taller as you dragged it down.  The extent is
        # what the element *said* it was, so the area is the same whatever
        # is drawn in it.
        w, h = _extent(node, state)
        x0, y0 = cx - w // 2, cy - h // 2
        _walk(args[1], state, cx, cy, out, hits)
        hits.append({
            "axis": "x" if tag == cons["TouchX"].tag else "y",
            "chan": _chan_id(args[0], state),
            "region": (x0, y0, x0 + w, y0 + h),
        })
        return
    raise GuiError(f"unknown substrate tag {tag}")


def _chan_id(node, state) -> int:
    """The channel a program put *in* the structure, as the id to write.

    At run time a `Chan a` is an `NChan(chan_id)`, so this is the whole of
    the "how does the host name a channel" problem: it does not name one.
    It reads the one it walked into.
    """
    node = _force(node, state)
    if not isinstance(node, NChan):
        raise GuiError(f"expected a channel, got {type(node).__name__}")
    return node.chan_id


def _flatten(node, state, cx: int = 0, cy: int = 0, out=None) -> list:
    """The shapes to draw — `_walk` with the hit table thrown away.

    The root's **centre** goes at `cx, cy`, and it defaults to the origin
    rather than to the middle of a window because the host that calls this
    does not know how big the window is — `touches` and `Substrate.picture`
    are both pure.  A program places what it draws with `moveXY`, which is
    what `moveXY` is for.
    """
    out = [] if out is None else out
    _walk(node, state, cx, cy, out, [])
    return out


def _attachments(node, state) -> list:
    """What listens, innermost first."""
    hits: list = []
    _walk(node, state, 0, 0, [], hits)
    return hits


def _under(hits: list, x: int, y: int) -> dict | None:
    """The deepest attachment the point lands on, or `None`.

    Forward, because `_walk` records an attachment after the subtree it
    wraps: the innermost is the first one written down.
    """
    for hit in hits:
        x0, y0, x1, y1 = hit["region"]
        if x0 <= x <= x1 and y0 <= y <= y1:
            return hit
    return None


# ── Driving it ──────────────────────────────────────────────────────────────


def _entry_signal(state):
    """The `NSig` cell `main` evaluated to.

    Held by reference, not re-read: a signal *is* the cell, and time
    advancing overwrites it in place.  That is the whole design — there is
    nowhere for an old value to live — so one reference stays current for
    the life of the program.
    """
    from .gmachine import NSig

    sig = state.stack[0] if state.stack else None
    while isinstance(sig, NInd):
        sig = sig.target
    if not isinstance(sig, NSig):
        raise GuiError(
            "the program's `scene` did not evaluate to a signal "
            f"(got {type(sig).__name__})"
        )
    return sig


def _event_node(state, event) -> NCon:
    """A Python `("Move", x, y)` as the `Event` constructor it names."""
    name, *args = event
    info = state.cons.get(name)
    if info is None:
        known = ", ".join(sorted(
            n for n in ("Tick", "Move", "Press", "Release", "Key")
            if n in state.cons))
        raise GuiError(f"unknown event {name!r} (the program knows: {known})")
    if len(args) != info.arity:
        raise GuiError(
            f"{name} takes {info.arity} argument(s), got {len(args)}")
    return NCon(info.tag, tuple(NNum(a) for a in args))


def scenes(source: str, events, rate: int = 0) -> list[list[tuple]]:
    """Every picture the program shows, one per event plus the first.

    Pure: no window, no clock, no pygame.  `events` is a list of tuples
    like `("Tick",)` or `("Press", 40, 60)`.

    `rate` is the sample rate of the synth in the same file, and matters
    only when there is one — see `_entry`.
    """
    from .audio import DEFAULT_RATE

    state = _compile(assembled(source, rate))
    reactive = init_program(state)
    sig = _entry_signal(state)

    out = [_flatten(sig.value, state)]
    if not reactive.chans:
        # A program that never looks at `events` has no channel, so there
        # is nothing to send it — the picture simply never changes.
        return out + [list(out[0]) for _ in events]

    channel = min(reactive.chans)
    for event in events:
        react(reactive, [(channel, _event_node(state, event))])
        out.append(_flatten(sig.value, state))
    return out


def touches(source: str, gestures, rate: int = 0) -> list[list[tuple]]:
    """Every picture, one per gesture — the canvas being *used*.

    Pure, like `scenes`, and the same shape: no window, no clock, no
    pygame.  A gesture is `("press", x, y)`, `("drag", x, y)` or
    `("release", x, y)` in canvas coordinates.

    What happens to one is the whole of S3.  The walk that drew the picture
    also said what listens and where, so a press finds the deepest
    attachment it lands on, and what reaches the program is a **number
    written to the channel that attachment carries** — the drag's position
    in that element's own coordinates, or a gate of 1 and 0.  Nothing is
    routed by name and nothing is registered: the channel was in the
    structure, put there by the program.

    A press **grabs**, so a drag that leaves the element still reaches it.
    That is what a fader is, and doing it any other way makes one that
    stops following your hand at its own edge.
    """
    from .audio import DEFAULT_RATE

    state = _compile(assembled(source, rate))
    reactive = init_program(state)
    sig = _entry_signal(state)

    out = [_flatten(sig.value, state)]
    held: dict | None = None
    for gesture in gestures:
        kind, x, y = gesture
        hits = _attachments(sig.value, state)
        if kind == "press":
            held = _under(hits, x, y)
        target = held
        writes = []
        if target is not None:
            # **Through `_gesture_value`, not a second copy of it.**  This
            # was written out again inline, so `touches` and
            # `Substrate.touch` were two implementations of one rule and
            # only one of them would have been changed here.  The same
            # split is what let `audioeditor` read the score at instant 0.
            value = _gesture_value(target, kind, x, y)
            if value is not None:
                writes.append((target["chan"], NNum(value)))
        if kind == "release":
            held = None
        if writes:
            react(reactive, writes)
        out.append(_flatten(sig.value, state))
    return out


class Substrate:
    """A program's canvas, running beside its sound.

    What the editor holds: the interpreted half of one file, drawn on
    demand and touched by a pointer.  `touches` is this without the state,
    for tests; this is the same thing with a hand on it.

    **Values are kept by channel *name*** — which is the whole of the
    bridge to the compiled half.  A program says `cutoff : Chan Int` once;
    the audio graph then carries a control source named `cutoff`, and the
    canvas carries that same channel as a runtime `NChan`.  The editor
    writes both from one gesture: the interpreted channel by id so the
    picture follows, and the control value by name so the sound does.
    """

    def __init__(self, source: str, rate: int = 0):
        from .audio import DEFAULT_RATE

        self.state = _compile(assembled(source, rate))
        # **Before the program runs.**  A channel is allocated when its
        # declaration is first forced, so forcing them here — in this
        # state, sharing its counter — is what gives every declared channel
        # an id *and* keeps that id the one the program itself will see.
        self.by_name = {name: self._force(name).chan_id
                        for name in _channel_names(source)}
        self.reactive = init_program(self.state)
        self.signal = _entry_signal(self.state)
        #: Channel name → the last value written to it.  What the audio
        #: side reads: `audioeditor.Workbench.control` asks by name.
        self.values: dict[str, int] = {}
        self._held: dict | None = None

    def _force(self, name: str):
        """Evaluate a global in place, leaving the machine as it was."""
        from .gmachine import PushGlobal, Unwind, run

        state = self.state
        saved = (state._code, state._pc, state.stack, state.dump)
        state._code, state._pc = [PushGlobal(name), Unwind()], 0
        state.stack, state.dump = [], []
        try:
            run(state)
            node = state.stack[0]
            while isinstance(node, NInd):
                node = node.target
            if not isinstance(node, NChan):
                raise GuiError(f"`{name}` is declared `Chan` and is not one")
            return node
        finally:
            state._code, state._pc, state.stack, state.dump = saved

    def picture(self) -> list:
        """The shapes to draw, right now."""
        return _flatten(self.signal.value, self.state)

    def write(self, name: str, value) -> bool:
        """Put a number on a channel the program declared, by name.

        The other direction from `touch`: that is a hand reaching the
        program, this is the *instrument* reaching it — what S5 is for.  A
        program that declares no such channel is not written to and does
        not pay for the reading.
        """
        cid = self.by_name.get(name)
        if cid is None:
            return False
        react(self.reactive, [(cid, NNum(value))])
        self.values[name] = value
        return True

    def touch(self, kind: str, x: int, y: int) -> None:
        """A press, a drag or a release, in canvas coordinates.

        A press **grabs**, so a drag that leaves the element still reaches
        it — which is what a fader is.
        """
        hits = _attachments(self.signal.value, self.state)
        if kind == "press":
            self._held = _under(hits, x, y)
        target = self._held
        if kind == "release":
            self._held = None
        if target is None:
            return
        value = _gesture_value(target, kind, x, y)
        if value is None:
            return
        react(self.reactive, [(target["chan"], NNum(value))])
        for name, cid in self.by_name.items():
            if cid == target["chan"]:
                self.values[name] = value


def _gesture_value(target: dict, kind: str, x: int, y: int):
    """What a gesture writes to the channel it found, or `None`.

    **A fraction of the element's own extent**, 0 at the left or top edge
    and 1 at the right or bottom, and **clamped there**.  Two things follow,
    and both were missing while this reported a raw pixel offset.

    *Motion is constrained by construction.*  A hand that kept going used
    to carry a fader's handle off the end of its own track, and there was
    nowhere in the program to say it should not — the element knew its
    extent and the number did not mention it.  The bound is now the extent,
    which the element declared, and no program restates it.

    *The number means something without knowing the size.*  0…1 whether the
    fader is 200 pixels or 40, so what it drives is written once and the
    picture is resized without touching it — and the same signal drives a
    synth parameter directly, which is what a control value is.

    A release writes nothing: a fader stays where it was let go.
    """
    if kind == "release":
        return None
    x0, y0, x1, y1 = target["region"]
    if target["axis"] == "x":
        here, low, span = x, x0, x1 - x0
    else:
        here, low, span = y, y0, y1 - y0
    # An element with no extent on the axis it listens to has no fraction
    # to report; 0 is the honest answer and the alternative is a division
    # by zero on a `Gap`.
    if span <= 0:
        return 0.0
    return min(1.0, max(0.0, (here - low) / span))


def _channel_names(source: str) -> list:
    """Every `name : Chan …` a program declares, in the order written.

    From the parsed signatures, like every other question about what a
    program declares — `audio._authored` keeps them in the order written.
    """
    from .audio import _authored
    from .syntax.ast import VApp, VConId

    def is_chan(t) -> bool:
        while isinstance(t, VApp):
            t = t.fn
        return isinstance(t, VConId) and t.value == "Chan"

    return [n for n, t in _authored(source)[0].items() if is_chan(t)]


# ── The window ──────────────────────────────────────────────────────────────

_DEFAULT_SIZE = (480, 360)


def run(source: str, size=_DEFAULT_SIZE, fps: int = 60, title="gestate",
        rate: int = 0) -> int:
    """Open a window and run the program until it is closed."""
    try:
        import pygame
    except ImportError:
        raise GuiError(
            "running a GUI program needs pygame (`pip install pygame`); "
            "`scenes()` works without it"
        )

    from .audio import DEFAULT_RATE

    state = _compile(assembled(source, rate))
    reactive = init_program(state)
    sig = _entry_signal(state)
    channel = min(reactive.chans) if reactive.chans else None

    pygame.init()
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption(title)
    clock = pygame.time.Clock()

    def send(event):
        if channel is not None:
            react(reactive, [(channel, _event_node(state, event))])

    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                else:
                    send(("Key", ev.key))
            elif ev.type == pygame.MOUSEMOTION:
                send(("Move", ev.pos[0], ev.pos[1]))
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                send(("Press", ev.pos[0], ev.pos[1]))
            elif ev.type == pygame.MOUSEBUTTONUP:
                send(("Release", ev.pos[0], ev.pos[1]))

        # One `Tick` a frame is what makes animation possible: a program
        # with no input still advances.
        send(("Tick",))

        screen.fill((0, 0, 0))
        for shape in (_shape(s, state) for s in _list(sig.value, state)):
            if shape[0] == "rect":
                _kind, x, y, w, h, colour = shape
                pygame.draw.rect(screen, colour, pygame.Rect(x, y, w, h))
            else:
                _kind, x, y, radius, colour = shape
                pygame.draw.circle(screen, colour, (x, y), radius)
        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()
    return 0


# ── CLI ─────────────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python -m gestate.gui",
        description="Run a gestate GUI program.")
    ap.add_argument("file")
    ap.add_argument("--frames", type=int, default=None,
                    help="print this many frames of shapes and exit, "
                         "without opening a window")
    ap.add_argument("--size", default="480x360")
    ap.add_argument("--fps", type=int, default=60)
    args = ap.parse_args(argv)

    # Inside the `try`, which is where it always belonged: a missing file
    # was the one error this boundary could not report, because reading it
    # happened before the boundary began.
    try:
        source = Path(args.file).read_text()
        if args.frames is not None:
            for i, scene in enumerate(scenes(source, [("Tick",)] * args.frames)):
                print(f"frame {i}: " + ", ".join(
                    f"{s[0]}{s[1:-1]}" for s in scene) or f"frame {i}: (empty)")
            return 0
        w, _sep, h = args.size.partition("x")
        return run(source, (int(w), int(h)), args.fps,
                   title=Path(args.file).stem)
    except Exception as exc:                     # noqa: BLE001 — CLI boundary
        print(f"gestate: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
