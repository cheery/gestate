//! The editor, in a window.
//!
//! ```text
//! cargo run -p gestate-editor --features window --example edit -- FILE
//! ```
//!
//! * **Zoom** — Ctrl-`+` / Ctrl-`-` step a nine-rung ladder, Ctrl-`0`
//!   returns to 10×20, and Ctrl-wheel does the same.
//! * **Select** — shift with any motion, drag with the mouse, shift-click
//!   to adjust, Ctrl-A for all of it.
//! * **Clipboard** — Ctrl-C, Ctrl-X, Ctrl-V.  In-process: see
//!   `keys::Clipboard` for why the system one belongs to whoever embeds
//!   the editor.
//! * Ctrl-Z / Ctrl-Y undo and redo; Ctrl-Home / Ctrl-End go to the ends.
//!
//! Nothing is saved — this is the view, and what owns the file is the
//! next piece.

use std::sync::Arc;
use gestate_editor::window::{open_blocking, Alone};

fn main() {
    let path = std::env::args().nth(1);
    let text = match &path {
        Some(p) => std::fs::read_to_string(p).unwrap_or_else(|e| {
            eprintln!("{p}: {e}");
            std::process::exit(1);
        }),
        None => "# gestate — the editor, in Rust.\n\
                 #\n\
                 # Type.  Arrows, Home, End, PageUp, PageDown.\n\
                 # Ctrl-Z undoes.  Ctrl-+ and Ctrl-- zoom.\n\
                 # Shift selects, Ctrl-C/X/V copy, cut and paste.\n\
                 \n\
                 sound : Sig Float\n\
                 sound = gain 0.4 (sine 220.0)\n".into(),
    };
    if let Err(e) = open_blocking(Arc::new(Alone(text)), 1000, 700) {
        eprintln!("could not open a window: {e:?}");
        std::process::exit(1);
    }
}
