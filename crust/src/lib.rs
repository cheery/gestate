//! crust — the G-machine's pure core, in Rust.  `spec/crust.md`.
//!
//! `gestate/gmachine.py` is the reference and this is its mirror, held
//! together by `test/test_crust.py`: the same compiled program, run by
//! both, must force to the same canonical value.  Only the pure core
//! crosses in this cut — the instructions a score's forcing needs — and
//! `gestate/crust.py` refuses to serialize anything beyond it, so a
//! program that arrives here is one this machine wholly understands.
//!
//! The heap is a `Vec<Node>` and a reference is an index: laziness is
//! mutation (`Update` overwrites a node with an indirection), and indices
//! make the mutation safe with no reference-counting ceremony.  Nothing
//! is collected in this cut; a score performer's working set is a window,
//! and the semispace copy can arrive when a long night needs it.
//!
//! Integers are `i128`, refused loudly past that width: the seed
//! arithmetic (`music.ges`, SplitMix64 against an explicit 2^64) needs
//! 64x64 products and nothing in the tree needs more.  Division floors,
//! as Python's does — `div_euclid` disagrees on a negative divisor, which
//! is exactly the kind of quiet corner parity tests exist for.  Floats
//! are `f64` beside the integers in one `Num`, the way `NNum` holds
//! either under Python's duck typing, with the promotions written out
//! and CPython's own float `%` and `//` transcribed rather than
//! approximated; a float literal crosses the seam as its IEEE bits and
//! is printed back as them, because the parity claimed for floats is
//! bit parity.

//! This file is the *library*: the machine, `Machine::from_text` and
//! `Machine::force_entry` for the CLI (`main.rs`), and an
//! `extern "C"` surface (`ffi`, at the bottom) for a host that loads
//! the cdylib — gestate's Python side does, over ctypes, the same way
//! it loads the graphs it compiles.  No panic crosses the C boundary:
//! every entry point catches, parks the message, and returns null.

use std::collections::HashMap;
use std::fmt::Write as _;

type Idx = usize;

/// What `NNum` holds: Python's duck typing made explicit.  The
/// reference keeps ints and floats in one node and lets the operators
/// promote; this enum is that fact written down, with the promotions
/// spelled out below rather than inherited.
#[derive(Clone, Copy, Debug)]
enum Num {
    I(i128),
    F(f64),
}

fn as_f(n: Num) -> f64 {
    match n {
        Num::I(i) => i as f64,   // `float(int)`: round-to-nearest, both
        Num::F(f) => f,
    }
}

#[derive(Clone, Debug)]
enum Node {
    Num(Num),
    /// A channel identity — the score's own name for a place a value
    /// comes from.  Created, never read: the host does the reading.
    Chan(i64),
    Ap(Idx, Idx),
    Global(usize, usize),        // arity, block id
    Ind(Option<Idx>),
    Con(i64, Vec<Idx>),
}

#[derive(Clone, Debug)]
enum Instr {
    Unwind,
    PushGlobal(String),
    PushInt(i128),
    Push(usize),
    PushArg(usize),
    Mkap,
    Update(usize),
    Pop(usize),
    Alloc(usize),
    Slide(usize),
    Eval,
    Pack(i64, usize),
    PackTuple(i64, usize),       // tag precomputed by the serializer
    Proj(usize),
    CaseJump(Vec<(i64, usize)>), // (tag, block id)
    EqInt(i64, i64),
    LtInt(i64, i64),
    AddInt,
    SubInt,
    MulInt,
    DivInt,
    ModInt,
    XorInt,
    PushFloat(u64),              // IEEE bits — exact across the seam
    DivFloat,
    ModFloat,
    ToFloat,
    FloorFloat,
    MathFloat(MathFn),
    NewChan,
    MatchFail,
}

/// The five transcendentals, `gmachine.MATH_FLOAT` — one instruction,
/// a name inside, exactly as the reference spells it.
#[derive(Clone, Copy, Debug)]
enum MathFn {
    Sin,
    Cos,
    Exp,
    Log,
    Sqrt,
}

pub struct Machine {
    heap: Vec<Node>,
    globals: HashMap<String, Idx>,
    blocks: Vec<Vec<Instr>>,
    stack: Vec<Idx>,             // top is the END, where Python's is [0]
    dump: Vec<(Vec<Instr>, usize, Vec<Idx>)>,
    code: Vec<Instr>,
    pc: usize,
    /// Fresh channel ids, minted in the order the reference mints
    /// them so a program means the same thing on both machines.
    chans: i64,
}

/// A refusal.  Spelled as a panic carrying the message, because the
/// machine has two landlords: the CLI catches it and exits 1 with the
/// text on stderr (the behaviour this always had), and the C surface
/// catches it at the boundary and hands the text to the host — a
/// panic must never unwind across FFI.
fn fail(msg: &str) -> ! {
    std::panic::panic_any(format!("crust: {msg}"))
}

// Python's floor division and modulo, exactly.
fn fdiv(a: i128, b: i128) -> i128 {
    let q = a / b;
    if (a % b != 0) && ((a % b < 0) != (b < 0)) { q - 1 } else { q }
}

fn fmod(a: i128, b: i128) -> i128 {
    a - fdiv(a, b) * b
}

// CPython's `float_divmod`, transcribed: `%` takes the divisor's sign
// (C `fmod` then one adjustment), and `//` is the quotient that pairs
// with it, floored with the half-ulp correction CPython applies.  Not
// `a.div_euclid(b)`, not `(a / b).floor()` — those disagree with the
// reference in exactly the corners a parity suite exists for.
fn pymod_f(a: f64, b: f64) -> f64 {
    let mut r = a % b;
    if r != 0.0 {
        if (b < 0.0) != (r < 0.0) {
            r += b;
        }
    } else {
        r = 0.0f64.copysign(b);
    }
    r
}

fn pyfloordiv_f(a: f64, b: f64) -> f64 {
    let r = a % b;
    let mut div = (a - r) / b;
    if r != 0.0 && (b < 0.0) != (r < 0.0) {
        div -= 1.0;
    }
    if div != 0.0 {
        let floordiv = div.floor();
        if div - floordiv > 0.5 { floordiv + 1.0 } else { floordiv }
    } else {
        0.0f64.copysign(a / b)
    }
}

impl Machine {
    fn alloc(&mut self, node: Node) -> Idx {
        self.heap.push(node);
        self.heap.len() - 1
    }

    fn deref(&self, mut i: Idx) -> Idx {
        loop {
            match &self.heap[i] {
                Node::Ind(Some(t)) => i = *t,
                Node::Ind(None) => fail("dereferenced a null indirection"),
                _ => return i,
            }
        }
    }

