//! gestate's CLAP shell — `spec/export.md`, target two.
//!
//! A CLAP plugin is a shared object the host probes for one symbol,
//! `clap_entry`, and everything else follows from the C structs that
//! symbol hands back: entry → factory → descriptor → plugin →
//! `process()`.  This file is that chain, wrapped around the two-symbol
//! engine contract in `engine.rs`.
//!
//! The shell has no opinions.  The graph decides the channel count and
//! the rate; the descriptor carries them; the shell's whole job is to
//! zero a state buffer, keep the control slots current, and turn the
//! engine's interleaved frames into the host's channel pointers.

mod abi;
mod engine;

use std::ffi::c_char;
use std::os::raw::c_void;

use abi::*;
use engine::{Descriptor, DESCRIPTOR};

// ── The instance ────────────────────────────────────────────────────────

/// `audioalloc.Voice`, in Rust: one voice of the bank and what it is
/// doing.  The semantics are that module's, mirrored deliberately —
/// free voices are taken released-longest-ago first (never-played
/// counts as released at the beginning of time), a full bank steals
/// the oldest, and a release finds the *oldest* voice on its key.
#[derive(Clone, Copy)]
struct VoiceState {
    key: Option<(i16, i16)>,
    started: i64,
    released: Option<i64>,
}

const FRESH_VOICE: VoiceState =
    VoiceState { key: None, started: -1, released: None };

/// One sounding instance: the zeroed state, the control slots at their
/// declared defaults, and a scratch buffer for the interleaved frames.
struct Instance {
    desc: &'static Descriptor,
    state: Vec<u8>,
    control: Vec<i64>,
    scratch: Vec<f32>,
    /// The transport's last word.  A rising edge rewinds — see
    /// `plugin_process`: a piece on a timeline starts when the
    /// timeline does.
    playing: bool,
    /// The instant the next block begins at — what a note's `gateAt`
    /// is stamped from, `t + event.time`, so an onset is
    /// sample-accurate however late in the block it lands.
    t: i64,
    voices: Vec<VoiceState>,
}

impl Instance {
    fn new(desc: &'static Descriptor) -> Self {
        let voices = engine::BANK.map_or(0, |b| b.voices.len());
        Instance {
            desc,
            state: vec![0u8; desc.state_bytes],
            control: desc.controls.iter().map(|c| c.init_bits).collect(),
            scratch: Vec::new(),
            playing: false,
            t: 0,
            voices: vec![FRESH_VOICE; voices],
        }
    }

    fn reset(&mut self) {
        // A fresh state is *zeroes*, not inits: the generated code's
        // first-instant branch seeds every node's `init` itself when
        // `t` is 0 — see `engine.rs`.
        self.state.iter_mut().for_each(|b| *b = 0);
        for (slot, c) in self.control.iter_mut().zip(self.desc.controls) {
            *slot = c.init_bits;
        }
        self.t = 0;
        self.voices.iter_mut().for_each(|v| *v = FRESH_VOICE);
    }

    /// The transport's rewind: the piece restarts, the knobs stay.
    ///
    /// Only non-knob slots reset — a knob's value is the *host's*
    /// belief (it drew the dial, it recorded the automation), and a
    /// plugin that quietly restored defaults on every play would
    /// disagree with its own parameter display from then on.
    fn rewind(&mut self) {
        self.state.iter_mut().for_each(|b| *b = 0);
        for (slot, c) in self.control.iter_mut().zip(self.desc.controls) {
            if !c.knob {
                *slot = c.init_bits;
            }
        }
        self.t = 0;
        self.voices.iter_mut().for_each(|v| *v = FRESH_VOICE);
    }

