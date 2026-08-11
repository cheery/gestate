//! The CLAP C ABI — exactly the subset one instrument needs.
//!
//! Hand-declared from `clap/clap.h` (CLAP 1.2, whose ABI is frozen)
//! rather than pulled from a binding crate: the shell owns every line
//! it ships, builds offline, and a reader can hold the whole surface
//! in one file.  Layouts must match the C headers *exactly* —
//! `#[repr(C)]` everywhere, and nothing here is called from Rust that
//! a host did not call first.

#![allow(non_camel_case_types, dead_code)]

use std::os::raw::{c_char, c_void};

#[repr(C)]
#[derive(Clone, Copy)]
pub struct clap_version {
    pub major: u32,
    pub minor: u32,
    pub revision: u32,
}

pub const CLAP_VERSION: clap_version = clap_version {
    major: 1,
    minor: 2,
    revision: 2,
};

// ── Entry and factory ───────────────────────────────────────────────────

#[repr(C)]
pub struct clap_plugin_entry {
    pub clap_version: clap_version,
    pub init: unsafe extern "C" fn(plugin_path: *const c_char) -> bool,
    pub deinit: unsafe extern "C" fn(),
    pub get_factory:
        unsafe extern "C" fn(factory_id: *const c_char) -> *const c_void,
}

pub const CLAP_PLUGIN_FACTORY_ID: &[u8] = b"clap.plugin-factory\0";

#[repr(C)]
pub struct clap_plugin_factory {
    pub get_plugin_count:
        unsafe extern "C" fn(factory: *const clap_plugin_factory) -> u32,
    pub get_plugin_descriptor: unsafe extern "C" fn(
        factory: *const clap_plugin_factory,
        index: u32,
    ) -> *const clap_plugin_descriptor,
    pub create_plugin: unsafe extern "C" fn(
        factory: *const clap_plugin_factory,
        host: *const clap_host,
        plugin_id: *const c_char,
    ) -> *const clap_plugin,
}

// ── Descriptor ──────────────────────────────────────────────────────────

#[repr(C)]
pub struct clap_plugin_descriptor {
    pub clap_version: clap_version,
    pub id: *const c_char,
    pub name: *const c_char,
    pub vendor: *const c_char,
    pub url: *const c_char,
    pub manual_url: *const c_char,
    pub support_url: *const c_char,
    pub version: *const c_char,
    pub description: *const c_char,
    /// Null-terminated array of null-terminated strings.
    pub features: *const *const c_char,
}

pub const CLAP_PLUGIN_FEATURE_INSTRUMENT: &[u8] = b"instrument\0";
pub const CLAP_PLUGIN_FEATURE_SYNTHESIZER: &[u8] = b"synthesizer\0";

// ── Host and plugin ─────────────────────────────────────────────────────

#[repr(C)]
pub struct clap_host {
    pub clap_version: clap_version,
    pub host_data: *mut c_void,
    pub name: *const c_char,
    pub vendor: *const c_char,
    pub url: *const c_char,
    pub version: *const c_char,
    pub get_extension: unsafe extern "C" fn(
        host: *const clap_host,
        extension_id: *const c_char,
    ) -> *const c_void,
    pub request_restart: unsafe extern "C" fn(host: *const clap_host),
    pub request_process: unsafe extern "C" fn(host: *const clap_host),
    pub request_callback: unsafe extern "C" fn(host: *const clap_host),
}

#[repr(C)]
pub struct clap_plugin {
    pub desc: *const clap_plugin_descriptor,
    pub plugin_data: *mut c_void,
    pub init: unsafe extern "C" fn(plugin: *const clap_plugin) -> bool,
    pub destroy: unsafe extern "C" fn(plugin: *const clap_plugin),
    pub activate: unsafe extern "C" fn(
        plugin: *const clap_plugin,
        sample_rate: f64,
        min_frames_count: u32,
        max_frames_count: u32,
    ) -> bool,
    pub deactivate: unsafe extern "C" fn(plugin: *const clap_plugin),
    pub start_processing:
        unsafe extern "C" fn(plugin: *const clap_plugin) -> bool,
    pub stop_processing: unsafe extern "C" fn(plugin: *const clap_plugin),
    pub reset: unsafe extern "C" fn(plugin: *const clap_plugin),
    pub process: unsafe extern "C" fn(
        plugin: *const clap_plugin,
        process: *const clap_process,
    ) -> clap_process_status,
    pub get_extension: unsafe extern "C" fn(
        plugin: *const clap_plugin,
        id: *const c_char,
    ) -> *const c_void,
    pub on_main_thread: unsafe extern "C" fn(plugin: *const clap_plugin),
}

