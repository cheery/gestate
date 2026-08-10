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
//! is exactly the kind of quiet corner parity tests exist for.

use std::collections::HashMap;
use std::fmt::Write as _;

type Idx = usize;

#[derive(Clone, Debug)]
enum Node {
    Num(i128),
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
    MatchFail,
}

struct Machine {
    heap: Vec<Node>,
    globals: HashMap<String, Idx>,
    blocks: Vec<Vec<Instr>>,
    stack: Vec<Idx>,             // top is the END, where Python's is [0]
    dump: Vec<(Vec<Instr>, usize, Vec<Idx>)>,
    code: Vec<Instr>,
    pc: usize,
}

fn fail(msg: &str) -> ! {
    eprintln!("crust: {msg}");
    std::process::exit(1);
}

// Python's floor division and modulo, exactly.
fn fdiv(a: i128, b: i128) -> i128 {
    let q = a / b;
    if (a % b != 0) && ((a % b < 0) != (b < 0)) { q - 1 } else { q }
}

fn fmod(a: i128, b: i128) -> i128 {
    a - fdiv(a, b) * b
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

    fn two_nums(&self, name: &str) -> (i128, i128) {
        // The first argument on top, the second below — `_prim_operands`.
        let n = self.stack.len();
        if n < 2 { fail(&format!("{name}: missing operands")); }
        let a = self.deref(self.stack[n - 1]);
        let b = self.deref(self.stack[n - 2]);
        match (&self.heap[a], &self.heap[b]) {
            (Node::Num(x), Node::Num(y)) => (*x, *y),
            _ => fail(&format!("{name}: operands must be integers")),
        }
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
                        Node::Num(_) | Node::Con(..) => {
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
                let i = self.alloc(Node::Num(n));
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
            Instr::EqInt(t, f) => {
                let (a, b) = self.two_nums("EqInt");
                self.prim_result(Node::Con(if a == b { t } else { f },
                                           vec![]));
            }
            Instr::LtInt(t, f) => {
                let (a, b) = self.two_nums("LtInt");
                self.prim_result(Node::Con(if a < b { t } else { f },
                                           vec![]));
            }
            Instr::AddInt => {
                let (a, b) = self.two_nums("AddInt");
                let v = a.checked_add(b).unwrap_or_else(
                    || fail("an integer wider than 128 bits"));
                self.prim_result(Node::Num(v));
            }
            Instr::SubInt => {
                let (a, b) = self.two_nums("SubInt");
                let v = a.checked_sub(b).unwrap_or_else(
                    || fail("an integer wider than 128 bits"));
                self.prim_result(Node::Num(v));
            }
            Instr::MulInt => {
                let (a, b) = self.two_nums("MulInt");
                let v = a.checked_mul(b).unwrap_or_else(
                    || fail("an integer wider than 128 bits"));
                self.prim_result(Node::Num(v));
            }
            Instr::DivInt => {
                let (a, b) = self.two_nums("DivInt");
                if b == 0 { fail("DivInt: division by zero"); }
                self.prim_result(Node::Num(fdiv(a, b)));
            }
            Instr::ModInt => {
                let (a, b) = self.two_nums("ModInt");
                if b == 0 { fail("ModInt: division by zero"); }
                self.prim_result(Node::Num(fmod(a, b)));
            }
            Instr::XorInt => {
                // The fold's meaning, not two's-complement: negatives are
                // refused, as the reference refuses them.
                let (a, b) = self.two_nums("XorInt");
                if a < 0 || b < 0 { fail("XorInt on a negative number"); }
                self.prim_result(Node::Num(a ^ b));
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

    /// The canonical spelling both machines print: `42`, `#tag(a b)`.
    fn show(&mut self, i: Idx, out: &mut String) {
        let i = self.force(i);
        match self.heap[i].clone() {
            Node::Num(n) => { write!(out, "{n}").unwrap(); }
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
                    "AddInt" => Instr::AddInt,
                    "SubInt" => Instr::SubInt,
                    "MulInt" => Instr::MulInt,
                    "DivInt" => Instr::DivInt,
                    "ModInt" => Instr::ModInt,
                    "XorInt" => Instr::XorInt,
                    "PushInt" => Instr::PushInt(num("n")),
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

fn main() {
    let path = std::env::args().nth(1)
        .unwrap_or_else(|| fail("usage: crust <program>"));
    let text = std::fs::read_to_string(&path)
        .unwrap_or_else(|e| fail(&format!("{path}: {e}")));
    let (blocks, globals, entry) = parse(&text);

    let mut m = Machine {
        heap: Vec::new(),
        globals: HashMap::new(),
        blocks,
        stack: Vec::new(),
        dump: Vec::new(),
        code: Vec::new(),
        pc: 0,
    };
    for (name, arity, block) in globals {
        let i = m.alloc(Node::Global(arity, block));
        m.globals.insert(name, i);
    }
    let root = *m.globals.get(&entry)
        .unwrap_or_else(|| fail(&format!("no entry global '{entry}'")));
    m.stack.push(root);
    m.code = vec![Instr::Unwind];
    m.run();
    let top = *m.stack.last().unwrap_or_else(|| fail("no result"));
    let mut out = String::new();
    m.show(top, &mut out);
    println!("{out}");
}