    fn two_nums(&self, name: &str) -> (Num, Num) {
        // The first argument on top, the second below — `_prim_operands`.
        let n = self.stack.len();
        if n < 2 { fail(&format!("{name}: missing operands")); }
        let a = self.deref(self.stack[n - 1]);
        let b = self.deref(self.stack[n - 2]);
        match (&self.heap[a], &self.heap[b]) {
            (Node::Num(x), Node::Num(y)) => (*x, *y),
            _ => fail(&format!("{name}: operands must be numbers")),
        }
    }

    fn two_ints(&self, name: &str) -> (i128, i128) {
        match self.two_nums(name) {
            (Num::I(a), Num::I(b)) => (a, b),
            _ => fail(&format!("{name}: operands must be integers")),
        }
    }

    fn one_num(&self, name: &str) -> Num {
        let n = self.stack.len();
        if n < 1 { fail(&format!("{name}: missing operand")); }
        match &self.heap[self.deref(self.stack[n - 1])] {
            Node::Num(x) => *x,
            _ => fail(&format!("{name}: operand must be a number")),
        }
    }

    fn prim_result1(&mut self, node: Node) {
        let i = self.alloc(node);
        let n = self.stack.len();
        self.stack.truncate(n - 1);
        self.stack.push(i);
    }

    fn prim_result(&mut self, node: Node) {
        let i = self.alloc(node);
        let n = self.stack.len();
        self.stack.truncate(n - 2);
        self.stack.push(i);
    }

    fn step(&mut self, instr: Instr) {
        match instr {
            Instr::Unwind => {
                let mut node = *self.stack.last()
                    .unwrap_or_else(|| fail("Unwind on an empty stack"));
                let mut walked = false;
                loop {
                    match self.heap[node].clone() {
                        Node::Ap(f, _) => {
                            self.stack.push(f);
                            node = f;
                            walked = true;
                        }
                        Node::Ind(Some(t)) => {
                            node = t;
                            *self.stack.last_mut().unwrap() = t;
                            walked = true;
                        }
                        Node::Ind(None) => fail("Unwind on null indirection"),
                        Node::Num(_) | Node::Con(..)
                        | Node::Chan(_) => {
                            if walked {
                                self.code.clear();
                                self.pc = 0;
                            }
                            return;
                        }
                        Node::Global(arity, block) => {
                            if self.stack.len() < arity + 1 {
                                fail("unwinding global with too few args");
                            }
                            self.code = self.blocks[block].clone();
                            self.pc = 0;
                            return;
                        }
                    }
                }
            }
            Instr::PushGlobal(name) => {
                let g = *self.globals.get(&name).unwrap_or_else(
                    || fail(&format!("unknown global '{name}'")));
                self.stack.push(g);
            }
            Instr::PushInt(n) => {
                let i = self.alloc(Node::Num(Num::I(n)));
                self.stack.push(i);
            }
            Instr::Push(n) => {
                let i = self.stack[self.stack.len() - 1 - n];
                self.stack.push(i);
            }
            Instr::PushArg(n) => {
                let ap = self.stack[self.stack.len() - 2 - n];
                match self.heap[self.deref(ap)] {
                    Node::Ap(_, arg) => self.stack.push(arg),
                    _ => fail("PushArg: stack slot is not an application"),
                }
            }
            Instr::Mkap => {
                let f = self.stack.pop().unwrap();
                let a = self.stack.pop().unwrap();
                let i = self.alloc(Node::Ap(f, a));
                self.stack.push(i);
            }
            Instr::Update(n) => {
                let result = self.stack.pop().unwrap();
                let target = self.stack[self.stack.len() - 1 - n];
                self.heap[target] = Node::Ind(Some(result));
            }
            Instr::Pop(n) => {
                let len = self.stack.len();
                self.stack.truncate(len - n);
            }
            Instr::Alloc(n) => {
                for _ in 0..n {
                    let i = self.alloc(Node::Ind(None));
                    self.stack.push(i);
                }
            }
            Instr::Slide(n) => {
                let top = self.stack.pop().unwrap();
                let len = self.stack.len();
                self.stack.truncate(len - n);
                self.stack.push(top);
            }
            Instr::Eval => {
                let a = *self.stack.last().unwrap();
                let below = self.stack[..self.stack.len() - 1].to_vec();
                self.dump.push(
                    (std::mem::take(&mut self.code), self.pc, below));
                self.stack = vec![a];
                self.code = vec![Instr::Unwind];
                self.pc = 0;
            }
            Instr::Pack(tag, arity) | Instr::PackTuple(tag, arity) => {
                // Drained low-to-high, the deepest cell first — which is
                // source order, the same order `_pack`'s reverse restores.
                let at = self.stack.len() - arity;
                let args: Vec<Idx> = self.stack.drain(at..).collect();
                let i = self.alloc(Node::Con(tag, args));
                self.stack.push(i);
            }
            Instr::Proj(k) => {
                let top = self.deref(*self.stack.last().unwrap());
                match &self.heap[top] {
                    Node::Con(_, args) if k < args.len() => {
                        let a = args[k];
                        *self.stack.last_mut().unwrap() = a;
                    }
                    _ => fail("Proj on a value that is not a constructor"),
                }
            }
            Instr::CaseJump(table) => {
                let popped = self.stack.pop().unwrap();
                let top = self.deref(popped);
                let (tag, args) = match &self.heap[top] {
                    Node::Con(t, a) => (*t, a.clone()),
                    _ => fail("CaseJump on non-constructor"),
                };
                for (t, block) in &table {
                    if *t == tag {
                        // Source order onto the stack: the last argument
                        // ends on top, as `list(reversed(args))` leaves it.
                        self.stack.extend(args.iter());
                        let mut body = self.blocks[*block].clone();
                        body.extend_from_slice(&self.code[self.pc..]);
                        self.code = body;
                        self.pc = 0;
                        return;
                    }
                }
                fail(&format!("CaseJump: no alt for tag {tag}"));
            }
            // The shared arithmetic promotes exactly as Python's
            // operators do under `NNum`'s duck typing: two ints stay
            // exact (checked at 128 bits), anything else is done in
            // doubles.
            Instr::EqInt(t, f) => {
                let (a, b) = self.two_nums("EqInt");
                let eq = match (a, b) {
                    (Num::I(x), Num::I(y)) => x == y,
                    _ => as_f(a) == as_f(b),
                };
                self.prim_result(Node::Con(if eq { t } else { f },
                                           vec![]));
            }
            Instr::LtInt(t, f) => {
                let (a, b) = self.two_nums("LtInt");
                let lt = match (a, b) {
                    (Num::I(x), Num::I(y)) => x < y,
                    _ => as_f(a) < as_f(b),
                };
                self.prim_result(Node::Con(if lt { t } else { f },
                                           vec![]));
            }
            Instr::AddInt => {
                let v = match self.two_nums("AddInt") {
                    (Num::I(a), Num::I(b)) => Num::I(
                        a.checked_add(b).unwrap_or_else(
                            || fail("an integer wider than 128 bits"))),
                    (a, b) => Num::F(as_f(a) + as_f(b)),
                };
                self.prim_result(Node::Num(v));
            }
            Instr::SubInt => {
                let v = match self.two_nums("SubInt") {
                    (Num::I(a), Num::I(b)) => Num::I(
                        a.checked_sub(b).unwrap_or_else(
                            || fail("an integer wider than 128 bits"))),
                    (a, b) => Num::F(as_f(a) - as_f(b)),
                };
                self.prim_result(Node::Num(v));
            }
            Instr::MulInt => {
                let v = match self.two_nums("MulInt") {
                    (Num::I(a), Num::I(b)) => Num::I(
                        a.checked_mul(b).unwrap_or_else(
                            || fail("an integer wider than 128 bits"))),
                    (a, b) => Num::F(as_f(a) * as_f(b)),
                };
                self.prim_result(Node::Num(v));
            }
            Instr::DivInt => {
                let v = match self.two_nums("DivInt") {
                    (Num::I(a), Num::I(b)) => {
                        if b == 0 { fail("DivInt: division by zero"); }
                        Num::I(fdiv(a, b))
                    }
                    (a, b) => {
                        if as_f(b) == 0.0 {
                            fail("DivInt: division by zero");
                        }
                        Num::F(pyfloordiv_f(as_f(a), as_f(b)))
                    }
                };
                self.prim_result(Node::Num(v));
            }
            Instr::ModInt => {
                let v = match self.two_nums("ModInt") {
                    (Num::I(a), Num::I(b)) => {
                        if b == 0 { fail("ModInt: division by zero"); }
                        Num::I(fmod(a, b))
                    }
                    (a, b) => {
                        if as_f(b) == 0.0 {
                            fail("ModInt: division by zero");
                        }
                        Num::F(pymod_f(as_f(a), as_f(b)))
                    }
                };
                self.prim_result(Node::Num(v));
            }
            Instr::XorInt => {
                // The fold's meaning, not two's-complement: negatives are
                // refused, as the reference refuses them.
                let (a, b) = self.two_ints("XorInt");
                if a < 0 || b < 0 { fail("XorInt on a negative number"); }
                self.prim_result(Node::Num(Num::I(a ^ b)));
            }
            Instr::PushFloat(bits) => {
                let i = self.alloc(Node::Num(Num::F(f64::from_bits(bits))));
                self.stack.push(i);
            }
            Instr::DivFloat => {
                let (a, b) = self.two_nums("DivFloat");
                if as_f(b) == 0.0 { fail("DivFloat: division by zero"); }
                self.prim_result(Node::Num(Num::F(as_f(a) / as_f(b))));
            }
            Instr::ModFloat => {
                let (a, b) = self.two_nums("ModFloat");
                if as_f(b) == 0.0 { fail("ModFloat: division by zero"); }
                self.prim_result(Node::Num(Num::F(pymod_f(as_f(a),
                                                          as_f(b)))));
            }
            Instr::ToFloat => {
                let a = self.one_num("ToFloat");
                self.prim_result1(Node::Num(Num::F(as_f(a))));
            }
            Instr::FloorFloat => {
                let a = as_f(self.one_num("FloorFloat"));
                if !a.is_finite() {
                    fail("FloorFloat on a value with no floor");
                }
                let f = a.floor();
                // `i128::MAX as f64` rounds up past the type; the strict
                // bound below is exact in doubles.
                if f >= 2f64.powi(127) || f < -(2f64.powi(127)) {
                    fail("an integer wider than 128 bits");
                }
                self.prim_result1(Node::Num(Num::I(f as i128)));
            }
            Instr::MathFloat(op) => {
                // The reference raises where C returns NaN — `log` and
                // `sqrt` of a negative — and the mirror refuses the
                // same way rather than agreeing on a value silently.
                let a = as_f(self.one_num("MathFloat"));
                let v = match op {
                    MathFn::Sin => a.sin(),
                    MathFn::Cos => a.cos(),
                    MathFn::Exp => a.exp(),
                    MathFn::Log => {
                        if a <= 0.0 { fail("log is undefined at or below zero"); }
                        a.ln()
                    }
                    MathFn::Sqrt => {
                        if a < 0.0 { fail("sqrt is undefined below zero"); }
                        a.sqrt()
                    }
                };
                self.prim_result1(Node::Num(Num::F(v)));
            }
            Instr::NewChan => {
                let id = self.chans;
                self.chans += 1;
                let i = self.alloc(Node::Chan(id));
                self.stack.push(i);
            }
            Instr::MatchFail => {
                fail("pattern match failure: no alternative matched");
            }
        }
    }

