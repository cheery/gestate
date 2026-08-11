//! The editor, in a window.
//!
//! ```text
//! cargo run -p gestate-editor --features window --example edit -- FILE
//! ```
//!
//! Ctrl-0 switches between 10×20 and 6×13; Ctrl-Z and Ctrl-Y undo and
//! redo; Ctrl-Home and Ctrl-End go to the ends.  Nothing is saved —
//! this is the view, and what owns the file is the next piece.

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
                 # Ctrl-Z undoes, Ctrl-0 changes the size.\n\
                 \n\
                 sound : Sig Float\n\
                 sound = gain 0.4 (sine 220.0)\n".into(),
    };
    if let Err(e) = open_blocking(Arc::new(Alone(text)), 1000, 700) {
        eprintln!("could not open a window: {e:?}");
        std::process::exit(1);
    }
}
