//! `gestate-editor` — the editor, in Rust.
//!
//! `spec/substrate.md` §"Why one window" argued the editor and the
//! canvas belong in one window, and made the case that moving the view
//! is cheap because `audioeditor.Workbench` imports no toolkit: it owns
//! the instrument, the rebuild thread, the knob values, the transport
//! and the keyboard, and it has headless tests.  A view is a second
//! view against the same object.
//!
//! This is that view, in Rust, for two reasons that are not taste:
//!
//! * **One painter.**  The language's own pictures are drawn by
//!   `gestate-panel` in a plugin window and were drawn a second time by
//!   `pygame` in the editor.  Two painters is two alphabets that drift
//!   — measured, four glyphs apart within an hour of being written —
//!   and one of them had been raising `NameError` for months because
//!   nothing but a person opening a window could notice.
//! * **A frame that costs nothing.**  Software rasterizing a screen of
//!   text is a few hundred thousand byte writes if the font is a bitmap
//!   and an unbounded amount of work if it is not.  Everything here is
//!   chosen to keep it the first.
//!
//! The shape, which is `shell/panel`'s shape:
//!
//! ```text
//!   rope + cursor  ──→  Display  ──→  paint  ──→  pixels
//! ```
//!
//! and everything left of the arrow into `paint` is a pure function
//! with no window in its signature.

pub mod document;
pub mod font;
pub mod furniture;
pub mod keys;
pub mod palette;
pub mod rope;
pub mod shapes;
pub mod view;
pub mod walk;

#[cfg(feature = "window")]
pub mod window;

#[cfg(feature = "capi")]
pub mod abi;

pub use document::Document;
pub use font::Font;
pub use rope::Rope;
pub use view::View;