// ── Processing ──────────────────────────────────────────────────────────

pub type clap_process_status = i32;
pub const CLAP_PROCESS_ERROR: clap_process_status = 0;
pub const CLAP_PROCESS_CONTINUE: clap_process_status = 1;

#[repr(C)]
pub struct clap_audio_buffer {
    pub data32: *mut *mut f32,
    pub data64: *mut *mut f64,
    pub channel_count: u32,
    pub latency: u32,
    pub constant_mask: u64,
}

#[repr(C)]
pub struct clap_input_events {
    pub ctx: *mut c_void,
    pub size: unsafe extern "C" fn(list: *const clap_input_events) -> u32,
    pub get: unsafe extern "C" fn(
        list: *const clap_input_events,
        index: u32,
    ) -> *const clap_event_header,
}

#[repr(C)]
pub struct clap_output_events {
    pub ctx: *mut c_void,
    pub try_push: unsafe extern "C" fn(
        list: *const clap_output_events,
        event: *const clap_event_header,
    ) -> bool,
}

#[repr(C)]
pub struct clap_event_header {
    pub size: u32,
    pub time: u32,
    pub space_id: u16,
    pub type_: u16,
    pub flags: u32,
}

// ── Params extension ────────────────────────────────────────────────────

pub const CLAP_EXT_PARAMS: &[u8] = b"clap.params\0";
pub const CLAP_PATH_SIZE: usize = 1024;
pub const CLAP_PARAM_IS_STEPPED: u32 = 1 << 0;
pub const CLAP_PARAM_IS_AUTOMATABLE: u32 = 1 << 5;

#[repr(C)]
pub struct clap_param_info {
    pub id: u32,
    pub flags: u32,
    pub cookie: *mut c_void,
    pub name: [c_char; CLAP_NAME_SIZE],
    pub module: [c_char; CLAP_PATH_SIZE],
    pub min_value: f64,
    pub max_value: f64,
    pub default_value: f64,
}

#[repr(C)]
pub struct clap_plugin_params {
    pub count: unsafe extern "C" fn(plugin: *const clap_plugin) -> u32,
    pub get_info: unsafe extern "C" fn(plugin: *const clap_plugin,
                                       param_index: u32,
                                       info: *mut clap_param_info) -> bool,
    pub get_value: unsafe extern "C" fn(plugin: *const clap_plugin,
                                        param_id: u32,
                                        out: *mut f64) -> bool,
    pub value_to_text: unsafe extern "C" fn(plugin: *const clap_plugin,
                                            param_id: u32,
                                            value: f64,
                                            out: *mut c_char,
                                            capacity: u32) -> bool,
    pub text_to_value: unsafe extern "C" fn(plugin: *const clap_plugin,
                                            param_id: u32,
                                            text: *const c_char,
                                            out: *mut f64) -> bool,
    pub flush: unsafe extern "C" fn(plugin: *const clap_plugin,
                                    in_events: *const clap_input_events,
                                    out_events: *const clap_output_events),
}

// ── State extension ─────────────────────────────────────────────────────

pub const CLAP_EXT_STATE: &[u8] = b"clap.state\0";

#[repr(C)]
pub struct clap_ostream {
    pub ctx: *mut c_void,
    pub write: unsafe extern "C" fn(stream: *const clap_ostream,
                                    buffer: *const c_void,
                                    size: u64) -> i64,
}

#[repr(C)]
pub struct clap_istream {
    pub ctx: *mut c_void,
    pub read: unsafe extern "C" fn(stream: *const clap_istream,
                                   buffer: *mut c_void,
                                   size: u64) -> i64,
}

#[repr(C)]
pub struct clap_plugin_state {
    pub save: unsafe extern "C" fn(plugin: *const clap_plugin,
                                   stream: *const clap_ostream) -> bool,
    pub load: unsafe extern "C" fn(plugin: *const clap_plugin,
                                   stream: *const clap_istream) -> bool,
}

// ── Note ports extension ────────────────────────────────────────────────

pub const CLAP_EXT_NOTE_PORTS: &[u8] = b"clap.note-ports\0";
pub const CLAP_NOTE_DIALECT_CLAP: u32 = 1 << 0;

#[repr(C)]
pub struct clap_note_port_info {
    pub id: u32,
    pub supported_dialects: u32,
    pub preferred_dialect: u32,
    pub name: [c_char; CLAP_NAME_SIZE],
}

