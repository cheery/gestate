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
    pub transport: *const c_void, // clap_event_transport; unread for now
    pub audio_inputs: *const clap_audio_buffer,
    pub audio_outputs: *mut clap_audio_buffer,
    pub audio_inputs_count: u32,
    pub audio_outputs_count: u32,
    pub in_events: *const clap_input_events,
    pub out_events: *const clap_output_events,
}