    /// `Allocator.note_on`: pick a voice, stamp its channels.  `at` is
    /// the note's own instant; `gateAt`/`offAt` are 1-based so an
    /// untouched bank reads as "never played" (`audioalloc`'s whole
    /// encoding).
    fn note_on(&mut self, at: i64, channel: i16, key: i16, velocity: f64) {
        let Some(bank) = engine::BANK else { return };
        let fields = bank.voices[0].len() - 2;
        let vel127 = (velocity * 127.0).round().clamp(0.0, 127.0) as i64;

        let mut payload = [0i64; 16];
        if let Some(table) = bank.table {
            let k = key.clamp(0, 127) as usize;
            let level = (vel127 as usize >> 2).min(table.levels - 1);
            let cell = k * table.levels + level;
            if !table.ok[cell] {
                return; // the instance declined: `Nothing` is an answer
            }
            let base = cell * table.fields;
            payload[..fields]
                .copy_from_slice(&table.data[base..base + fields]);
        } else {
            // The structural default the live path uses for a bank
            // with no `FromMIDI` instance: `(key, velocity)[:fields]`,
            // through each slot's own reinterpretation.
            let raw = [key as f64, vel127 as f64];
            for (j, slot) in bank.voices[0][2..].iter().enumerate() {
                payload[j] = self.desc.controls[*slot]
                    .bits_of(raw.get(j).copied().unwrap_or(0.0));
            }
        }

        // Free voices, released-longest-ago first; else steal oldest.
        let pick = self.voices.iter().enumerate()
            .filter(|(_, v)| v.key.is_none())
            .min_by_key(|(i, v)| (v.released.unwrap_or(-1), *i))
            .map(|(i, _)| i)
            .unwrap_or_else(|| {
                self.voices.iter().enumerate()
                    .min_by_key(|(i, v)| (v.started, *i))
                    .map(|(i, _)| i).unwrap()
            });

        self.voices[pick] =
            VoiceState { key: Some((channel, key)), started: at,
                         released: None };
        let chans = bank.voices[pick];
        self.control[chans[0]] = at + 1;
        self.control[chans[1]] = 0;
        for (j, slot) in chans[2..].iter().enumerate() {
            self.control[*slot] = payload[j];
        }
    }

    /// `Allocator.note_off`: the oldest voice on this key releases; a
    /// release for a key nothing plays is ordinary and is nothing.
    fn note_off(&mut self, at: i64, channel: i16, key: i16) {
        let Some(bank) = engine::BANK else { return };
        let held = self.voices.iter().enumerate()
            .filter(|(_, v)| v.key == Some((channel, key))
                    && v.released.is_none())
            .min_by_key(|(i, v)| (v.started, *i))
            .map(|(i, _)| i);
        if let Some(i) = held {
            self.voices[i].released = Some(at);
            self.voices[i].key = None;
            self.control[bank.voices[i][1]] = at + 1;
        }
    }

    /// Apply every `PARAM_VALUE` in the list to its slot.  At the
    /// block's start, not sample-accurately — which is not a corner
    /// cut: control rate in gestate *is* once per block, so this is
    /// the engine's own semantics meeting the host's event list.
    unsafe fn drain(&mut self, events: *const clap_input_events) {
        if events.is_null() {
            return;
        }
        let list = &*events;
        for i in 0..(list.size)(events) {
            let header = (list.get)(events, i);
            if header.is_null() {
                continue;
            }
            let h = &*header;
            if h.space_id != CLAP_CORE_EVENT_SPACE_ID {
                continue;
            }
            match h.type_ {
                CLAP_EVENT_PARAM_VALUE => {
                    let ev = &*(header as *const clap_event_param_value);
                    let slot = ev.param_id as usize;
                    if let Some(c) = self.desc.controls.get(slot) {
                        if c.knob {
                            self.control[slot] = c.bits_of(ev.value);
                        }
                    }
                }
                // Notes are stamped `t + event.time`: the *value*
                // carries the true onset, so an event late in the
                // block still begins its note at the right sample —
                // "a note delivered at a block boundary still begins
                // partway through the block".
                CLAP_EVENT_NOTE_ON => {
                    let ev = &*(header as *const clap_event_note);
                    self.note_on(self.t + h.time as i64, ev.channel,
                                 ev.key, ev.velocity);
                }
                CLAP_EVENT_NOTE_OFF | CLAP_EVENT_NOTE_CHOKE => {
                    let ev = &*(header as *const clap_event_note);
                    self.note_off(self.t + h.time as i64, ev.channel,
                                  ev.key);
                }
                _ => {}
            }
        }
    }