#[repr(C)]
pub struct clap_plugin_note_ports {
    pub count: unsafe extern "C" fn(plugin: *const clap_plugin,
                                    is_input: bool) -> u32,
    pub get: unsafe extern "C" fn(plugin: *const clap_plugin, index: u32,
                                  is_input: bool,
                                  info: *mut clap_note_port_info) -> bool,
}

// ── Core events ─────────────────────────────────────────────────────────

pub const CLAP_CORE_EVENT_SPACE_ID: u16 = 0;
pub const CLAP_EVENT_NOTE_ON: u16 = 0;
pub const CLAP_EVENT_NOTE_OFF: u16 = 1;
pub const CLAP_EVENT_NOTE_CHOKE: u16 = 2;
pub const CLAP_EVENT_PARAM_VALUE: u16 = 5;

#[repr(C)]
pub struct clap_event_note {
    pub header: clap_event_header,
    pub note_id: i32,
    pub port_index: i16,
    pub channel: i16,
    pub key: i16,
    /// 0..1 — a double, not the 0..127 MIDI speaks.
    pub velocity: f64,
}

#[repr(C)]
pub struct clap_event_param_value {
    pub header: clap_event_header,
    pub param_id: u32,
    pub cookie: *mut c_void,
    pub note_id: i32,
    pub port_index: i16,
    pub channel: i16,
    pub key: i16,
    pub value: f64,
}

// ── Transport ───────────────────────────────────────────────────────────

pub const CLAP_TRANSPORT_HAS_TEMPO: u32 = 1 << 0;
pub const CLAP_TRANSPORT_HAS_BEATS_TIMELINE: u32 = 1 << 1;
pub const CLAP_TRANSPORT_IS_PLAYING: u32 = 1 << 4;
/// `clap_beattime` is fixed-point: beats × this.
pub const CLAP_BEATTIME_FACTOR: i64 = 1 << 31;

#[repr(C)]
pub struct clap_event_transport {
    pub header: clap_event_header,
    pub flags: u32,
    pub song_pos_beats: i64,
    pub song_pos_seconds: i64,
    pub tempo: f64,
    pub tempo_inc: f64,
    pub loop_start_beats: i64,
    pub loop_end_beats: i64,
    pub loop_start_seconds: i64,
    pub loop_end_seconds: i64,
    pub bar_start: i64,
    pub bar_number: i32,
    pub tsig_num: u16,
    pub tsig_denom: u16,
}

// ── Audio ports extension ───────────────────────────────────────────────
//
// Not optional in practice: a host learns what buffers to hand
// `process()` from this, and a plugin without it has *no ports* — it
// loads, and sits silent.

pub const CLAP_EXT_AUDIO_PORTS: &[u8] = b"clap.audio-ports\0";
pub const CLAP_NAME_SIZE: usize = 256;
pub const CLAP_AUDIO_PORT_IS_MAIN: u32 = 1 << 0;
pub const CLAP_INVALID_ID: u32 = u32::MAX;
pub const CLAP_PORT_MONO: &[u8] = b"mono\0";
pub const CLAP_PORT_STEREO: &[u8] = b"stereo\0";

#[repr(C)]
pub struct clap_audio_port_info {
    pub id: u32,
    pub name: [c_char; CLAP_NAME_SIZE],
    pub flags: u32,
    pub channel_count: u32,
    pub port_type: *const c_char,
    pub in_place_pair: u32,
}

#[repr(C)]
pub struct clap_plugin_audio_ports {
    pub count: unsafe extern "C" fn(plugin: *const clap_plugin,
                                    is_input: bool) -> u32,
    pub get: unsafe extern "C" fn(plugin: *const clap_plugin,
                                  index: u32,
                                  is_input: bool,
                                  info: *mut clap_audio_port_info) -> bool,
}

#[repr(C)]
pub struct clap_process {
    pub steady_time: i64,
    pub frames_count: u32,
    /// Null in a free-running host — an instrument then simply plays.
    pub transport: *const clap_event_transport,
    pub audio_inputs: *const clap_audio_buffer,
    pub audio_outputs: *mut clap_audio_buffer,
    pub audio_inputs_count: u32,
    pub audio_outputs_count: u32,
    pub in_events: *const clap_input_events,
    pub out_events: *const clap_output_events,
}

// ── Parameter gestures ──────────────────────────────────────────────────
//
// **What makes a drag one edit.**  Without these a host sees four
// hundred parameter writes and has to guess where the user's gesture
// began and ended — which is the difference between one undo step and
// four hundred, and between one automation-write region and a smear.
// `spec/panel.md` §"Knobs" is why the panel emits them.

