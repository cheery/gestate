/* host.c — the audio callback, with no interpreter in it.
 *
 * `spec/liveaudio.md` stage 4's rule is that the *language* never enters
 * the audio callback, and it was kept: per block Python did about 16 us of
 * control work against a 5,333 us budget, and no arithmetic at all.  What
 * it could not escape is that a Python frame can be *stopped* — the GIL for
 * a slice, the cyclic collector for a hundred milliseconds — and a thread
 * that is stopped misses its deadline however little it had to do.
 *
 * So the four things that were left are moved here:
 *
 *   the swap      which engine is sounding, and when the change lands
 *   the fade      the crossfade across an edit
 *   the knobs     the control block the generated code reads
 *   the clock     counting frames, and feeding the player
 *
 * None of it is DSP.  The DSP is the generated code this calls into, one
 * function per compiled graph, exactly as before.
 *
 * **Python's job is now to *prepare and publish*.**  It compiles a graph,
 * migrates the running state into it, and hands over a `slot` — two
 * function pointers and a state pointer.  Publishing is a single store
 * that the render thread reads between blocks, so a swap can never land
 * inside a buffer.  Nothing here allocates, takes a lock, or calls back
 * into Python.
 */

#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

/* **The device, when there is one to open.**  Built with `-DGESTATE_ALSA
 * -lasound` where `alsa/asoundlib.h` is installed, and without it where it
 * is not — `audiohost.library` probes and decides, the way every other
 * backend in this project gates itself.  Without it the pipe entry point
 * below is what is left, which is the same arrangement `audiolive` has:
 * a device if there is one, a player process if there is not. */
#ifdef GESTATE_ALSA
#include <alsa/asoundlib.h>
#endif

/* The two entry points every compiled graph exposes — `audiollvm` emits
 * both, and their signatures are fixed by it. */
typedef void (*render_fn)(void *state, float *out, int64_t n, void *control);
typedef void (*mix_fn)(void *state, float *out, int64_t n, void *control,
                       double g0, double g1);

/* How many bands the analyser reports.  Eight is what fits across a
 * window as bars wide enough to see, and octave-ish spacing is what an ear
 * hears — the corners below are 110 Hz doubling to 11 kHz. */
#define GESTATE_BANDS 8

typedef struct {
    render_fn render;
    mix_fn mix;
    void *state;
} slot;