    fn process(&mut self, out: &clap_audio_buffer, frames: u32) {
        let ch = self.desc.channels as usize;
        let need = frames as usize * ch;
        if self.scratch.len() < need {
            self.scratch.resize(need, 0.0);
        }
        unsafe {
            engine::render(self.state.as_mut_ptr(),
                           self.scratch.as_mut_ptr(),
                           frames as i64,
                           self.control.as_ptr());
        }
        self.t += frames as i64;
        // The engine speaks interleaved frames; a CLAP port is one
        // pointer per channel.  A host channel past what the graph has
        // repeats the last one, which is how mono meets a stereo port.
        unsafe {
            let ports = out.channel_count as usize;
            for p in 0..ports {
                let dst = *out.data32.add(p);
                let src_ch = p.min(ch - 1);
                for i in 0..frames as usize {
                    *dst.add(i) = self.scratch[i * ch + src_ch];
                }
            }
        }
    }
}

// ── clap_plugin vtable ──────────────────────────────────────────────────

unsafe fn instance<'a>(plugin: *const clap_plugin) -> &'a mut Instance {
    &mut *((*plugin).plugin_data as *mut Instance)
}

unsafe extern "C" fn plugin_init(_plugin: *const clap_plugin) -> bool {
    true
}

unsafe extern "C" fn plugin_destroy(plugin: *const clap_plugin) {
    drop(Box::from_raw((*plugin).plugin_data as *mut Instance));
    drop(Box::from_raw(plugin as *mut clap_plugin));
}

unsafe extern "C" fn plugin_activate(plugin: *const clap_plugin,
                                     sample_rate: f64,
                                     _min_frames: u32,
                                     _max_frames: u32) -> bool {
    // `sampleRate` is a constant folded through the compiled graph, so
    // the first cut refuses the rates it would lie at rather than
    // resampling behind the host's back — `spec/export.md`, "what
    // export must refuse".
    let inst = instance(plugin);
    if sample_rate as u32 != inst.desc.rate {
        return false;
    }
    inst.reset();
    true
}

unsafe extern "C" fn plugin_deactivate(_plugin: *const clap_plugin) {}

unsafe extern "C" fn plugin_start(_plugin: *const clap_plugin) -> bool {
    true
}

unsafe extern "C" fn plugin_stop(_plugin: *const clap_plugin) {}

unsafe extern "C" fn plugin_reset(plugin: *const clap_plugin) {
    instance(plugin).reset();
}

unsafe extern "C" fn plugin_process(plugin: *const clap_plugin,
                                    process: *const clap_process)
                                    -> clap_process_status {
    let p = &*process;
    if p.audio_outputs_count == 0 || p.audio_outputs.is_null() {
        return CLAP_PROCESS_ERROR;
    }
    let out = &*p.audio_outputs;
    if out.data32.is_null() {
        return CLAP_PROCESS_ERROR;
    }
    let inst = instance(plugin);
    // **One rule: it plays while the transport runs, or while a note
    // does.**  Self-playing material lives on the timeline — silence
    // while stopped, and the rising edge rewinds to the piece's top,
    // sparing the knobs (`rewind` vs `reset`: a knob's value is the
    // host's belief).  Notes live under the player's hands — a DAW
    // sends keyboard notes with the timeline stopped, and they must
    // sound, held or ringing out; a voice counts as ringing for ten
    // seconds after its release, which is what lets a tail die
    // naturally instead of being cut at the key.  A hybrid — a bed
    // with a bank on top — gets both halves of the rule at once.
    //
    // The transport is handled **before** the events drain.  It was
    // the other way once, and the first note of every play — which
    // always shares a block with the play edge — was applied and then
    // wiped by the rewind.  A null transport is a free-running host,
    // and everything simply plays.
    let mut stopped = false;
    if !p.transport.is_null() {
        let now = (*p.transport).flags & CLAP_TRANSPORT_IS_PLAYING != 0;
        if now && !inst.playing {
            inst.rewind();
        }
        inst.playing = now;
        stopped = !now;
    }
    inst.drain(p.in_events);
    let grace = 10 * inst.desc.rate as i64;
    let keyed = inst.voices.iter().any(|v| {
        v.key.is_some()
            || v.released.map_or(false, |r| inst.t - r < grace)
    });
    if stopped && !keyed {
        let ports = out.channel_count as usize;
        for c in 0..ports {
            std::ptr::write_bytes(*out.data32.add(c), 0,
                                  p.frames_count as usize);
        }
        return CLAP_PROCESS_CONTINUE;
    }
    inst.process(out, p.frames_count);
    CLAP_PROCESS_CONTINUE
}

