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

/// One sounding instance: the zeroed state, the control slots at their
/// declared defaults, and a scratch buffer for the interleaved frames.
struct Instance {
    desc: &'static Descriptor,
    state: Vec<u8>,
    control: Vec<i64>,
    scratch: Vec<f32>,
}

impl Instance {
    fn new(desc: &'static Descriptor) -> Self {
        Instance {
            desc,
            state: vec![0u8; desc.state_bytes],
            control: desc.controls.iter().map(|c| c.init_bits).collect(),
            scratch: Vec::new(),
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
    instance(plugin).process(out, p.frames_count);
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

unsafe extern "C" fn plugin_get_extension(_plugin: *const clap_plugin,
                                          id: *const c_char)
                                          -> *const c_void {
    if !id.is_null() {
        let want = std::ffi::CStr::from_ptr(id);
        if want.to_bytes_with_nul() == CLAP_EXT_AUDIO_PORTS {
            return &AUDIO_PORTS as *const _ as *const c_void;
        }
    }
    // Params and note ports are the next milestone; a null for the
    // rest is a plugin without those extensions, which hosts accept.
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
