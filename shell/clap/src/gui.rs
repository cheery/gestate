//! `clap.gui` — the panel, attached to the plugin.
//!
//! `spec/panel.md` is the design.  This module is the seam: it turns
//! the descriptor into a `gestate_panel::Model`, opens a `baseview`
//! window parented into the host's, and carries parameter changes back
//! out as CLAP events.
//!
//! **The whole module is behind the `gui` feature**, so the plugin CI
//! builds — and the one a host loads without it — are the
//! dependency-free shell they have always been.

use std::ffi::{c_char, c_void, CStr};
use std::sync::{Arc, Mutex};

use gestate_panel::model::{Accepts, BankView, Knob, Model};
use gestate_panel::window::Sink;
use gestate_panel::{panels, Change};

use crate::abi::*;
use crate::engine::{self, Descriptor};

/// What the window and the plugin pass between them.
///
/// **Two queues, both small, and neither on the audio thread's
/// critical path.**  `changes` goes window → plugin and is drained into
/// `out_events`; `values` goes plugin → window so the panel follows
/// automation.  The audio side only ever `try_lock`s: a panel that is
/// mid-frame must never be able to stall a render, and a change that
/// waits one block is inaudible where a missed deadline is not.
#[derive(Default)]
pub struct Queue {
    changes: Mutex<Vec<Change>>,
    values: Mutex<Vec<(u32, f64)>>,
}

impl Sink for Queue {
    fn push(&self, change: Change) {
        if let Ok(mut q) = self.changes.lock() {
            // A bound, because a host that never calls `process` (a
            // stopped transport with no flush) must not let a long drag
            // grow this without limit.  Dropping the *oldest* values
            // keeps the newest position, which is the one that matters;
            // gestures are never dropped because an unmatched BEGIN
            // leaves the host in a gesture forever.
            if q.len() > 4096 {
                q.retain(|c| !matches!(c, Change::Value(..)));
            }
            q.push(change);
        }
    }

    fn values(&self) -> Vec<(u32, f64)> {
        match self.values.lock() {
            Ok(mut v) if !v.is_empty() => std::mem::take(&mut *v),
            _ => Vec::new(),
        }
    }
}

impl Queue {
    /// Called from the audio thread — never blocks.
    pub fn take_changes(&self) -> Vec<Change> {
        match self.changes.try_lock() {
            Ok(mut q) if !q.is_empty() => std::mem::take(&mut *q),
            _ => Vec::new(),
        }
    }

    /// Called from the audio thread when a parameter moved — never
    /// blocks, and a dropped update is corrected by the next one.
    pub fn report(&self, param: u32, value: f64) {
        if let Ok(mut v) = self.values.try_lock() {
            v.retain(|(p, _)| *p != param);
            v.push((param, value));
        }
    }
}

/// The GUI's own state, one per plugin instance.
#[derive(Default)]
pub struct Gui {
    window: Option<gestate_panel::window::Handle>,
    pub queue: Arc<Queue>,
    /// The size a host resized us to, once it has.
    size: Option<(i32, i32)>,
    /// Whether `create` has run.  `set_parent` is what actually opens
    /// the window — CLAP calls `create` first with only an API name,
    /// and a window with no parent yet has nowhere to go.
    created: bool,
}

// SAFETY: `baseview::Window` is `!Send` because it must be used from
// the thread that made it.  CLAP promises exactly that: every
// `clap.gui` method is main-thread, and this handle is only ever
// touched from those methods.  The plugin struct that owns it is moved
// across threads by neither us nor the host.
unsafe impl Send for Gui {}

impl Gui {
    pub fn is_open(&self) -> bool {
        self.window.is_some()
    }
}

/// The descriptor, as a thing to look at.
///
/// A knob's `param` is its **control slot index**, which is exactly the
/// id `params_get_info` hands the host — so the panel and the host name
/// the same parameter without a second table to keep in step.
pub fn model_of(desc: &'static Descriptor, control: &[i64],
                routing: &[u16]) -> Model {
    let knobs = desc.controls.iter().enumerate()
        .filter(|(_, c)| c.knob)
        .map(|(slot, c)| Knob {
            name: c.chan.strip_suffix("Chan").unwrap_or(c.chan).to_string(),
            param: slot as u32,
            value: control.get(slot).map(|b| c.value_of(*b))
                          .unwrap_or_else(|| c.init_value()),
            min: c.min,
            max: c.max,
            integer: c.kind == engine::Kind::Int,
        })
        .collect();

    // A routing cell's id is `controls.len() + bank*16 + channel` —
    // `params_get_info`'s own numbering, taken rather than re-derived.
    let base = desc.controls.len() as u32;
    let banks = engine::BANKS.iter().enumerate().map(|(i, b)| BankView {
        name: b.name.to_string(),
        voices: b.voices.len(),
        accepts: match b.table {
            None => Accepts::Everything,
            Some(t) => Accepts::Table {
                levels: t.levels,
                ok: t.ok.to_vec(),
            },
        },
        routing: routing.get(i).copied().unwrap_or(0),
        routing_param0: base + (i * 16) as u32,
    }).collect();

    Model { title: desc.name.to_string(), knobs, banks }
}

