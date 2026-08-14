//! Time a walked canvas, headless: what one frame of `Walker::frame`
//! costs, first and late — a number `GESTATE_EDITOR_TIME`'s paint
//! bucket can only show summed with the painting.
//!
//!     cargo run --release --example walktime -- fixture.walk [frames]
use gestate_editor::walk::{Walk, Walker};

fn main() {
    let path = std::env::args().nth(1).expect("a .walk file");
    let n: usize = std::env::args().nth(2)
        .and_then(|s| s.parse().ok()).unwrap_or(600);
    let text = std::fs::read_to_string(&path).expect("readable");
    let walk = Walk::read(&text).expect("a payload");
    let mut w = Walker::open(&walk).expect("loads");
    let mut items = 0;
    let mut hits = 0;
    // In tenths, so a cost that grows with the heap shows as a slope.
    for tenth in 0..10 {
        let t0 = std::time::Instant::now();
        for _ in 0..n / 10 {
            let d = w.frame(500, 400);
            items = d.items.len();
            hits = d.hits.len();
        }
        let ms = t0.elapsed().as_secs_f64() * 1000.0 / (n / 10) as f64;
        println!("tenth {tenth}: {ms:.3} ms/frame");
    }
    println!("{items} items, {hits} hits");
    // And the painter's half, at the editor window's own size.
    let mut c = gestate_panel::paint::Canvas::opaque(
        1128, 760, gestate_panel::list::Colour::rgb(0x14, 0x16, 0x1a));
    let t0 = std::time::Instant::now();
    let m = 200;
    for _ in 0..m {
        c.clear(gestate_panel::list::Colour::rgb(0x14, 0x16, 0x1a));
        gestate_panel::paint::paint(&mut c, w.frame(500, 400));
    }
    let ms = t0.elapsed().as_secs_f64() * 1000.0 / m as f64;
    println!("clear+walk+paint: {ms:.3} ms/frame");
    if let Some(f) = w.fault() {
        println!("fault: {f}");
    }
}
