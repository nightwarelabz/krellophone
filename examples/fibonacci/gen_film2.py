#!/usr/bin/env python3
"""Generator for fibfilm2.krell - the Fibonacci film in bright blue,
audio-reactive light. The Moonlight score's event tables are embedded
as data; per frame the Krell program itself analyzes the music
(band energies + onset strength from the note events), and every
phyllotaxis dot pulsates with its band's energy through expanding
anamorphic waves, plus a horizontal anamorphic streak at the core.
Host services only: write, malloc, atoi, sin, cos, sqrt, exp.
Output: one PPM (P6) frame on stdout. Args: [frame] [total] [size].
"""
import pathlib, re, json

EV = json.load(open(pathlib.Path(__file__).with_name('../moonlight/events.json'))) \
    if False else json.load(open('/home/hatch/workspace/moonlight/events.json'))
events = EV['events']
NEV = len(events)

def decl(name, ty, vals, per=16):
    out = [f'data {name}: {ty} = {{']
    for i in range(0, len(vals), per):
        out.append('  ' + ', '.join(str(v) for v in vals[i:i+per]) + (',' if i + per < len(vals) else ''))
    out.append('}')
    return '\n'.join(out)

TABLES = '\n'.join([
    decl('evstart', 'i32', [e[0] for e in events]),
    decl('evdur', 'i32', [e[1] for e in events]),
    decl('evnote', 'i8', [e[2] for e in events]),
    decl('evvel', 'i8', [e[3] for e in events]),
    decl('evcount', 'i32', [NEV]),
])

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
@@TABLES@@

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

; analyze the music at this frame, in Krell, from the note tables.
; glo: [0]=E low [1]=E mid [2]=E high [3]=E all [4]=onset [5]=t seconds
fn analyze(i64, ptr) -> void {
  entry(fr: i64, glo: ptr):
    %ps = dataptr 3
    %pd = dataptr 4
    %pn = dataptr 5
    %pv = dataptr 6
    %pc = dataptr 7
    %cp = gep i32 %pc, 0
    %cnt32 = load i32, %cp
    %cnt = sext i64 %cnt32
    %frf = sitofp f64 fr
    %pos = fmul f64 %frf, 1837.5
    %tf = fdiv f64 %frf, 24.0
    br loop(0, %cnt, %pos, %tf, glo, %ps, %pd, %pn, %pv, 0.0, 0.0, 0.0, 0.0)
  loop(i: i64, cnt: i64, pos: f64, tf: f64, glo: ptr, ps: ptr, pd: ptr, pn: ptr, pv: ptr, al: f64, am: f64, ah: f64, ons: f64):
    %done = icmp.sge i64 i, cnt
    condbr %done, fin(cnt, pos, tf, glo, ps, pd, pn, pv, al, am, ah, ons), body(i, cnt, pos, tf, glo, ps, pd, pn, pv, al, am, ah, ons)
  body(i: i64, cnt: i64, pos: f64, tf: f64, glo: ptr, ps: ptr, pd: ptr, pn: ptr, pv: ptr, al: f64, am: f64, ah: f64, ons: f64):
    %sp = gep i32 ps, i
    %st32 = load i32, %sp
    %st = sitofp f64 %st32
    %age0 = fsub f64 pos, %st
    %age = fdiv f64 %age0, 44100.0
    %future = fcmp.olt f64 %age, 0.0
    condbr %future, fin(cnt, pos, tf, glo, ps, pd, pn, pv, al, am, ah, ons), act(i, cnt, pos, tf, glo, ps, pd, pn, pv, al, am, ah, ons, %age)
  act(i: i64, cnt: i64, pos: f64, tf: f64, glo: ptr, ps: ptr, pd: ptr, pn: ptr, pv: ptr, al: f64, am: f64, ah: f64, ons: f64, age: f64):
    %dp = gep i32 pd, i
    %du32 = load i32, %dp
    %du = sitofp f64 %du32
    %durs = fdiv f64 %du, 44100.0
    %win = fadd f64 %durs, 4.0
    %inwin = fcmp.olt f64 age, %win
    %np = gep i8 pn, i
    %n8 = load i8, %np
    %n = sext i64 %n8
    %nf = sitofp f64 %n
    %islow = icmp.slt i64 %n, 48
    %ishigh = icmp.sge i64 %n, 72
    %tau0 = select f64 %ishigh, 0.7, 1.1
    %tau = select f64 %islow, 1.8, %tau0
    %vp = gep i8 pv, i
    %v8 = load i8, %vp
    %v = sext i64 %v8
    %vf = sitofp f64 %v
    %veln = fdiv f64 %vf, 114.0
    %w = fmul f64 %veln, %veln
    %na = fsub f64 0.0, %age
    %ex0 = fdiv f64 %na, %tau
    %env = call f64 exp(%ex0)
    %contrib0 = fmul f64 %w, %env
    %contrib = select f64 %inwin, %contrib0, 0.0
    %ml64 = zext i64 %islow
    %ml = sitofp f64 %ml64
    %mh64 = zext i64 %ishigh
    %mh = sitofp f64 %mh64
    %notl = fsub f64 1.0, %ml
    %noth = fsub f64 1.0, %mh
    %mm = fmul f64 %notl, %noth
    %al2 = fadd f64 al, %contrib * %ml
    %am2 = fadd f64 am, %contrib * %mm
    %ah2 = fadd f64 ah, %contrib * %mh
    %isOn = fcmp.olt f64 age, 0.35
    %of0 = fdiv f64 age, 0.35
    %of1 = fsub f64 1.0, %of0
    %oc = fmul f64 %w, %of1
    %oc2 = select f64 %isOn, %oc, 0.0
    %ons2 = fadd f64 ons, %oc2
    %i2 = add i64 i, 1
    br loop(%i2, cnt, pos, tf, glo, ps, pd, pn, pv, %al2, %am2, %ah2, %ons2)
  fin(cnt: i64, pos: f64, tf: f64, glo: ptr, ps: ptr, pd: ptr, pn: ptr, pv: ptr, al: f64, am: f64, ah: f64, ons: f64):
    %el0 = fdiv f64 al, 1.35
    %el = call f64 clamp01(%el0)
    %em0 = fdiv f64 am, 2.4
    %em = call f64 clamp01(%em0)
    %eh0 = fdiv f64 ah, 0.95
    %eh = call f64 clamp01(%eh0)
    %eo0 = fdiv f64 ons, 1.8
    %eo = call f64 clamp01(%eo0)
    %ea0 = fadd f64 %el, %em
    %ea1 = fadd f64 %ea0, %eh
    %ea2 = fmul f64 %ea1, 0.55
    %ea = call f64 clamp01(%ea2)
    %g0 = gep f64 glo, 0
    store f64 %g0, %el
    %g1 = gep f64 glo, 1
    store f64 %g1, %em
    %g2 = gep f64 glo, 2
    store f64 %g2, %eh
    %g3 = gep f64 glo, 3
    store f64 %g3, %ea
    %g4 = gep f64 glo, 4
    store f64 %g4, %eo
    %g5 = gep f64 glo, 5
    store f64 %g5, tf
    ret
}

