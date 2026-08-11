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
#[cfg(feature = "dynscore")]
pub mod dynscore;
pub mod engine;
#[cfg(feature = "gui")]
mod gui;
mod score;

use std::ffi::c_char;
use std::os::raw::c_void;

use abi::*;
use engine::{Descriptor, DESCRIPTOR};
use score::{NoteKey, VoiceState, FRESH_VOICE};

// ── The instance ────────────────────────────────────────────────────────
//
// (`VoiceState` and the allocation itself live in `score.rs` now,
// shared between this file's MIDI path and the score cursor — one
// bank is one set of voices however its notes arrive.)

/// One sounding instance: the zeroed state, the control slots at their
/// declared defaults, and a scratch buffer for the interleaved frames.
pub(crate) struct Instance {
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
    /// Per bank, per voice.
    voices: Vec<Vec<VoiceState>>,
    /// The routing matrix, one 16-bit row per bank: bit `c` set means
    /// the bank listens on MIDI channel `c`.  Defaults to the
    /// diagonal — channel *n* plays bank *n*, `audiomidi
    /// .by_midi_channel`'s own rule — and every cell is a stepped
    /// parameter, so the DAW's generic UI *is* the checkbox matrix.
    routing: Vec<u16>,
    /// Per bank, whether the score plays it — the other half of the
    /// switch whose first half is `routing`.  Defaults to the banks the
    /// score actually writes, so a piece plays itself and a keyboard
    /// bank stays the keyboard's.
    plays_score: Vec<bool>,
    /// The compiled rate `activate` picked — the graph being played.
    active: Option<&'static engine::RateCase>,
    /// The shell's own beat position, for a host with a tempo but no
    /// beats timeline; a timeline host overwrites it every block.
    beat_pos: f64,
    /// The score cursor — `spec/dynamicscore.md` stage one's Rust
    /// half.  Idle for a plugin whose `SCORE` is empty.
    performer: score::Performer,
    /// The piece as a program, for a score no event list can hold —
    /// opened on `activate`, when the rate is finally known.
    #[cfg(feature = "dynscore")]
    piece: Option<dynscore::Performer>,
    /// The host, kept from `factory_create` so a panel can ask it to
    /// flush a change made while the transport is stopped
    /// (`spec/panel.md` §"What the ABI has to grow").
    host: *const clap_host,
    #[cfg(feature = "gui")]
    gui: gui::Gui,
    /// Panel changes applied here and still owed to the host.
    #[cfg(feature = "gui")]
    gui_outbox: Vec<gestate_panel::Change>,
}

/// Whether the score plays each bank, before anyone says otherwise:
/// the banks it actually writes.
fn default_plays() -> Vec<bool> {
    (0..engine::BANKS.len())
        .map(|b| engine::SCORED.get(b).copied().unwrap_or(false))
        .collect()
}

/// Which MIDI channel feeds which bank, before anyone says otherwise.
///
/// **Scored banks get nothing.**  The old default was the plain
/// diagonal — channel *n* plays bank *n* — which is right for an
/// instrument and wrong for a piece: it routes the player's notes into
/// the voices the score is using, so the score falls silent and the
/// player hears only themselves.  `moods` writes *both* its banks, and
/// under the diagonal every key pressed took one away from it.
///
/// So the channels go to the banks the piece does **not** write, in
/// order: the first unscored bank is channel 1, the next is channel 2.
/// A piece that plays everything accepts no MIDI by default, which is
/// the honest reading of a self-playing piece — and every cell is still
/// a parameter, so a player who wants to double a scored bank by hand
/// can switch it on in the panel.
fn default_routing() -> Vec<u16> {
    let any_free = (0..engine::BANKS.len())
        .any(|b| !engine::SCORED.get(b).copied().unwrap_or(false));
    if !any_free {
        // **A plugin must be playable by hand.**  When the piece owns
        // every bank there is no free one to give the channels to, and
        // refusing MIDI outright would make the instrument
        // indistinguishable from a broken one — `fmpoly` is a piano
        // with a demo score, and a piano you cannot play is not an
        // improvement.  So the diagonal stands, and the `from score`
        // switch is how a player hands a bank over instead.
        return (0..engine::BANKS.len())
            .map(|b| if b < 16 { 1 << b } else { 0 })
            .collect();
    }
    let mut next = 0u32;
    engine::BANKS.iter().enumerate().map(|(b, _)| {
        let scored = engine::SCORED.get(b).copied().unwrap_or(false);
        if scored || next >= 16 {
            return 0;
        }
        let bit = 1u16 << next;
        next += 1;
        bit
    }).collect()
}

