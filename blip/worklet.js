// The worklet: `audiollvm.native_blocks` in the browser.  One module
// instance, the state at `__heap_base`, the output buffer after it, the
// control slots after that — the layout `audiowasm.run` documents — and
// `render_block(state, out, want, slots)` once per quantum.
//
// Instantiated synchronously from a compiled `WebAssembly.Module`,
// because an OfflineAudioContext renders to its end before an async
// instantiate resolves, and a page whose check renders silence has
// checked nothing.
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
    this.next = 0;
    this.t = 0;
    const heap = this.ex.__heap_base.value;
    this.state = heap;
    this.buf = heap + o.stateBytes;
    this.slotsAt = this.buf + 8 * o.quantum * o.channels;
    const need = this.slotsAt + 8 * o.slots + 16;
    while (this.ex.memory.buffer.byteLength < need) this.ex.memory.grow(1);
    new Uint8Array(this.ex.memory.buffer, this.state, o.stateBytes).fill(0);
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
      if (this.types[slot] === "Float") f64[base + slot] = value;
      else i64[base + slot] = BigInt(value);
    }
    this.ex.render_block(this.state, this.buf, BigInt(n), this.slotsAt);
    const got = new Float64Array(this.ex.memory.buffer, this.buf, n * this.channels);
    for (let c = 0; c < out.length; c++) {
      const ch = out[c];
      const src = c < this.channels ? c : 0;
      for (let i = 0; i < n; i++) ch[i] = got[i * this.channels + src];
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
