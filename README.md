# krellophone

A polyphonic music synthesis engine written in pure [Krell](https://github.com/nightwarelabz/krell), with example compositions.

Every sound is computed sample by sample by a Krell program. There is no
sample library, no host audio code, and no runtime besides the compiled
program itself: a piece goes in as an event table, and a finished WAV file
comes out.

## The engine

`engine/` holds the instrument in composable parts:

| File | Contents |
| --- | --- |
| `ext.inc` | Extern declarations (libc write/malloc, libm) |
| `engine_body.krell` | Core helpers: MIDI-to-frequency, a runtime-built 4096-entry sine wavetable, waveform lookup, soft clipper, WAV header writers, buffer zeroing |
| `engine.krell` | `ext.inc` and `engine_body.krell` pre-joined |
| `noteon.krell` | Voice allocation: a 40-voice dense active list with voice stealing |
| `rsample.krell` | The per-sample renderer: oscillators, envelopes, stereo placement, and a Schroeder reverb (4 combs + 2 allpass chains per side) |
| `main.krell` | Entry point and the render loop |

Engine properties:

- Full MIDI pitch range; frequency from the equal-temperament formula at
  render time.
- 40-voice polyphony. Each voice runs a partial stack whose gains follow
  velocity (brightness scales with how hard the note is struck), a
  register-scaled decay, and a pitch-based stereo position.
- Two presets: **0, fortepiano** (percussive envelope) and **1, strings**
  (sustained ADSR with vibrato).
- A score is five data tables — start, duration, note, velocity, preset —
  plus a count. Any piece that can be expressed as note events can be
  rendered.
- Rendering is chunkable: the program takes `(start_sample, count)`
  arguments and renders any window of a piece, with a 3-second pre-roll so
  reverb and envelopes agree across chunk boundaries.
- Output is 44.1 kHz stereo WAV, written to stdout, with the header sizes
  computed from the sample count.

## Building and running

Requires the Krell toolchain and a C compiler. Krell builds to assembly;
the C compiler assembles and links it.

```sh
krellc build examples/mozart/mozart.krell --target x86_64 -o mozart.s
cc mozart.s -o mozart -lm
./mozart > rondo.wav
```

A complete piece program is assembled by concatenation, in this order:
score tables, then `ext.inc`, `engine_body.krell`, `noteon.krell`,
`rsample.krell`, `main.krell`.

## Examples

- **examples/mozart/** — Mozart, *Rondo alla Turca* (Sonata K. 331, third
  movement), complete: 1,614 note events rendered by the engine.
  `mozart_test.krell` is a six-note test card (a low fortepiano note, a
  strings chord, a high fortepiano note) for verifying an engine build.
  `midparse.py` and `encode.py` are the pipeline that turns a MIDI file of
  the public-domain score into the engine's event tables, with dynamics
  and phrasing applied.
- **examples/miasma-homage/** — `synth.krell`, a standalone 120-second
  composition at 96 BPM in D minor.
- **examples/field-music/** — `fieldmusic.krell`, a 60-second piece
  generated from an interference field pattern.
- **examples/lateralus-homage/** — `homage.krell`, a 60-second cut, and
  `homage_full.krell`, the full 480-second version whose section lengths
  follow the Fibonacci sequence.
- **examples/epicycle-audio/** — `epicycle-audio.krell`: the Fourier
  epicycle drawing, heard — every wheel of the drawing whose frequency
  falls in the audible band becomes a tone.
- **examples/moonlight/** — Beethoven, *Moonlight Sonata* (Piano Sonata
  No. 14, first movement), complete: 1,142 note events from the Mutopia
  public-domain score rendered by the engine, with editorial dynamics
  (the score MIDI carries uniform velocity). `midparse.py` and
  `encode_moon.py` are the MIDI → tables pipeline. The performance is a
  release asset (`moonlight.mp3`).
- **examples/fibonacci/** — Fibonacci computed and filmed entirely in
  Krell: `fib.krell` cross-verifies four Fibonacci engines and prints
  exact F(1000) and F(10000); the film programs (`fibfilm`, `fibfilm2`,
  `fibfilm4`) draw 2,584 = F(18) phyllotaxis seeds by the golden angle
  around a golden logarithmic spiral. `fibfilm2` and `fibfilm4` embed
  the Moonlight event tables and analyze the music in Krell to drive
  the light — in `fibfilm4` the field spirals with differential shear
  and strong onsets launch wavefronts from the center through the
  total circumference. The films are release assets.
- **examples/live-count/** — a speed demonstration film: every frame
  computed live by `livecount.krell`, golden-angle phyllotaxis particles
  by recurrence, the per-frame count climbing from 10,000 to about
  2.99 million (about 904 million particles across the film), the count
  stamped onto each frame by the program itself. The soundtrack
  (`livecount_audio.krell`) is an 8-voice Krell synth whose note density
  ramps with the particle climb. The film is a release asset.

## License

Apache-2.0. See `LICENSE`.