    fn run(&mut self) {
        loop {
            if self.pc >= self.code.len() {
                match self.dump.pop() {
                    None => return,
                    Some((code, pc, mut below)) => {
                        self.code = code;
                        self.pc = pc;
                        if let Some(&top) = self.stack.last() {
                            below.push(top);
                        }
                        self.stack = below;
                    }
                }
            } else {
                let instr = self.code[self.pc].clone();
                self.pc += 1;
                self.step(instr);
            }
        }
    }

    /// Reduce `i` to WHNF on the machine itself, `_force`-style: the
    /// caller's frame is parked on the dump and restored after.
    fn force(&mut self, i: Idx) -> Idx {
        let code = std::mem::take(&mut self.code);
        let stack = std::mem::replace(&mut self.stack, vec![i]);
        let pc = self.pc;
        self.code = vec![Instr::Unwind];
        self.pc = 0;
        self.run();
        let out = self.deref(*self.stack.last().unwrap_or(&i));
        self.code = code;
        self.stack = stack;
        self.pc = pc;
        out
    }

    /// The canonical spelling both machines print: `42`, `#tag(a b)`,
    /// and a float as its IEEE bits — `f3ff8000000000000` — because
    /// the parity claimed for floats is *bit* parity, and the two
    /// languages' decimal printers disagree about exponents long
    /// before the numbers do.
    fn show(&mut self, i: Idx, out: &mut String) {
        let i = self.force(i);
        match self.heap[i].clone() {
            Node::Num(Num::I(n)) => { write!(out, "{n}").unwrap(); }
            Node::Num(Num::F(x)) => {
                write!(out, "f{:016x}", x.to_bits()).unwrap();
            }
            Node::Con(tag, args) => {
                write!(out, "#{tag}(").unwrap();
                for (k, a) in args.iter().enumerate() {
                    if k > 0 { out.push(' '); }
                    self.show(*a, out);
                }
                out.push(')');
            }
            other => fail(&format!("show: unexpected node {other:?}")),
        }
    }
}

