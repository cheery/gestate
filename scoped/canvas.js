// The picture, in the tab — `card:audiovisual-gallery.md`, day two.
//
// Six pieces on the site declare a `substrate` and every one of them has
// been playing here with its visual half on the floor.  This is the
// page's half of the seam `shell/web` opens: load `gestate_web.wasm`,
// hand it the serialized second program, and then, once a frame, one
// instant and one picture.
//
// **Nothing here decides what a substrate means.**  The walk is
// `gestate_panel::substrate` inside the module, held against
// `gestate/gui.py` tree for tree by `test/test_gallery.py`.  What this
// file does is move bytes across a C ABI and paint an `i32` array onto a
// 2D context.  A second walk in JavaScript would be a second
// implementation kept, which is the cost `card:online.md` C1 was stood
// down for.
//
// **The module imports nothing**, so there is no import object below —
// `crust`'s zero-dependency rule reaching the browser.
//
// The wire's format is `shell/web/src/lib.rs` §"The wire", and it is
// read here with a cursor because a record's length is implied by its
// kind.

const TAU = Math.PI * 2;

export class Picture {
  // `data.canvas` as `gestate.online.canvas_of` wrote it, and the
  // `<canvas>` to paint on.
  constructor(instance, spec, element) {
    this.ex = instance.exports;
    this.spec = spec;
    this.el = element;
    this.ctx = element.getContext("2d");
    this.owned = [];
    this.w = this.open(spec);
    // Channel ids for the meters, resolved once: an id is allocated when
    // a declaration is first forced, so it is the shell's to give and
    // never the page's to derive (`web_channel`).
    this.chan = {};
    for (const name of spec.chans) this.chan[name] = this.id(name);
    this.pending = new Map();
    this.traces = new Map();
    this.grabbing = false;
  }

  static async load(url, spec, element) {
    const bytes = await fetch(url).then((r) => r.arrayBuffer());
    const { instance } = await WebAssembly.instantiate(bytes, {});
    return new Picture(instance, spec, element);
  }

  bytes(data) {
    const p = this.ex.web_alloc(data.length);
    new Uint8Array(this.ex.memory.buffer).set(data, p);
    this.owned.push([p, data.length]);
    return [p, data.length];
  }

  doubles(values) {
    const p = this.ex.web_alloc(values.length * 8);
    new Float64Array(this.ex.memory.buffer, p, values.length).set(values);
    this.owned.push([p, values.length * 8]);
    return p;
  }

  open(spec) {
    const enc = new TextEncoder();
    const [text, textLen] = this.bytes(enc.encode(spec.text));
    const [entry, entryLen] = this.bytes(enc.encode(spec.entry || "main"));
    const tagsP = this.ex.web_alloc(14 * 8);
    this.owned.push([tagsP, 14 * 8]);
    new BigInt64Array(this.ex.memory.buffer, tagsP, 14)
      .set(spec.tags.map((t) => BigInt(t)));
    const names = spec.chans.map((n) => n + "\0").join("");
    const [chans, chansLen] = this.bytes(enc.encode(names));
    const w = this.ex.web_open(text, textLen, entry, entryLen, tagsP, chans, chansLen);
    if (!w) throw new Error(this.say(0));
    return w;
  }

  // The shell's last sentence, NUL-terminated in its own memory.
  say(w) {
    const p = this.ex.web_error(w === undefined ? this.w : w);
    if (!p) return "";
    const mem = new Uint8Array(this.ex.memory.buffer);
    let end = p;
    while (mem[end]) end++;
    return new TextDecoder().decode(mem.subarray(p, end));
  }

  id(name) {
    const [p, n] = this.bytes(new TextEncoder().encode(name));
    return Number(this.ex.web_channel(this.w, p, n));
  }

  // What the instrument told the picture this frame — `{peak, bands,
  // traces}` as the worklet measured it.  Held until the next tick,
  // because the sound arrives on a message and the picture on a frame
  // and neither waits for the other.
  tell(meters) {
    if (meters.peak !== undefined && this.chan.peak >= 0) {
      this.pending.set(this.chan.peak, meters.peak);
    }
    for (const [k, value] of Object.entries(meters.bands || {})) {
      const c = this.chan["band" + k];
      if (c !== undefined && c >= 0) this.pending.set(c, value);
    }
    for (const [label, points] of Object.entries(meters.traces || {})) {
      const c = this.chan[label];
      if (c !== undefined && c >= 0) this.traces.set(c, points);
    }
  }