typedef struct {
    slot current;
    slot leaving;          /* the engine being faded out, or a null render */
    slot staged;           /* published by Python, taken between blocks */

    /* `staged` is valid when this is 1.  One writer (Python) and one
     * reader (the render thread), and the reader clears it — so a second
     * publish before the first is taken simply replaces it, which is what
     * a person typing means by it. */
    volatile int has_staged;

    int64_t fading;        /* frames of crossfade left, 0 when none */
    int64_t fade_len;

    int channels;
    void *control;         /* the knob block; Python writes, the graph reads */
    int64_t frames;        /* frames rendered since the start */
    volatile int stop;
    /* **Leave now, and never mind the fade.**
     *
     * `stop` is the polite one: it asks for a fade-out and the loops
     * wait for silence to *arrive*, which is what keeps a quit from
     * popping.  That waiting has a premise — that the device is
     * consuming frames — and when another program holds the card the
     * premise is false: `snd_pcm_writei` blocks, the fade never
     * advances, and the loop never reaches its exit.  The thread then
     * outlives the interpreter and segfaults reading a workspace Python
     * has freed, which is the crash `Workbench.stop` warns about.
     *
     * So there are two stops. This is the one that does not negotiate,
     * and a click on the way out is the correct trade against a core
     * file. */
    volatile int halt;

    /* The transport, which was a Python object between the driver and the
     * engine.  Play, stop, seek and loop are a comparison and a store
     * each — cheap here, and the reason they were up there was that a
     * block boundary is the only place they are cheap *anywhere*. */
    volatile int playing;
    int64_t position;      /* where the engine has reached, in frames */
    int64_t loop_start;
    int64_t loop_end;      /* 0 or less: no loop */
    volatile int64_t seek_to;   /* below zero: nothing pending */

    /* **How many times the card ran dry**, and how long the worst wait
     * to fill it was, in microseconds.
     *
     * An underrun is recoverable and recovering silently is what a
     * player does — but *counting* it is what a diagnostic does, and
     * without the count a stutter is an argument about whether anybody
     * heard one.  A rebuild is the suspect and the machine is the
     * witness: the numbers say whether a crackle happened, how often,
     * and whether the block that came late was late by a millisecond
     * or by fifty.
     *
     * Read from another thread and never reset by the loop, so they
     * are `volatile` and monotonic; the caller subtracts. */
    volatile int64_t dry;
    volatile int64_t worst_us;

    /* A meter, for a canvas that draws one.  Sampled rather than scanned:
     * sixteen points of a block is enough to see a needle move. */
    volatile int watch_peak;
    volatile float peak;
    /* Sum of squares and how many, for an RMS.  Peak's sibling and taken
     * on the same walk: what a meter shows and what a *level* is are
     * different questions — a peak says whether it clipped, an RMS says
     * how loud it sounded. */
    volatile double square_sum;
    volatile int64_t square_n;

    /* **The master fader**, and it is what stands between a keypress and a
     * pop.  Going to silence in one sample is a step in the waveform, and
     * a step is a click however quiet what came before it was — so
     * stopping, starting and quitting all move this instead of switching.
     *
     * `gain` is where it is, `mute_len` how many samples it takes to
     * cross.  A fade-out has to *finish* before the loop may leave, which
     * is why `run_device` drains rather than breaking on `stop`. */
    double gain;
    int64_t mute_len;

    /* **A spectrum, for a canvas that draws one.**  Eight bands from
     * seven one-pole lowpasses: band `k` is what `lp[k]` passes and
     * `lp[k-1]` did not, and the top band is what none of them did.  A
     * crude filter bank and the right one here — the output is eight
     * numbers a person looks at sixty times a second, not an analysis.
     *
     * Off unless a program asks, like the meter: this is the one place
     * with no time to spare, and a reading nobody looks at is a cost
     * nobody agreed to. */
    volatile int watch_bands;
    double band_lp[GESTATE_BANDS - 1];
    double band_k[GESTATE_BANDS - 1];
    volatile float band_env[GESTATE_BANDS];
    double band_release;

    /* `snd_pcm_t *` when a device is open.  `void *` so that the struct is
     * the same size and shape whether or not ALSA was compiled in — the
     * Python side lays out no part of this, but a struct that changed with
     * a build flag is a trap waiting for the day something does. */
    void *pcm;

    /* **The tap: what the device was actually given.**
     * `board/done/unheard-output.md`, and the whole of its argument is that
     * nothing in this tree could read this.  Every audio oracle here
     * reads an *offline render* or a *counter*, and an offline render
     * renders a knob at its resting value — so a defect in the first
     * blocks, in a control channel, or in a handover is invisible to all
     * of them, and the only instrument left is a person listening.
     *
     * **Null unless armed**, which is a comparison beside a syscall.
     * The budget this file guards is `gestate_host_fill`'s — *"no
     * arithmetic at all"* in the **per-sample** loop — and this is not
     * there: it is one branch per *block*, next to `snd_pcm_writei`.
     *
     * Bounded and pre-allocated, so the loop never allocates and the
     * instrument can never grow into a memory leak wearing a
     * diagnostic's name.  It fills once and stops: the first N frames
     * are what a *test* can assert on, and a ring that kept the last N
     * would answer a different question ("the pop I just heard") that
     * cannot be asserted on reproducibly. */
    float *tap;
    int64_t tap_cap;         /* frames it can hold */
    volatile int64_t tap_n;  /* frames it holds */
} host;

/* Keep what the writer just handed over — `frames` of it, interleaved.
 *
 * **Called with what the sink accepted, never with what was filled.**
 * `snd_pcm_writei` answers with how many frames the card *took*, and
 * capturing the offered count instead would be a different claim wearing
 * this one's name: *what we meant to send* rather than *what the device
 * received*.  The second is the only one worth an instrument.
 */
