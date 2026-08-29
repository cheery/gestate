// The page's half: fetch the module and its data, compile once, and
// hand both to the worklet.  `?check=N` renders N frames through an
// OfflineAudioContext instead of the speakers and writes them into
// `<pre id="check">`; with `&to=<path>` it also POSTs them there, which
// is how `test/test_online.py` reads the browser's answer back without
// a sound card — a headless Chrome's virtual time does not run an
// offline render to its end, so the test waits on the wall clock for
// this request instead of dumping the DOM.
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

  // Compiled here and instantiated synchronously in the worklet: an
  // OfflineAudioContext renders to its end before an async instantiate
  // in the processor would resolve, and would render silence.
  const node = async (ctx) => {
    await ctx.audioWorklet.addModule("worklet.js");
    return new AudioWorkletNode(ctx, "gestate", {
      numberOfInputs: 0,
      numberOfOutputs: 1,
      outputChannelCount: [data.channels],
      processorOptions: { module, ...data },
    });
  };

  const check = new URLSearchParams(location.search).get("check");
  if (check) {
    const frames = parseInt(check, 10);
    const ctx = new OfflineAudioContext(data.channels, frames, data.rate);
    const n = await node(ctx);
    n.connect(ctx.destination);
    const buf = await ctx.startRendering();
    const lines = [];
    for (let c = 0; c < data.channels; c++) lines.push(Array.from(buf.getChannelData(c)).join(" "));
    document.getElementById("check").textContent = lines.join("\n");
    say("checked " + frames + " frames");
    const to = new URLSearchParams(location.search).get("to");
    if (to) await fetch(to, { method: "POST", body: lines.join("\n") });
    return;
  }

  let ctx = null;
  const seconds = (t) => (t / data.rate).toFixed(1) + " s";
  say("ready — " + seconds(data.duration));
  button.disabled = false;
  button.onclick = async () => {
    if (ctx) {
      await ctx.close();
      ctx = null;
      button.textContent = "play";
      say("stopped");
      return;
    }
    ctx = new AudioContext({ sampleRate: data.rate });
    const n = await node(ctx);
    n.port.onmessage = async (e) => {
      if (e.data.done) {
        if (ctx) await ctx.close();
        ctx = null;
        button.textContent = "play";
        say("ended at " + seconds(e.data.t));
      } else say(seconds(e.data.t) + " of " + seconds(data.duration));
    };
    n.connect(ctx.destination);
    await ctx.resume();
    button.textContent = "stop";
    say("playing");
  };
})();
