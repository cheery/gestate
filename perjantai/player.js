// The page's half: fetch the module and its data, compile once, and
// hand both to the worklet.  `?check=N` renders N frames through an
// OfflineAudioContext instead of the speakers and writes them into
// `<pre id="check">`; with `&to=<path>` it also POSTs them there, which
// is how `test/test_online.py` reads the browser's answer back without
// a sound card — a headless Chrome's virtual time does not run an
// offline render to its end, so the test waits on the wall clock for
// this request instead of dumping the DOM.  `&set=slot:value,...` is
// a knob turned before the check, the same way a hand turns one.
//
// The knobs are the sliders the generator put beside each declaration
// (`gestate.online.knobs`).  Their values live here, on the page: a
// slider moved while the piece plays goes to the worklet on its port,
// and one moved before play goes in with the options, so stop and
// play again keeps what was turned.
(async () => {
  const stem = document.body.dataset.stem;
  const status = document.getElementById("status");
  const button = document.getElementById("play");
  const say = (s) => { status.textContent = s; };

  let module, data;
  try {
    const [bytes, json] = await Promise.all([
      fetch(stem + ".wasm").then((r) => r.arrayBuffer()),
      fetch(stem + ".json").then((r) => r.json()),
    ]);
    module = await WebAssembly.compile(bytes);
    data = json;
  } catch (e) {
    say("could not load the sound: " + e);
    return;
  }

  const turned = {};
  let live = null;
  const turn = (slot, value) => {
    turned[slot] = value;
    if (live) live.port.postMessage({ slot, value });
  };
  for (const input of document.querySelectorAll("input[data-slot]")) {
    const out = input.parentElement.querySelector("output");
    input.oninput = () => {
      const value = input.dataset.type === "Float" ? parseFloat(input.value) : parseInt(input.value, 10);
      out.textContent = input.value;
      turn(parseInt(input.dataset.slot, 10), value);
    };
  }

  // Compiled here and instantiated synchronously in the worklet: an
  // OfflineAudioContext renders to its end before an async instantiate
  // in the processor would resolve, and would render silence.
  const node = async (ctx) => {
    await ctx.audioWorklet.addModule("worklet.js");
    return new AudioWorkletNode(ctx, "gestate", {
      numberOfInputs: 0,
      numberOfOutputs: 1,
      outputChannelCount: [data.channels],
      processorOptions: {
        module, overrides: { ...turned }, ...data,
        // Only when the picture is actually up: the filter bank and the
        // ring read are the instrument reaching a canvas, and a page
        // with no canvas must not pay for either.
        meters: picture ? data.canvas.meters : null,
      },
    });
  };

  // The picture — `card:audiovisual-gallery.md`.  A piece that draws
  // one gets it whether or not it is playing: a fader on a stopped
  // piece still moves, which is `gestate/gui.py`'s own rule and the
  // strangest thing to get wrong.  A shell that will not load costs the
  // canvas and never the sound.
  let picture = null;
  const face = document.getElementById("picture");
  if (data.canvas && face) {
    try {
      // Imported only when the file draws: a piece with no substrate
      // gets no `canvas.js` written beside it at all, and 45 of the 50
      // pages on the site are that piece.
      const { Picture } = await import("./canvas.js");
      picture = await Picture.load(data.canvas.wasm, data.canvas, face);
      face.hidden = false;
      const spot = (e) => {
        const r = face.getBoundingClientRect();
        return [Math.round(e.clientX - r.left), Math.round(e.clientY - r.top)];
      };
      face.onpointerdown = (e) => {
        face.setPointerCapture(e.pointerId);
        picture.press(...spot(e));
      };
      face.onpointermove = (e) => { if (picture.grabbing) picture.motion(...spot(e)); };
      face.onpointerup = () => picture.release();
      const frame = () => { picture.step(); requestAnimationFrame(frame); };
      requestAnimationFrame(frame);
      // **For the gate, and it is the same affordance `?check=N` is.**
      // `test_online.py` reads the picture back over the wire and holds
      // it to what `gestate/gui.py` draws — the comparison
      // `test_gallery.py` makes under `wasmtime`, made again here
      // against the page a person actually loads, because the payload
      // the generator wrote is between the two and nothing else checks
      // it.  A page nobody is testing is not slowed by one property.
      window.gestatePicture = picture;
    } catch (e) {
      picture = null;
      say("the picture would not load: " + e);
    }
  } else if (data.canvasSkipped) {
    // Said rather than swallowed: the page was made on a machine
    // without the toolchain, and a silent missing canvas is a bug
    // report nobody can write.
    const note = document.getElementById("nopicture");
    if (note) {
      note.textContent = "This piece draws a picture and this page was "
        + "built without it — " + data.canvasSkipped + ".";
      note.hidden = false;
    }
  }

  const params = new URLSearchParams(location.search);
  const check = params.get("check");
  if (check) {
    const sets = (params.get("set") || "").split(",").filter(Boolean)
      .map((pair) => pair.split(":")).map(([s, v]) => [parseInt(s, 10), parseFloat(v)]);
    const frames = parseInt(check, 10);
    const ctx = new OfflineAudioContext(data.channels, frames, data.rate);
    // `&at=F` turns the knobs at frame F *while rendering*, on the
    // port — the path a hand on a playing piece takes; without it they
    // are turned first and go in with the options.
    const at = params.get("at");
    // One message for all of them — the worklet says why — and not
    // `turn`: that is a slider's path, one value at a time.
    let n;
    if (at) {
      ctx.suspend(parseInt(at, 10) / data.rate).then(() => {
        for (const [slot, value] of sets) turned[slot] = value;
        n.port.postMessage({ set: sets });
        ctx.resume();
      });
    } else for (const [slot, value] of sets) turn(slot, value);
    n = await node(ctx);
    // **The meters, on the same render.**  A picture *of* the sound —
    // a peak, a band, a scope's trace — is measured in the worklet
    // beside the samples, so the only place to check it is a render
    // that produced samples.  `&meters=1` keeps the last report the
    // worklet posted and returns it instead of the frames.
    const seen = [];
    n.port.onmessage = (e) => { if (e.data.meters) seen.push(e.data.meters); };
    n.connect(ctx.destination);
    const buf = await ctx.startRendering();
    if (params.get("meters")) {
      const body = JSON.stringify({ reports: seen.length, last: seen[seen.length - 1] || null });
      document.getElementById("check").textContent = body;
      say("metered " + seen.length + " reports");
      const to0 = params.get("to");
      if (to0) await fetch(to0, { method: "POST", body });
      return;
    }
    const lines = [];
    for (let c = 0; c < data.channels; c++) lines.push(Array.from(buf.getChannelData(c)).join(" "));
    document.getElementById("check").textContent = lines.join("\n");
    say("checked " + frames + " frames");
    const to = params.get("to");
    if (to) await fetch(to, { method: "POST", body: lines.join("\n") });
    return;
  }

  let ctx = null;
  const seconds = (t) => (t / data.rate).toFixed(1) + " s";
  // A score that unfolds has no end to bake to, so what the page
  // carries is a window of it and the page says which — a piece that
  // stops after thirty seconds without saying so reads as a bug, and
  // the truth is more interesting than the bug.
  const endless = (data.unfolds || []).length > 0;
  const window_ = endless
    ? seconds(data.duration) + " of a score that does not end"
    : seconds(data.duration);
  say("ready — " + window_);
  if (endless) {
    const note = document.getElementById("unfolds");
    if (note) {
      note.textContent = "This score unfolds forever (" + data.unfolds.join(", ")
        + "). The page carries the first " + seconds(data.duration)
        + " of it; at the desk you say how long.";
      note.hidden = false;
    }
  }
  button.disabled = false;
  button.onclick = async () => {
    if (ctx) {
      await ctx.close();
      ctx = null;
      live = null;
      button.textContent = "play";
      say("stopped");
      return;
    }
    ctx = new AudioContext({ sampleRate: data.rate });
    const n = await node(ctx);
    n.port.onmessage = async (e) => {
      if (e.data.meters) { if (picture) picture.tell(e.data.meters); return; }
      if (e.data.done) {
        if (ctx) await ctx.close();
        ctx = null;
        live = null;
        button.textContent = "play";
        say(endless ? "the window ends here — the piece does not"
                    : "ended at " + seconds(e.data.t));
      } else say(seconds(e.data.t) + " of " + window_);
    };
    n.connect(ctx.destination);
    live = n;
    await ctx.resume();
    button.textContent = "stop";
    say("playing");
  };
})();