static void tapped(host *h, const float *from, int64_t frames) {
    if (!h->tap || frames <= 0) return;
    int64_t room = h->tap_cap - h->tap_n;
    if (room <= 0) return;
    if (frames > room) frames = room;
    memcpy(h->tap + h->tap_n * h->channels, from,
           (size_t)frames * (size_t)h->channels * sizeof *h->tap);
    h->tap_n += frames;
}

/* **`t` is the first field of `%State`.**  `audiollvm._render_block` reads
 * it with `getelementptr %State, ptr %s, i32 0, i32 0`, so the instant a
 * graph is at lives at offset zero of its state and a seek is one store.
 * The two are a pair: change the struct's first field and change this. */
/* **How long a fill took, and the worst so far.**  The render has a
 * block to finish in — 5.3 ms at 48 kHz — and a rebuild that starves
 * it shows up here before the card runs dry, which is what makes this
 * the earlier of the two warnings. */
static int64_t now_us(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (int64_t)t.tv_sec * 1000000 + t.tv_nsec / 1000;
}

static void filled_in(host *h, int64_t began) {
    int64_t took = now_us() - began;
    if (took > h->worst_us) h->worst_us = took;
}

static void seek_state(void *state, int64_t to) {
    if (state) *(int64_t *)state = to;
}

host *gestate_host_new(int channels, int64_t fade_len, void *control) {
    host *h = calloc(1, sizeof *h);
    if (!h) return 0;
    h->channels = channels < 1 ? 1 : channels;
    h->fade_len = fade_len < 1 ? 1 : fade_len;
    h->control = control;
    h->playing = 1;
    h->seek_to = -1;
    /* Silent, and fading up: the first block of a session is the same
     * step as any other and pops the same way. */
    h->gain = 0.0;
    h->halt = 0;
    h->mute_len = fade_len / 4 > 1 ? fade_len / 4 : 1;
    /* **Armed from the environment, at the one moment nothing is
     * playing** — `board/done/unheard-output.md`.  A variable rather than a
     * rebuild, because the defect this exists for is the kind somebody
     * meets once and cannot reproduce on demand: an instrument you have
     * to recompile for is an instrument that is not there when you need
     * it.  `GESTATE_EDITOR_TIME` is the spelling precedent.
     *
     * The value is how many *frames* to keep.  Zero, absent or
     * unparseable means no tap at all, and then the loops below never
     * touch it. */
    const char *want = getenv("GESTATE_HOST_TAP");
    if (want && *want) {
        long long frames = atoll(want);
        if (frames > 0) {
            h->tap = calloc((size_t)frames * (size_t)h->channels,
                            sizeof *h->tap);
            /* A tap that could not be allocated is simply not armed:
             * failing to make a *diagnostic* must never stop the sound
             * it was going to be a diagnostic about. */
            h->tap_cap = h->tap ? (int64_t)frames : 0;
        }
    }
    return h;
}

void gestate_host_free(host *h) {
    if (h) free(h->tap);
    free(h);
}

/* How many frames the tap holds, and a copy of them.
 *
 * **Copied out rather than pointed at**, because the reader is Python on
 * another thread and the writer is the render loop: handing over a
 * pointer would be handing over a race.  `frames` is what the caller has
 * room for; the answer is how many were given. */
int64_t gestate_host_tap_frames(host *h) { return h ? h->tap_n : 0; }

int64_t gestate_host_tap_read(host *h, float *out, int64_t frames) {
    if (!h || !h->tap || frames <= 0) return 0;
    int64_t have = h->tap_n;
    if (frames > have) frames = have;
    memcpy(out, h->tap,
           (size_t)frames * (size_t)h->channels * sizeof *out);
    return frames;
}

/* The engine that is sounding now, set once before the thread starts. */
void gestate_host_install(host *h, render_fn render, mix_fn mix, void *state) {
    h->current.render = render;
    h->current.mix = mix;
    h->current.state = state;
}