impl Instance {
    fn new(desc: &'static Descriptor) -> Self {
        Instance {
            desc,
            state: Vec::new(),
            control: desc.controls.iter().map(|c| c.init_bits).collect(),
            scratch: Vec::new(),
            playing: false,
            t: 0,
            voices: engine::BANKS.iter()
                .map(|b| vec![FRESH_VOICE; b.voices.len()]).collect(),
            routing: default_routing(),
            plays_score: default_plays(),
            active: None,
            beat_pos: 0.0,
            performer: score::Performer::new(),
            host: std::ptr::null(),
            #[cfg(feature = "dynscore")]
            piece: None,
            #[cfg(feature = "gui")]
            gui: gui::Gui::default(),
            #[cfg(feature = "gui")]
            gui_outbox: Vec::new(),
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
        self.beat_pos = 0.0;
        self.voices.iter_mut()
            .for_each(|bank| bank.iter_mut()
                      .for_each(|v| *v = FRESH_VOICE));
        self.routing = default_routing();
        self.performer.reset();
    }

    /// The transport's rewind: the piece restarts, the knobs stay.
    ///
    /// Only non-knob slots reset — a knob's value is the *host's*
    /// belief (it drew the dial, it recorded the automation), and a
    /// plugin that quietly restored defaults on every play would
    /// disagree with its own parameter display from then on.  The
    /// routing matrix is the host's belief too, and survives.
    /// The transport rewound: the piece starts again from its top.
    ///
    /// **The player's hands are not the piece.**  A rewind wipes the
    /// engine, the cursor and the score's voices — but a key held
    /// across the moment you press play is still held afterwards, and
    /// erasing it made a listening score answer an empty world at
    /// exactly the instant a player had set one up.  So the MIDI voices
    /// are taken down and put back: their records survive, and their
    /// gates are re-stamped at the rewound clock so the engine, which
    /// *is* zeroed, sounds them again from zero.
    ///
    /// This is `score::Performer::seek`'s rule — only scored banks are
    /// touched — applied to the coarser move.
    fn rewind(&mut self) {
        let held: Vec<(usize, usize, NoteKey, Vec<i64>)> = self.voices
            .iter().enumerate().flat_map(|(b, bank)| {
                bank.iter().enumerate().filter_map(move |(i, v)| {
                    match v.key {
                        Some(k @ NoteKey::Midi(..)) if v.released.is_none() =>
                            Some((b, i, k)),
                        _ => None,
                    }
                })
            })
            .filter_map(|(b, i, k)| {
                // Checked, not indexed: this runs on the audio thread
                // inside a host, where a panic is that host's crash.
                let slots = engine::BANKS.get(b)?.voices.get(i)?;
                let payload: Vec<i64> = slots.iter().skip(2)
                    .filter_map(|s| self.control.get(*s).copied())
                    .collect();
                Some((b, i, k, payload))
            })
            .collect();

        self.state.iter_mut().for_each(|b| *b = 0);
        for (slot, c) in self.control.iter_mut().zip(self.desc.controls) {
            if !c.knob {
                *slot = c.init_bits;
            }
        }
        self.t = 0;
        self.beat_pos = 0.0;
        self.voices.iter_mut()
            .for_each(|bank| bank.iter_mut()
                      .for_each(|v| *v = FRESH_VOICE));
        self.performer.reset();

        for (b, i, key, payload) in held {
            let Some(slots) = engine::BANKS.get(b)
                .and_then(|bk| bk.voices.get(i)) else { continue };
            if let Some(v) = self.voices.get_mut(b)
                .and_then(|bk| bk.get_mut(i))
            {
                *v = VoiceState { key: Some(key), started: 0,
                                  released: None };
            }
            let mut put = |slot: usize, value: i64| {
                if let Some(c) = self.control.get_mut(slot) {
                    *c = value;
                }
            };
            if let Some(g) = slots.first() { put(*g, 1); }   // the new zero
            if let Some(o) = slots.get(1) { put(*o, 0); }
            for (slot, value) in slots.iter().skip(2).zip(&payload) {
                put(*slot, *value);
            }
        }
    }

    /// `Allocator.note_on`, per routed bank: the routing matrix says
    /// which banks hear channel `channel`, and each that does
    /// allocates its own voice — two banks on one channel is a
    /// layered patch, which is what a matrix buys over a selector.
    fn note_on(&mut self, at: i64, channel: i16, key: i16, velocity: f64) {
        let ch = channel.clamp(0, 15) as u16;
        for b in 0..engine::BANKS.len() {
            if self.routing[b] & (1 << ch) != 0 {
                self.note_on_bank(b, at, channel, key, velocity);
            }
        }
    }

    /// One bank's `note_on`: pick a voice, stamp its channels.  `at`
    /// is the note's own instant; `gateAt`/`offAt` are 1-based so an
    /// untouched bank reads as "never played" (`audioalloc`'s whole
    /// encoding).
    fn note_on_bank(&mut self, b: usize, at: i64, channel: i16, key: i16,
                    velocity: f64) {
        let bank = &engine::BANKS[b];
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

        // Free voices, released-longest-ago first; else steal oldest —
        // `score::pick_voice`, the same allocation the cursor uses.
        let vs = &mut self.voices[b];
        let pick = score::pick_voice(vs);
        vs[pick] = VoiceState { key: Some(NoteKey::Midi(channel, key)),
                                started: at, released: None };
        let chans = bank.voices[pick];
        self.control[chans[0]] = at + 1;
        self.control[chans[1]] = 0;
        for (j, slot) in chans[2..].iter().enumerate() {
            self.control[*slot] = payload[j];
        }
    }

    /// `Allocator.note_off`, in **every** bank holding this key — not
    /// only the routed ones, because the matrix may have changed while
    /// the note was down, and a note that cannot be released is worse
    /// than one that plays on the wrong bank.
    fn note_off(&mut self, at: i64, channel: i16, key: i16) {
        for (b, bank) in engine::BANKS.iter().enumerate() {
            if let Some(i) = score::release_voice(
                &mut self.voices[b], NoteKey::Midi(channel, key), at) {
                self.control[bank.voices[i][1]] = at + 1;
            }
        }
    }

    /// Apply every `PARAM_VALUE` in the list to its slot.  At the
    /// block's start, not sample-accurately — which is not a corner
    /// cut: control rate in gestate *is* once per block, so this is
    /// the engine's own semantics meeting the host's event list.
    /// One parameter into this instance — a knob's slot, or a routing
    /// cell's bit.
    ///
    /// **One place, because there are two writers.**  The host writes
    /// parameters through `drain`; the panel writes them through
    /// `emit_gui_changes`.  When only `drain` knew how to apply a
    /// routing cell, a click in the panel changed the picture and
    /// nothing else until the host happened to echo the value back —
    /// which is a matrix that looks like it works.
    fn apply_param(&mut self, param_id: u32, value: f64) {
        let id = param_id as usize;
        let n = self.desc.controls.len();
        if id < n {
            if let Some(c) = self.desc.controls.get(id) {
                if c.knob {
                    self.control[id] = c.bits_of(value);
                }
            }
            return;
        }
        // Above the control slots: `n + bank*16 + channel` is a
        // routing cell, and past the whole matrix comes one score
        // switch per bank.
        let cell = id - n;
        let cells = engine::BANKS.len() * 16;
        if cell >= cells {
            if let Some(on) = self.plays_score.get_mut(cell - cells) {
                *on = value >= 0.5;
            }
            return;
        }
        let (b, ch) = (cell / 16, cell % 16);
        if b >= self.routing.len() {
            return;
        }
        if value >= 0.5 {
            self.routing[b] |= 1 << ch;
            return;
        }
        self.routing[b] &= !(1 << ch);
        // **And let go of what that channel is holding.**  Routing is
        // read at note-*on*, so a cell switched off while a key is down
        // would otherwise leave the note sounding until the player
        // happened to release it — a control that looks dead, because
        // the only way to hear it is to stop playing.  A bank that no
        // longer listens to a channel releases the voices that channel
        // put there, and nothing else: notes from other channels, and
        // the score's own notes, are not this cell's business.
        let at = self.t;
        let Some(bank) = engine::BANKS.get(b) else { return };
        for i in 0..self.voices[b].len() {
            let v = self.voices[b][i];
            let Some(NoteKey::Midi(vch, _)) = v.key else { continue };
            if vch as usize != ch || v.released.is_some() {
                continue;
            }
            self.voices[b][i].released = Some(at);
            self.voices[b][i].key = None;
            if let Some(off) = bank.voices.get(i).and_then(|c| c.get(1)) {
                if let Some(slot) = self.control.get_mut(*off) {
                    *slot = at + 1;
                }
            }
        }
    }

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
                    self.apply_param(ev.param_id, ev.value);
                    // **Every parameter, not just the knobs.**
                    // Automation and the host's own generic UI reach
                    // the panel here and only here, and a routing cell
                    // switched from the DAW's own view has to move the
                    // matrix too — otherwise the two disagree and the
                    // panel is the one that looks broken.
                    #[cfg(feature = "gui")]
                    self.report_to_gui(ev.param_id, ev.value);
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
        if let Some(case) = self.active {
            unsafe {
                (case.render)(self.state.as_mut_ptr(),
                              self.scratch.as_mut_ptr(),
                              frames as i64,
                              self.control.as_ptr());
            }
        } else {
            self.scratch[..need].fill(0.0);
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
    // The host's own extensions are readable from `init` onwards, and
    // this is the first thing in this shell that wants one: the panel
    // has to be able to ask for a flush, or a control moved while the
    // transport is stopped waits for play.
    #[cfg(feature = "gui")]
    {
        let inst = instance(_plugin);
        inst.gui.queue.attach(inst.host);
    }
    true
}

unsafe extern "C" fn plugin_destroy(plugin: *const clap_plugin) {
    drop(Box::from_raw((*plugin).plugin_data as *mut Instance));
    drop(Box::from_raw(plugin as *mut clap_plugin));
}

/// Whether this plugin carries a piece it must force rather than read.
#[cfg(feature = "dynscore")]
fn has_program() -> bool {
    engine::program().is_some()
}

#[cfg(not(feature = "dynscore"))]
fn has_program() -> bool {
    false
}

/// The world a listening piece asks about: the keys held on each bank.
///
/// **Taken before the performance advances**, and that is not an
/// implementation detail — a question is answered with the world at its
/// own instant, and the block boundary is where a host's note events
/// have all landed.  Sorted, because a chord is a set but a reading is
/// a value in a transcript and one spelling of it replays.
#[cfg(feature = "dynscore")]
fn held_keys(inst: &Instance) -> Vec<Vec<i64>> {
    inst.voices.iter().map(|bank| {
        let mut keys: Vec<i64> = bank.iter().filter_map(|v| match v.key {
            Some(NoteKey::Midi(_ch, note)) if v.released.is_none() =>
                Some(note as i64),
            _ => None,
        }).collect();
        keys.sort_unstable();
        keys.dedup();
        keys
    }).collect()
}

/// The forced piece follows the transport's jump.
#[cfg(feature = "dynscore")]
unsafe fn seek_piece(inst: &mut Instance, tb: &score::Tables, tempo: f64,
                     target: i64) {
    let Some(mut perf) = inst.piece.take() else { return };
    if let Some(program) = engine::program() {
        perf.origin = inst.performer.origin;
        perf.seek(program, tb, tempo, target, inst.t,
                  &mut inst.voices, &mut inst.control);
    }
    inst.piece = Some(perf);
}

/// Force and perform the program's own notes for this block.
#[cfg(feature = "dynscore")]
unsafe fn advance_piece(inst: &mut Instance, tb: &score::Tables,
                        tempo: f64, end: i64, frames: i64) {
    let Some(mut perf) = inst.piece.take() else { return };
    let Some(program) = engine::program() else {
        inst.piece = Some(perf);
        return;
    };
    let held = held_keys(inst);
    perf.origin = inst.performer.origin;
    perf.advance(program, tb, tempo, &mut inst.voices,
                 &mut inst.control, end, frames.max(1),
                 &|bank| held.get(bank).cloned().unwrap_or_default());
    inst.piece = Some(perf);
}

/// Open the piece, if this plugin carries one.
///
/// **At `activate`, not at `init`** — the program is forced against a
/// rate, and the rate is what `activate` is for.  A refusal is kept and
/// reported rather than thrown: a plugin whose piece will not load is
/// still an instrument you can play with your hands.
#[cfg(feature = "dynscore")]
unsafe fn open_piece(inst: &mut Instance) {
    inst.piece = engine::program()
        .and_then(|p| dynscore::Piece::open(p, 0).ok())
        .map(dynscore::Performer::new);
}

unsafe extern "C" fn plugin_activate(plugin: *const clap_plugin,
                                     sample_rate: f64,
                                     _min_frames: u32,
                                     _max_frames: u32) -> bool {
    // `sampleRate` is a constant folded through the compiled graph, so
    // a plugin carries one whole graph per rate it is honest at
    // (`RATES`) and still refuses the rates it would lie at rather
    // than resampling behind the host's back — `spec/export.md`.
    let inst = instance(plugin);
    let Some(case) = engine::RATES.iter()
        .find(|c| c.rate == sample_rate as u32) else {
        return false;
    };
    inst.active = Some(case);
    inst.state = vec![0u8; case.state_bytes];
    inst.reset();
    #[cfg(feature = "dynscore")]
    open_piece(inst);
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
    let mut rose = false;
    let mut fell = false;
    if !p.transport.is_null() {
        let now = (*p.transport).flags & CLAP_TRANSPORT_IS_PLAYING != 0;
        rose = now && !inst.playing;
        fell = !now && inst.playing;
        if rose {
            inst.rewind();
            // **Two plays are one performance.**  A baked cursor
            // rewinds by resetting its index; a forced one has to
            // re-open its stream, or the second play carries on from
            // wherever the first one stopped.
            #[cfg(feature = "dynscore")]
            open_piece(inst);
        }
        inst.playing = now;
        stopped = !now;
    }
    // **The hands, before the piece asks about them.**  A listening
    // score's question is answered with the world at its own instant,
    // and a note that arrived in *this* block is part of that world —
    // draining after the score advanced answered every question with
    // the previous block's hands, which is a ladder that plays the
    // chord it was holding a block ago, or nothing.
    inst.drain(p.in_events);
    // **The host clock**: `beat` and `beatRate` are the renderer's
    // own, and in a DAW the renderer is the transport.  The three
    // descriptor-declared slots carry a *line* — beat at this block's
    // start, beats per second, and the anchor sample — which the
    // program's `beat` evaluates at `ticks`, audio-rate smooth.  A
    // timeline host pins the position exactly; a tempo-only host gets
    // the shell's own accumulation; a stopped transport freezes the
    // clock by zeroing the slope; and no transport at all leaves the
    // channels at their defaults — the program conducts itself at its
    // declared `bpm`, exactly as it does offline.
    if let (Some((b, s, t0)), false) =
        (engine::BEAT_SLOTS, p.transport.is_null()) {
        let tr = &*p.transport;
        if tr.flags & CLAP_TRANSPORT_HAS_TEMPO != 0 && tr.tempo > 0.0 {
            let rate = inst.active.map_or(48000, |c| c.rate) as f64;
            let playing = tr.flags & CLAP_TRANSPORT_IS_PLAYING != 0;
            let bps = tr.tempo / 60.0;
            if tr.flags & CLAP_TRANSPORT_HAS_BEATS_TIMELINE != 0 {
                inst.beat_pos = tr.song_pos_beats as f64
                    / CLAP_BEATTIME_FACTOR as f64;
            }
            inst.control[b] = inst.beat_pos.to_bits() as i64;
            inst.control[s] = (if playing { bps } else { 0.0 })
                .to_bits() as i64;
            inst.control[t0] = inst.t;
            if playing
                && tr.flags & CLAP_TRANSPORT_HAS_BEATS_TIMELINE == 0 {
                inst.beat_pos += bps * p.frames_count as f64 / rate;
            }
        }
    }
    // **The score cursor** — `spec/dynamicscore.md` stage one's Rust
    // half.  The piece's events live in *beats* in the descriptor; the
    // cursor performs each as the timeline reaches it, a jump in the
    // timeline is a seek (a loop is a seek on a boundary, and the
    // second pass is the first), and a host with no transport at all
    // free-runs the piece at its own declared tempo — everything
    // simply plays.  Steady playback stays anchored to `origin`
    // rather than re-deriving it per block, so the delivery
    // boundaries and the stamped instants keep the bake's exact
    // integers, which is the stage's parity clause.
    // **Or a program**: an unfolding piece has an empty `SCORE` — that
    // is the whole reason it carries an interpreter — so a guard on the
    // event list alone silences exactly the scores this stage exists
    // for.  The cursor below does nothing for them; `advance_piece`
    // does the work.
    if !engine::SCORE.is_empty() || has_program() {
        let rate = inst.active.map_or(inst.desc.rate, |c| c.rate);
        // Copied rather than borrowed: `Tables` is read while `voices`
        // and `control` are written, and a switch cannot change inside
        // one block anyway — the host's parameter events landed before
        // this point.
        let plays = inst.plays_score.clone();
        let tb = score::Tables {
            events: engine::SCORE,
            banks: engine::BANKS,
            plays: &plays,
            controls: inst.desc.controls,
            tpb: engine::SCORE_TPB,
            rate,
        };
        let (tempo, playing, actual) = if p.transport.is_null() {
            (engine::SCORE_BPM, true, inst.t - inst.performer.origin)
        } else {
            let tr = &*p.transport;
            let tempo = if tr.flags & CLAP_TRANSPORT_HAS_TEMPO != 0
                && tr.tempo > 0.0 { tr.tempo } else { engine::SCORE_BPM };
            let playing = tr.flags & CLAP_TRANSPORT_IS_PLAYING != 0;
            let actual = if tr.flags
                & CLAP_TRANSPORT_HAS_BEATS_TIMELINE != 0 {
                score::beats_q31_samples(tr.song_pos_beats, tempo, rate)
            } else {
                (inst.beat_pos * 60.0 / tempo * rate as f64)
                    .floor() as i64
            };
            (tempo, playing, actual)
        };
        if fell {
            // The timeline stopped: the piece's notes release now —
            // they live on the timeline — while a played key, which
            // lives under the player's hands, holds on.
            for (b, bank) in engine::BANKS.iter().enumerate() {
                for i in 0..inst.voices[b].len() {
                    if matches!(inst.voices[b][i].key,
                                Some(NoteKey::Score(_))) {
                        inst.voices[b][i].released = Some(inst.t);
                        inst.voices[b][i].key = None;
                        inst.control[bank.voices[i][1]] = inst.t + 1;
                    }
                }
            }
        }
        if playing {
            if actual < 0 {
                // A count-in: the piece has not begun.  Stand at the
                // top with the anchor placed so beat zero lands on
                // time, and deliver nothing.
                if inst.performer.pos != 0 {
                    inst.performer.seek(&tb, tempo, 0, inst.t,
                                        &mut inst.voices,
                                        &mut inst.control);
                }
                inst.performer.origin = inst.t - actual;
            } else {
                // A jump reads as a seek; steady playback stays
                // anchored.  The slack is a block (or 20 ms, the
                // larger): host jitter stays under it, a loop seam
                // or a dragged playhead does not.
                let predicted = inst.t - inst.performer.origin;
                let slack = (p.frames_count as i64)
                    .max(rate as i64 / 50);
                if rose || (actual - predicted).abs() > slack {
                    inst.performer.seek(&tb, tempo, actual, inst.t,
                                        &mut inst.voices,
                                        &mut inst.control);
                    // The forced piece jumps too, or the playhead moves
                    // and the music does not.
                    #[cfg(feature = "dynscore")]
                    seek_piece(inst, &tb, tempo, actual);
                }
                let end = inst.t - inst.performer.origin
                    + p.frames_count as i64;
                inst.performer.advance(&tb, tempo, &mut inst.voices,
                                       &mut inst.control, end);
                // **The unfolding half.**  `SCORE` is empty for a piece
                // no list can hold, so the cursor above delivers
                // nothing and this forces the program instead.  The two
                // never both have work: an export bakes or it carries a
                // program, never both.
                // **Absolute samples**, where the cursor above takes
                // score-relative ones: this performer stamps its notes
                // at engine instants and gates its questions on engine
                // instants, so it is told where the engine is.
                #[cfg(feature = "dynscore")]
                advance_piece(inst, &tb, tempo,
                              inst.t + p.frames_count as i64,
                              p.frames_count as i64);
            }
        }
    }
    // The panel's own changes join the host's, after them: a drag that
    // lands in the same block as an automation write is the user's, and
    // the user is the later authority.
    #[cfg(feature = "gui")]
    inst.emit_gui_changes(p.out_events);
    let grace = 10 * inst.active.map_or(48000, |c| c.rate) as i64;
    let keyed = inst.voices.iter().flatten().any(|v| {
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

fn knob_count(plugin: *const clap_plugin) -> u32 {
    unsafe {
        instance(plugin).desc.controls.iter()
            .filter(|c| c.knob).count() as u32
    }
}

fn write_name(dst: &mut [c_char; CLAP_NAME_SIZE], text: &str) {
    *dst = [0; CLAP_NAME_SIZE];
    for (d, s) in dst.iter_mut()
        .zip(text.bytes().take(CLAP_NAME_SIZE - 1)) {
        *d = s as c_char;
    }
}

unsafe extern "C" fn params_count(plugin: *const clap_plugin) -> u32 {
    // Knobs, then the routing matrix, then one "does the score play
    // this bank" switch per bank.
    knob_count(plugin) + (engine::BANKS.len() * 17) as u32
}

unsafe extern "C" fn params_get_info(plugin: *const clap_plugin,
                                     index: u32,
                                     info: *mut clap_param_info) -> bool {
    if info.is_null() {
        return false;
    }
    let out = &mut *info;
    let knobs = knob_count(plugin);
    if index < knobs {
        let Some((slot, c)) = nth_knob(plugin, index) else {
            return false;
        };
        out.id = slot as u32;
        out.flags = CLAP_PARAM_IS_AUTOMATABLE
            | if c.kind == engine::Kind::Int { CLAP_PARAM_IS_STEPPED }
              else { 0 };
        out.cookie = std::ptr::null_mut();
        write_name(&mut out.name,
                   c.chan.strip_suffix("Chan").unwrap_or(c.chan));
        out.module = [0; CLAP_PATH_SIZE];
        out.min_value = c.min;
        out.max_value = c.max;
        out.default_value = c.init_value();
        return true;
    }
    // A routing cell — the checkbox matrix, one stepped 0/1 per
    // (bank × MIDI channel), grouped under `routing` so a host that
    // draws modules draws the matrix as its own panel.  The default is
    // the diagonal: channel *n* plays bank *n*.
    let cell = (index - knobs) as usize;
    let n = instance(plugin).desc.controls.len();
    let cells = engine::BANKS.len() * 16;
    if cell >= cells {
        // **The score switch.**  Whether the piece plays this bank —
        // the other half of the routing matrix, and stepped like every
        // cell in it, so a DAW draws it as a checkbox and can automate
        // a bank away mid-song.
        let b = cell - cells;
        let Some(bank) = engine::BANKS.get(b) else {
            return false;
        };
        out.id = (n + cell) as u32;
        out.flags = CLAP_PARAM_IS_AUTOMATABLE | CLAP_PARAM_IS_STEPPED;
        out.cookie = std::ptr::null_mut();
        write_name(&mut out.name, &format!("{} from score", bank.name));
        // Its own module: a host that groups by module draws the
        // matrix and the switches as two panels, which is what they
        // are — sixteen channels *into* a bank, and one question about
        // who plays it.
        out.module = [0; CLAP_PATH_SIZE];
        for (d, s) in out.module.iter_mut().zip(b"score\0") {
            *d = *s as c_char;
        }
        out.min_value = 0.0;
        out.max_value = 1.0;
        out.default_value =
            engine::SCORED.get(b).copied().unwrap_or(false) as u32 as f64;
        return true;
    }
    let (b, ch) = (cell / 16, cell % 16);
    let Some(bank) = engine::BANKS.get(b) else {
        return false;
    };
    out.id = (n + cell) as u32;
    out.flags = CLAP_PARAM_IS_AUTOMATABLE | CLAP_PARAM_IS_STEPPED;
    out.cookie = std::ptr::null_mut();
    write_name(&mut out.name, &format!("{} ch{}", bank.name, ch + 1));
    out.module = [0; CLAP_PATH_SIZE];
    for (d, s) in out.module.iter_mut().zip(b"routing\0") {
        *d = *s as c_char;
    }
    out.min_value = 0.0;
    out.max_value = 1.0;
    out.default_value = (b < 16 && ch == b) as u32 as f64;
    true
}

unsafe extern "C" fn params_get_value(plugin: *const clap_plugin,
                                      param_id: u32,
                                      out: *mut f64) -> bool {
    if out.is_null() {
        return false;
    }
    let inst = instance(plugin);
    let id = param_id as usize;
    let n = inst.desc.controls.len();
    if id < n {
        return match inst.desc.controls.get(id) {
            Some(c) if c.knob => {
                *out = c.value_of(inst.control[id]);
                true
            }
            _ => false,
        };
    }
    let cell = id - n;
    let cells = engine::BANKS.len() * 16;
    if cell >= cells {
        return match inst.plays_score.get(cell - cells) {
            Some(on) => {
                *out = *on as u32 as f64;
                true
            }
            None => false,
        };
    }
    let (b, ch) = (cell / 16, cell % 16);
    match inst.routing.get(b) {
        Some(row) => {
            *out = ((row >> ch) & 1) as f64;
            true
        }
        None => false,
    }
}

unsafe extern "C" fn params_value_to_text(plugin: *const clap_plugin,
                                          param_id: u32, value: f64,
                                          out: *mut c_char,
                                          capacity: u32) -> bool {
    if out.is_null() || capacity == 0 {
        return false;
    }
    let id = param_id as usize;
    let n = instance(plugin).desc.controls.len();
    let text = if id < n {
        let Some(c) = instance(plugin).desc.controls.get(id) else {
            return false;
        };
        if !c.knob {
            return false;
        }
        match c.kind {
            engine::Kind::Int => format!("{}", value.round() as i64),
            engine::Kind::Float => format!("{value:.3}"),
        }
    } else {
        String::from(if value >= 0.5 { "on" } else { "off" })
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
                                  out: *const clap_output_events) {
    let inst = instance(plugin);
    inst.drain(in_events);
    // **The stopped-transport path.**  A knob dragged while nothing is
    // processing has no `process` call to ride out on; the host calls
    // `flush` instead, which is why the panel asks for one.
    #[cfg(feature = "gui")]
    inst.emit_gui_changes(out);
    #[cfg(not(feature = "gui"))]
    let _ = out;
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
    (is_input && !engine::BANKS.is_empty()) as u32
}

unsafe extern "C" fn notes_get(_plugin: *const clap_plugin, index: u32,
                               is_input: bool,
                               info: *mut clap_note_port_info) -> bool {
    if !is_input || index != 0 || info.is_null()
        || engine::BANKS.is_empty() {
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

// ── State: the session remembers the knobs and the matrix ──────────────
//
// What saves is what the *host* believes in: knob slots and routing
// rows, behind a magic, a version, and a shape hash of the exported
// program — a preset from a different export refuses to load rather
// than pouring bits into the wrong slots.  Engine state does not save:
// a note mid-decay belongs to the take, not the project.

const STATE_MAGIC: u32 = 0x67657374; // "gest"
const STATE_VERSION: u32 = 1;

fn shape_hash(desc: &Descriptor) -> u64 {
    // FNV-1a over what the slots mean; two exports that disagree on
    // any of it must not exchange state.
    let mut h: u64 = 0xcbf29ce484222325;
    let mut eat = |bytes: &[u8]| {
        for b in bytes {
            h ^= *b as u64;
            h = h.wrapping_mul(0x100000001b3);
        }
    };
    eat(desc.id.as_bytes());
    eat(&(desc.state_bytes as u64).to_le_bytes());
    for c in desc.controls {
        eat(c.chan.as_bytes());
        eat(&[c.knob as u8, (c.kind == engine::Kind::Float) as u8]);
    }
    for b in engine::BANKS {
        eat(b.name.as_bytes());
    }
    h
}

unsafe extern "C" fn state_save(plugin: *const clap_plugin,
                                stream: *const clap_ostream) -> bool {
    if stream.is_null() {
        return false;
    }
    let inst = instance(plugin);
    let mut out: Vec<u8> = Vec::new();
    out.extend(STATE_MAGIC.to_le_bytes());
    out.extend(STATE_VERSION.to_le_bytes());
    out.extend(shape_hash(inst.desc).to_le_bytes());
    let knobs: Vec<usize> = inst.desc.controls.iter().enumerate()
        .filter(|(_, c)| c.knob).map(|(i, _)| i).collect();
    out.extend((knobs.len() as u32).to_le_bytes());
    for slot in &knobs {
        out.extend((*slot as u32).to_le_bytes());
        out.extend(inst.control[*slot].to_le_bytes());
    }
    out.extend((inst.routing.len() as u32).to_le_bytes());
    for row in &inst.routing {
        out.extend(row.to_le_bytes());
    }
    let mut sent = 0usize;
    while sent < out.len() {
        let n = ((*stream).write)(stream,
                                  out[sent..].as_ptr() as *const c_void,
                                  (out.len() - sent) as u64);
        if n <= 0 {
            return false;
        }
        sent += n as usize;
    }
    true
}

unsafe fn read_exact(stream: *const clap_istream, buf: &mut [u8]) -> bool {
    let mut got = 0usize;
    while got < buf.len() {
        let n = ((*stream).read)(stream,
                                 buf[got..].as_mut_ptr() as *mut c_void,
                                 (buf.len() - got) as u64);
        if n <= 0 {
            return false;
        }
        got += n as usize;
    }
    true
}

unsafe extern "C" fn state_load(plugin: *const clap_plugin,
                                stream: *const clap_istream) -> bool {
    if stream.is_null() {
        return false;
    }
    let inst = instance(plugin);
    let mut w4 = [0u8; 4];
    let mut w8 = [0u8; 8];
    if !read_exact(stream, &mut w4)
        || u32::from_le_bytes(w4) != STATE_MAGIC {
        return false;
    }
    if !read_exact(stream, &mut w4)
        || u32::from_le_bytes(w4) != STATE_VERSION {
        return false;
    }
    if !read_exact(stream, &mut w8)
        || u64::from_le_bytes(w8) != shape_hash(inst.desc) {
        return false;
    }
    if !read_exact(stream, &mut w4) {
        return false;
    }
    for _ in 0..u32::from_le_bytes(w4) {
        if !read_exact(stream, &mut w4) {
            return false;
        }
        let slot = u32::from_le_bytes(w4) as usize;
        if !read_exact(stream, &mut w8) {
            return false;
        }
        match inst.desc.controls.get(slot) {
            Some(c) if c.knob => {
                inst.control[slot] = i64::from_le_bytes(w8);
            }
            _ => return false,
        }
    }
    if !read_exact(stream, &mut w4) {
        return false;
    }
    let rows = u32::from_le_bytes(w4) as usize;
    if rows != inst.routing.len() {
        return false;
    }
    let mut w2 = [0u8; 2];
    for b in 0..rows {
        if !read_exact(stream, &mut w2) {
            return false;
        }
        inst.routing[b] = u16::from_le_bytes(w2);
    }
    true
}

static STATE: clap_plugin_state = clap_plugin_state {
    save: state_save,
    load: state_load,
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
            && !engine::BANKS.is_empty() {
            return &NOTE_PORTS as *const _ as *const c_void;
        }
        if want.to_bytes_with_nul() == CLAP_EXT_STATE {
            return &STATE as *const _ as *const c_void;
        }
        #[cfg(feature = "gui")]
        if want.to_bytes_with_nul() == CLAP_EXT_GUI {
            return &gui::GUI as *const _ as *const c_void;
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
                                    host: *const clap_host,
                                    _id: *const c_char)
                                    -> *const clap_plugin {
    let Some(desc) = DESCRIPTOR else {
        return std::ptr::null();
    };
    let mut inst = Instance::new(desc);
    inst.host = host;
    let data = Box::into_raw(Box::new(inst));
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

// ── The panel's changes, on their way to the host ───────────────────────
//
// `spec/panel.md` §"Knobs": a drag is `GESTURE_BEGIN`, values,
// `GESTURE_END`, and the *host* writes the slot.  The plugin applies
// the value to its own control buffer at the same time — not because
// the host's echo is unreliable, but because a knob turned while the
// transport is stopped must be audible on the next block whether or not
// the host has answered yet.

#[cfg(feature = "gui")]
impl Instance {
    /// Drain the window's queue into the host's event list.
    ///
    /// Runs on the audio thread, so the queue is only ever `try_lock`ed
    /// (`gui::Queue::take_changes`): a panel mid-frame must never stall
    /// a render, and a change that waits one block is inaudible where a
    /// missed deadline is not.
    unsafe fn emit_gui_changes(&mut self, out: *const clap_output_events) {
        if !self.gui.is_open() {
            return;
        }
        // **Applied here, emitted below — and the two are separate on
        // purpose.**  They used to share one early return on a null
        // `out_events`, so a host that gave us nowhere to send events
        // (or a block where we simply had none) dropped the change
        // instead of applying it: every click in the routing matrix
        // moved the picture and nothing else.  A panel writes the
        // instance first, because that is what makes the next block
        // sound right, and tells the host when there is a queue to tell
        // it through.
        for change in self.gui.queue.take_changes() {
            if let gestate_panel::Change::Value(id, value) = change {
                self.apply_param(id, value);
            }
            // Kept until a host gives us somewhere to put it: a
            // gesture the host never hears leaves its automation lane
            // and its undo out of step with what is sounding.
            if self.gui_outbox.len() < 8192 {
                self.gui_outbox.push(change);
            }
        }
        if out.is_null() || self.gui_outbox.is_empty() {
            return;
        }
        let changes = std::mem::take(&mut self.gui_outbox);
        let push = (*out).try_push;
        for change in changes {
            match change {
                gestate_panel::Change::Begin(id)
                | gestate_panel::Change::End(id) => {
                    let kind = match change {
                        gestate_panel::Change::Begin(_) =>
                            CLAP_EVENT_PARAM_GESTURE_BEGIN,
                        _ => CLAP_EVENT_PARAM_GESTURE_END,
                    };
                    let ev = clap_event_param_gesture {
                        header: clap_event_header {
                            size: std::mem::size_of::
                                    <clap_event_param_gesture>() as u32,
                            time: 0,
                            space_id: CLAP_CORE_EVENT_SPACE_ID,
                            type_: kind,
                            flags: 0,
                        },
                        param_id: id,
                    };
                    push(out, &ev.header as *const clap_event_header);
                }
                gestate_panel::Change::Value(id, value) => {
                    let ev = clap_event_param_value {
                        header: clap_event_header {
                            size: std::mem::size_of::
                                    <clap_event_param_value>() as u32,
                            time: 0,
                            space_id: CLAP_CORE_EVENT_SPACE_ID,
                            type_: CLAP_EVENT_PARAM_VALUE,
                            flags: 0,
                        },
                        param_id: id,
                        cookie: std::ptr::null_mut(),
                        note_id: -1,
                        port_index: -1,
                        channel: -1,
                        key: -1,
                        value,
                    };
                    push(out, &ev.header as *const clap_event_header);
                }
            }
        }
    }

    /// Tell an open panel what a parameter is now — how automation and
    /// the host's own generic UI reach the faders.
    fn report_to_gui(&self, param: u32, value: f64) {
        if self.gui.is_open() {
            self.gui.queue.report(param, value);
        }
    }
}
