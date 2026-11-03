# Fibonacci, Computed Entirely in Krell

Two Krell programs. Every number, digit, and pixel in their output is
computed by the Krell program itself; the only host services used are
`write` and `malloc` (the film also calls libm `sin`/`cos`/`sqrt`/`exp`
and `atoi`). The films are release assets on this repository.

## 1. `fib.krell` — the compute program

Four independent Fibonacci engines in one module, cross-verifying each
other and five identities, then leaving 64 bits behind:

- **Engines:** naive recursion; two-slot iteration; fast doubling
  (per-depth scratch pairs); binary powering of the 2×2 matrix
  `[[1,1],[1,0]]`.
- **Cross-verification, 1,763 checks in total, all passing:** recursion,
  fast doubling and matrix power each against iteration; the Cassini
  identity; the summation identity `sum F(i) = F(n+2) − 1`; the gcd
  identity `gcd(F(m),F(n)) = F(gcd(m,n))`; the addition formula.
  The program counts its own checks and prints the verdict; its exit
  code is the failure count (0).
- **Operation counts for n = 32, instrumented and printed by the
  program:** naive recursion 7,049,155 calls; iteration 32 additions;
  fast doubling 18 multiplications over 6 levels; matrix power 7 matrix
  multiplications (56 scalar multiplications).
- **Golden ratio:** `F(n+1)/F(n)` printed digit by digit to 15 decimal
  places for n = 10…90, converging on 1.618033988749895.
- **Exact big Fibonacci** in base-10⁹ limbs (three fixed buffers,
  in-place triple steps): prints **F(1000)** in full (209 digits, digit
  sum 1005) and **F(10000)** in full (2090 digits, digit sum 9123),
  with digit counts, last 9 digits, and leading digits — all computed
  and formatted by the program (its own decimal printers).

Verified independently of the program: the F(0)…F(92) table, both big
values digit for digit, digit counts and sums, last-9 and leading
digits, and every ratio line were recomputed outside Krell and match.
The reference interpreter agrees with the native build
(`fib_iter 92 → 7540113804746346429`, `fib_fast 90` and
`fib_matrix 90 → 2880067194370816120`, `fib_rec 28 → 317811`).

Module identity (canonical hash):
`2cdb3739b28bdd6f975442430d94a077a9237b053e7d98eed0c4260cfd233aca`

### Build and run

```sh
# with krellc built from the Krell v2.0-branch toolchain (WP11 tree)
krellc parse fib.krell -o fib.krel
krellc verify fib.krel --target x86_64   # also aarch64, riscv64
krellc build fib.krel --target x86_64 -O -o fib.s
cc -O2 -o fib fib.s -lm
./fib            # full report; exit code 0; ~0.1 s
```

## 2. `fibfilm.krell` — the film

A 12-second seamless loop, 960×960, 24 fps, 288 frames, each frame one
PPM on stdout. Everything in the frame is Fibonacci:

- **2,584 = F(18) phyllotaxis seeds** placed by the golden angle
  (137.50776405…°) with radius ∝ √k, soft-stamped into a float canvas
  (5×5 kernel), brightness shimmering at 5 cycles per film.
- **The golden logarithmic spiral** — radius ×φ every half turn —
  sampled 9,000 times, counter-rotating against the seed field while
  the field itself makes exactly one full turn per film; breathing at
  2 cycles. Frame 288 is byte-identical to frame 0 (verified).
- **Per-pixel tone mapping in Krell:** deep-blue radial field, gold
  light through a `1 − exp(−v)` curve, white-hot cores, distance tint,
  vignette.

```sh
krellc parse fibfilm.krell -o fibfilm.krel
krellc build fibfilm.krel --target x86_64 -O -o fibfilm.s
cc -O2 -o fibfilm fibfilm.s -lm
for i in $(seq 0 287); do ./fibfilm $i 288 960 > f$i.ppm; done
ffmpeg -framerate 24 -i f%d.ppm -c:v libx264 -pix_fmt yuv420p -crf 15 fib-film.mp4
```

## 3. `fibfilm2.krell` — the film in blue, driven by the music

The same field, relit by a Krell performance of Beethoven's Moonlight
Sonata, first movement (`../moonlight/` — the song was
rendered entirely in Krell by the krellophone engine from the Mutopia
public-domain score, 1,142 notes, 279.0 s).

- The film program embeds the performance's score tables as data and
  **analyzes the music itself, in Krell, every frame**: it walks the
  note events and accumulates low/mid/high register energies
  (register-scaled exponential decays) plus an onset-strength signal —
  no host-side envelope is baked in.
- Each of the 2,584 dots is bound to a register band by its radius
  (core = bass, rim = treble) and **pulsates in bright blue crisp
  light** with its band's energy; the pulsation travels as expanding
  anamorphic waves (three wavefronts across the radius), over
  wave-sheet glows in the deep-blue field, with a **horizontal
  anamorphic streak** through the core that fires on the music's
  attacks. The golden spiral breathes with the total energy.