/* Hand over an engine Python has already migrated into.  A plain store:
 * the render thread reads `has_staged` between blocks and never inside
 * one, so there is no moment at which half a `slot` can be in use. */
void gestate_host_publish(host *h, render_fn render, mix_fn mix, void *state) {
    h->staged.render = render;
    h->staged.mix = mix;
    h->staged.state = state;
    h->has_staged = 1;
}

int64_t gestate_host_frames(host *h) { return h->frames; }
/* The card's own account of the trouble: how many blocks it ran dry
 * for, and the longest a single fill took.  Monotonic — the caller
 * takes differences, because "since when" is the caller's question. */
int64_t gestate_host_dry(host *h) { return h ? h->dry : 0; }
int64_t gestate_host_worst_us(host *h) { return h ? h->worst_us : 0; }
/* Read it and start again — `peak`'s manners, and for the same reason:
 * the question is almost always "how bad was it *during that*", and a
 * high-water mark that never clears answers a different one. */
int64_t gestate_host_take_worst(host *h) {
    if (!h) return 0;
    int64_t worst = h->worst_us;
    h->worst_us = 0;
    return worst;
}
int64_t gestate_host_position(host *h) { return h->position; }
void gestate_host_playing(host *h, int on) { h->playing = on ? 1 : 0; }
int gestate_host_is_playing(host *h) { return h->playing; }
void gestate_host_seek(host *h, int64_t to) { h->seek_to = to < 0 ? 0 : to; }
void gestate_host_watch_peak(host *h, int on) { h->watch_peak = on ? 1 : 0; }

int gestate_host_bands(void) { return GESTATE_BANDS; }

/* Tune the bank to a sample rate and switch it on.  Called once, from
 * Python, before anything is playing. */
void gestate_host_watch_bands(host *h, int on, unsigned rate) {
    static const double corner[GESTATE_BANDS - 1] = {
        110.0, 250.0, 550.0, 1200.0, 2600.0, 5500.0, 11000.0
    };
    for (int k = 0; k < GESTATE_BANDS - 1; k++) {
        double f = corner[k];
        if (f > (double)rate * 0.45) f = (double)rate * 0.45;
        h->band_k[k] = 1.0 - exp(-2.0 * 3.14159265358979323846 * f
                                 / (double)rate);
        h->band_lp[k] = 0.0;
    }
    /* A bar that fell as fast as the sound does is unreadable; 150 ms is
     * long enough to see and short enough to follow a rhythm. */
    h->band_release = exp(-1.0 / (0.15 * (double)rate));
    for (int k = 0; k < GESTATE_BANDS; k++) h->band_env[k] = 0.0f;
    h->watch_bands = on ? 1 : 0;
}

float gestate_host_band(host *h, int k) {
    if (k < 0 || k >= GESTATE_BANDS) return 0.0f;
    return h->band_env[k];
}

void gestate_host_loop(host *h, int64_t start, int64_t end) {
    h->loop_start = start < 0 ? 0 : start;
    h->loop_end = end;
}

/* Read the meter and clear it, so each look reports the span since the
 * last one rather than the loudest thing that ever happened. */
float gestate_host_peak(host *h) {
    float was = h->peak;
    h->peak = 0.0f;
    return was;
}

/* The same span, as an RMS.  Cleared on reading for the same reason. */
float gestate_host_rms(host *h) {
    double sum = h->square_sum;
    int64_t n = h->square_n;
    h->square_sum = 0.0;
    h->square_n = 0;
    return n > 0 ? (float)sqrt(sum / (double)n) : 0.0f;
}
int gestate_host_fading(host *h) { return h->fading > 0; }
void gestate_host_stop(host *h) { h->stop = 1; }

/* Defined against the device, below: make a blocked write return.
 *
 * Setting a flag is not enough on its own.  A loop stuck inside
 * `snd_pcm_writei` is not going to look at a flag — it is waiting for
 * room in a ring buffer that a card somebody else owns will never
 * drain, and it waits there for as long as the program runs.  Something
 * has to reach in and end the wait. */
