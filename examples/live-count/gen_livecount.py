#!/usr/bin/env python3
"""Generator for livecount.krell - the Live Count film.

Every frame, the Krell program itself computes N particles live
(phyllotaxis by golden-angle recurrence, no trig per particle), where
N climbs exponentially from 10,000 to ~3,000,000 over the film, and
stamps the current count onto the frame as digits made of light dots.
Host services only: write, malloc, atoi, sin, cos, sqrt, exp, pow.
Output: one PPM (P6) frame on stdout. Args: [frame] [total] [size].
"""
import pathlib, re

SRC = r"""
extern write(i32, ptr, i64) -> i64
extern malloc(i64) -> ptr
extern atoi(ptr) -> i32
extern sin(f64) -> f64
extern cos(f64) -> f64
extern sqrt(f64) -> f64
extern exp(f64) -> f64
extern pow(f64, f64) -> f64

data dh1: i8 = { 80, 54, 10 }
data dsp: i8 = { 32 }
data dh2: i8 = { 10, 50, 53, 53, 10 }
data glyphs: i64 = { @@GLYPHS@@ }

fn wh1() -> void {
  entry():
    %p = dataptr 0
    %r = call i64 write(1, %p, 3)
    ret
}
fn wsp() -> void {
  entry():
    %p = dataptr 1
    %r = call i64 write(1, %p, 1)
    ret
}
fn wh2() -> void {
  entry():
    %p = dataptr 2
    %r = call i64 write(1, %p, 5)
    ret
}

fn print_u64(i64) -> void {
  entry(x: i64):
    %buf = call ptr malloc(32)
    %z = icmp.eq i64 x, 0
    condbr %z, zero(%buf), loop(24, x, %buf)
  zero(buf: ptr):
    %p = gep i8 buf, 0
    store i8 %p, 48
    %w = call i64 write(1, buf, 1)
    ret
  loop(pos: i64, x: i64, buf: ptr):
    %done = icmp.sle i64 x, 0
    condbr %done, dump(pos, buf), body(pos, x, buf)
  body(pos: i64, x: i64, buf: ptr):
    %d = urem i64 x, 10
    %ch = add i64 %d, 48
    %ch8 = trunc i8 %ch
    %p2 = sub i64 pos, 1
    %pp = gep i8 buf, %p2
    store i8 %pp, %ch8
    %x2 = udiv i64 x, 10
    br loop(%p2, %x2, buf)
  dump(pos: i64, buf: ptr):
    %pp = gep i8 buf, pos
    %len = sub i64 24, pos
    %w = call i64 write(1, %pp, %len)
    ret
}

fn clamp01(f64) -> f64 {
  entry(v: f64):
    %lo = fcmp.olt f64 v, 0.0
    %a = select f64 %lo, 0.0, v
    %hi = fcmp.ogt f64 %a, 1.0
    %b = select f64 %hi, 1.0, %a
    ret %b
}

fn clamp255(f64) -> f64 {
  entry(v: f64):
    %lo = fcmp.olt f64 v, 0.0
    %a = select f64 %lo, 0.0, v
    %hi = fcmp.ogt f64 %a, 255.0
    %b = select f64 %hi, 255.0, %a
    ret %b
}

fn zero_canvas(ptr, i64) -> void {
  entry(buf: ptr, n: i64):
    br loop(0, buf, n)
  loop(i: i64, buf: ptr, n: i64):
    %done = icmp.sge i64 i, n
    condbr %done, fin(), body(i, buf, n)
  body(i: i64, buf: ptr, n: i64):
    %p = gep f64 buf, i
    store f64 %p, 0.0
    %i2 = add i64 i, 1
    br loop(%i2, buf, n)
  fin():
    ret
}

@@SPLAT@@

; particles: golden-angle phyllotaxis by recurrence. (c,s) starts at the
; field rotation and steps by the golden angle each particle - no trig
; in the hot loop. radius = sqrt(k/N) * Rmax * breath.
fn particle_pass(ptr, i64, i64, f64, f64, f64) -> void {
  entry(buf: ptr, S: i64, N: i64, rot: f64, breath: f64, wscale: f64):
    %sf = sitofp f64 S
    %rmax0 = fmul f64 %sf, 0.42
    %rmax = fmul f64 %rmax0, breath
    %half = fmul f64 %sf, 0.5
    %nf = sitofp f64 N
    %c0 = call f64 cos(rot)
    %s0 = call f64 sin(rot)
    br loop(0, %c0, %s0, buf, S, N, %rmax, %half, %nf, wscale)
  loop(k: i64, c: f64, s: f64, buf: ptr, S: i64, N: i64, rmax: f64, half: f64, nf: f64, wscale: f64):
    %done = icmp.sge i64 k, N
    condbr %done, fin(), body(k, c, s, buf, S, N, rmax, half, nf, wscale)
  body(k: i64, c: f64, s: f64, buf: ptr, S: i64, N: i64, rmax: f64, half: f64, nf: f64, wscale: f64):
    %kf0 = sitofp f64 k
    %kf = fadd f64 %kf0, 0.5
    %fr0 = fdiv f64 %kf, nf
    %rf = call f64 sqrt(%fr0)
    %r = fmul f64 %rf, rmax
    %dx = fmul f64 %r, c
    %dy = fmul f64 %r, s
    %x = fadd f64 half, %dx
    %y = fadd f64 half, %dy
    %cs = fmul f64 c, s
    %pu0 = fmul f64 %cs, 0.34
    %pulse = fadd f64 %pu0, 0.83
    %fa0 = fmul f64 %rf, 0.5
    %fall = fsub f64 1.15, %fa0
    %w0 = fmul f64 wscale, %pulse
    %w = fmul f64 %w0, %fall
    %ix = fptosi i64 %x
    %iy = fptosi i64 %y
    call void splat(buf, S, %ix, %iy, %w)
    %cc = fmul f64 c, -0.7373688780783201
    %ss = fmul f64 s, 0.6754902942615235
    %c2 = fsub f64 %cc, %ss
    %sc = fmul f64 s, -0.7373688780783201
    %cs2 = fmul f64 c, 0.6754902942615235
    %s2 = fadd f64 %sc, %cs2
    %k2 = add i64 k, 1
    br loop(%k2, %c2, %s2, buf, S, N, rmax, half, nf, wscale)
  fin():
    ret
}

fn count_digits(i64) -> i64 {
  entry(v: i64):
    br loop(v, 0)
  loop(t: i64, n: i64):
    %done = icmp.sle i64 t, 0
    condbr %done, fin(n), body(t, n)
  body(t: i64, n: i64):
    %t2 = udiv i64 t, 10
    %n2 = add i64 n, 1
    br loop(%t2, %n2)
  fin(n: i64):
    ret n
}

; one digit, 3x5 font, mask bit (14-j); each lit cell is a 2x2 cluster
; of splats so the digit reads as light dots, like the particles.
fn draw_digit(ptr, i64, i64, i64, i64, i64) -> void {
  entry(buf: ptr, S: i64, x0: i64, y0: i64, cell: i64, mask: i64):
    br loop(0, buf, S, x0, y0, cell, mask)
  loop(j: i64, buf: ptr, S: i64, x0: i64, y0: i64, cell: i64, mask: i64):
    %done = icmp.sge i64 j, 15
    condbr %done, fin(), body(j, buf, S, x0, y0, cell, mask)
  body(j: i64, buf: ptr, S: i64, x0: i64, y0: i64, cell: i64, mask: i64):
    %sh = sub i64 14, j
    %bits = lshr i64 mask, %sh
    %bit = and i64 %bits, 1
    %on = icmp.eq i64 %bit, 1
    condbr %on, lit(j, buf, S, x0, y0, cell, mask), next(j, buf, S, x0, y0, cell, mask)
  lit(j: i64, buf: ptr, S: i64, x0: i64, y0: i64, cell: i64, mask: i64):
    %col = urem i64 j, 3
    %row = udiv i64 j, 3
    %hc = udiv i64 cell, 2
    %cx0 = mul i64 %col, cell
    %cx1 = add i64 %cx0, x0
    %cx = add i64 %cx1, %hc
    %cy0 = mul i64 %row, cell
    %cy1 = add i64 %cy0, y0
    %cy = add i64 %cy1, %hc
    call void splat(buf, S, %cx, %cy, 1.2)
    %cxb = add i64 %cx, 2
    call void splat(buf, S, %cxb, %cy, 1.2)
    %cyb = add i64 %cy, 2
    call void splat(buf, S, %cx, %cyb, 1.2)
    call void splat(buf, S, %cxb, %cyb, 1.2)
    br next(j, buf, S, x0, y0, cell, mask)
  next(j: i64, buf: ptr, S: i64, x0: i64, y0: i64, cell: i64, mask: i64):
    %j2 = add i64 j, 1
    br loop(%j2, buf, S, x0, y0, cell, mask)
  fin():
    ret
}

fn draw_number(ptr, i64, i64) -> void {
  entry(buf: ptr, S: i64, val: i64):
    %n = call i64 count_digits(val)
    %cell = udiv i64 S, 128
    %adv = mul i64 %cell, 4
    %wtot0 = mul i64 %n, %adv
    %wtot = sub i64 %wtot0, %cell
    %spare = sub i64 S, %wtot
    %x0 = udiv i64 %spare, 2
    %marg = udiv i64 S, 74
    %h5 = mul i64 %cell, 5
    %y00 = sub i64 S, %h5
    %y0 = sub i64 %y00, %marg
    br loop(val, 0, buf, S, %n, %cell, %adv, %x0, %y0)
  loop(rem: i64, idx: i64, buf: ptr, S: i64, n: i64, cell: i64, adv: i64, x0: i64, y0: i64):
    %done = icmp.sle i64 rem, 0
    condbr %done, fin(), body(rem, idx, buf, S, n, cell, adv, x0, y0)
  body(rem: i64, idx: i64, buf: ptr, S: i64, n: i64, cell: i64, adv: i64, x0: i64, y0: i64):
    %d = urem i64 rem, 10
    %gp = dataptr 3
    %mp = gep i64 %gp, %d
    %mask = load i64, %mp
    %nm1 = sub i64 n, 1
    %posl = sub i64 %nm1, idx
    %dx0 = mul i64 %posl, adv
    %dx = add i64 x0, %dx0
    call void draw_digit(buf, S, %dx, y0, cell, %mask)
    %rem2 = udiv i64 rem, 10
    %idx2 = add i64 idx, 1
    br loop(%rem2, %idx2, buf, S, n, cell, adv, x0, y0)
  fin():
    ret
}

; tone-map one pixel: deep blue field, travelling wave-sheet glow that
; grows with the count, blue particle light, white-hot cores.
fn shade(ptr, i64, i64, i64, ptr, f64, f64) -> void {
  entry(buf: ptr, S: i64, x: i64, y: i64, row: ptr, tf: f64, ea: f64):
    %idx0 = mul i64 y, S
    %idx = add i64 %idx0, x
    %cp = gep f64 buf, %idx
    %v = load f64, %cp
    %sf = sitofp f64 S
    %half = fmul f64 %sf, 0.5
    %xf = sitofp f64 x
    %yf = sitofp f64 y
    %dx0 = fsub f64 %xf, %half
    %dx = fdiv f64 %dx0, %half
    %dy0 = fsub f64 %yf, %half
    %dy = fdiv f64 %dy0, %half
    %dx2 = fmul f64 %dx, %dx
    %dy2 = fmul f64 %dy, %dy
    %d2 = fadd f64 %dx2, %dy2
    %d = call f64 sqrt(%d2)
    %t0 = fsub f64 1.0, %d
    %t = call f64 clamp01(%t0)
    %t2 = fmul f64 %t, %t
    %bgr0 = fmul f64 %t2, 10.0
    %bgr = fadd f64 %bgr0, 4.0
    %bgg0 = fmul f64 %t2, 20.0
    %bgg = fadd f64 %bgg0, 10.0
    %bgb0 = fmul f64 %t2, 46.0
    %bgb = fadd f64 %bgb0, 30.0
    %ws0 = fmul f64 %d, 5.0
    %ws1 = fmul f64 tf, 14.0
    %ws2 = fsub f64 %ws0, %ws1
    %ws3 = fmul f64 %ws2, 6.283185307179586
    %ws4 = call f64 sin(%ws3)
    %ws5 = fmul f64 %ws4, 0.5
    %ws6 = fadd f64 %ws5, 0.5
    %wp2 = fmul f64 %ws6, %ws6
    %wp4 = fmul f64 %wp2, %wp2
    %wp6 = fmul f64 %wp4, %wp2
    %wfall = fsub f64 1.0, %d
    %wfc = call f64 clamp01(%wfall)
    %wamp0 = fmul f64 ea, %wp6
    %wamp = fmul f64 %wamp0, %wfc
    %war = fmul f64 %wamp, 14.0
    %wag = fmul f64 %wamp, 34.0
    %wab = fmul f64 %wamp, 84.0
    %e0 = fmul f64 %v, 1.5
    %e1 = fsub f64 0.0, %e0
    %e2 = call f64 exp(%e1)
    %g = fsub f64 1.0, %e2
    %h = fmul f64 %g, %g
    %ar = fmul f64 %g, 46.0
    %ag = fmul f64 %g, 118.0
    %ab = fmul f64 %g, 255.0
    %hr = fmul f64 %h, 175.0
    %hg = fmul f64 %h, 205.0
    %hb = fmul f64 %h, 255.0
    %vg0 = fmul f64 %d2, 0.30
    %vg = fsub f64 1.0, %vg0
    %rr0 = fadd f64 %bgr, %ar
    %rr1 = fadd f64 %rr0, %hr
    %rr2 = fadd f64 %rr1, %war
    %rr = fmul f64 %rr2, %vg
    %gg0 = fadd f64 %bgg, %ag
    %gg1 = fadd f64 %gg0, %hg
    %gg2 = fadd f64 %gg1, %wag
    %gg = fmul f64 %gg2, %vg
    %bb0 = fadd f64 %bgb, %ab
    %bb1 = fadd f64 %bb0, %hb
    %bb2 = fadd f64 %bb1, %wab
    %bb = fmul f64 %bb2, %vg
    %rc = call f64 clamp255(%rr)
    %gc = call f64 clamp255(%gg)
    %bc = call f64 clamp255(%bb)
    %ri = fptosi i64 %rc
    %gi = fptosi i64 %gc
    %bi = fptosi i64 %bc
    %o0 = mul i64 x, 3
    %rp = gep i8 row, %o0
    %r8 = trunc i8 %ri
    store i8 %rp, %r8
    %o1 = add i64 %o0, 1
    %gp = gep i8 row, %o1
    %g8 = trunc i8 %gi
    store i8 %gp, %g8
    %o2 = add i64 %o0, 2
    %bp = gep i8 row, %o2
    %b8 = trunc i8 %bi
    store i8 %bp, %b8
    ret
}

fn render_row(ptr, i64, i64, ptr, f64, f64) -> void {
  entry(buf: ptr, S: i64, y: i64, row: ptr, tf: f64, ea: f64):
    br loop(0, buf, S, y, row, tf, ea)
  loop(x: i64, buf: ptr, S: i64, y: i64, row: ptr, tf: f64, ea: f64):
    %done = icmp.sge i64 x, S
    condbr %done, fin(), body(x, buf, S, y, row, tf, ea)
  body(x: i64, buf: ptr, S: i64, y: i64, row: ptr, tf: f64, ea: f64):
    call void shade(buf, S, x, y, row, tf, ea)
    %x2 = add i64 x, 1
    br loop(%x2, buf, S, y, row, tf, ea)
  fin():
    ret
}

fn main(i32, ptr) -> i32 {
  entry(argc: i32, argv: ptr):
    %h1 = icmp.sge i32 argc, 2
    condbr %h1, a1(argc, argv), setup(0, 1728, 960)
  a1(argc: i32, argv: ptr):
    %p1 = gep ptr argv, 1
    %s1 = load ptr, %p1
    %av1 = call i32 atoi(%s1)
    %fr = sext i64 %av1
    %h2 = icmp.sge i32 argc, 3
    condbr %h2, a2(argc, argv, %fr), setup(%fr, 1728, 960)
  a2(argc: i32, argv: ptr, fr: i64):
    %p2 = gep ptr argv, 2
    %s2 = load ptr, %p2
    %av2 = call i32 atoi(%s2)
    %tot = sext i64 %av2
    %h3 = icmp.sge i32 argc, 4
    condbr %h3, a3(argv, fr, %tot), setup(fr, %tot, 960)
  a3(argv: ptr, fr: i64, tot: i64):
    %p3 = gep ptr argv, 3
    %s3 = load ptr, %p3
    %av3 = call i32 atoi(%s3)
    %sz = sext i64 %av3
    br setup(fr, tot, %sz)
  setup(fr: i64, tot: i64, S: i64):
    %npix = mul i64 S, S
    %nbytes = mul i64 %npix, 8
    %buf = call ptr malloc(%nbytes)
    call void zero_canvas(%buf, %npix)
    %rowb = mul i64 S, 3
    %row = call ptr malloc(%rowb)
    %frf = sitofp f64 fr
    %totf = sitofp f64 tot
    %ph = fdiv f64 %frf, %totf
    %sf2 = sitofp f64 S
    %ex = fmul f64 %ph, 5.703782474656201
    %eN = call f64 exp(%ex)
    %nf = fmul f64 %eN, 10000.0
    %N = fptosi i64 %nf
    %rot = fmul f64 %ph, 12.566370614359172
    %br0 = fmul f64 %ph, 18.84955592153876
    %br1 = call f64 sin(%br0)
    %br2 = fmul f64 %br1, 0.03
    %breath = fadd f64 %br2, 1.0
    %ratio = fdiv f64 10000.0, %nf
    %pw = call f64 pow(%ratio, 0.62)
    %ws0 = fmul f64 %pw, 1.35
    %sfr = fdiv f64 %sf2, 960.0
    %sff = fmul f64 %sfr, %sfr
    %wscale = fmul f64 %ws0, %sff
    %ea0 = fmul f64 %ph, 0.45
    %ea = fadd f64 %ea0, 0.25
    call void particle_pass(%buf, S, %N, %rot, %breath, %wscale)
    call void draw_number(%buf, S, %N)
    call void wh1()
    call void print_u64(S)
    call void wsp()
    call void print_u64(S)
    call void wh2()
    br rows(0, %buf, S, %row, %rowb, %ph, %ea)
  rows(y: i64, buf: ptr, S: i64, row: ptr, rowb: i64, ph: f64, ea: f64):
    %done = icmp.sge i64 y, S
    condbr %done, fin(), rbody(y, buf, S, row, rowb, ph, ea)
  rbody(y: i64, buf: ptr, S: i64, row: ptr, rowb: i64, ph: f64, ea: f64):
    call void render_row(buf, S, y, row, ph, ea)
    %w = call i64 write(1, row, rowb)
    %y2 = add i64 y, 1
    br rows(%y2, buf, S, row, rowb, ph, ea)
  fin():
    ret 0
}
"""