// ── Audio ports: the one extension that is not optional ────────────────

unsafe extern "C" fn ports_count(_plugin: *const clap_plugin,
                                 is_input: bool) -> u32 {
    (!is_input) as u32
}

unsafe extern "C" fn ports_get(plugin: *const clap_plugin, index: u32,
                               is_input: bool,
                               info: *mut clap_audio_port_info) -> bool {
    if is_input || index != 0 || info.is_null() {
        return false;
    }
    let channels = instance(plugin).desc.channels;
    let out = &mut *info;
    out.id = 0;
    out.name = [0; CLAP_NAME_SIZE];
    for (dst, src) in out.name.iter_mut().zip(b"out\0") {
        *dst = *src as c_char;
    }
    out.flags = CLAP_AUDIO_PORT_IS_MAIN;
    out.channel_count = channels;
    out.port_type = if channels == 2 {
        CLAP_PORT_STEREO.as_ptr() as *const c_char
    } else {
        CLAP_PORT_MONO.as_ptr() as *const c_char
    };
    out.in_place_pair = CLAP_INVALID_ID;
    true
}

static AUDIO_PORTS: clap_plugin_audio_ports = clap_plugin_audio_ports {
    count: ports_count,
    get: ports_get,
};

// ── Params: the knobs, as the DAW's own ────────────────────────────────
//
// A parameter's id *is* its control slot index, so an id needs no
// table to resolve; the non-knob slots — a bank's note channels —
// simply advertise no parameter over them.  Names are the channel's,
// with a trailing `Chan` trimmed: `cutoffChan` is the author's
// spelling of a channel, `cutoff` of a knob.

unsafe fn nth_knob(plugin: *const clap_plugin, index: u32)
                   -> Option<(usize, &'static engine::Control)> {
    instance(plugin).desc.controls.iter().enumerate()
        .filter(|(_, c)| c.knob)
        .nth(index as usize)
}

unsafe extern "C" fn params_count(plugin: *const clap_plugin) -> u32 {
    instance(plugin).desc.controls.iter().filter(|c| c.knob).count() as u32
}

unsafe extern "C" fn params_get_info(plugin: *const clap_plugin,
                                     index: u32,
                                     info: *mut clap_param_info) -> bool {
    let Some((slot, c)) = nth_knob(plugin, index) else {
        return false;
    };
    if info.is_null() {
        return false;
    }
    let out = &mut *info;
    out.id = slot as u32;
    out.flags = CLAP_PARAM_IS_AUTOMATABLE
        | if c.kind == engine::Kind::Int { CLAP_PARAM_IS_STEPPED }
          else { 0 };
    out.cookie = std::ptr::null_mut();
    out.name = [0; CLAP_NAME_SIZE];
    let shown = c.chan.strip_suffix("Chan").unwrap_or(c.chan);
    for (dst, src) in out.name.iter_mut()
        .zip(shown.bytes().take(CLAP_NAME_SIZE - 1)) {
        *dst = src as c_char;
    }
    out.module = [0; CLAP_PATH_SIZE];
    out.min_value = c.min;
    out.max_value = c.max;
    out.default_value = c.init_value();
    true
}

unsafe extern "C" fn params_get_value(plugin: *const clap_plugin,
                                      param_id: u32,
                                      out: *mut f64) -> bool {
    let inst = instance(plugin);
    let slot = param_id as usize;
    match inst.desc.controls.get(slot) {
        Some(c) if c.knob && !out.is_null() => {
            *out = c.value_of(inst.control[slot]);
            true
        }
        _ => false,
    }
}

unsafe extern "C" fn params_value_to_text(plugin: *const clap_plugin,
                                          param_id: u32, value: f64,
                                          out: *mut c_char,
                                          capacity: u32) -> bool {
    let slot = param_id as usize;
    let Some(c) = instance(plugin).desc.controls.get(slot) else {
        return false;
    };
    if !c.knob || out.is_null() || capacity == 0 {
        return false;
    }
    let text = match c.kind {
        engine::Kind::Int => format!("{}", value.round() as i64),
        engine::Kind::Float => format!("{value:.3}"),
    };
    let take = text.len().min(capacity as usize - 1);
    std::ptr::copy_nonoverlapping(text.as_ptr() as *const c_char,
                                  out, take);
    *out.add(take) = 0;
    true
}

