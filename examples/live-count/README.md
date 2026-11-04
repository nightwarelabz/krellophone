# Live Count — a Krell speed demonstration film

72 seconds, 960×960, 24 fps, 1,728 frames. The film is a release asset on this repository (`live-count.mp4`).

## What it proves

Every frame is computed from scratch by a Krell program
(`livecount.krell`, verified for x86_64 and aarch64).
Each frame, the program computes **N particles live** — golden-angle
phyllotaxis by recurrence, no per-particle trig, no baked frames —
where N climbs exponentially across the film:

- frame 0: **10,000 particles**
- mid-film: **173,205 particles**
- final frame: **~2.99 million particles**
- **~904 million particles computed across the film**

The current count is stamped onto each frame by the Krell program
itself, as digits formed of light dots under the disc. Exposure is
re-normalized per frame inside the program as N grows, so the sparse
opening field of separate dots densifies into a continuous luminous
fabric — the count climbing *is* the picture.

The soundtrack (`livecount_audio.krell`) is also pure Krell: an
8-voice synth (Dm–Bb–F–C pad + arpeggio) whose note density ramps
exponentially from one pluck per 0.42 s to one per ~18 ms, mirroring
the particle climb. Measured crescendo: RMS −21.3 dB (0–12 s) →
−15.8 dB (30–42 s) → −12.0 dB (60–72 s), peak −0.72 dB.

## Render record

- All 12 chunks (144 frames each) frame-count verified before join.
- Krell frame computation: 362 s wall on 4 workers (~1,448 core-seconds)
  for ~904M particles plus 1,728 full-frame per-pixel tone maps.
- Final file: `live-count.mp4`, 1,728 frames, 72.000 s, H.264 + AAC,
  sha256 `2ddf7f4750d79faf4d26cd64d7d04881406e8249bd180fa5cbc35b03ead4e2e3`.
- Stills inspected at frames 0 / 864 / 1727 and from the finished mp4
  at t=71 s (count 2,771,512 on screen).

## Build

```sh
python3 gen_livecount.py        # writes livecount.krell
python3 gen_audio.py            # writes livecount_audio.krell
krellc parse livecount.krell -o livecount.krel
krellc build livecount.krel --target x86_64 -o livecount.s
cc -O2 -o livecount livecount.s -lm
./livecount <frame> 1728 960 > frame.ppm
bash render.sh                  # chunked parallel render + census
./livecount_audio 72 > audio.f64   # raw f64le PCM, 22050 Hz
```