; 2584 = F(18) phyllotaxis seeds, each pulsating with its register band.
fn seed_pass(ptr, i64, f64, ptr) -> void {
  entry(buf: ptr, S: i64, rot: f64, glo: ptr):
    %sf = sitofp f64 S
    %rmax = fmul f64 %sf, 0.46
    %half = fmul f64 %sf, 0.5
    %e0p = gep f64 glo, 0
    %el = load f64, %e0p
    %e1p = gep f64 glo, 1
    %em = load f64, %e1p
    %e2p = gep f64 glo, 2
    %eh = load f64, %e2p
    %e5p = gep f64 glo, 5
    %tf = load f64, %e5p
    br loop(0, buf, S, rot, %rmax, %half, %el, %em, %eh, %tf)
  loop(k: i64, buf: ptr, S: i64, rot: f64, rmax: f64, half: f64, el: f64, em: f64, eh: f64, tf: f64):
    %done = icmp.sge i64 k, 2584
    condbr %done, fin(), body(k, buf, S, rot, rmax, half, el, em, eh, tf)
  body(k: i64, buf: ptr, S: i64, rot: f64, rmax: f64, half: f64, el: f64, em: f64, eh: f64, tf: f64):
    %kf = sitofp f64 k
    %kp = fadd f64 %kf, 0.5
    %fr0 = fdiv f64 %kp, 2584.0
    %fr = call f64 sqrt(%fr0)
    %r = fmul f64 %fr, rmax
    %ang0 = fmul f64 %kf, 2.39996322972865332
    %ang = fadd f64 %ang0, rot
    %ca = call f64 cos(%ang)
    %sa = call f64 sin(%ang)
    %dx = fmul f64 %r, %ca
    %dy = fmul f64 %r, %sa
    %x = fadd f64 half, %dx
    %y = fadd f64 half, %dy
    %lo = fcmp.olt f64 %fr, 0.5
    %b10 = fsub f64 em, el
    %b11 = fmul f64 %fr, 2.0
    %b12 = fmul f64 %b10, %b11
    %b1 = fadd f64 el, %b12
    %b20 = fsub f64 eh, em
    %b21 = fsub f64 %fr, 0.5
    %b22 = fmul f64 %b21, 2.0
    %b23 = fmul f64 %b20, %b22
    %b2 = fadd f64 em, %b23
    %eb = select f64 %lo, %b1, %b2
    %wv0 = fmul f64 %fr, 3.0
    %wv1 = fmul f64 tf, 0.45
    %wv2 = fsub f64 %wv0, %wv1
    %wv3 = fmul f64 %wv2, 6.283185307179586
    %wv4 = call f64 sin(%wv3)
    %wv5 = fmul f64 %wv4, 0.5
    %wv = fadd f64 %wv5, 0.5
    %br0 = fmul f64 %eb, 0.95
    %br1 = fadd f64 %br0, 1.05
    %br2 = fmul f64 %br1, %wv
    %br3 = fmul f64 %eb, %br2
    %bright = fadd f64 %br3, 0.30
    %tw0 = fmul f64 tf, 0.9
    %tw1 = fmul f64 %kf, 0.6180339887498949
    %tw2 = fadd f64 %tw0, %tw1
    %tw3 = call f64 sin(%tw2)
    %tw4 = fmul f64 %tw3, 0.15
    %tw = fadd f64 %tw4, 0.9
    %fall0 = fmul f64 %fr, 0.55
    %fall = fsub f64 1.18, %fall0
    %w0 = fmul f64 %tw, %fall
    %w = fmul f64 %w0, %bright
    %ix = fptosi i64 %x
    %iy = fptosi i64 %y
    call void splat(buf, S, %ix, %iy, %w)
    %k2 = add i64 k, 1
    br loop(%k2, buf, S, rot, rmax, half, el, em, eh, tf)
  fin():
    ret
}

