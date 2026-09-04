// The worklet: `audiollvm.native_blocks` in the browser.  One module
// instance, the state at `__heap_base`, the output buffer after it, the
// control slots after that — the layout `audiowasm.run` documents — and
// `render_block(state, out, want, slots)` once per quantum.
//
// Instantiated synchronously from a compiled `WebAssembly.Module`,
// because an OfflineAudioContext renders to its end before an async
// instantiate resolves, and a page whose check renders silence has
// checked nothing.
//
// A knob the person turned is an *override*: written into its slot
// after the score's changes every block, so it wins over the baked
// value at t=0 and stays won.  It arrives with the options (turned
// before play) or on the port (turned while playing), and a slot no
// hand touched is the score's alone.  `{set: [[slot, value], …]}` is
// several at once, for the page's check: of two turns posted together
// to a *suspended* offline render, the first was applied at the next
// quantum and the second not within the second that followed
// (2026-08-30) — so the check turns every knob in one message and
// resumes.  A playing context idles between quanta, and a slider's
// own `{slot, value}` reaches it at once.
class GestateProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    const o = options.processorOptions;
    const env = {};
    for (const name of o.imports) env[name] = HOST[name];
    this.ex = new WebAssembly.Instance(o.module, { env }).exports;
    this.channels = o.channels;
    this.types = o.types;
    this.changes = o.changes;
    this.duration = o.duration;
    this.overrides = new Map();
    for (const [slot, value] of Object.entries(o.overrides || {})) this.overrides.set(+slot, value);
    this.port.onmessage = (e) => {
      if ("slot" in e.data) this.overrides.set(e.data.slot, e.data.value);
      for (const [slot, value] of e.data.set || []) this.overrides.set(slot, value);
    };
    this.next = 0;
    this.t = 0;
    this.meters = o.meters || null;
    if (this.meters) this.armMeters(o.rate);
    const heap = this.ex.__heap_base.value;
    this.state = heap;
    this.buf = heap + o.stateBytes;
    this.slotsAt = this.buf + 8 * o.quantum * o.channels;
    this.slotCount = o.slots;
    const need = this.slotsAt + 8 * o.slots + 16;
    while (this.ex.memory.buffer.byteLength < need) this.ex.memory.grow(1);
    new Uint8Array(this.ex.memory.buffer, this.state, o.stateBytes).fill(0);
  }

  // **The instrument reaching the picture** — what `gestate/host.c`
  // does for the desk, done here beside the sound the worklet is
  // already rendering.  A page has no C host, and a picture *of* the
  // sound needs the numbers on the same thread the samples are on.
  //
  // The bank is `host.c`'s, constant for constant: seven one-pole
  // lowpasses, band `k` is what `lp[k]` passes and `lp[k-1]` did not,
  // the top band is what none of them did, and each envelope falls with
  // a 150 ms release because a bar that fell as fast as the sound does
  // is unreadable.  **A file that declares no band pays for none of
  // it** (`examples/audio/spectrum.ges`), which is why `meters.bands`
  // is a list and not a flag.
  armMeters(rate) {
    const corner = [110, 250, 550, 1200, 2600, 5500, 11000];
    this.bandK = corner.map((f) => 1 - Math.exp(-2 * Math.PI * Math.min(f, rate * 0.45) / rate));
    this.bandLp = corner.map(() => 0);
    this.bandEnv = new Array(8).fill(0);
    this.bandRelease = Math.exp(-1 / (0.15 * rate));
    this.peak = 0;
    this.sinceReport = 0;
  }

  // One block, down the bank, on the mean of the channels: a spectrum of
  // the picture and not of one ear (`host.c`).
  meter(got, n) {
    const m = this.meters;
    const chans = this.channels;
    if (m.bands.length) {
      const scale = 1 / chans;
      for (let i = 0; i < n; i++) {
        let x = 0;
        for (let c = 0; c < chans; c++) x += got[i * chans + c];
        x *= scale;
        let below = 0;
        for (let k = 0; k < 7; k++) {
          this.bandLp[k] += this.bandK[k] * (x - this.bandLp[k]);
          const now = Math.abs(this.bandLp[k] - below);
          below = this.bandLp[k];
          const was = this.bandEnv[k] * this.bandRelease;
          this.bandEnv[k] = now > was ? now : was;
        }
        const top = Math.abs(x - below);
        const was = this.bandEnv[7] * this.bandRelease;
        this.bandEnv[7] = top > was ? top : was;
      }
    }
    if (m.peak) {
      // Sampled, not scanned — sixteen points of a block is enough to
      // see a needle move, and it is `host.c`'s own bargain.
      const span = n * chans;
      const step = Math.max(1, (span / 16) | 0);
      for (let i = 0; i < span; i += step) {
        const a = Math.abs(got[i]);
        if (a > this.peak) this.peak = a;
      }
    }
  }

  // The ring the module already keeps, downsampled by max-absolute per
  // bucket — `audioeditor.Workbench.TRACE_POINTS`, because a scope that
  // averages away a click is a scope that lies.  `read_scope_<i>` copies
  // the window oldest-first with the writer's own cursor, so no offset
  // crosses the boundary (`spec/scope.md`).
  trace(spec) {
    const need = spec.length * 8;
    if (this.scopeAt === undefined) {
      this.scopeAt = this.slotsAt + 8 * this.slotCount + 16;
      const want = this.scopeAt + need;
      while (this.ex.memory.buffer.byteLength < want) this.ex.memory.grow(1);
    }
    this.ex["read_scope_" + spec.index](this.state, this.scopeAt, BigInt(spec.length));
    const window = new Float64Array(this.ex.memory.buffer, this.scopeAt, spec.length);
    const size = Math.max(1, (spec.length / spec.points) | 0);
    const points = [];
    for (let b = 0; b < spec.points; b++) {
      let best = 0;
      for (let i = b * size; i < (b + 1) * size && i < spec.length; i++) {
        if (Math.abs(window[i]) > Math.abs(best)) best = window[i];
      }
      points.push(best);
    }
    return points;
  }

  // Read and cleared, so each look reports the span since the last one
  // rather than the loudest thing that ever happened (`host.c`).
  report() {
    const m = this.meters;
    const out = {};
    if (m.peak) { out.peak = this.peak; this.peak = 0; }
    if (m.bands.length) {
      out.bands = {};
      for (const k of m.bands) out.bands[k] = this.bandEnv[k];
    }
    if (m.scopes.length) {
      out.traces = {};
      for (const spec of m.scopes) out.traces[spec.label] = this.trace(spec);
    }
    this.port.postMessage({ meters: out });
  }

  write(f64, i64, base, slot, value) {
    if (this.types[slot] === "Float") f64[base + slot] = value;
    else i64[base + slot] = BigInt(Math.round(value));
  }

  process(inputs, outputs) {
    const out = outputs[0];
    const n = out[0].length;
    const mem = this.ex.memory.buffer;
    const f64 = new Float64Array(mem);
    const i64 = new BigInt64Array(mem);
    const base = this.slotsAt >> 3;
    while (this.next < this.changes.length && this.changes[this.next][0] <= this.t) {
      const [, slot, value] = this.changes[this.next++];
      this.write(f64, i64, base, slot, value);
    }
    for (const [slot, value] of this.overrides) this.write(f64, i64, base, slot, value);
    this.ex.render_block(this.state, this.buf, BigInt(n), this.slotsAt);
    const got = new Float64Array(this.ex.memory.buffer, this.buf, n * this.channels);
    for (let c = 0; c < out.length; c++) {
      const ch = out[c];
      const src = c < this.channels ? c : 0;
      for (let i = 0; i < n; i++) ch[i] = got[i * this.channels + src];
    }
    if (this.meters) {
      this.meter(got, n);
      // Once a displayed frame, near enough: 60 Hz against the quantum's
      // 344, and the picture is redrawn on `requestAnimationFrame`
      // anyway.  Posting per quantum would be five messages a frame,
      // four of them read by nobody.
      if (++this.sinceReport >= 6) { this.sinceReport = 0; this.report(); }
    }
    this.t += n;
    if (this.t >= this.duration) {
      this.port.postMessage({ done: true, t: this.t });
      return false;
    }
    if ((this.t / n) % 16 === 0) this.port.postMessage({ t: this.t });
    return true;
  }
}

// What the module imports and what supplies it — `audiowasm.HOST`, the
// same names.  `fmax`/`fmin` are C's; `Math.max`/`min` differ only on
// NaN, which no graph here produces on purpose.
const HOST = {
  exp: Math.exp, log: Math.log, sin: Math.sin, cos: Math.cos, pow: Math.pow,
  fmax: Math.max, fmin: Math.min, floor: Math.floor, sqrt: Math.sqrt,
};

registerProcessor("gestate", GestateProcessor);