void gestate_host_unblock(host *h);

/* Stop without waiting for the fade — see `halt` on the struct. */
void gestate_host_halt(host *h) {
    h->halt = 1;
    h->stop = 1;
    gestate_host_unblock(h);
}

/* Put the master fader somewhere directly.
 *
 * For a caller with no device to pop: an offline render, and the
 * comparison that proves this host renders what the engine does.  A
 * session that is going to a sound card should leave it alone and let it
 * fade up, which is what it is for. */
void gestate_host_set_gain(host *h, double g) {
    h->gain = g < 0.0 ? 0.0 : (g > 1.0 ? 1.0 : g);
}

/* One block.  This is the whole audio path.
 *
 * The staged engine is taken first, so a swap lands on a block boundary.
 * While a fade is running both engines are rendered with complementary
 * ramps into the same buffer — the generated `render_block_mix_f32`
 * multiplies by a gain going `g0`→`g1` across the block and accumulates,
 * and the two ramps sum to unity. */
void gestate_host_fill(host *h, float *out, int64_t n) {
    /* **Timed here, where every caller passes.**  The two driver loops
     * are not the only ones — the plugin's process callback fills too,
     * and so does a test — and a mark that only some of them set is a
     * mark that means different things on different days. */
    int64_t began = now_us();
    if (h->seek_to >= 0) {
        int64_t to = h->seek_to;
        h->seek_to = -1;
        seek_state(h->current.state, to);
        seek_state(h->leaving.state, to);
        h->position = to;
    }
    if (h->loop_end > 0 && h->position >= h->loop_end) {
        seek_state(h->current.state, h->loop_start);
        seek_state(h->leaving.state, h->loop_start);
        h->position = h->loop_start;
    }
    /* Where the master fader is at the start and end of this block.  It
     * moves toward 1 while playing and toward 0 while stopped or stopping,
     * and the clock only freezes once it has *arrived* at 0 — so a stopped
     * transport is still stopped, it just takes eight milliseconds to get
     * there and the tail is heard rather than cut. */
    int wanted = h->playing && !h->stop;
    double m0 = h->gain;
    double per = (double)n / (double)h->mute_len;
    double m1 = wanted ? m0 + per : m0 - per;
    if (m1 > 1.0) m1 = 1.0;
    if (m1 < 0.0) m1 = 0.0;
    h->gain = m1;

    if (m0 <= 0.0 && m1 <= 0.0) {
        /* Fully down.  The clock does not move and the state is left
         * alone, because the state *is* the instrument. */
        memset(out, 0, (size_t)n * (size_t)h->channels * sizeof *out);
        return;
    }
    if (h->has_staged) {
        h->leaving = h->current;
        h->current = h->staged;
        h->has_staged = 0;
        h->fading = h->fade_len;
    }

    if (h->fading > 0 && h->leaving.mix) {
        int64_t done = h->fade_len - h->fading;
        double a0 = (double)done / (double)h->fade_len;
        /* `a1` is deliberately *not* clamped: the generated ramp clamps
         * per sample, which is what lets a fade shorter than one block
         * arrive partway through it and hold rather than being stretched
         * across the whole buffer. */
        double a1 = (double)(done + n) / (double)h->fade_len;
        if (a0 > 1.0) a0 = 1.0;

        /* The two fades compose by scaling the crossfade's endpoints.
         * A product of two linear ramps is quadratic and this is linear,
         * so it is an approximation — of two fades that overlap only when
         * an edit lands during a start or a stop, over a few
         * milliseconds, and both monotone.  Exact where it matters: when
         * the master is at 1 this is what it always was. */
        memset(out, 0, (size_t)n * (size_t)h->channels * sizeof *out);
        h->current.mix(h->current.state, out, n, h->control, a0 * m0, a1 * m1);
        h->leaving.mix(h->leaving.state, out, n, h->control,
                       (1.0 - a0) * m0, (1.0 - a1) * m1);

        h->fading -= n;
        if (h->fading <= 0) {
            h->fading = 0;
            h->leaving.render = 0;
            h->leaving.mix = 0;
            h->leaving.state = 0;
        }
    } else if (h->current.render && m0 >= 1.0 && m1 >= 1.0) {
        /* The ordinary case: the fader is up and out of the way, so this
         * is the one call it always was. */
        h->current.render(h->current.state, out, n, h->control);
    } else if (h->current.mix) {
        memset(out, 0, (size_t)n * (size_t)h->channels * sizeof *out);
        h->current.mix(h->current.state, out, n, h->control, m0, m1);
    } else {
        memset(out, 0, (size_t)n * (size_t)h->channels * sizeof *out);
    }
    h->frames += n;
    h->position += n;

    if (h->watch_bands) {
        /* Down the bank once per frame, on the sum of the channels: a
         * spectrum of the picture, not of one ear. */
        double scale = 1.0 / (double)h->channels;
        for (int64_t i = 0; i < n; i++) {
            double x = 0.0;
            for (int c = 0; c < h->channels; c++)
                x += out[i * h->channels + c];
            x *= scale;
            double below = 0.0;
            for (int k = 0; k < GESTATE_BANDS - 1; k++) {
                h->band_lp[k] += h->band_k[k] * (x - h->band_lp[k]);
                double got = fabs(h->band_lp[k] - below);
                below = h->band_lp[k];
                double was = h->band_env[k] * h->band_release;
                h->band_env[k] = (float)(got > was ? got : was);
            }
            double top = fabs(x - below);
            double was = h->band_env[GESTATE_BANDS - 1] * h->band_release;
            h->band_env[GESTATE_BANDS - 1] =
                (float)(top > was ? top : was);
        }
    }
    if (h->watch_peak) {
        /* **Sampled, not scanned** — sixteen points of a block is enough
         * to see a needle move, and is a rounding error beside the block
         * itself.  The RMS rides the same sixteen: an average of a
         * sixteenth of the samples is an average. */
        int64_t span = n * h->channels;
        int64_t step = span / 16;
        if (step < 1) step = 1;
        double sum = h->square_sum;
        int64_t count = h->square_n;
        for (int64_t i = 0; i < span; i += step) {
            float v = out[i] < 0 ? -out[i] : out[i];
            if (v > h->peak) h->peak = v;
            sum += (double)out[i] * (double)out[i];
            count++;
        }
        h->square_sum = sum;
        h->square_n = count;
    }
    filled_in(h, began);
}