; the golden log spiral, breathing with the total musical energy.
fn spiral_pass(ptr, i64, f64, ptr) -> void {
  entry(buf: ptr, S: i64, rot: f64, glo: ptr):
    %sf = sitofp f64 S
    %rmax = fmul f64 %sf, 0.46
    %half = fmul f64 %sf, 0.5
    %rscale = fdiv f64 %rmax, 147.1
    %e3p = gep f64 glo, 3
    %ea = load f64, %e3p
    %gain0 = fmul f64 %ea, 0.95
    %gain = fadd f64 %gain0, 0.30
    br loop(0, buf, S, rot, %rmax, %half, %rscale, %gain)
  loop(s: i64, buf: ptr, S: i64, rot: f64, rmax: f64, half: f64, rscale: f64, gain: f64):
    %done = icmp.sge i64 s, 9000
    condbr %done, fin(), body(s, buf, S, rot, rmax, half, rscale, gain)
  body(s: i64, buf: ptr, S: i64, rot: f64, rmax: f64, half: f64, rscale: f64, gain: f64):
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
    %w0 = fadd f64 %fd2, 0.03
    %w = fmul f64 %w0, gain
    %ix = fptosi i64 %x
    %iy = fptosi i64 %y
    call void splat(buf, S, %ix, %iy, %w)
    %s2 = add i64 s, 1
    br loop(%s2, buf, S, rot, rmax, half, rscale, gain)
  fin():
    ret
}