/// The flat text format `gestate/crust.py` writes.  Lines, whitespace
/// split: `crust 1`, `block`, `I <Instr> <args…>`, `global <name> <arity>
/// <block>`, `entry <name>`.
fn parse(text: &str) -> (Vec<Vec<Instr>>, Vec<(String, usize, usize)>, String) {
    let mut blocks: Vec<Vec<Instr>> = Vec::new();
    let mut globals = Vec::new();
    let mut entry = String::new();
    let mut lines = text.lines().peekable();
    match lines.next() {
        Some(l) if l.trim() == "crust 1" => {}
        _ => fail("not a crust 1 program"),
    }
    for line in lines {
        let mut w = line.split_whitespace();
        match w.next() {
            None => {}
            Some("block") => blocks.push(Vec::new()),
            Some("global") => {
                let name = w.next().unwrap_or_else(|| fail("global: name"));
                let arity = w.next().and_then(|s| s.parse().ok())
                    .unwrap_or_else(|| fail("global: arity"));
                let block = w.next().and_then(|s| s.parse().ok())
                    .unwrap_or_else(|| fail("global: block"));
                globals.push((name.to_string(), arity, block));
            }
            Some("entry") => {
                entry = w.next().unwrap_or_else(|| fail("entry: name"))
                    .to_string();
            }
            Some("I") => {
                let op = w.next().unwrap_or_else(|| fail("I: opcode"));
                let mut num = |what: &str| -> i128 {
                    w.next().and_then(|s| s.parse().ok())
                        .unwrap_or_else(|| fail(&format!("{op}: {what}")))
                };
                let instr = match op {
                    "Unwind" => Instr::Unwind,
                    "Mkap" => Instr::Mkap,
                    "Eval" => Instr::Eval,
                    "MatchFail" => Instr::MatchFail,
                    "NewChan" => Instr::NewChan,
                    "AddInt" => Instr::AddInt,
                    "SubInt" => Instr::SubInt,
                    "MulInt" => Instr::MulInt,
                    "DivInt" => Instr::DivInt,
                    "ModInt" => Instr::ModInt,
                    "XorInt" => Instr::XorInt,
                    "DivFloat" => Instr::DivFloat,
                    "ModFloat" => Instr::ModFloat,
                    "ToFloat" => Instr::ToFloat,
                    "FloorFloat" => Instr::FloorFloat,
                    "PushInt" => Instr::PushInt(num("n")),
                    "PushFloat" => Instr::PushFloat(num("bits") as u64),
                    "MathFloat" => {
                        let fn_ = match w.next() {
                            Some("sin") => MathFn::Sin,
                            Some("cos") => MathFn::Cos,
                            Some("exp") => MathFn::Exp,
                            Some("log") => MathFn::Log,
                            Some("sqrt") => MathFn::Sqrt,
                            other => fail(&format!(
                                "MathFloat: unknown fn {other:?}")),
                        };
                        Instr::MathFloat(fn_)
                    }
                    "Push" => Instr::Push(num("n") as usize),
                    "PushArg" => Instr::PushArg(num("n") as usize),
                    "Update" => Instr::Update(num("n") as usize),
                    "Pop" => Instr::Pop(num("n") as usize),
                    "Alloc" => Instr::Alloc(num("n") as usize),
                    "Slide" => Instr::Slide(num("n") as usize),
                    "Proj" => Instr::Proj(num("n") as usize),
                    "Pack" => {
                        let tag = num("tag") as i64;
                        Instr::Pack(tag, num("arity") as usize)
                    }
                    "PackTuple" => {
                        let tag = num("tag") as i64;
                        Instr::PackTuple(tag, num("arity") as usize)
                    }
                    "EqInt" => {
                        let t = num("true") as i64;
                        Instr::EqInt(t, num("false") as i64)
                    }
                    "LtInt" => {
                        let t = num("true") as i64;
                        Instr::LtInt(t, num("false") as i64)
                    }
                    "PushGlobal" => Instr::PushGlobal(
                        w.next().unwrap_or_else(|| fail("PushGlobal: name"))
                            .to_string()),
                    "CaseJump" => {
                        let pairs = num("n") as usize;
                        let mut table = Vec::with_capacity(pairs);
                        for _ in 0..pairs {
                            let tag = num("tag") as i64;
                            table.push((tag, num("block") as usize));
                        }
                        Instr::CaseJump(table)
                    }
                    other => fail(&format!("unknown instruction {other}")),
                };
                blocks.last_mut()
                    .unwrap_or_else(|| fail("instruction before any block"))
                    .push(instr);
            }
            Some(other) => fail(&format!("unknown line {other}")),
        }
    }
    if entry.is_empty() { fail("no entry"); }
    (blocks, globals, entry)
}

impl Machine {
    /// A machine loaded from the flat text format, its heap holding
    /// one node per global and nothing forced yet.  The heap then
    /// *persists* across `force_entry` calls, which is the point of
    /// being a library: a shared thunk forced once is forced.
    pub fn from_text(text: &str) -> (Machine, String) {
        let (blocks, globals, entry) = parse(text);
        let mut m = Machine {
            heap: Vec::new(),
            globals: HashMap::new(),
            blocks,
            stack: Vec::new(),
            dump: Vec::new(),
            code: Vec::new(),
            pc: 0,
            chans: 0,
        };
        for (name, arity, block) in globals {
            let i = m.alloc(Node::Global(arity, block));
            m.globals.insert(name, i);
        }
        (m, entry)
    }

    /// Force the named zero-argument global to a value and spell it
    /// canonically.  The stack and code are the call's own (leftovers
    /// from an interrupted run are overwritten); the heap is shared.
    /// After a *failed* force, values already computed are intact —
    /// `Update` writes its indirection in one instruction — but the
    /// interrupted redex may be left black-holed, so a later force
    /// through it refuses rather than answers.  A refusal, never
    /// corruption.
    pub fn force_entry(&mut self, entry: &str) -> String {
        let root = *self.globals.get(entry)
            .unwrap_or_else(|| fail(&format!("no entry global '{entry}'")));
        self.stack = vec![root];
        self.dump.clear();
        self.code = vec![Instr::Unwind];
        self.pc = 0;
        self.run();
        let top = *self.stack.last()
            .unwrap_or_else(|| fail("no result"));
        let mut out = String::new();
        self.show(top, &mut out);
        out
    }
}