/* Render into a pipe until told to stop — the player's own back-pressure
 * is the clock, exactly as the Python pipe driver used it.  Runs on a
 * thread Python starts and never re-enters Python, so a collection cannot
 * stall it.
 *
 * Returns the number of frames written, or -1 if the pipe closed. */
int64_t gestate_host_run(host *h, int fd, float *scratch, int64_t block,
                         int64_t total) {
    size_t bytes = (size_t)block * (size_t)h->channels * sizeof *scratch;
    int64_t written = 0;
    while (total <= 0 || written < total) {
        /* **Drained, not broken out of.**  Leaving the moment `stop` is
         * set closes the device mid-waveform, which is the pop you hear on
         * quit; `fill` is already fading toward silence by then, so this
         * waits for it to arrive. */
        if (h->halt) break;
        if (h->stop && h->gain <= 0.0) break;
        int64_t want = block;
        if (total > 0 && written + want > total) want = total - written;
        gestate_host_fill(h, scratch, want);
        size_t left = (size_t)want * (size_t)h->channels * sizeof *scratch;
        const char *at = (const char *)scratch;
        while (left) {
            ssize_t put = write(fd, at, left);
            if (put <= 0) return -1;
            left -= (size_t)put;
            at += put;
        }
        /* The whole block went, or this loop returned — so what the sink
         * received is `want`.  **The tap is in this loop as well as the
         * device's**, and that is what makes it testable: a machine with
         * no sound card can still hold the instrument to what it claims,
         * which is most machines and every one the suite runs on. */
        tapped(h, scratch, want);
        written += want;
        (void)bytes;
    }
    return written;
}


