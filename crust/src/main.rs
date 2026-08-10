//! The CLI over the library: read a program, force its entry, print
//! the canonical value.  A refusal is the library's panic caught
//! here — message to stderr, exit 1, exactly the behaviour this
//! binary always had.

use std::panic::{catch_unwind, AssertUnwindSafe};

use crust::Machine;

fn main() {
    std::panic::set_hook(Box::new(|_| {}));
    let out = catch_unwind(AssertUnwindSafe(|| {
        let path = std::env::args().nth(1)
            .unwrap_or_else(|| std::panic::panic_any(
                "crust: usage: crust <program>".to_string()));
        let text = std::fs::read_to_string(&path)
            .unwrap_or_else(|e| std::panic::panic_any(
                format!("crust: {path}: {e}")));
        let (mut m, entry) = Machine::from_text(&text);
        m.force_entry(&entry)
    }));
    match out {
        Ok(value) => println!("{value}"),
        Err(payload) => {
            let msg = payload.downcast::<String>().map(|s| *s)
                .unwrap_or_else(|_| "crust: unknown failure".to_string());
            eprintln!("{msg}");
            std::process::exit(1);
        }
    }
}
