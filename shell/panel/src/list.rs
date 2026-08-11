//! The display list — **the vocabulary the substrate already speaks.**
//!
//! `gestate/gui.py`'s `_walk` reduces a `Sub` to exactly two drawing
//! items and one hit item, and this module is that reduction's Rust
//! twin.  Panel one produces these from the descriptor; the canvas will
//! produce them from a `Sub` tree walked by the G-machine.  Two
//! producers, one painter — which is the whole reason the list is a
//! type of its own rather than calls into the painter.
//!
//! Coordinates are pixels with the origin at the top left, and a
//! `Rect` is placed by its **corner** here where a `Sub` places by its
//! centre.  The centre convention belongs to the language's layout
//! (`gui.ges` arranges by centres so no combinator needs an alignment
//! argument); by the time the walk emits an item it has already done
//! that arithmetic — `_walk` emits `cx - w // 2`.  So the list is
//! corner-based and the conversion lives where the centres do.

/// Opaque 8-bit-per-channel colour.  No alpha: `over` is painter's
/// order and the substrate has no transparency, so a blend would be a
/// capability nothing asks for (`gui.ges`'s `Colour` is three
/// components).
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Colour {
    pub r: u8,
    pub g: u8,
    pub b: u8,
}

impl Colour {
    pub const fn rgb(r: u8, g: u8, b: u8) -> Self {
        Colour { r, g, b }
    }

    /// The 0x00RRGGBB word `softbuffer` presents, and the one the
    /// painter's buffer holds.
    pub const fn word(self) -> u32 {
        ((self.r as u32) << 16) | ((self.g as u32) << 8) | (self.b as u32)
    }
}

/// One thing to draw.
///
/// `Text` began as chrome only — a `Sub` had no label, and panel one
/// drew its own names host-side.  `Label w h s c` joined the language
/// (`spec/substrate.md`), so both sources emit this now, which is what
/// "one painter, two sources" was always going to mean.  It rides in
/// this enum rather than beside it because the painter's ordering is
/// painter's order — a label drawn after a rect must be able to land
/// on top of it, and two lists would have to be interleaved by hand.
///
/// `scale` multiplies the 3×5 cell.  For chrome the panel picks it;
/// for a label the **walk** fits it to the box the program declared, so
/// by the time an item exists the question is settled either way and a
/// painter never measures anything.
#[derive(Clone, PartialEq, Debug)]
pub enum Item {
    /// Corner, size, colour.
    Rect { x: i32, y: i32, w: i32, h: i32, c: Colour },
    /// Centre, radius, colour — `gui.py`'s `("dot", cx, cy, r, colour)`.
    Dot { cx: i32, cy: i32, r: i32, c: Colour },
    /// Chrome only.  `scale` multiplies the 3×5 cell.
    Text { x: i32, y: i32, s: String, c: Colour, scale: i32 },
}

/// Which axis a drag writes, mirroring `TouchX`/`TouchY` in `gui.ges`.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Axis {
    X,
    Y,
}

/// What kind of thing a region is.
///
/// **Two, because the descriptor has two.**  A knob is continuous and
/// wants a drag; a routing cell is a stepped 0/1 the host already
/// declares, and wants a click.  Giving them one shape would mean a
/// checkbox you have to drag, which is the sort of interface nobody
/// admits to having designed.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Kind {
    /// Drag along an axis, value from position.
    Fader(Axis),
    /// Click to flip.  The value is in the model, not the geometry.
    Toggle,
    /// **Panel-local, and never a parameter.**  A view preference — how
    /// big the text is — is not something a host should automate,
    /// undo, or save in a song: it belongs to the person looking at the
    /// window, not to the piece.  So a button carries its action code
    /// in the `Kind` and leaves `param` meaningless, which is what
    /// stops one from ever being handed to `out_events`.
    ///
    /// Anything looking a hit up by id must match on the kind too —
    /// `param` is `NO_PARAM` here, and a search by id alone will find
    /// a button where it meant a fader.
    Button(u32),
    /// **A substrate's attachment**: drag along an axis and write a
    /// *channel* the program named, not a parameter.
    ///
    /// The two coexist because the two halves of the window mean
    /// different things.  Panel one draws the descriptor, and a knob
    /// there is the host's parameter — the DAW owns it, automates it,
    /// undoes it.  A canvas draws the *program*, and what an element
    /// feeds is a channel the program declared and reads back itself
    /// (`spec/substrate.md`: "the channel travels as a value, inside
    /// the structure").  Collapsing them would make a canvas element
    /// into an automatable plugin parameter, which is not what it is.
    Chan(Axis, i64),
}

