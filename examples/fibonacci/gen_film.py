#!/usr/bin/env python3
"""Generator for fibfilm.krell - Fibonacci phyllotaxis + golden spiral,
computed per frame and per pixel entirely in Krell.
Host services only: write, malloc, atoi, sin, cos, sqrt, exp.
Output: one PPM (P6) frame on stdout. Args: [frame] [total] [size].
Animation is periodic: rotation makes exactly one full turn over the
film, breathing is 2 cycles, shimmer 5 cycles - frame `total` == frame 0.
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

data dh1: i8 = { 80, 54, 10 }
data dsp: i8 = { 32 }
data dh2: i8 = { 10, 50, 53, 53, 10 }

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

; 2584 = F(18) phyllotaxis seeds: angle k * golden angle, radius ~ sqrt(k).
fn seed_pass(ptr, i64, f64, f64, f64) -> void {
  entry(buf: ptr, S: i64, rot: f64, pulse: f64, ph: f64):
    %sf = sitofp f64 S
    %rmax = fmul f64 %sf, 0.46
    %half = fmul f64 %sf, 0.5
    br loop(0, buf, S, rot, pulse, ph, %rmax, %half)
  loop(k: i64, buf: ptr, S: i64, rot: f64, pulse: f64, ph: f64, rmax: f64, half: f64):
    %done = icmp.sge i64 k, 2584
    condbr %done, fin(), body(k, buf, S, rot, pulse, ph, rmax, half)
  body(k: i64, buf: ptr, S: i64, rot: f64, pulse: f64, ph: f64, rmax: f64, half: f64):
    %kf = sitofp f64 k
    %kp = fadd f64 %kf, 0.5
    %fr0 = fdiv f64 %kp, 2584.0
    %fr = call f64 sqrt(%fr0)
    %rr0 = fmul f64 %fr, rmax
    %r = fmul f64 %rr0, pulse
    %ang0 = fmul f64 %kf, 2.39996322972865332
    %ang = fadd f64 %ang0, rot
    %ca = call f64 cos(%ang)
    %sa = call f64 sin(%ang)
    %dx = fmul f64 %r, %ca
    %dy = fmul f64 %r, %sa
    %x = fadd f64 half, %dx
    %y = fadd f64 half, %dy
    %sh0 = fmul f64 ph, 31.41592653589793
    %sh1 = fmul f64 %kf, 0.6180339887498949
    %sh2 = fadd f64 %sh0, %sh1
    %sh = call f64 sin(%sh2)
    %w0 = fmul f64 %sh, 0.30
    %w1 = fadd f64 %w0, 1.0
    %fall0 = fmul f64 %fr, 0.55
    %fall = fsub f64 1.18, %fall0
    %w = fmul f64 %w1, %fall
    %ix = fptosi i64 %x
    %iy = fptosi i64 %y
    call void splat(buf, S, %ix, %iy, %w)
    %k2 = add i64 k, 1
    br loop(%k2, buf, S, rot, pulse, ph, rmax, half)
  fin():
    ret
}

; the golden log spiral: radius grows by phi every half turn,
; sampled 9000 times, counter-rotating against the seed field.
fn spiral_pass(ptr, i64, f64) -> void {
  entry(buf: ptr, S: i64, rot: f64):
    %sf = sitofp f64 S
    %rmax = fmul f64 %sf, 0.46
    %half = fmul f64 %sf, 0.5
    %rscale = fdiv f64 %rmax, 147.1
    br loop(0, buf, S, rot, %rmax, %half, %rscale)
  loop(s: i64, buf: ptr, S: i64, rot: f64, rmax: f64, half: f64, rscale: f64):
    %done = icmp.sge i64 s, 9000
    condbr %done, fin(), body(s, buf, S, rot, rmax, half, rscale)
  body(s: i64, buf: ptr, S: i64, rot: f64, rmax: f64, half: f64, rscale: f64):
    %sf2 = sitofp f64 s
    %th = fmul f64 %sf2, 0.00362
    %ex0 = fmul f64 %th, 0.1532
    %ex = call f64 exp(%ex0)
    %r = fmul f64 %ex, rscale
    %ang = fsub f64 %th, rot
    %ca = call f64 cos(%ang)
    %sa = call f64 sin(%ang)
    %dx = fmul f64 %r, %ca
    %dy = fmul f64 %r, %sa
    %x = fadd f64 half, %dx
    %y = fadd f64 half, %dy
    %fd0 = fdiv f64 %r, rmax
    %fd1 = fsub f64 1.0, %fd0
    %fd2 = fmul f64 %fd1, 0.13
    %w = fadd f64 %fd2, 0.03
    %ix = fptosi i64 %x
    %iy = fptosi i64 %y
    call void splat(buf, S, %ix, %iy, %w)
    %s2 = add i64 s, 1
    br loop(%s2, buf, S, rot, rmax, half, rscale)
  fin():
    ret
}

; tone-map one pixel: deep blue field + gold light + white-hot core.
fn shade(ptr, i64, i64, i64, ptr) -> void {
  entry(buf: ptr, S: i64, x: i64, y: i64, row: ptr):
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
    %bgr0 = fmul f64 %t2, 18.0
    %bgr = fadd f64 %bgr0, 5.0
    %bgg0 = fmul f64 %t2, 22.0
    %bgg = fadd f64 %bgg0, 8.0
    %bgb0 = fmul f64 %t2, 40.0
    %bgb = fadd f64 %bgb0, 26.0
    %e0 = fmul f64 %v, 1.55
    %e1 = fsub f64 0.0, %e0
    %e2 = call f64 exp(%e1)
    %g = fsub f64 1.0, %e2
    %tr0 = fmul f64 %d, 0.25
    %tr = fsub f64 1.05, %tr0
    %tb0 = fmul f64 %d, 0.5
    %tb = fadd f64 %tb0, 0.8
    %ar0 = fmul f64 %g, 235.0
    %ar = fmul f64 %ar0, %tr
    %ag = fmul f64 %g, 165.0
    %ab0 = fmul f64 %g, 70.0
    %ab = fmul f64 %ab0, %tb
    %h = fmul f64 %g, %g
    %hr = fmul f64 %h, 90.0
    %hg = fmul f64 %h, 85.0
    %hb = fmul f64 %h, 80.0
    %vg0 = fmul f64 %d2, 0.30
    %vg = fsub f64 1.0, %vg0
    %rr0 = fadd f64 %bgr, %ar
    %rr1 = fadd f64 %rr0, %hr
    %rr = fmul f64 %rr1, %vg
    %gg0 = fadd f64 %bgg, %ag
    %gg1 = fadd f64 %gg0, %hg
    %gg = fmul f64 %gg1, %vg
    %bb0 = fadd f64 %bgb, %ab
    %bb1 = fadd f64 %bb0, %hb
    %bb = fmul f64 %bb1, %vg
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

fn render_row(ptr, i64, i64, ptr) -> void {
  entry(buf: ptr, S: i64, y: i64, row: ptr):
    br loop(0, buf, S, y, row)
  loop(x: i64, buf: ptr, S: i64, y: i64, row: ptr):
    %done = icmp.sge i64 x, S
    condbr %done, fin(), body(x, buf, S, y, row)
  body(x: i64, buf: ptr, S: i64, y: i64, row: ptr):
    call void shade(buf, S, x, y, row)
    %x2 = add i64 x, 1
    br loop(%x2, buf, S, y, row)
  fin():
    ret
}

fn main(i32, ptr) -> i32 {
  entry(argc: i32, argv: ptr):
    %h1 = icmp.sge i32 argc, 2
    condbr %h1, a1(argc, argv), setup(0, 288, 960)
  a1(argc: i32, argv: ptr):
    %p1 = gep ptr argv, 1
    %s1 = load ptr, %p1
    %av1 = call i32 atoi(%s1)
    %fr = sext i64 %av1
    %h2 = icmp.sge i32 argc, 3
    condbr %h2, a2(argc, argv, %fr), setup(%fr, 288, 960)
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
    %rot = fmul f64 %ph, 6.283185307179586
    %br0 = fmul f64 %ph, 12.566370614359172
    %br1 = call f64 sin(%br0)
    %br2 = fmul f64 %br1, 0.035
    %pulse = fadd f64 %br2, 1.0
    call void seed_pass(%buf, S, %rot, %pulse, %ph)
    call void spiral_pass(%buf, S, %rot)
    call void wh1()
    call void print_u64(S)
    call void wsp()
    call void print_u64(S)
    call void wh2()
    br rows(0, %buf, S, %row, %rowb)
  rows(y: i64, buf: ptr, S: i64, row: ptr, rowb: i64):
    %done = icmp.sge i64 y, S
    condbr %done, fin(), rbody(y, buf, S, row, rowb)
  rbody(y: i64, buf: ptr, S: i64, row: ptr, rowb: i64):
    call void render_row(buf, S, y, row)
    %w = call i64 write(1, row, rowb)
    %y2 = add i64 y, 1
    br rows(%y2, buf, S, row, rowb)
  fin():
    ret 0
}
"""