// ── The forcing protocol — `audiodynamic.ScoreStream`'s twin ────────────
//
// `pull(horizon)` returns every event whose onset lies below `horizon`
// ticks, as far as the fuel allowed, and keeps the reference's two
// facts honest across calls: `frontier`, the tick below which the
// stream is complete, and `stalled`, whether the last pull ran out of
// budget mid-thought.  A parked forcing is resumable — the machine's
// own registers hold the interrupted walk, and the next pull re-enters
// it — so an expensive-but-finite section arrives late rather than
// never.  Patience (the wall clock) stays host-side, where the wall
// clock lives; fuel and burst are the budgets here, exactly the two
// that make sense in-process.
//
// The wire is flat i64s, the rung-one choice: per event
// `[onset, offset, voice_tag, nfields, (kind, value) × nfields]` with
// kind 0 an integer and kind 1 a float as its IEEE bits, and the
// whole pull as `[count, events…]` in a buffer the stream owns until
// the next call.  Nested payload constructors are flattened, which is
// what the allocator does with them anyway (`audioscore._flatten`).

impl Machine {
    /// The run loop under a step budget, resumable: `false` means the
    /// fuel ran out and the registers hold the walk mid-flight —
    /// calling again continues it.  `gmachine.StepLimit`'s twin.
    fn run_fuel(&mut self, fuel: &mut i64) -> bool {
        loop {
            if self.pc >= self.code.len() {
                match self.dump.pop() {
                    None => return true,
                    Some((code, pc, mut below)) => {
                        self.code = code;
                        self.pc = pc;
                        if let Some(&top) = self.stack.last() {
                            below.push(top);
                        }
                        self.stack = below;
                    }
                }
            } else {
                if *fuel <= 0 {
                    return false;
                }
                *fuel -= 1;
                let instr = self.code[self.pc].clone();
                self.pc += 1;
                self.step(instr);
            }
        }
    }

    /// Cheney's semispace copy.  Roots: the globals, the machine's own
    /// registers (a parked forcing lives there), and whatever indices
    /// the caller still holds — passed in so they are *rewritten*, not
    /// merely kept alive.  Code blocks hold no heap references
    /// (`PushGlobal` is by name), so only nodes move.
    pub fn collect(&mut self, extra: &mut [&mut Idx]) -> usize {
        let mut fwd: Vec<usize> = vec![usize::MAX; self.heap.len()];
        let mut to: Vec<Node> = Vec::new();

        fn copy(heap: &[Node], fwd: &mut [usize], to: &mut Vec<Node>,
                i: Idx) -> Idx {
            if fwd[i] != usize::MAX {
                return fwd[i];
            }
            fwd[i] = to.len();
            to.push(heap[i].clone());
            fwd[i]
        }

        for root in extra.iter_mut() {
            **root = copy(&self.heap, &mut fwd, &mut to, **root);
        }
        for slot in self.stack.iter_mut() {
            *slot = copy(&self.heap, &mut fwd, &mut to, *slot);
        }
        for (_, _, below) in self.dump.iter_mut() {
            for slot in below.iter_mut() {
                *slot = copy(&self.heap, &mut fwd, &mut to, *slot);
            }
        }
        let names: Vec<String> = self.globals.keys().cloned().collect();
        for name in names {
            let i = self.globals[&name];
            let j = copy(&self.heap, &mut fwd, &mut to, i);
            self.globals.insert(name, j);
        }
        let mut scan = 0;
        while scan < to.len() {
            let node = to[scan].clone();
            let rewritten = match node {
                Node::Ap(f, a) => Node::Ap(
                    copy(&self.heap, &mut fwd, &mut to, f),
                    copy(&self.heap, &mut fwd, &mut to, a)),
                Node::Ind(Some(t)) => Node::Ind(
                    Some(copy(&self.heap, &mut fwd, &mut to, t))),
                Node::Con(tag, args) => Node::Con(
                    tag,
                    args.iter().map(|&a| copy(&self.heap, &mut fwd,
                                              &mut to, a)).collect()),
                other => other,
            };
            to[scan] = rewritten;
            scan += 1;
        }
        self.heap = to;
        self.heap.len()
    }
}

/// A stream over one machine's heap — hold it beside the `Machine` it
/// was opened on; its indices mean nothing on any other.
pub struct Stream {
    node: Idx,
    /// One event forced but standing beyond the horizon asked about:
    /// `(onset, wire words)`.
    ready: Option<(i64, Vec<i64>)>,
    pub done: bool,
    pub stalled: bool,
    pub frontier: i64,
    /// The node a parked forcing is mid-walk on — `_scratch_for`.
    parked_for: Option<Idx>,
    cons_tag: i64,
    nil_tag: i64,
    tuple3_tag: i64,
    /// `Some((CueEv, CueAsk, CueEnd tags))` for a `liveMain` stream —
    /// the cells carry cues rather than bare triples, the stream can
    /// end in a question, and a subtree reports its own end
    /// (`audiodynamic.LiveStream`, ariadne's self-terminated cues).
    live: Option<(i64, i64, i64)>,
    /// `(tick, port, key)` when a question is owed, else `None` — the
    /// key being the question's stamped position, so a rejoin can be
    /// answered from the thread (`spec/ariadne.md`).
    pub ask: Option<(i64, i64, i64)>,
    /// The question's continuation — it holds the entire rest of the
    /// performance, so answering is applying it and walking on.
    ask_k: Option<Idx>,
    buf: Vec<i64>,
    /// The collector's pacing: live words after the last copy.
    last_live: usize,
}

/// What one cell yielded: an event, a parked budget, or — live
/// streams only — a question that must be answered before anything
/// more can exist.
enum Cell {
    Event((i64, Vec<i64>)),
    Parked,
    Question,
    /// A fact, not an event — a `CueEnd`, harvested into the frontier
    /// and stepped over.
    Skip,
}

/// Collect when the heap outgrows this or twice the last live set,
/// whichever is larger — between pulls, never inside one.
const COLLECT_FLOOR: usize = 1 << 18;