- 6,696 frames, 960×960, 24 fps, 279.000 s — exactly the length of
  the performance, which is muxed in as the soundtrack (AAC from the
  Krell WAV). `fib-film-blue-full.mp4` is the archival encode
  (CRF 12 segments, stream-copied join); `fib-film-blue.mp4` is the
  delivery encode (CRF 21). Both verified: 6,696 frames, 279.000 s,
  stills inspected at the opening, mid-swell, and close — the light
  tracks the music (hushed opening, blazing attacks, receding end).

```sh
krellc parse fibfilm2.krell -o fibfilm2.krel
krellc build fibfilm2.krel --target x86_64 -o fibfilm2.s   # no -O needed
cc -O2 -o fibfilm2 fibfilm2.s -lm
./fibfilm2 <frame> 6696 960 > frame.ppm
```

## 4. `fibfilm4.krell` — the film in motion: spiraling field + onset wavefronts

- Built after review of the blue film: its field rotated only one turn
  over the whole piece, so the spiral read as still, and its waves were
  brightness-only. `fibfilm4` (generator `gen_film4.py`) keeps the same
  score analysis and palette, and changes the motion:
  - **The field spirals.** The seed field rotates two turns per film
    with differential shear (inner radii turn faster than outer), so
    the phyllotaxis visibly winds and morphs instead of spinning
    rigidly. The golden spiral counter-rotates six turns per film on
    its own angle, its light traveling along the arm, its scale
    breathing ±5% with total energy.
  - **Waves push outward from the center, per the music.** The
    analysis keeps the four most recent strong onsets (velocity ≥ 82).
    Each launches a wavefront from the center at 0.5 radius-fraction
    per second; as the front passes, seeds flare (×1.1) and a blue
    ring-glow is added over the whole frame, corners included, decaying
    as exp(−0.35·dt). Wavefronts cross the total circumference and
    exit at the rim.
  - The dot field and spiral extend to 0.485 of the frame width, so
    the light reaches the edge circle.
- Authoring note: the spiral's breathing scale is pre-scaled ×0.94 —
  at full breath the outermost samples would otherwise leave the
  canvas (0.94 × 1.05 = 0.987 of the field radius, always inside).
- 6,696 frames, 960×960, 24 fps, 279.000 s, Moonlight performance
  muxed in as the soundtrack. `fib-film-waves-full.mp4` is the
  archival encode (CRF 12); `fib-film-waves.mp4` is the delivery
  encode (CRF 21). Rendered in 168-frame chunks, each chunk verified
  by exact frame count before the stream-copy join; stills inspected
  at the hushed opening (t=2 s), a wavefront reaching the rim
  (t=69.5 s), the fully sheared mid-film field (t=140 s), and the
  receding close (t=272 s).

```sh
krellc parse fibfilm4.krell -o fibfilm4.krel
krellc build fibfilm4.krel --target x86_64 -o fibfilm4.s   # no -O needed
cc -O2 -o fibfilm4 fibfilm4.s -lm
./fibfilm4 <frame> 6696 960 > frame.ppm
bash render4.sh   # resumable chunked render into film4/
```

## Implementation notes

- Krell hash-conses pure instructions per function: a literal first
  materialized in a non-dominating block makes sibling uses fail
  verification ("use not dominated by definition"). Both sources are
  generated with every literal seeded as an explicit `iconst`/`fconst`
  in the function's entry block (see `seed_constants` in the
  generators, `gen_fib.py` / `gen_film.py`, which emit the `.krell`
  sources).
- A cyclic permutation of block arguments (rotating three buffer
  pointers through a loop header) is not safe on the native backend:
  the buffers alias and the big-Fibonacci iteration degenerated into
  doubling. `big_fib` therefore keeps buffer roles fixed and advances
  three steps per iteration in place (`C=A+B`, `A=B+C`, `B=A+C`;
  `big_add` is index-wise, so its destination may alias one operand).

## Files

| file | what |
|---|---|
| `fib.krell` / `fibfilm.krell` | the two Krell sources |
| `gen_fib.py` / `gen_film.py` | their generators (literal seeding) |
| `fib_output.txt` | the compute program's full report |
| `fib-film.mp4` | the film (H.264, 960×960, 24 fps, 12.000 s, 288 frames) |
| `fib-hero-1920.png` | frame 36 rendered at 1920×1920 |
| `still-*.png` | film frames 0 / 72 / 144 / 216 at 960×960 |
| `fib`, `fibfilm`, `*.krel`, `*.s`, `fib.ll` | build products |

SHA-256:

```
d5e60b48a7f24ba4e0ea654c2c6b79a256fca9e98aab56ab9e652a4cd58004bd  fib.krell
75a774865dfeae7fc3f27aa7f64da3ac0baf591028aceb1e9b2c139fe1f4ea81  fibfilm.krell
1e64514450d90a14ec85ce06e3ed74c2641e931c9eff35eb231aa996de202fc7  fib-film.mp4
bd91fc230257d0fcafc58e11f39763ff311f8cabfbdcb6449957186c02b01a86  fib_output.txt
```