// ── The vtable ──────────────────────────────────────────────────────────

/// The one window API this build can draw on.
fn native_api() -> &'static [u8] {
    if cfg!(target_os = "windows") {
        CLAP_WINDOW_API_WIN32
    } else if cfg!(target_os = "macos") {
        CLAP_WINDOW_API_COCOA
    } else {
        CLAP_WINDOW_API_X11
    }
}

unsafe fn api_matches(api: *const c_char) -> bool {
    !api.is_null() && CStr::from_ptr(api).to_bytes_with_nul() == native_api()
}

unsafe extern "C" fn gui_is_api_supported(_p: *const clap_plugin,
                                          api: *const c_char,
                                          is_floating: bool) -> bool {
    // **Embedded only.**  A floating window is a second lifetime to get
    // right for a panel that has no reason to leave its host.
    !is_floating && api_matches(api)
}

unsafe extern "C" fn gui_get_preferred_api(_p: *const clap_plugin,
                                           api: *mut *const c_char,
                                           is_floating: *mut bool) -> bool {
    if api.is_null() || is_floating.is_null() {
        return false;
    }
    *api = native_api().as_ptr() as *const c_char;
    *is_floating = false;
    true
}

unsafe extern "C" fn gui_create(plugin: *const clap_plugin,
                                api: *const c_char,
                                is_floating: bool) -> bool {
    if is_floating || !api_matches(api) {
        return false;
    }
    crate::instance(plugin).gui.created = true;
    true
}

unsafe extern "C" fn gui_destroy(plugin: *const clap_plugin) {
    let gui = &mut crate::instance(plugin).gui;
    if let Some(w) = gui.window.take() {
        w.close();
    }
    gui.created = false;
}

unsafe extern "C" fn gui_set_scale(_p: *const clap_plugin, _s: f64) -> bool {
    // **Declined, and the panel offers its own control instead.**  The
    // font is a bitmap, so it enlarges in whole steps; a host handing
    // us 1.5 could only be honoured by blurring the one thing this
    // painter does exactly.  The `TEXT -/+` buttons are the same
    // setting under the reader's hand, where a display-density guess
    // belongs.
    false
}

unsafe extern "C" fn gui_get_size(plugin: *const clap_plugin,
                                  width: *mut u32,
                                  height: *mut u32) -> bool {
    if width.is_null() || height.is_null() {
        return false;
    }
    let inst = crate::instance(plugin);
    // Once a window exists it owns its size — a host asking after a
    // resize must be told what it resized *to*, not what the descriptor
    // originally wanted.
    let (w, h) = match &inst.gui.size {
        Some((w, h)) => (*w, *h),
        None => panels::size(&model_of(inst.desc, &inst.control,
                                       &inst.routing),
                             panels::SCALE_DEFAULT),
    };
    *width = w as u32;
    *height = h as u32;
    true
}

unsafe extern "C" fn gui_can_resize(_p: *const clap_plugin) -> bool {
    true
}

unsafe extern "C" fn gui_get_resize_hints(_p: *const clap_plugin,
                                          hints: *mut c_void) -> bool {
    if hints.is_null() {
        return false;
    }
    // **Free in both directions, no aspect ratio.**  Width gives the
    // faders a longer throw and the note strips more room; height just
    // shows more of the list.  Nothing here scales, so there is no
    // ratio to preserve.
    *(hints as *mut clap_gui_resize_hints) = clap_gui_resize_hints {
        can_resize_horizontally: true,
        can_resize_vertically: true,
        preserve_aspect_ratio: false,
        aspect_ratio_width: 1,
        aspect_ratio_height: 1,
    };
    true
}

/// The nearest size the panel will actually draw at.
///
/// A floor rather than a grid: below it the routing matrix stops
/// fitting, and a host that asks for 40×20 should be told the truth
/// rather than handed a window with nothing legible in it.  Height has
/// almost none, because a short window **scrolls** rather than
/// overflowing.
///
/// The numbers are the panel's own — it knows what its widest row needs
/// — and a second set here would be a second place to get it wrong.
fn clamp_size(w: u32, h: u32) -> (u32, u32) {
    let k = panels::Metrics::new(panels::SCALE_DEFAULT);
    (w.max(k.min_width() as u32), h.max(k.min_height() as u32))
}