impl Stream {
    /// The root, built the way `stream_root` builds it: the entry
    /// applied to the seed, and to the tick too when resuming.
    pub fn open(m: &mut Machine, entry: &str, seed: i64, tick: i64,
                use_tick: bool, cons_tag: i64, nil_tag: i64,
                tuple3_tag: i64) -> Stream {
        let g = *m.globals.get(entry)
            .unwrap_or_else(|| fail(&format!("no entry global '{entry}'")));
        let s = m.alloc(Node::Num(Num::I(seed as i128)));
        let mut root = m.alloc(Node::Ap(g, s));
        if use_tick {
            let t = m.alloc(Node::Num(Num::I(tick as i128)));
            root = m.alloc(Node::Ap(root, t));
        }
        Stream {
            node: root,
            ready: None,
            done: false,
            stalled: false,
            frontier: 0,
            parked_for: None,
            cons_tag,
            nil_tag,
            tuple3_tag,
            live: None,
            ask: None,
            ask_k: None,
            buf: Vec::new(),
            last_live: 0,
        }
    }

    /// The listening reading — `liveMain seed tick`, whose cells are
    /// cues.  The tick always applies: `liveMain` is resume-aware by
    /// its own second argument.
    pub fn open_live(m: &mut Machine, entry: &str, seed: i64, tick: i64,
                     cons_tag: i64, nil_tag: i64, ev_tag: i64,
                     ask_tag: i64, end_tag: i64) -> Stream {
        let mut s = Stream::open(m, entry, seed, tick, true,
                                 cons_tag, nil_tag, 0);
        s.live = Some((ev_tag, ask_tag, end_tag));
        s
    }

    /// `LiveStream.answer`: the port's reading in, the performance
    /// continuing into what the continuation returns.
    pub fn answer(&mut self, m: &mut Machine, reading: &[i64]) {
        let Some(k) = self.ask_k else {
            fail("no question is owed");
        };
        let mut lst = m.alloc(Node::Con(self.nil_tag, vec![]));
        for &v in reading.iter().rev() {
            let n = m.alloc(Node::Num(Num::I(v as i128)));
            lst = m.alloc(Node::Con(self.cons_tag, vec![n, lst]));
        }
        self.node = m.alloc(Node::Ap(k, lst));
        self.ask = None;
        self.ask_k = None;
    }

    /// WHNF of `node` within the budget, or `None` — parked in the
    /// machine's registers, resumable.  `ScoreStream._whnf`.
    fn whnf(&mut self, m: &mut Machine, node: Idx, fuel: &mut i64)
            -> Option<Idx> {
        if self.parked_for != Some(node) {
            m.stack = vec![node];
            m.dump.clear();
            m.code = vec![Instr::Unwind];
            m.pc = 0;
            self.parked_for = Some(node);
        }
        if !m.run_fuel(fuel) {
            return None;
        }
        self.parked_for = None;
        let top = *m.stack.last().unwrap_or(&node);
        Some(m.deref(top))
    }

    /// One payload's fields as `(kind, value)` words, the structure
    /// kept — `ScoreStream._flat`'s exact shape on a wire: kind 0 an
    /// integer, kind 1 a float as its bits, kind 2 a constructor
    /// whose value is its child count, the children following in
    /// order.  A nested payload decodes back to the nested tuple the
    /// reference yields, because `history` is an interface and the
    /// editor indexes into it.  `false`: parked, owed.
    fn flat(&mut self, m: &mut Machine, args: &[Idx], out: &mut Vec<i64>,
            fuel: &mut i64) -> bool {
        for &a in args {
            let Some(n) = self.whnf(m, a, fuel) else {
                return false;
            };
            match m.heap[n].clone() {
                Node::Num(Num::I(v)) => {
                    out.push(0);
                    out.push(i64::try_from(v).unwrap_or_else(
                        |_| fail("a payload value wider than 64 bits")));
                }
                Node::Num(Num::F(x)) => {
                    out.push(1);
                    out.push(x.to_bits() as i64);
                }
                Node::Con(_, inner) => {
                    out.push(2);
                    out.push(inner.len() as i64);
                    if !self.flat(m, &inner, out, fuel) {
                        return false;
                    }
                }
                _ => fail("a payload field that is not a value"),
            }
        }
        true
    }

    /// One cell — `ScoreStream._event`, and `LiveStream._event` when
    /// the stream is live.  Re-entered from the top after a park; what
    /// was forced is WHNF in the shared heap, so only the unfinished
    /// field costs again.
    fn event(&mut self, m: &mut Machine, cell: Idx, fuel: &mut i64)
             -> Cell {
        let Some(head) = self.whnf(m, cell, fuel) else {
            return Cell::Parked;
        };
        let args = match (self.live, m.heap[head].clone()) {
            (Some((_, _, endt)), Node::Con(t, args)) if t == endt => {
                let Some(en) = self.whnf(m, args[0], fuel) else {
                    return Cell::Parked;
                };
                match m.heap[en] {
                    Node::Num(Num::I(e)) => {
                        self.frontier = self.frontier.max(
                            i64::try_from(e).unwrap_or_else(
                                |_| fail("an end wider than 64 bits")));
                    }
                    _ => fail("an end with no instant"),
                }
                return Cell::Skip;
            }
            (Some((_, askt, _)), Node::Con(t, args)) if t == askt => {
                // A question: its instant and port forced (either may
                // park the budget mid-question), then the pull parks
                // on it — nothing beyond a question can exist yet.
                let Some(tn) = self.whnf(m, args[0], fuel) else {
                    return Cell::Parked;
                };
                let Some(pn) = self.whnf(m, args[1], fuel) else {
                    return Cell::Parked;
                };
                let Some(kn) = self.whnf(m, args[2], fuel) else {
                    return Cell::Parked;
                };
                // The port is a **channel**: its own id is the
                // identity the host keys a reading by.
                let (tick, port, key) = match (&m.heap[tn], &m.heap[pn],
                                               &m.heap[kn]) {
                    (Node::Num(Num::I(t)), Node::Chan(p),
                     Node::Num(Num::I(k))) => (
                        i64::try_from(*t).unwrap_or_else(
                            |_| fail("a tick wider than 64 bits")),
                        *p,
                        i64::try_from(*k).unwrap_or_else(
                            |_| fail("a key wider than 64 bits"))),
                    _ => fail("a question with no instant or channel"),
                };
                self.ask = Some((tick, port, key));
                self.ask_k = Some(args[3]);
                self.frontier = self.frontier.max(tick);
                return Cell::Question;
            }
            (Some((ev, _, _)), Node::Con(t, args)) if t == ev => args,
            (Some(_), _) => fail("expected a cue in the live stream"),
            (None, Node::Con(t, args)) if t == self.tuple3_tag
                && args.len() == 3 => args,
            (None, _) => fail("expected an (onset, offset, voice) triple"),
        };
        let mut ticks = [0i64; 2];
        for (k, slot) in ticks.iter_mut().enumerate() {
            let Some(n) = self.whnf(m, args[k], fuel) else {
                return Cell::Parked;
            };
            match m.heap[n] {
                Node::Num(Num::I(v)) => {
                    *slot = i64::try_from(v).unwrap_or_else(
                        |_| fail("a tick wider than 64 bits"));
                }
                _ => fail("expected a number in a stream event"),
            }
        }
        let Some(voice) = self.whnf(m, args[2], fuel) else {
            return Cell::Parked;
        };
        let (vtag, vargs) = match m.heap[voice].clone() {
            Node::Con(t, a) => (t, a),
            _ => fail("expected a `Voice` value"),
        };
        let mut ev = vec![ticks[0], ticks[1], vtag, 0];
        let mut fields = Vec::new();
        if !self.flat(m, &vargs, &mut fields, fuel) {
            return Cell::Parked;
        }
        ev[3] = fields.len() as i64;    // *words*, the payload nesting
                                        // being variable-width
        ev.extend(fields);
        Cell::Event((ticks[0], ev))
    }