/// A region that listens, and what it writes to.
///
/// The substrate's walk emits `{axis, chan, region}` where `chan` is an
/// `NChan` id.  Panel one writes **parameters**, not channels
/// (`spec/panel.md` §"Knobs": a plugin does not own its own
/// parameters), so the target is a parameter index and the shell maps
/// it to the host's id.  When the canvas lands it brings the channel
/// spelling with it and this becomes a two-case enum; today one case
/// honestly stated beats a second case with no producer.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Hit {
    pub kind: Kind,
    /// The parameter this writes, or `NO_PARAM` for a `Button`.
    pub param: u32,
    /// `(x0, y0, x1, y1)`, half-open at the far edge.
    pub region: (i32, i32, i32, i32),
}

/// The `param` of a hit that writes no parameter.
pub const NO_PARAM: u32 = u32::MAX;

impl Hit {
    pub fn contains(&self, x: i32, y: i32) -> bool {
        let (x0, y0, x1, y1) = self.region;
        x >= x0 && x < x1 && y >= y0 && y < y1
    }

    /// Where a point sits along this hit's axis, as 0.0 at the low edge
    /// and 1.0 at the high one.
    ///
    /// **Y is inverted deliberately.**  Screen y grows downward and a
    /// fader grows upward; a panel that returned raw fractions would
    /// have every knob run backwards, which is the kind of thing that
    /// is obvious in a session and invisible in a unit test unless the
    /// test says so.  Out-of-region points clamp, because a drag that
    /// leaves the track should pin at the end rather than jump.
    pub fn fraction(&self, x: i32, y: i32) -> f64 {
        let (x0, y0, x1, y1) = self.region;
        let f = match self.kind {
            Kind::Fader(Axis::X) =>
                (x - x0) as f64 / ((x1 - x0).max(1)) as f64,
            Kind::Fader(Axis::Y) =>
                1.0 - (y - y0) as f64 / ((y1 - y0).max(1)) as f64,
            Kind::Chan(Axis::X, _) =>
                (x - x0) as f64 / ((x1 - x0).max(1)) as f64,
            Kind::Chan(Axis::Y, _) =>
                1.0 - (y - y0) as f64 / ((y1 - y0).max(1)) as f64,
            // Neither a toggle nor a button has a position to read:
            // one's value is its own, the other has no value at all.
            Kind::Toggle | Kind::Button(_) => 0.0,
        };
        f.clamp(0.0, 1.0)
    }
}

/// What a walk produces: what to draw, and what listens.
///
/// `hits` comes out **innermost first**, the order `gui.py` documents
/// and for the reason it gives — the deepest region containing a point
/// is the one that gets the press.  Panel one's regions do not nest,
/// but the order is part of the contract the canvas will rely on, so it
/// is stated and kept from the start.
#[derive(Clone, Default, PartialEq, Debug)]
pub struct Display {
    pub items: Vec<Item>,
    pub hits: Vec<Hit>,
}

impl Display {
    pub fn new() -> Self {
        Display::default()
    }

    pub fn rect(&mut self, x: i32, y: i32, w: i32, h: i32, c: Colour) {
        self.items.push(Item::Rect { x, y, w, h, c });
    }

    pub fn dot(&mut self, cx: i32, cy: i32, r: i32, c: Colour) {
        self.items.push(Item::Dot { cx, cy, r, c });
    }

    pub fn text(&mut self, x: i32, y: i32, s: &str, c: Colour, scale: i32) {
        self.items.push(Item::Text { x, y, s: s.to_string(), c, scale });
    }

    pub fn hit(&mut self, kind: Kind, param: u32,
               region: (i32, i32, i32, i32)) {
        self.hits.push(Hit { kind, param, region });
    }

    /// The deepest region containing a point, or nothing.
    pub fn pick(&self, x: i32, y: i32) -> Option<Hit> {
        self.hits.iter().copied().find(|h| h.contains(x, y))
    }
}