pub const CLAP_EVENT_PARAM_GESTURE_BEGIN: u16 = 6;
pub const CLAP_EVENT_PARAM_GESTURE_END: u16 = 7;

#[repr(C)]
pub struct clap_event_param_gesture {
    pub header: clap_event_header,
    pub param_id: u32,
}

// ── The host's parameter extension ──────────────────────────────────────
//
// The first *host* extension this shell asks for.  `request_flush` is
// the one that matters: a knob dragged while the plugin is not
// processing — a stopped transport, which is when people set sounds up —
// has no `process` call to ride out on, and without this the change sits
// in the queue until the user presses play.

pub const CLAP_EXT_PARAMS_HOST: &[u8] = b"clap.params\0";

pub const CLAP_PARAM_RESCAN_VALUES: u32 = 1 << 0;
pub const CLAP_PARAM_RESCAN_TEXT: u32 = 1 << 1;
pub const CLAP_PARAM_RESCAN_INFO: u32 = 1 << 2;
pub const CLAP_PARAM_RESCAN_ALL: u32 = 1 << 3;

#[repr(C)]
pub struct clap_host_params {
    pub rescan: unsafe extern "C" fn(host: *const clap_host, flags: u32),
    pub clear: unsafe extern "C" fn(host: *const clap_host,
                                    param_id: u32, flags: u32),
    pub request_flush: unsafe extern "C" fn(host: *const clap_host),
}

// ── The GUI extension ───────────────────────────────────────────────────
//
// `spec/panel.md` §"What the ABI has to grow".  The subset below is what
// an embedded, fixed-size, host-parented panel needs and no more: this
// shell does not float, does not resize and does not offer an API it
// cannot draw on.

pub const CLAP_EXT_GUI: &[u8] = b"clap.gui\0";

pub const CLAP_WINDOW_API_X11: &[u8] = b"x11\0";
pub const CLAP_WINDOW_API_WIN32: &[u8] = b"win32\0";
pub const CLAP_WINDOW_API_COCOA: &[u8] = b"cocoa\0";
pub const CLAP_WINDOW_API_WAYLAND: &[u8] = b"wayland\0";

/// The platform's own window id, tagged by `api`.
///
/// The C side is a union of a pointer and an `unsigned long`; the
/// pointer is the wider of the two on every platform this builds for,
/// so one pointer-sized field reads either — an X11 `Window` arrives in
/// the low bits and is recovered by casting back.
#[repr(C)]
pub struct clap_window {
    pub api: *const c_char,
    pub handle: *mut c_void,
}

#[repr(C)]
pub struct clap_plugin_gui {
    pub is_api_supported: unsafe extern "C" fn(plugin: *const clap_plugin,
                                               api: *const c_char,
                                               is_floating: bool) -> bool,
    pub get_preferred_api: unsafe extern "C" fn(plugin: *const clap_plugin,
                                                api: *mut *const c_char,
                                                is_floating: *mut bool)
                                                -> bool,
    pub create: unsafe extern "C" fn(plugin: *const clap_plugin,
                                     api: *const c_char,
                                     is_floating: bool) -> bool,
    pub destroy: unsafe extern "C" fn(plugin: *const clap_plugin),
    pub set_scale: unsafe extern "C" fn(plugin: *const clap_plugin,
                                        scale: f64) -> bool,
    pub get_size: unsafe extern "C" fn(plugin: *const clap_plugin,
                                       width: *mut u32,
                                       height: *mut u32) -> bool,
    pub can_resize: unsafe extern "C" fn(plugin: *const clap_plugin) -> bool,
    pub get_resize_hints: unsafe extern "C" fn(plugin: *const clap_plugin,
                                               hints: *mut c_void) -> bool,
    pub adjust_size: unsafe extern "C" fn(plugin: *const clap_plugin,
                                          width: *mut u32,
                                          height: *mut u32) -> bool,
    pub set_size: unsafe extern "C" fn(plugin: *const clap_plugin,
                                       width: u32, height: u32) -> bool,
    pub set_parent: unsafe extern "C" fn(plugin: *const clap_plugin,
                                         window: *const clap_window) -> bool,
    pub set_transient: unsafe extern "C" fn(plugin: *const clap_plugin,
                                            window: *const clap_window)
                                            -> bool,
    pub suggest_title: unsafe extern "C" fn(plugin: *const clap_plugin,
                                            title: *const c_char),
    pub show: unsafe extern "C" fn(plugin: *const clap_plugin) -> bool,
    pub hide: unsafe extern "C" fn(plugin: *const clap_plugin) -> bool,
}