    /// Every event with onset below `horizon` ticks, budget
    /// permitting — `ScoreStream.pull`, wire-shaped.  Collects
    /// between pulls when the heap has outgrown its pace.
    pub fn pull(&mut self, m: &mut Machine, horizon: i64, mut fuel: i64,
                burst: usize) -> &[i64] {
        if self.ask.is_some() {
            // A question is owed first — `LiveStream.pull`'s refusal.
            self.buf.clear();
            self.buf.push(0);
            return &self.buf;
        }
        if m.heap.len() > COLLECT_FLOOR.max(2 * self.last_live) {
            let mut roots: Vec<&mut Idx> = vec![&mut self.node];
            if let Some(p) = self.parked_for.as_mut() {
                roots.push(p);
            }
            if let Some(k) = self.ask_k.as_mut() {
                roots.push(k);
            }
            self.last_live = m.collect(&mut roots);
        }
        self.buf.clear();
        self.buf.push(0);
        let mut count = 0i64;
        let mut last_onset: Option<i64> = None;
        self.stalled = false;
        while !self.done {
            if count as usize >= burst {
                self.stalled = true;    // outran a budget, not the horizon
                break;
            }
            if let Some((onset, _)) = &self.ready {
                if *onset >= horizon {
                    break;
                }
                let (onset, ev) = self.ready.take().unwrap();
                self.buf.extend_from_slice(&ev);
                last_onset = Some(onset);
                count += 1;
                continue;
            }
            let Some(n) = self.whnf(m, self.node, &mut fuel) else {
                self.stalled = true;
                break;
            };
            let (tag, args) = match m.heap[n].clone() {
                Node::Con(t, a) => (t, a),
                _ => fail("expected a list cell in the score stream"),
            };
            if tag != self.cons_tag && tag != self.nil_tag {
                fail("expected a list cell in the score stream");
            }
            self.node = n;              // WHNF remembered: re-asking is free
            if tag == self.nil_tag {
                self.done = true;
                break;
            }
            match self.event(m, args[0], &mut fuel) {
                Cell::Parked | Cell::Question => {
                    self.stalled = true;
                    break;
                }
                Cell::Skip => {
                    self.node = args[1];
                }
                Cell::Event((onset, ev)) => {
                    self.node = args[1];
                    self.ready = Some((onset, ev));
                }
            }
        }
        if self.done {
            // nothing more is coming; `frontier` stops mattering
        } else if self.stalled {
            if let Some(o) = last_onset {
                self.frontier = self.frontier.max(o);
            }
        } else {
            self.frontier = self.frontier.max(horizon);
        }
        if self.ask.is_some() {
            self.stalled = false;       // a question is not a stall
        }
        self.buf[0] = count;
        &self.buf
    }
}

// ── The C surface — what a ctypes host calls ────────────────────────────

pub mod ffi {
    //! Five functions, strings both ways, panics never crossing.
    //!
    //! The contract: a null return means failure and `crust_error()`
    //! holds the message (thread-local, valid until the next failure
    //! on that thread).  Strings returned by `crust_force` are owned
    //! by the caller and returned through `crust_free_str`; machines
    //! through `crust_free`.

    use std::cell::RefCell;
    use std::ffi::{c_char, CStr, CString};
    use std::panic::{catch_unwind, AssertUnwindSafe};
    use std::sync::Once;

    use super::Machine;

    thread_local! {
        static LAST: RefCell<CString> =
            RefCell::new(CString::new("").unwrap());
    }

    static QUIET: Once = Once::new();

    /// The default panic hook prints "thread panicked at …" to
    /// stderr; a host that gets its error through `crust_error` does
    /// not want the noise twice.  Installed on first use of this
    /// surface, so the CLI (which never enters here) keeps its own
    /// reporting.
    fn hush() {
        QUIET.call_once(|| std::panic::set_hook(Box::new(|_| {})));
    }

    fn park(payload: Box<dyn std::any::Any + Send>) {
        let msg = payload.downcast::<String>().map(|s| *s)
            .unwrap_or_else(|_| "crust: unknown failure".to_string());
        let c = CString::new(msg.replace('\0', "?"))
            .unwrap_or_else(|_| CString::new("crust: failure").unwrap());
        LAST.with(|l| *l.borrow_mut() = c);
    }

    /// # Safety
    /// `text` must be a NUL-terminated UTF-8 program in the flat
    /// format.  Returns a machine to be freed with `crust_free`, or
    /// null with the message in `crust_error`.
    #[no_mangle]
    pub unsafe extern "C" fn crust_load(text: *const c_char)
                                        -> *mut Machine {
        hush();
        if text.is_null() {
            park(Box::new("crust: load of a null program".to_string()));
            return std::ptr::null_mut();
        }
        let text = CStr::from_ptr(text).to_string_lossy().into_owned();
        match catch_unwind(move || Machine::from_text(&text).0) {
            Ok(m) => Box::into_raw(Box::new(m)),
            Err(e) => {
                park(e);
                std::ptr::null_mut()
            }
        }
    }

    /// # Safety
    /// `m` from `crust_load`, `entry` NUL-terminated.  Returns the
    /// canonical spelling as a string to be freed with
    /// `crust_free_str`, or null with the message in `crust_error`.
    #[no_mangle]
    pub unsafe extern "C" fn crust_force(m: *mut Machine,
                                         entry: *const c_char)
                                         -> *mut c_char {
        hush();
        if m.is_null() || entry.is_null() {
            park(Box::new("crust: force on a null machine".to_string()));
            return std::ptr::null_mut();
        }
        let entry = CStr::from_ptr(entry).to_string_lossy().into_owned();
        let machine = &mut *m;
        match catch_unwind(AssertUnwindSafe(
            || machine.force_entry(&entry))) {
            Ok(out) => CString::new(out.replace('\0', "?"))
                .map(CString::into_raw)
                .unwrap_or(std::ptr::null_mut()),
            Err(e) => {
                park(e);
                std::ptr::null_mut()
            }
        }
    }