GLYPH_ROWS = {
    0: ["111", "101", "101", "101", "111"],
    1: ["010", "110", "010", "010", "111"],
    2: ["111", "001", "111", "100", "111"],
    3: ["111", "001", "111", "001", "111"],
    4: ["101", "101", "111", "001", "001"],
    5: ["111", "100", "111", "001", "111"],
    6: ["111", "100", "111", "101", "111"],
    7: ["111", "001", "010", "010", "010"],
    8: ["111", "101", "111", "101", "111"],
    9: ["111", "101", "111", "001", "111"],
}

def glyph_mask(rows):
    bits = "".join(rows)
    m = 0
    for j, ch in enumerate(bits):
        if ch == "1":
            m |= 1 << (14 - j)
    return m

GLYPHS = ", ".join(str(glyph_mask(GLYPH_ROWS[d])) for d in range(10))
SRC = SRC.replace("@@GLYPHS@@", GLYPHS)


def build_splat():
    taps = [(0,0,1.0),(1,0,0.35),(-1,0,0.35),(0,1,0.35),(0,-1,0.35),
            (1,1,0.15),(1,-1,0.15),(-1,1,0.15),(-1,-1,0.15)]
    L = []
    L.append("; soft 3x3 stamp into the float canvas at (ix, iy); caller")
    L.append("; guarantees 1 <= ix, iy <= S-2.")
    L.append("fn splat(ptr, i64, i64, i64, f64) -> void {")
    L.append("  entry(buf: ptr, S: i64, ix: i64, iy: i64, w: f64):")
    L.append("    %row = mul i64 iy, S")
    L.append("    %c = add i64 %row, ix")
    L.append("    %rm1 = sub i64 %c, S")
    L.append("    %rp1 = add i64 %c, S")
    rows = {-1:"%rm1", 0:"%c", 1:"%rp1"}
    for i,(dx,dy,f) in enumerate(taps):
        base = rows[dy]
        if dx == 0: idx = base
        elif dx == 1: idx = f"%t{i}"; L.append(f"    {idx} = add i64 {base}, 1")
        else: idx = f"%t{i}"; L.append(f"    {idx} = sub i64 {base}, 1")
        if f == 1.0: wv = "w"
        else:
            wv = f"%w{i}"; L.append(f"    {wv} = fmul f64 w, {f}")
        L.append(f"    %a{i} = gep f64 buf, {idx}")
        L.append(f"    %v{i} = load f64, %a{i}")
        L.append(f"    %n{i} = fadd f64 %v{i}, {wv}")
        L.append(f"    store f64 %a{i}, %n{i}")
    L.append("    ret")
    L.append("}")
    return "\n".join(L)