unsafe extern "C" fn params_text_to_value(plugin: *const clap_plugin,
                                          param_id: u32,
                                          text: *const c_char,
                                          out: *mut f64) -> bool {
    let slot = param_id as usize;
    let Some(c) = instance(plugin).desc.controls.get(slot) else {
        return false;
    };
    if !c.knob || text.is_null() || out.is_null() {
        return false;
    }
    match std::ffi::CStr::from_ptr(text).to_str()
        .ok().and_then(|s| s.trim().parse::<f64>().ok()) {
        Some(v) => {
            *out = v;
            true
        }
        None => false,
    }
}

unsafe extern "C" fn params_flush(plugin: *const clap_plugin,
                                  in_events: *const clap_input_events,
                                  _out: *const clap_output_events) {
    instance(plugin).drain(in_events);
}

static PARAMS: clap_plugin_params = clap_plugin_params {
    count: params_count,
    get_info: params_get_info,
    get_value: params_get_value,
    value_to_text: params_value_to_text,
    text_to_value: params_text_to_value,
    flush: params_flush,
};

// ── Note ports: a keyboard's door to the bank ───────────────────────────

unsafe extern "C" fn notes_count(_plugin: *const clap_plugin,
                                 is_input: bool) -> u32 {
    (is_input && engine::BANK.is_some()) as u32
}

unsafe extern "C" fn notes_get(_plugin: *const clap_plugin, index: u32,
                               is_input: bool,
                               info: *mut clap_note_port_info) -> bool {
    if !is_input || index != 0 || info.is_null() || engine::BANK.is_none() {
        return false;
    }
    let out = &mut *info;
    out.id = 0;
    out.supported_dialects = CLAP_NOTE_DIALECT_CLAP;
    out.preferred_dialect = CLAP_NOTE_DIALECT_CLAP;
    out.name = [0; CLAP_NAME_SIZE];
    for (dst, src) in out.name.iter_mut().zip(b"notes\0") {
        *dst = *src as c_char;
    }
    true
}

static NOTE_PORTS: clap_plugin_note_ports = clap_plugin_note_ports {
    count: notes_count,
    get: notes_get,
};

unsafe extern "C" fn plugin_get_extension(_plugin: *const clap_plugin,
                                          id: *const c_char)
                                          -> *const c_void {
    if !id.is_null() {
        let want = std::ffi::CStr::from_ptr(id);
        if want.to_bytes_with_nul() == CLAP_EXT_AUDIO_PORTS {
            return &AUDIO_PORTS as *const _ as *const c_void;
        }
        if want.to_bytes_with_nul() == CLAP_EXT_PARAMS {
            return &PARAMS as *const _ as *const c_void;
        }
        if want.to_bytes_with_nul() == CLAP_EXT_NOTE_PORTS
            && engine::BANK.is_some() {
            return &NOTE_PORTS as *const _ as *const c_void;
        }
    }
    // A null for the rest is a plugin without those extensions,
    // which hosts accept.
    std::ptr::null()
}

unsafe extern "C" fn plugin_on_main_thread(_plugin: *const clap_plugin) {}

// ── Descriptor, factory, entry ──────────────────────────────────────────

const FEATURES: [*const c_char; 3] = [
    CLAP_PLUGIN_FEATURE_INSTRUMENT.as_ptr() as *const c_char,
    CLAP_PLUGIN_FEATURE_SYNTHESIZER.as_ptr() as *const c_char,
    std::ptr::null(),
];

/// The descriptor's strings live in `engine::Descriptor` as `&str`s;
/// CLAP wants C strings with static lifetime, so they are materialised
/// once, NUL-terminated, and leaked on purpose — a plugin's identity
/// lives as long as its library does.
fn c_leak(s: &str) -> *const c_char {
    let mut owned = String::with_capacity(s.len() + 1);
    owned.push_str(s);
    owned.push('\0');
    Box::leak(owned.into_boxed_str()).as_ptr() as *const c_char
}

