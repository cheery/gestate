//! Pointer in, parameter changes out.
//!
//! **The gestures are the point.**  `spec/panel.md` §"Knobs": a drag has
//! to arrive at the host as one `GESTURE_BEGIN`, the values, and one
//! `GESTURE_END`, because that is what makes it one undo step and one
//! automation-write region rather than four hundred.  Getting that
//! wrong is invisible in a screenshot and obvious a week later in a
//! session, so it is a state machine with a test rather than three
//! `if`s in an event handler.
//!
//! Nothing here draws and nothing here touches a host: it is pointer
//! events to a list of `Change`s, which is a pure function of the state
//! and the event.

use crate::list::{Display, Kind};
use crate::model::Model;

/// What the shell must tell the host.
#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Change {
    Begin(u32),
    Value(u32, f64),
    End(u32),
}

#[derive(Clone, Copy, PartialEq, Debug)]
enum Grab {
    Idle,
    /// Dragging `param`; `last` is the value already sent, so a pointer
    /// that moves within one pixel-step does not re-send it.
    Dragging { param: u32, last: f64 },
}

pub struct Interaction {
    grab: Grab,
}

impl Default for Interaction {
    fn default() -> Self {
        Interaction::new()
    }
}

impl Interaction {
    pub fn new() -> Self {
        Interaction { grab: Grab::Idle }
    }

    /// The parameter being dragged, for `panels::view`'s `hot`.
    pub fn hot(&self) -> Option<u32> {
        match self.grab {
            Grab::Dragging { param, .. } => Some(param),
            Grab::Idle => None,
        }
    }

    pub fn is_dragging(&self) -> bool {
        matches!(self.grab, Grab::Dragging { .. })
    }

    /// A press.  Lands on the deepest region containing the point, and
    /// **jumps the value there immediately** — a fader you click at the
    /// far end should go to the far end, which is what every plugin
    /// does and what a player expects.
    pub fn press(&mut self, d: &Display, m: &Model, x: i32, y: i32)
        -> Vec<Change>
    {
        if self.is_dragging() {
            // A second button while dragging: ignore rather than open a
            // second gesture the host would have to reconcile.
            return Vec::new();
        }
        let Some(hit) = d.pick(x, y) else {
            return Vec::new();
        };
        // **A click is a whole gesture.**  A toggle has nothing to drag
        // — its value comes from the model, not from where in the cell
        // you landed — so it opens and closes in one press rather than
        // leaving a gesture hanging until the mouse comes up somewhere.
        if hit.kind == Kind::Toggle {
            let Some(on) = m.banks.iter().find_map(|b| {
                let c = hit.param.checked_sub(b.routing_param0)? as usize;
                (c < 16).then(|| b.listens_on(c))
            }) else {
                return Vec::new();
            };
            let v = if on { 0.0 } else { 1.0 };
            return vec![Change::Begin(hit.param),
                        Change::Value(hit.param, v),
                        Change::End(hit.param)];
        }
        let Some(knob) = m.knobs.iter().find(|k| k.param == hit.param) else {
            return Vec::new();
        };
        let v = knob.value_at(hit.fraction(x, y));
        self.grab = Grab::Dragging { param: hit.param, last: v };
        vec![Change::Begin(hit.param), Change::Value(hit.param, v)]
    }

    /// A motion.  Silent unless a drag is open, and silent when the
    /// value has not actually changed — a host that gets a `Value` per
    /// mouse event for a value that did not move is being told noise.
    pub fn motion(&mut self, d: &Display, m: &Model, x: i32, y: i32)
        -> Vec<Change>
    {
        let Grab::Dragging { param, last } = self.grab else {
            return Vec::new();
        };
        // **The region is the one the drag started on**, not whatever is
        // under the pointer now: dragging off a fader and onto its
        // neighbour must not hand the gesture over.
        //
        // Matched on *kind* as well as id, because a button carries no
        // parameter and leaves `param` meaningless — looking one up by
        // id alone once found a button where a fader was meant, and a
        // drag then read its position out of the wrong box.
        let Some(hit) = d.hits.iter()
            .find(|h| h.param == param && matches!(h.kind, Kind::Fader(_)))
        else {
            return Vec::new();
        };
        let Some(knob) = m.knobs.iter().find(|k| k.param == param) else {
            return Vec::new();
        };
        let v = knob.value_at(hit.fraction(x, y));
        if v == last {
            return Vec::new();
        }
        self.grab = Grab::Dragging { param, last: v };
        vec![Change::Value(param, v)]
    }

    /// A release.  Closes the gesture, exactly once.
    pub fn release(&mut self) -> Vec<Change> {
        match self.grab {
            Grab::Dragging { param, .. } => {
                self.grab = Grab::Idle;
                vec![Change::End(param)]
            }
            Grab::Idle => Vec::new(),
        }
    }
}
