//! The reactive sweep — `gestate/reactive.py`, in Rust.
//!
//! Rizzo's `κ ↦ w ⇒` sequence: each instant triggers a sweep over every
//! live signal, and a signal whose clock fires is advanced one step
//! while the rest are put back untouched.  `spec/frp.md` is the design
//! and `reactive.py` is the reference this is held against — it decides
//! what a program *means*, and nothing here is allowed to disagree with
//! it.
//!
//! **What makes the port possible at all** is that signal cells live in
//! a stable arena (`Machine::sigs`) rather than in the copying heap: a
//! signal is a *place*, the sweep identifies it by where it stands, and
//! `spec/crust.md` §"the reactive half" argues that at length.
//!
//! **Deliberately not ported: the `cl`/`ticked` cross-check.**  Python
//! snapshots each signal's clock before the sweep and asserts the two
//! agree, which is a check on *the reference implementation's own*
//! consistency (§4.3).  Crust is held against that reference instead —
//! the same programs, the same instants, the same values out — so
//! carrying the check here would be re-deriving an invariant its
//! landlord already proves.

use std::collections::HashMap;

use super::{fail, Idx, Machine, Node, Num, SigId};

// The six ⃝∃ forms and the two data types the FRP interface names, at
// the tags `declarations.py` pins them to.  They travel as numbers
// because a tag *is* a number to the machine; `gmachine.py` is where
// they are decided.
pub const TAG_NOTHING: i64 = 80;
pub const TAG_JUST: i64 = 81;
pub const TAG_SYNC_L: i64 = 82;
pub const TAG_SYNC_R: i64 = 83;
pub const TAG_SYNC_BOTH: i64 = 84;
pub const TAG_WAIT: i64 = 90;
pub const TAG_WATCH: i64 = 91;
pub const TAG_SYNC: i64 = 92;
pub const TAG_NEVER: i64 = 93;
pub const TAG_TAIL: i64 = 94;
pub const TAG_EXISTS5: i64 = 95;
pub const TAG_DELAY: i64 = 96;

/// What arrived this instant: channel id to the value it carries.
pub type Arrivals = HashMap<i64, Idx>;

impl Machine {
    /// A signal cell that is not on the *now* heap has not been reached
    /// by this sweep, and reading it would answer last step's value.
    fn require_current(&self, id: SigId, what: &str) {
        match self.sig(id) {
            None => fail(&format!("{what} on a collected signal")),
            Some(c) if !c.current => fail(&format!(
                "{what} of a signal on the earlier heap: it has not been \
                 updated yet this step")),
            Some(_) => {}
        }
    }

    fn is_just(&self, i: Idx) -> bool {
        matches!(self.heap[self.deref(i)], Node::Con(TAG_JUST, _))
    }

    /// Whether a ⃝∃ node's tail fires on this instant's arrivals.
    ///
    /// **No case for `TAG_DELAY`**: `delay t : ⃝∀A` is never a signal
    /// tail — tails are `⃝∃(Sig A)` — so it cannot reach here.  An
    /// earlier revision of the reference fired unconditionally at this
    /// point, which made an empty clock behave like a universal one.
    pub fn ticked(&self, arrivals: &Arrivals, node: Idx) -> bool {
        let n = self.deref(node);
        let (tag, args) = match &self.heap[n] {
            Node::Con(t, a) => (*t, a.clone()),
            _ => return false,
        };
        match tag {
            TAG_NEVER => false,
            TAG_EXISTS5 if args.len() >= 2 => self.ticked(arrivals, args[1]),
            TAG_WAIT if !args.is_empty() => {
                match self.heap[self.deref(args[0])] {
                    Node::Chan(id) => arrivals.contains_key(&id),
                    _ => false,
                }
            }
            TAG_WATCH if !args.is_empty() => {
                match self.heap[self.deref(args[0])] {
                    Node::Sig(id) => {
                        self.require_current(id, "watch");
                        let c = self.sig(id).unwrap();
                        // "in1 v ⟨⊤⟩" — Just-shaped *and* updated this
                        // step.
                        self.is_just(c.value) && c.ticked
                    }
                    _ => false,
                }
            }
            TAG_TAIL if !args.is_empty() => {
                match self.heap[self.deref(args[0])] {
                    Node::Sig(id) => {
                        self.require_current(id, "tail");
                        self.sig(id).unwrap().ticked
                    }
                    _ => false,
                }
            }
            TAG_SYNC if args.len() >= 2 => {
                self.ticked(arrivals, args[0])
                    || self.ticked(arrivals, args[1])
            }
            _ => false,
        }
    }

    /// Apply a function node to an argument, forcing the result — the
    /// reference's `_apply`.
    fn apply1(&mut self, f: Idx, arg: Idx) -> Idx {
        let ap = self.alloc(Node::Ap(f, arg));
        self.force_node(ap)
    }