; one pixel: deep blue field, anamorphic wave sheets, the horizontal
; anamorphic streak through the core, and the blue dot light itself.
fn shade(ptr, i64, i64, i64, ptr, ptr) -> void {
  entry(buf: ptr, S: i64, x: i64, y: i64, row: ptr, glo: ptr):
    %idx0 = mul i64 y, S
    %idx = add i64 %idx0, x
    %cp = gep f64 buf, %idx
    %v = load f64, %cp
    %e3p = gep f64 glo, 3
    %ea = load f64, %e3p
    %e4p = gep f64 glo, 4
    %eo = load f64, %e4p
    %e5p = gep f64 glo, 5
    %tf = load f64, %e5p
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
    %ws0 = fmul f64 %d, 4.0
    %ws1 = fmul f64 tf, 0.8
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
    %wamp0 = fmul f64 %ea, %wp6
    %wamp = fmul f64 %wamp0, %wfc
    %wab = fmul f64 %wamp, 30.0
    %wag = fmul f64 %wamp, 12.0
    %dy9 = fmul f64 %dy2, 900.0
    %ndy = fsub f64 0.0, %dy9
    %sexp = call f64 exp(%ndy)
    %adx = select f64 fcmp.olt f64 %dx, 0.0, %dx * -1.0, %dx
    %sden = fmul f64 %adx, 3.5
    %sden1 = fadd f64 %sden, 1.0
    %sf0 = fdiv f64 %sexp, %sden1
    %sg0 = fmul f64 %eo, 0.85
    %sg1 = fmul f64 %ea, 0.30
    %sg = fadd f64 %sg0, %sg1
    %sfac = fmul f64 %sf0, %sg
    %str = fmul f64 %sfac, 70.0
    %stg = fmul f64 %sfac, 120.0
    %stb = fmul f64 %sfac, 240.0
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
    %rr2 = fadd f64 %rr1, %str
    %rr = fmul f64 %rr2, %vg
    %gg0 = fadd f64 %bgg, %ag
    %gg1 = fadd f64 %gg0, %hg
    %gg2 = fadd f64 %gg1, %stg
    %gg3 = fadd f64 %gg2, %wag
    %gg = fmul f64 %gg3, %vg
    %bb0 = fadd f64 %bgb, %ab
    %bb1 = fadd f64 %bb0, %hb
    %bb2 = fadd f64 %bb1, %stb
    %bb3 = fadd f64 %bb2, %wab
    %bb = fmul f64 %bb3, %vg
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

fn render_row(ptr, i64, i64, ptr, ptr) -> void {
  entry(buf: ptr, S: i64, y: i64, row: ptr, glo: ptr):
    br loop(0, buf, S, y, row, glo)
  loop(x: i64, buf: ptr, S: i64, y: i64, row: ptr, glo: ptr):
    %done = icmp.sge i64 x, S
    condbr %done, fin(), body(x, buf, S, y, row, glo)
  body(x: i64, buf: ptr, S: i64, y: i64, row: ptr, glo: ptr):
    call void shade(buf, S, x, y, row, glo)
    %x2 = add i64 x, 1
    br loop(%x2, buf, S, y, row, glo)
  fin():
    ret
}

fn main(i32, ptr) -> i32 {
  entry(argc: i32, argv: ptr):
    %h1 = icmp.sge i32 argc, 2
    condbr %h1, a1(argc, argv), setup(0, 6696, 960)
  a1(argc: i32, argv: ptr):
    %p1 = gep ptr argv, 1
    %s1 = load ptr, %p1
    %av1 = call i32 atoi(%s1)
    %fr = sext i64 %av1
    %h2 = icmp.sge i32 argc, 3
    condbr %h2, a2(argc, argv, %fr), setup(%fr, 6696, 960)
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
    %glo = call ptr malloc(64)
    call void analyze(fr, %glo)
    %frf = sitofp f64 fr
    %totf = sitofp f64 tot
    %ph = fdiv f64 %frf, %totf
    %rot = fmul f64 %ph, 6.283185307179586
    call void seed_pass(%buf, S, %rot, %glo)
    call void spiral_pass(%buf, S, %rot, %glo)
    call void wh1()
    call void print_u64(S)
    call void wsp()
    call void print_u64(S)
    call void wh2()
    br rows(0, %buf, S, %row, %rowb, %glo)
  rows(y: i64, buf: ptr, S: i64, row: ptr, rowb: i64, glo: ptr):
    %done = icmp.sge i64 y, S
    condbr %done, fin(), rbody(y, buf, S, row, rowb, glo)
  rbody(y: i64, buf: ptr, S: i64, row: ptr, rowb: i64, glo: ptr):
    call void render_row(buf, S, y, row, glo)
    %w = call i64 write(1, row, rowb)
    %y2 = add i64 y, 1
    br rows(%y2, buf, S, row, rowb, glo)
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

src = SRC.replace("@@TABLES@@", TABLES).replace("@@SPLAT@@", build_splat())
# analyze uses inline operator form %contrib * %ml in three lines; expand
src = src.replace("%al2 = fadd f64 al, %contrib * %ml",
                  "%cl = fmul f64 %contrib, %ml\n    %al2 = fadd f64 al, %cl")
src = src.replace("%am2 = fadd f64 am, %contrib * %mm",
                  "%cm = fmul f64 %contrib, %mm\n    %am2 = fadd f64 am, %cm")
src = src.replace("%ah2 = fadd f64 ah, %contrib * %mh",
                  "%chv = fmul f64 %contrib, %mh\n    %ah2 = fadd f64 ah, %chv")
# shade: %adx line uses inline select+negation form; expand it
src = src.replace("%adx = select f64 fcmp.olt f64 %dx, 0.0, %dx * -1.0, %dx",
                  "%dxneg = fsub f64 0.0, %dx\n    %isneg = fcmp.olt f64 %dx, 0.0\n    %adx = select f64 %isneg, %dxneg, %dx")

path = pathlib.Path(__file__).with_name("fibfilm2.krell")
path.write_text(seed_constants(src.strip() + "\n"))
print("wrote", path, "events embedded:", NEV)