def build_splat():
    taps = [(0,0,1.0),(1,0,0.45),(-1,0,0.45),(0,1,0.45),(0,-1,0.45),
            (1,1,0.22),(1,-1,0.22),(-1,1,0.22),(-1,-1,0.22),
            (2,0,0.10),(-2,0,0.10),(0,2,0.10),(0,-2,0.10),
            (2,1,0.05),(2,-1,0.05),(-2,1,0.05),(-2,-1,0.05),
            (1,2,0.05),(1,-2,0.05),(-1,2,0.05),(-1,-2,0.05),
            (2,2,0.03),(2,-2,0.03),(-2,2,0.03),(-2,-2,0.03)]
    L = []
    L.append("; soft 5x5 stamp into the float canvas at (ix, iy); caller")
    L.append("; guarantees 2 <= ix, iy <= S-3.")
    L.append("fn splat(ptr, i64, i64, i64, f64) -> void {")
    L.append("  entry(buf: ptr, S: i64, ix: i64, iy: i64, w: f64):")
    L.append("    %row = mul i64 iy, S")
    L.append("    %c = add i64 %row, ix")
    L.append("    %s2 = mul i64 S, 2")
    L.append("    %rm2 = sub i64 %c, %s2")
    L.append("    %rm1 = sub i64 %c, S")
    L.append("    %rp1 = add i64 %c, S")
    L.append("    %rp2 = add i64 %c, %s2")
    rows = {-2:"%rm2", -1:"%rm1", 0:"%c", 1:"%rp1", 2:"%rp2"}
    for i,(dx,dy,f) in enumerate(taps):
        base = rows[dy]
        if dx == 0: idx = base
        elif dx == 1: idx = f"%t{i}"; L.append(f"    {idx} = add i64 {base}, 1")
        elif dx == -1: idx = f"%t{i}"; L.append(f"    {idx} = sub i64 {base}, 1")
        elif dx == 2: idx = f"%t{i}"; L.append(f"    {idx} = add i64 {base}, 2")
        else: idx = f"%t{i}"; L.append(f"    {idx} = sub i64 {base}, 2")
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

path = pathlib.Path(__file__).with_name("fibfilm.krell")
path.write_text(seed_constants(SRC.strip() + "\n"))
print("wrote", path)