    /// Advance a ⃝∃ tail one step, to the new value.
    ///
    /// `wait κ` reads **its own** channel out of `arrivals` rather than
    /// being handed one value: with a single arrival the two are the
    /// same, and with two — an audio clock and a control clock landing
    /// together — handing one node to both sides of a `sync` would give
    /// one clock the other's sample.
    pub fn advance(&mut self, arrivals: &Arrivals, tail: Idx) -> Idx {
        let t = self.deref(tail);
        let (tag, args) = match &self.heap[t] {
            Node::Con(tg, a) => (*tg, a.clone()),
            other => fail(&format!("advance on a non-constructor: {other:?}")),
        };
        match tag {
            // A ⃝∀ value is available whenever any clock ticks.
            TAG_DELAY => {
                if args.is_empty() {
                    fail("advance delay: empty node");
                }
                self.deref(args[0])
            }
            TAG_WAIT => {
                let ch = match self.heap[self.deref(args[0])] {
                    Node::Chan(id) => id,
                    _ => fail("advance wait: argument is not a channel"),
                };
                match arrivals.get(&ch) {
                    Some(v) => *v,
                    // `ticked` gates every call, so the sweep cannot
                    // reach this; it is here because the two must not be
                    // able to drift.
                    None => fail(&format!(
                        "advance wait on channel {ch}, which did not arrive \
                         this instant")),
                }
            }
            TAG_WATCH => {
                let id = match self.heap[self.deref(args[0])] {
                    Node::Sig(id) => id,
                    _ => fail("advance watch on a non-signal"),
                };
                self.require_current(id, "watch");
                let value = self.deref(self.sig(id).unwrap().value);
                match &self.heap[value] {
                    Node::Con(TAG_JUST, inner) if !inner.is_empty() =>
                        inner[0],
                    _ => fail("advance watch on a non-Just"),
                }
            }
            TAG_TAIL => self.deref(args[0]),
            // ⟨v 5 w⟩ ⇒ f ⟨w⟩ where v = delay f.  The ⃝∀ side carries no
            // clock of its own, so it is unwrapped; the ⃝∃ side supplies
            // both the value and the clock.
            TAG_EXISTS5 => {
                let d = self.deref(args[0]);
                let v = self.deref(args[1]);
                let v_new = self.advance(arrivals, v);
                let f = match &self.heap[d] {
                    Node::Con(TAG_DELAY, inner) if !inner.is_empty() =>
                        inner[0],
                    _ => fail("advance ⟨5⟩: the left side is not a delay"),
                };
                self.apply1(f, v_new)
            }
            TAG_SYNC => {
                let (v, w) = (self.deref(args[0]), self.deref(args[1]));
                let tv = self.ticked(arrivals, v);
                let tw = self.ticked(arrivals, w);
                // `sync v w` produces a `Sync A B` — an ordinary data
                // type user code pattern-matches.  Building another
                // delayed computation here would hand `case` a tag it
                // has no alternative for.
                match (tv, tw) {
                    (true, false) => {
                        let v_new = self.advance(arrivals, v);
                        self.alloc(Node::Con(TAG_SYNC_L, vec![v_new]))
                    }
                    (false, true) => {
                        let w_new = self.advance(arrivals, w);
                        self.alloc(Node::Con(TAG_SYNC_R, vec![w_new]))
                    }
                    // Both at once: before arrivals were a set this was
                    // reachable only when the two shared a channel; a
                    // block boundary is now the ordinary way here.
                    _ => {
                        let v_new = self.advance(arrivals, v);
                        let w_new = self.advance(arrivals, w);
                        self.alloc(Node::Con(TAG_SYNC_BOTH,
                                             vec![v_new, w_new]))
                    }
                }
            }
            other => fail(&format!("advance: unknown tag {other}")),
        }
    }