unsafe extern "C" fn gui_adjust_size(_p: *const clap_plugin,
                                     width: *mut u32,
                                     height: *mut u32) -> bool {
    if width.is_null() || height.is_null() {
        return false;
    }
    let (w, h) = clamp_size(*width, *height);
    *width = w;
    *height = h;
    true
}

unsafe extern "C" fn gui_set_size(plugin: *const clap_plugin,
                                  w: u32, h: u32) -> bool {
    let (w, h) = clamp_size(w, h);
    let inst = crate::instance(plugin);
    inst.gui.size = Some((w as i32, h as i32));
    match &inst.gui.window {
        Some(win) => win.resize(w as i32, h as i32),
        // Before the window exists this is just the size to open at,
        // which `get_size` will now report.
        None => true,
    }
}

unsafe extern "C" fn gui_set_parent(plugin: *const clap_plugin,
                                    window: *const clap_window) -> bool {
    if window.is_null() {
        return false;
    }
    let w = &*window;
    if !api_matches(w.api) {
        return false;
    }
    let inst = crate::instance(plugin);
    if !inst.gui.created || inst.gui.window.is_some() {
        return false;
    }

    let Some(handle) = raw_parent(w.handle) else {
        return false;
    };
    let model = model_of(inst.desc, &inst.control, &inst.routing);
    let queue = inst.gui.queue.clone();
    let size = inst.gui.size;

    // SAFETY: the host's contract is that the parent window outlives
    // `gui.destroy`, and `gui_destroy` is where this window is closed.
    match unsafe {
        gestate_panel::window::open_parented(handle, model, queue, size)
    } {
        Ok(win) => {
            inst.gui.window = Some(win);
            true
        }
        Err(_) => false,
    }
}

/// The platform id in `clap_window`, as a raw-window-handle.
#[cfg(all(unix, not(target_os = "macos")))]
fn raw_parent(handle: *mut c_void) -> Option<raw_window_handle::RawWindowHandle> {
    use raw_window_handle::{RawWindowHandle, XcbWindowHandle};
    let id = handle as usize as u32;
    // An X11 window id of 0 is `None`, which is a host bug rather than
    // a root window we should draw on.
    let id = std::num::NonZeroU32::new(id)?;
    Some(RawWindowHandle::Xcb(XcbWindowHandle::new(id)))
}

#[cfg(target_os = "windows")]
fn raw_parent(handle: *mut c_void) -> Option<raw_window_handle::RawWindowHandle> {
    use raw_window_handle::{RawWindowHandle, Win32WindowHandle};
    let h = std::num::NonZeroIsize::new(handle as isize)?;
    Some(RawWindowHandle::Win32(Win32WindowHandle::new(h)))
}

#[cfg(target_os = "macos")]
fn raw_parent(handle: *mut c_void) -> Option<raw_window_handle::RawWindowHandle> {
    use raw_window_handle::{AppKitWindowHandle, RawWindowHandle};
    let p = std::ptr::NonNull::new(handle)?;
    Some(RawWindowHandle::AppKit(AppKitWindowHandle::new(p)))
}

unsafe extern "C" fn gui_set_transient(_p: *const clap_plugin,
                                       _w: *const clap_window) -> bool {
    false
}

unsafe extern "C" fn gui_suggest_title(_p: *const clap_plugin,
                                       _t: *const c_char) {}

unsafe extern "C" fn gui_show(plugin: *const clap_plugin) -> bool {
    match &crate::instance(plugin).gui.window {
        Some(w) => w.show(),
        None => false,
    }
}

unsafe extern "C" fn gui_hide(plugin: *const clap_plugin) -> bool {
    match &crate::instance(plugin).gui.window {
        Some(w) => w.hide(),
        None => false,
    }
}

pub static GUI: clap_plugin_gui = clap_plugin_gui {
    is_api_supported: gui_is_api_supported,
    get_preferred_api: gui_get_preferred_api,
    create: gui_create,
    destroy: gui_destroy,
    set_scale: gui_set_scale,
    get_size: gui_get_size,
    can_resize: gui_can_resize,
    get_resize_hints: gui_get_resize_hints,
    adjust_size: gui_adjust_size,
    set_size: gui_set_size,
    set_parent: gui_set_parent,
    set_transient: gui_set_transient,
    suggest_title: gui_suggest_title,
    show: gui_show,
    hide: gui_hide,
};
