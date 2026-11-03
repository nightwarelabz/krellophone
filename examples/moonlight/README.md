# Moonlight Sonata, First Movement — Performed Entirely in Krell

Ludwig van Beethoven, Piano Sonata No. 14 in C-sharp minor, Op. 27
No. 2, first movement (Adagio sostenuto), performed note-for-note by
the Krell synthesis engine (the krellophone engine: runtime-built
wavetable oscillators, 40-voice polyphony, fortepiano preset,
Schroeder reverb — every sample computed by the Krell program; the
host provides only `write`/`malloc` and libm).

The performance (MP3) and the Fibonacci films it soundtracks are
release assets on this repository.

## Source and interpretation

- Score: the Mutopia Project's public-domain edition (MIDI,
  `moonlight-mids.zip`, piece 276), movement 1: **1,142 notes**,
  pitch range F1–D#6, 69 bars of 4/4, tempo meta 1,000,000 µs/quarter
  (♩ = 60) taken as written — total 279.0 s including a 3 s natural
  decay tail.
- The score MIDI carries uniform velocity, so dynamics are editorial
  (encoded in `encode_moon.py`): melody (long right-hand notes) sings
  at the top, triplet figuration murmurs beneath, bass octaves form
  the floor with extended pedal resonance; one long phrase arch
  swells over the movement with 8-bar breathing, a hushed opening and
  a receding close; ±1 tick / small velocity humanization throughout.

## Build and run

```sh
python3 midparse.py           # moonlight1.mid -> score.json
python3 encode_moon.py        # score.json -> tables.inc + events.json
cat ../../engine/ext.inc tables.inc ../../engine/engine_body.krell \
    ../../engine/noteon.krell ../../engine/rsample.krell \
    ../../engine/main.krell > moonlight.krell
krellc parse moonlight.krell -o moonlight.krel
krellc build moonlight.krel --target x86_64 -o moonlight.s   # NO -O (below)
cc -O2 -o moonlight moonlight.s -lm
./moonlight 0 12303900 > moonlight.wav
```

**Build note:** the engine must be built *without* `krellc -O`. The
optimized build of this program segfaults in the render loop (the
byte-identical Mozart source shows the same split: its shipped `.s`
hash-matches the no-`-O` build exactly, and the `-O` build crashes).
The Fibonacci compute program is unaffected and builds with `-O`.

## Verification

- WAV: 12,303,900 samples, 44.1 kHz stereo, 279.0 s; peak 0.7775,
  zero clipped samples; final chord decays to 0.0005 by the last
  sample (no abrupt cut).
- Opening-second spectrum carries exactly the C# minor sonority:
  strong C#2/C#3, G#3, C#4, E4 partials.
- RMS stays musical throughout (0.10–0.15 in 30 s windows, easing to
  0.096 in the final window).

## Files

| file | what |
|---|---|
| `moonlight.krell` | the assembled Krell program (score tables + engine) |
| `tables.inc` | the score as Krell data (start/duration/note/velocity/preset) |
| `encode_moon.py`, `midparse.py` | MIDI → tables pipeline |
| `moonlight1.mid` | Mutopia source score |
| `events.json` | the event list (also embedded in the Fibonacci film) |
| `moonlight.mp3` | the performance (MP3 192 kbps) — release asset |

The performance is the soundtrack of the audio-reactive Fibonacci
films (`../fibonacci/`): those programs embed these same event tables
and compute the music's band energies themselves, in Krell, to drive
the light.