    /// One signal off the earlier heap: advance it if its clock fires,
    /// put it back either way.
    fn update_one(&mut self, arrivals: &Arrivals, id: SigId) {
        let Some(cell) = self.sig(id).cloned() else { return };
        let tail = self.deref(cell.tail);
        let fires = self.ticked(arrivals, tail);

        if !fires {
            if let Some(c) = self.sig_mut(id) {
                c.ticked = false;
                c.current = true;
            }
            self.now.push(id);
            return;
        }

        // **Running user code can allocate signals of its own** —
        // `switch` and friends build new dataflow, and `SigCons`
        // registers each on the now heap as it goes.  They are held
        // aside: `l` keeps its identity, because everything already
        // pointing at it must see the update, so the signal `advance`
        // returns is folded *into* `l` in place and must not also
        // survive as a cell of its own.
        let mark = self.now.len();
        let l_new = self.advance(arrivals, tail);
        let allocated: Vec<SigId> = self.now.drain(mark..).collect();

        let folded = match self.heap[self.deref(l_new)] {
            Node::Sig(new_id) => {
                let n = self.sig(new_id).cloned();
                if let (Some(n), Some(c)) = (n, self.sig_mut(id)) {
                    c.value = n.value;
                    c.tail = n.tail;
                    c.ticked = true;
                    c.current = true;
                }
                Some(new_id)
            }
            _ => {
                // A plain value: wrap it in a signal whose tail never
                // fires again.
                let never = self.alloc(Node::Con(TAG_NEVER, vec![]));
                if let Some(c) = self.sig_mut(id) {
                    c.value = l_new;
                    c.tail = never;
                    c.ticked = true;
                    c.current = true;
                }
                None
            }
        };
        self.now.push(id);
        for a in allocated {
            if Some(a) != folded {
                self.now.push(a);
            }
        }
    }

    /// One instant — all of `arrivals` at once — over every live signal.
    pub fn reactive_step(&mut self, arrivals: &Arrivals) {
        let earlier: Vec<SigId> = std::mem::take(&mut self.now);
        // Everything moves behind the ✓ frontier; each cell goes back
        // on the now heap as the sweep reaches it.
        for id in &earlier {
            if let Some(c) = self.sig_mut(*id) {
                c.current = false;
            }
        }
        for id in earlier {
            self.update_one(arrivals, id);
        }
    }

    /// The now heap, for a driver that wants to pin what it is holding.
    pub fn now_signals(&self) -> &[SigId] {
        &self.now
    }

    /// Read a signal's current value without the machine's stack —
    /// what a host walking a `Sub` tree needs.
    pub fn sig_value(&self, id: SigId) -> Option<Idx> {
        self.sig(id).map(|c| c.value)
    }
}