  // One instant, then one picture.  `cx, cy` place the picture's origin
  // in the page's coordinates, so a hit region is testable against a
  // pointer event with no second transform — the canvas is sized to the
  // picture and the origin is its centre, which is where `gui.py` puts
  // it.
  step() {
    // A whole window cannot ride the scalar wire, so it is staged first
    // and spent by this tick (`web_list`).
    for (const [chan, points] of this.traces) {
      this.ex.web_list(this.w, BigInt(chan), this.doubles(points), points.length);
    }
    this.traces.clear();
    const flat = [];
    for (const [chan, value] of this.pending) flat.push(chan, value);
    this.pending.clear();
    const p = flat.length ? this.doubles(flat) : 0;
    const cx = this.el.width >> 1;
    const cy = this.el.height >> 1;
    this.ex.web_tick(this.w, p, flat.length >> 1, BigInt(-1), cx, cy);
    this.paint();
  }

  paint() {
    const base = this.ex.web_display(this.w);
    if (!base) return;
    const words = new Int32Array(this.ex.memory.buffer);
    const at = (i) => words[(base >> 2) + i];
    const items = at(0);
    const hits = at(1);
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.el.width, this.el.height);
    let c = 2;
    for (let n = 0; n < items; n++) {
      const kind = at(c);
      if (kind === 0) {
        ctx.fillStyle = rgb(at(c + 5));
        ctx.fillRect(at(c + 1), at(c + 2), at(c + 3), at(c + 4));
        c += 6;
      } else if (kind === 1) {
        ctx.fillStyle = rgb(at(c + 4));
        ctx.beginPath();
        ctx.arc(at(c + 1), at(c + 2), at(c + 3), 0, TAU);
        ctx.fill();
        c += 5;
      } else if (kind === 2) {
        const scale = at(c + 3);
        const len = at(c + 5);
        let s = "";
        for (let i = 0; i < len; i++) s += String.fromCodePoint(at(c + 6 + i));
        ctx.fillStyle = rgb(at(c + 4));
        // The panel draws its own 5×7 glyphs; a page has a font, and the
        // scale is what the walk already decided the text is worth.
        ctx.font = `${7 * scale}px ui-monospace, monospace`;
        ctx.textBaseline = "top";
        ctx.fillText(s, at(c + 1), at(c + 2));
        c += 6 + len;
      } else {
        return; // an unknown kind means the wire moved; draw nothing new
      }
    }
    this.regions = [];
    for (let n = 0; n < hits; n++) {
      this.regions.push({
        kind: at(c), axis: at(c + 1), extra: at(c + 2),
        x0: at(c + 3), y0: at(c + 4), x1: at(c + 5), y1: at(c + 6),
      });
      c += 7;
    }
  }

  // A hand.  The shell owns grabbing, so a drag that leaves the element
  // still reaches the fader it started on — which is what a fader is.
  press(x, y) { this.hand(this.ex.web_press(this.w, x, y)); }
  motion(x, y) { this.hand(this.ex.web_motion(this.w, x, y)); }
  release() { this.ex.web_release(this.w); this.grabbing = false; }

  hand(pairs) {
    this.grabbing = !!this.ex.web_grabbing(this.w);
    const n = Number(pairs);
    if (!n) return;
    const p = this.ex.web_writes(this.w);
    const got = new Float64Array(this.ex.memory.buffer, p, n * 2);
    const out = [];
    for (let i = 0; i < n; i++) out.push([got[i * 2], got[i * 2 + 1]]);
    // A touch's writes go back in on the next tick, so the picture
    // follows the hand; whether they also reach the *sound* is the
    // `clap.params` row and is not wired here.
    for (const [chan, value] of out) this.pending.set(chan, value);
    return out;
  }
}

function rgb(word) {
  return `rgb(${(word >> 16) & 255},${(word >> 8) & 255},${word & 255})`;
}