static mut CLAP_DESC: Option<clap_plugin_descriptor> = None;

unsafe fn clap_descriptor(desc: &'static Descriptor)
                          -> *const clap_plugin_descriptor {
    let slot = &raw mut CLAP_DESC;
    if (*slot).is_none() {
        let empty = b"\0".as_ptr() as *const c_char;
        *slot = Some(clap_plugin_descriptor {
            clap_version: CLAP_VERSION,
            id: c_leak(desc.id),
            name: c_leak(desc.name),
            vendor: c_leak("gestate"),
            url: empty,
            manual_url: empty,
            support_url: empty,
            version: c_leak(desc.version),
            description: c_leak("A gestate graph: fixed memory, \
                                 bounded work per block."),
            features: FEATURES.as_ptr(),
        });
    }
    (*slot).as_ref().unwrap() as *const _
}

unsafe extern "C" fn factory_count(_f: *const clap_plugin_factory) -> u32 {
    DESCRIPTOR.is_some() as u32
}

unsafe extern "C" fn factory_descriptor(_f: *const clap_plugin_factory,
                                        index: u32)
                                        -> *const clap_plugin_descriptor {
    match DESCRIPTOR {
        Some(desc) if index == 0 => clap_descriptor(desc),
        _ => std::ptr::null(),
    }
}

unsafe extern "C" fn factory_create(_f: *const clap_plugin_factory,
                                    _host: *const clap_host,
                                    _id: *const c_char)
                                    -> *const clap_plugin {
    let Some(desc) = DESCRIPTOR else {
        return std::ptr::null();
    };
    let data = Box::into_raw(Box::new(Instance::new(desc)));
    Box::into_raw(Box::new(clap_plugin {
        desc: clap_descriptor(desc),
        plugin_data: data as *mut c_void,
        init: plugin_init,
        destroy: plugin_destroy,
        activate: plugin_activate,
        deactivate: plugin_deactivate,
        start_processing: plugin_start,
        stop_processing: plugin_stop,
        reset: plugin_reset,
        process: plugin_process,
        get_extension: plugin_get_extension,
        on_main_thread: plugin_on_main_thread,
    }))
}

static FACTORY: clap_plugin_factory = clap_plugin_factory {
    get_plugin_count: factory_count,
    get_plugin_descriptor: factory_descriptor,
    create_plugin: factory_create,
};

unsafe extern "C" fn entry_init(_path: *const c_char) -> bool {
    true
}

unsafe extern "C" fn entry_deinit() {}

unsafe extern "C" fn entry_get_factory(id: *const c_char) -> *const c_void {
    if id.is_null() {
        return std::ptr::null();
    }
    let want = std::ffi::CStr::from_ptr(id);
    if want.to_bytes_with_nul() == CLAP_PLUGIN_FACTORY_ID {
        &FACTORY as *const _ as *const c_void
    } else {
        std::ptr::null()
    }
}

/// The one symbol a host looks for.
#[no_mangle]
#[allow(non_upper_case_globals)]
pub static clap_entry: clap_plugin_entry = clap_plugin_entry {
    clap_version: CLAP_VERSION,
    init: entry_init,
    deinit: entry_deinit,
    get_factory: entry_get_factory,
};

// SAFETY: every field is a fn pointer or plain data the host reads.
unsafe impl Sync for clap_plugin_entry {}
unsafe impl Sync for clap_plugin_factory {}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_entry_answers_for_the_factory_and_nothing_else() {
        unsafe {
            let ok = entry_get_factory(
                CLAP_PLUGIN_FACTORY_ID.as_ptr() as *const c_char);
            assert!(!ok.is_null());
            let no = entry_get_factory(b"clap.wrong\0".as_ptr()
                                       as *const c_char);
            assert!(no.is_null());
            assert!(entry_get_factory(std::ptr::null()).is_null());
        }
    }

    #[test]
    fn an_empty_shell_offers_no_plugin() {
        // Without the `engine` feature the factory must say zero —
        // a host that loads this sees a well-formed library with
        // nothing in it, never a plugin that cannot sound.
        unsafe {
            let n = factory_count(&FACTORY);
            assert_eq!(n as usize, DESCRIPTOR.iter().count());
        }
    }
}