/* ── The device ─────────────────────────────────────────────────────────
 *
 * `run_device` is the whole audio path: fill a block, write it, repeat,
 * until something outside sets `stop`.  Python starts it on a thread and
 * does not enter it again, so neither the GIL nor a collection can reach
 * it — which is the entire reason this file exists.
 */

#ifdef GESTATE_ALSA

int gestate_host_open(host *h, const char *device, unsigned rate,
                      unsigned latency_us) {
    snd_pcm_t *pcm = 0;
    if (snd_pcm_open(&pcm, device, SND_PCM_STREAM_PLAYBACK, 0) < 0)
        return -1;
    if (snd_pcm_set_params(pcm, SND_PCM_FORMAT_FLOAT_LE,
                           SND_PCM_ACCESS_RW_INTERLEAVED,
                           (unsigned)h->channels, rate, 1, latency_us) < 0) {
        snd_pcm_close(pcm);
        return -2;
    }
    h->pcm = pcm;
    return 0;
}

int64_t gestate_host_run_device(host *h, float *scratch, int64_t block,
                                int64_t total) {
    int64_t written = 0;
    if (!h->pcm) return -1;
    while (total <= 0 || written < total) {
        /* Drained rather than broken out of — see the pipe loop above. */
        if (h->halt) break;
        if (h->stop && h->gain <= 0.0) break;
        int64_t want = block;
        if (total > 0 && written + want > total) want = total - written;
        gestate_host_fill(h, scratch, want);
        snd_pcm_sframes_t put = snd_pcm_writei((snd_pcm_t *)h->pcm,
                                               scratch, (snd_pcm_uframes_t)want);
        if (put < 0) {
            /* An underrun is recoverable and is not news: the machine was
             * busy for a moment.  Recovering silently is what a player
             * does; failing to is what a crackle used to be — but it is
             * counted, because a stutter nobody can measure is a stutter
             * two people can disagree about. */
            h->dry += 1;
            put = snd_pcm_recover((snd_pcm_t *)h->pcm, (int)put, 1);
            if (put < 0) return -1;
            continue;
        }
        /* **`put`, not `want`** — what the card took.  A short write is
         * rare and is exactly the moment the difference matters. */
        tapped(h, scratch, put);
        written += put;
    }
    /* **Drain only if draining can finish.**  `snd_pcm_drain` waits for
     * the card to play out what is queued, which on a card somebody else
     * is holding is a wait with no end; `snd_pcm_drop` throws the queue
     * away and returns.  Having decided not to wait for the fade, this
     * must not then wait for the buffer. */
    if (h->halt) {
        snd_pcm_drop((snd_pcm_t *)h->pcm);
    } else {
        snd_pcm_drain((snd_pcm_t *)h->pcm);
    }
    return written;
}

void gestate_host_close_device(host *h) {
    if (h->pcm) {
        snd_pcm_close((snd_pcm_t *)h->pcm);
        h->pcm = 0;
    }
}

/* **Called from another thread, on purpose.**  `snd_pcm_drop` throws
 * away what is queued and makes a blocked `writei` or `drain` return at
 * once — which is the only way to get the device loop back to a place
 * where it can be told anything.  The loop checks `halt` before it
 * would use the handle again, so the drop does not race a write into a
 * closed device. */
void gestate_host_unblock(host *h) {
    if (h->pcm) snd_pcm_drop((snd_pcm_t *)h->pcm);
}

int gestate_host_has_device(void) { return 1; }

#else

int gestate_host_open(host *h, const char *device, unsigned rate,
                      unsigned latency_us) {
    (void)h; (void)device; (void)rate; (void)latency_us;
    return -3;
}
int64_t gestate_host_run_device(host *h, float *scratch, int64_t block,
                                int64_t total) {
    (void)h; (void)scratch; (void)block; (void)total;
    return -1;
}
void gestate_host_close_device(host *h) { (void)h; }
void gestate_host_unblock(host *h) { (void)h; }
int gestate_host_has_device(void) { return 0; }

#endif