/// A value a host puts on a channel this instant.
pub fn arrival_int(m: &mut Machine, v: i64) -> Idx {
    m.alloc(Node::Num(Num::I(v as i128)))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Machine, Node, Num};

    fn machine() -> Machine {
        let (m, _e) = Machine::from_text(
            "crust 1\nblock\nI Unwind\nglobal main 0 0\nentry main\n");
        m
    }

    /// `x ::: wait κ` — a cell that fires when its channel arrives, and
    /// takes that channel's own value.
    fn waiting_on(m: &mut Machine, chan: i64, start: i64) -> SigId {
        let value = m.alloc(Node::Num(Num::I(start as i128)));
        let ch = m.alloc(Node::Chan(chan));
        let tail = m.alloc(Node::Con(TAG_WAIT, vec![ch]));
        let id = m.sig_alloc(value, tail);
        m.sig_retain(id);
        id
    }

    fn int_at(m: &Machine, i: Idx) -> i64 {
        match m.heap_at(m.deref(i)) {
            Node::Num(Num::I(v)) => *v as i64,
            other => panic!("not an integer: {other:?}"),
        }
    }

    #[test]
    fn a_signal_takes_its_own_channels_value() {
        let mut m = machine();
        let a = waiting_on(&mut m, 7, 0);
        m.push_now(a);
        let v = m.alloc(Node::Num(Num::I(42)));
        let mut arrivals = Arrivals::new();
        arrivals.insert(7, v);
        m.reactive_step(&arrivals);
        assert_eq!(int_at(&m, m.sig_value(a).unwrap()), 42);
        assert!(m.sig(a).unwrap().ticked, "it fired");
        assert!(m.sig(a).unwrap().current, "and is back on the now heap");
    }

    #[test]
    fn a_signal_whose_channel_is_silent_keeps_its_value() {
        let mut m = machine();
        let a = waiting_on(&mut m, 7, 5);
        m.push_now(a);
        let v = m.alloc(Node::Num(Num::I(99)));
        let mut arrivals = Arrivals::new();
        arrivals.insert(8, v);              // a different channel
        m.reactive_step(&arrivals);
        assert_eq!(int_at(&m, m.sig_value(a).unwrap()), 5, "untouched");
        assert!(!m.sig(a).unwrap().ticked, "it did not fire");
    }

    #[test]
    fn two_channels_do_not_hand_each_other_their_samples() {
        // The defect the reference's own docstring records: with one
        // arrival, handing the same node to both sides looks right.
        let mut m = machine();
        let a = waiting_on(&mut m, 1, 0);
        let b = waiting_on(&mut m, 2, 0);
        m.push_now(a);
        m.push_now(b);
        let va = m.alloc(Node::Num(Num::I(10)));
        let vb = m.alloc(Node::Num(Num::I(20)));
        let mut arrivals = Arrivals::new();
        arrivals.insert(1, va);
        arrivals.insert(2, vb);
        m.reactive_step(&arrivals);
        assert_eq!(int_at(&m, m.sig_value(a).unwrap()), 10);
        assert_eq!(int_at(&m, m.sig_value(b).unwrap()), 20);
    }

    #[test]
    fn never_never_fires() {
        let mut m = machine();
        let value = m.alloc(Node::Num(Num::I(3)));
        let never = m.alloc(Node::Con(TAG_NEVER, vec![]));
        let id = m.sig_alloc(value, never);
        m.sig_retain(id);
        m.push_now(id);
        let v = m.alloc(Node::Num(Num::I(1)));
        let mut arrivals = Arrivals::new();
        arrivals.insert(1, v);
        m.reactive_step(&arrivals);
        assert!(!m.sig(id).unwrap().ticked);
        assert_eq!(int_at(&m, m.sig_value(id).unwrap()), 3);
    }

    #[test]
    fn sync_reports_which_side_fired() {
        let mut m = machine();
        let c1 = m.alloc(Node::Chan(1));
        let c2 = m.alloc(Node::Chan(2));
        let w1 = m.alloc(Node::Con(TAG_WAIT, vec![c1]));
        let w2 = m.alloc(Node::Con(TAG_WAIT, vec![c2]));
        let sync = m.alloc(Node::Con(TAG_SYNC, vec![w1, w2]));
        let start = m.alloc(Node::Num(Num::I(0)));
        let id = m.sig_alloc(start, sync);
        m.sig_retain(id);
        m.push_now(id);

        // Only the left channel arrives.
        let va = m.alloc(Node::Num(Num::I(11)));
        let mut only_left = Arrivals::new();
        only_left.insert(1, va);
        m.reactive_step(&only_left);
        let v = m.deref(m.sig_value(id).unwrap());
        match m.heap_at(v) {
            Node::Con(TAG_SYNC_L, args) => {
                assert_eq!(int_at(&m, args[0]), 11)
            }
            other => panic!("expected a left-only Sync, got {other:?}"),
        }
    }

    #[test]
    fn both_at_once_is_a_both() {
        let mut m = machine();
        let c1 = m.alloc(Node::Chan(1));
        let c2 = m.alloc(Node::Chan(2));
        let w1 = m.alloc(Node::Con(TAG_WAIT, vec![c1]));
        let w2 = m.alloc(Node::Con(TAG_WAIT, vec![c2]));
        let sync = m.alloc(Node::Con(TAG_SYNC, vec![w1, w2]));
        let start = m.alloc(Node::Num(Num::I(0)));
        let id = m.sig_alloc(start, sync);
        m.sig_retain(id);
        m.push_now(id);
        // A block boundary: an audio clock and a control clock together.
        let va = m.alloc(Node::Num(Num::I(1)));
        let vb = m.alloc(Node::Num(Num::I(2)));
        let mut both = Arrivals::new();
        both.insert(1, va);
        both.insert(2, vb);
        m.reactive_step(&both);
        let v = m.deref(m.sig_value(id).unwrap());
        match m.heap_at(v) {
            Node::Con(TAG_SYNC_BOTH, args) => {
                assert_eq!(int_at(&m, args[0]), 1);
                assert_eq!(int_at(&m, args[1]), 2);
            }
            other => panic!("expected a both-Sync, got {other:?}"),
        }
    }

    #[test]
    fn a_cell_keeps_its_place_in_the_sweep_across_a_collection() {
        // **A hand-built `wait` cell is one-shot**: `advance` yields the
        // arrival's *value*, and `update_one` wraps a plain value in a
        // signal whose tail is `never`.  A program's `x ::: mkSig (wait
        // c)` rebuilds its tail each step; this fixture is the leaf, so
        // it fires once and then rests.  What is under test is the
        // *identity*, which has to survive both.
        let mut m = machine();
        let a = waiting_on(&mut m, 7, 0);
        m.push_now(a);
        let v = m.alloc(Node::Num(Num::I(1)));
        let mut arrivals = Arrivals::new();
        arrivals.insert(7, v);

        m.reactive_step(&arrivals);
        assert_eq!(int_at(&m, m.sig_value(a).unwrap()), 1);

        for _ in 0..5 {
            let mut nothing = m.alloc(Node::Num(Num::I(0)));
            m.collect(&mut [&mut nothing]);
            m.reactive_step(&arrivals);
            // Same id, still on the now heap, value intact — which is
            // what lets a driver key its clocks by cell.
            assert_eq!(m.now_signals(), &[a]);
            assert_eq!(int_at(&m, m.sig_value(a).unwrap()), 1);
            assert!(!m.sig(a).unwrap().ticked, "never fires again");
        }
    }
}