SRC = SRC.replace("@@SPLAT@@", build_splat())

def seed_constants(text):
    """Seed every literal of a function as an explicit const in its entry
    block: Krell hash-conses pure ops per function, so a literal first
    materialized in a non-dominating block poisons sibling uses."""
    lines = text.split("\n")
    res = []
    i = 0
    while i < len(lines):
        line = lines[i]
        res.append(line)
        if line.startswith("fn "):
            body = [line]
            i += 1
            while i < len(lines) and lines[i] != "}":
                body.append(lines[i])
                res.append(lines[i])
                i += 1
            if i < len(lines):
                body.append("}")
                res.append("}")
            btext = "\n".join(body)
            ints = set()
            for m in re.finditer(r"(?<![A-Za-z0-9_.%])-?\d+(?![0-9.])", btext):
                ints.add(int(m.group(0)))
            floats = set()
            for m in re.finditer(r"(?<![A-Za-z0-9_.%])-?\d+\.\d+(?:e[+-]?\d+)?", btext):
                floats.add(m.group(0))
            seeds = []
            k = 0
            for v in sorted(ints):
                for ty in ("i64", "i32", "i8"):
                    seeds.append(f"    %_s{k} = iconst {ty} {v}")
                    k += 1
            for v in sorted(floats):
                seeds.append(f"    %_s{k} = fconst f64 {v}")
                k += 1
            if seeds:
                for j in range(len(res) - 1, -1, -1):
                    if re.match(r"\s+entry\(.*\):\s*$", res[j]):
                        res[j + 1:j + 1] = seeds
                        break
        i += 1
    return "\n".join(res)

path = pathlib.Path(__file__).with_name("livecount.krell")
path.write_text(seed_constants(SRC.strip() + "\n"))
print("wrote", path)