    /// The last failure's message on this thread.  Borrowed; valid
    /// until the next failing call from the same thread.
    #[no_mangle]
    pub extern "C" fn crust_error() -> *const c_char {
        LAST.with(|l| l.borrow().as_ptr())
    }

    /// # Safety
    /// `s` must have come from `crust_force`, once.
    #[no_mangle]
    pub unsafe extern "C" fn crust_free_str(s: *mut c_char) {
        if !s.is_null() {
            drop(CString::from_raw(s));
        }
    }

    /// # Safety
    /// `m` must have come from `crust_load`, once.
    #[no_mangle]
    pub unsafe extern "C" fn crust_free(m: *mut Machine) {
        if !m.is_null() {
            drop(Box::from_raw(m));
        }
    }

    use super::Stream;

    /// # Safety
    /// `m` from `crust_load`, `entry` NUL-terminated.  The stream's
    /// indices live in this machine's heap: pass the same `m` to every
    /// later call.  Free with `crust_stream_free`.
    #[no_mangle]
    pub unsafe extern "C" fn crust_stream_open(m: *mut Machine,
                                               entry: *const c_char,
                                               seed: i64, tick: i64,
                                               use_tick: i64,
                                               cons_tag: i64,
                                               nil_tag: i64,
                                               tuple3_tag: i64)
                                               -> *mut Stream {
        hush();
        if m.is_null() || entry.is_null() {
            park(Box::new("crust: stream on a null machine".to_string()));
            return std::ptr::null_mut();
        }
        let entry = CStr::from_ptr(entry).to_string_lossy().into_owned();
        let machine = &mut *m;
        match catch_unwind(AssertUnwindSafe(|| Stream::open(
            machine, &entry, seed, tick, use_tick != 0,
            cons_tag, nil_tag, tuple3_tag))) {
            Ok(s) => Box::into_raw(Box::new(s)),
            Err(e) => {
                park(e);
                std::ptr::null_mut()
            }
        }
    }

    /// # Safety
    /// `s` and `m` as opened together.  Returns the wire buffer —
    /// `[count, events…]`, owned by the stream, valid until the next
    /// pull — or null with the message in `crust_error`.
    #[no_mangle]
    pub unsafe extern "C" fn crust_stream_pull(s: *mut Stream,
                                               m: *mut Machine,
                                               horizon: i64, fuel: i64,
                                               burst: i64)
                                               -> *const i64 {
        hush();
        if s.is_null() || m.is_null() {
            park(Box::new("crust: pull on a null stream".to_string()));
            return std::ptr::null();
        }
        let stream = &mut *s;
        let machine = &mut *m;
        match catch_unwind(AssertUnwindSafe(
            || stream.pull(machine, horizon, fuel,
                           burst.max(0) as usize).as_ptr())) {
            Ok(p) => p,
            Err(e) => {
                park(e);
                std::ptr::null()
            }
        }
    }

    /// # Safety
    /// `out` must hold four i64s: done, stalled, frontier, heap words.
    #[no_mangle]
    pub unsafe extern "C" fn crust_stream_stat(s: *const Stream,
                                               m: *const Machine,
                                               out: *mut i64) {
        if s.is_null() || m.is_null() || out.is_null() {
            return;
        }
        let stream = &*s;
        *out.add(0) = stream.done as i64;
        *out.add(1) = stream.stalled as i64;
        *out.add(2) = stream.frontier;
        *out.add(3) = (*m).heap.len() as i64;
    }

    /// # Safety
    /// `s` must have come from `crust_stream_open`, once.
    #[no_mangle]
    pub unsafe extern "C" fn crust_stream_free(s: *mut Stream) {
        if !s.is_null() {
            drop(Box::from_raw(s));
        }
    }

    /// # Safety
    /// As `crust_stream_open`; the cells are `liveMain`'s cues, and
    /// the tick always applies (resume-aware by its own argument).
    #[no_mangle]
    pub unsafe extern "C" fn crust_stream_open_live(m: *mut Machine,
                                                    entry: *const c_char,
                                                    seed: i64, tick: i64,
                                                    cons_tag: i64,
                                                    nil_tag: i64,
                                                    ev_tag: i64,
                                                    ask_tag: i64,
                                                    end_tag: i64)
                                                    -> *mut Stream {
        hush();
        if m.is_null() || entry.is_null() {
            park(Box::new("crust: stream on a null machine".to_string()));
            return std::ptr::null_mut();
        }
        let entry = CStr::from_ptr(entry).to_string_lossy().into_owned();
        let machine = &mut *m;
        match catch_unwind(AssertUnwindSafe(|| Stream::open_live(
            machine, &entry, seed, tick, cons_tag, nil_tag,
            ev_tag, ask_tag, end_tag))) {
            Ok(s) => Box::into_raw(Box::new(s)),
            Err(e) => {
                park(e);
                std::ptr::null_mut()
            }
        }
    }

    /// # Safety
    /// `out` must hold three i64s.  Returns 1 with `[tick, port, key]`
    /// written when a question is owed, else 0.
    #[no_mangle]
    pub unsafe extern "C" fn crust_stream_ask(s: *const Stream,
                                              out: *mut i64) -> i64 {
        if s.is_null() || out.is_null() {
            return 0;
        }
        match (*s).ask {
            Some((tick, port, key)) => {
                *out.add(0) = tick;
                *out.add(1) = port;
                *out.add(2) = key;
                1
            }
            None => 0,
        }
    }

    /// # Safety
    /// `values` must hold `n` i64s (n may be 0 with a null pointer).
    /// Returns 0, or -1 with the message in `crust_error`.
    #[no_mangle]
    pub unsafe extern "C" fn crust_stream_answer(s: *mut Stream,
                                                 m: *mut Machine,
                                                 values: *const i64,
                                                 n: i64) -> i64 {
        hush();
        if s.is_null() || m.is_null() {
            park(Box::new("crust: answer on a null stream".to_string()));
            return -1;
        }
        let reading: Vec<i64> = if values.is_null() || n <= 0 {
            Vec::new()
        } else {
            std::slice::from_raw_parts(values, n as usize).to_vec()
        };
        let stream = &mut *s;
        let machine = &mut *m;
        match catch_unwind(AssertUnwindSafe(
            || stream.answer(machine, &reading))) {
            Ok(()) => 0,
            Err(e) => {
                park(e);
                -1
            }
        }
    }
}
