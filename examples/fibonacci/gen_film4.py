#!/usr/bin/env python3
"""Generator for fibfilm4.krell - the Fibonacci film in bright blue,
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
    %i6 = gep f64 glo, 6
    store f64 %i6, -100.0
    %i7 = gep f64 glo, 7
    store f64 %i7, 0.0
    %i8 = gep f64 glo, 8
    store f64 %i8, -100.0
    %i9 = gep f64 glo, 9
    store f64 %i9, 0.0
    %i10 = gep f64 glo, 10
    store f64 %i10, -100.0
    %i11 = gep f64 glo, 11
    store f64 %i11, 0.0
    %i12 = gep f64 glo, 12
    store f64 %i12, -100.0
    %i13 = gep f64 glo, 13
    store f64 %i13, 0.0
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
    %isStrong = icmp.sge i64 %v, 82
    %isNew = fcmp.olt f64 age, 4.5
    %f1 = zext i64 %isStrong
    %f2 = zext i64 %isNew
    %fm = mul i64 %f1, %f2
    %fire = icmp.eq i64 %fm, 1
    condbr %fire, shift(i, cnt, pos, tf, glo, ps, pd, pn, pv, %al2, %am2, %ah2, %ons2, age, %veln), next(i, cnt, pos, tf, glo, ps, pd, pn, pv, %al2, %am2, %ah2, %ons2)
  shift(i: i64, cnt: i64, pos: f64, tf: f64, glo: ptr, ps: ptr, pd: ptr, pn: ptr, pv: ptr, al: f64, am: f64, ah: f64, ons: f64, age: f64, veln: f64):
    %q10 = gep f64 glo, 10
    %t3v = load f64, %q10
    %q11 = gep f64 glo, 11
    %s3v = load f64, %q11
    %q12 = gep f64 glo, 12
    store f64 %q12, %t3v
    %q13 = gep f64 glo, 13
    store f64 %q13, %s3v
    %q8 = gep f64 glo, 8
    %t2v = load f64, %q8
    %q9 = gep f64 glo, 9
    %s2v = load f64, %q9
    %q10b = gep f64 glo, 10
    store f64 %q10b, %t2v
    %q11b = gep f64 glo, 11
    store f64 %q11b, %s2v
    %q6 = gep f64 glo, 6
    %t1v = load f64, %q6
    %q7 = gep f64 glo, 7
    %s1v = load f64, %q7
    %q8b = gep f64 glo, 8
    store f64 %q8b, %t1v
    %q9b = gep f64 glo, 9
    store f64 %q9b, %s1v
    %ton = fsub f64 tf, age
    %q6b = gep f64 glo, 6
    store f64 %q6b, %ton
    %q7b = gep f64 glo, 7
    store f64 %q7b, veln
    br next(i, cnt, pos, tf, glo, ps, pd, pn, pv, al, am, ah, ons)
  next(i: i64, cnt: i64, pos: f64, tf: f64, glo: ptr, ps: ptr, pd: ptr, pn: ptr, pv: ptr, al: f64, am: f64, ah: f64, ons: f64):
    %i2 = add i64 i, 1
    br loop(%i2, cnt, pos, tf, glo, ps, pd, pn, pv, al, am, ah, ons)
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
    %rmax = fmul f64 %sf, 0.485
    %half = fmul f64 %sf, 0.5
    %e0p = gep f64 glo, 0
    %el = load f64, %e0p
    %e1p = gep f64 glo, 1
    %em = load f64, %e1p
    %e2p = gep f64 glo, 2
    %eh = load f64, %e2p
    %e5p = gep f64 glo, 5
    %tf = load f64, %e5p
    %w6 = gep f64 glo, 6
    %wt1 = load f64, %w6
    %w7 = gep f64 glo, 7
    %ws1 = load f64, %w7
    %w8 = gep f64 glo, 8
    %wt2 = load f64, %w8
    %w9 = gep f64 glo, 9
    %ws2 = load f64, %w9
    %w10 = gep f64 glo, 10
    %wt3 = load f64, %w10
    %w11 = gep f64 glo, 11
    %ws3 = load f64, %w11
    %w12 = gep f64 glo, 12
    %wt4 = load f64, %w12
    %w13 = gep f64 glo, 13
    %ws4 = load f64, %w13
    br loop(0, buf, S, rot, %rmax, %half, %el, %em, %eh, %tf, %wt1, %ws1, %wt2, %ws2, %wt3, %ws3, %wt4, %ws4)
  loop(k: i64, buf: ptr, S: i64, rot: f64, rmax: f64, half: f64, el: f64, em: f64, eh: f64, tf: f64, wt1: f64, ws1: f64, wt2: f64, ws2: f64, wt3: f64, ws3: f64, wt4: f64, ws4: f64):
    %done = icmp.sge i64 k, 2584
    condbr %done, fin(), body(k, buf, S, rot, rmax, half, el, em, eh, tf, wt1, ws1, wt2, ws2, wt3, ws3, wt4, ws4)
  body(k: i64, buf: ptr, S: i64, rot: f64, rmax: f64, half: f64, el: f64, em: f64, eh: f64, tf: f64, wt1: f64, ws1: f64, wt2: f64, ws2: f64, wt3: f64, ws3: f64, wt4: f64, ws4: f64):
    %kf = sitofp f64 k
    %kp = fadd f64 %kf, 0.5
    %fr0 = fdiv f64 %kp, 2584.0
    %fr = call f64 sqrt(%fr0)
    %r = fmul f64 %fr, rmax
    %ang0 = fmul f64 %kf, 2.39996322972865332
    %sh0 = fmul f64 %fr, 0.6
    %shf = fsub f64 1.3, %sh0
    %rotl = fmul f64 rot, %shf
    %ang = fadd f64 %ang0, %rotl
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
    %bright0 = fadd f64 %br3, 0.30
    %dt1 = fsub f64 tf, wt1
    %wr1 = fmul f64 %dt1, 0.5
    %wd1 = fsub f64 %fr, %wr1
    %wd21 = fmul f64 %wd1, %wd1
    %wg01 = fdiv f64 %wd21, 0.0012
    %wg11 = fsub f64 0.0, %wg01
    %wg1 = call f64 exp(%wg11)
    %wc01 = fmul f64 %dt1, 0.35
    %wc11 = fsub f64 0.0, %wc01
    %wc1 = call f64 exp(%wc11)
    %wv_1 = fmul f64 ws1, %wg1
    %wv1 = fmul f64 %wv_1, %wc1
    %dt2 = fsub f64 tf, wt2
    %wr2 = fmul f64 %dt2, 0.5
    %wd2 = fsub f64 %fr, %wr2
    %wd22 = fmul f64 %wd2, %wd2
    %wg02 = fdiv f64 %wd22, 0.0012
    %wg12 = fsub f64 0.0, %wg02
    %wg2 = call f64 exp(%wg12)
    %wc02 = fmul f64 %dt2, 0.35
    %wc12 = fsub f64 0.0, %wc02
    %wc2 = call f64 exp(%wc12)
    %wv_2 = fmul f64 ws2, %wg2
    %wv2 = fmul f64 %wv_2, %wc2
    %dt3 = fsub f64 tf, wt3
    %wr3 = fmul f64 %dt3, 0.5
    %wd3 = fsub f64 %fr, %wr3
    %wd23 = fmul f64 %wd3, %wd3
    %wg03 = fdiv f64 %wd23, 0.0012
    %wg13 = fsub f64 0.0, %wg03
    %wg3 = call f64 exp(%wg13)
    %wc03 = fmul f64 %dt3, 0.35
    %wc13 = fsub f64 0.0, %wc03
    %wc3 = call f64 exp(%wc13)
    %wv_3 = fmul f64 ws3, %wg3
    %wv3 = fmul f64 %wv_3, %wc3
    %dt4 = fsub f64 tf, wt4
    %wr4 = fmul f64 %dt4, 0.5
    %wd4 = fsub f64 %fr, %wr4
    %wd24 = fmul f64 %wd4, %wd4
    %wg04 = fdiv f64 %wd24, 0.0012
    %wg14 = fsub f64 0.0, %wg04
    %wg4 = call f64 exp(%wg14)
    %wc04 = fmul f64 %dt4, 0.35
    %wc14 = fsub f64 0.0, %wc04
    %wc4 = call f64 exp(%wc14)
    %wv_4 = fmul f64 ws4, %wg4
    %wv4 = fmul f64 %wv_4, %wc4
    %rsum0 = fadd f64 %wv1, %wv2
    %rsum1 = fadd f64 %rsum0, %wv3
    %rsum = fadd f64 %rsum1, %wv4
    %rgain = fmul f64 %rsum, 1.1
    %bright = fadd f64 %bright0, %rgain
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
    br loop(%k2, buf, S, rot, rmax, half, el, em, eh, tf, wt1, ws1, wt2, ws2, wt3, ws3, wt4, ws4)
  fin():
    ret
}

; the golden log spiral, breathing with the total musical energy.
fn spiral_pass(ptr, i64, f64, ptr) -> void {
  entry(buf: ptr, S: i64, rot: f64, glo: ptr):
    %sf = sitofp f64 S
    %rmax = fmul f64 %sf, 0.485
    %half = fmul f64 %sf, 0.5
    %rscale = fdiv f64 %rmax, 147.1
    %e3p = gep f64 glo, 3
    %ea = load f64, %e3p
    %e5p = gep f64 glo, 5
    %tf = load f64, %e5p
    %gain0 = fmul f64 %ea, 0.95
    %gain = fadd f64 %gain0, 0.30
    %rs0 = fmul f64 rot, 0.5
    %rs1 = call f64 sin(%rs0)
    %rs2 = fmul f64 %rs1, 0.05
    %rsf = fadd f64 %rs2, 1.0
    %rscaleB = fmul f64 %rscale, 0.94
    %rscale2 = fmul f64 %rscaleB, %rsf
    br loop(0, buf, S, rot, %rmax, %half, %rscale2, %gain, %tf)
  loop(s: i64, buf: ptr, S: i64, rot: f64, rmax: f64, half: f64, rscale: f64, gain: f64, tf: f64):
    %done = icmp.sge i64 s, 9000
    condbr %done, fin(), body(s, buf, S, rot, rmax, half, rscale, gain, tf)
  body(s: i64, buf: ptr, S: i64, rot: f64, rmax: f64, half: f64, rscale: f64, gain: f64, tf: f64):
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
    %wg = fmul f64 %w0, gain
    %fl0 = fmul f64 %th, 2.0
    %fl1 = fmul f64 tf, 1.9
    %fl2 = fsub f64 %fl0, %fl1
    %fl3 = call f64 sin(%fl2)
    %fl4 = fmul f64 %fl3, 0.55
    %fl = fadd f64 %fl4, 0.72
    %w = fmul f64 %wg, %fl
    %ix = fptosi i64 %x
    %iy = fptosi i64 %y
    call void splat(buf, S, %ix, %iy, %w)
    %s2 = add i64 s, 1
    br loop(%s2, buf, S, rot, rmax, half, rscale, gain, tf)
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
    %w6 = gep f64 glo, 6
    %wt1 = load f64, %w6
    %w7 = gep f64 glo, 7
    %ws1 = load f64, %w7
    %w8 = gep f64 glo, 8
    %wt2 = load f64, %w8
    %w9 = gep f64 glo, 9
    %ws2 = load f64, %w9
    %w10 = gep f64 glo, 10
    %wt3 = load f64, %w10
    %w11 = gep f64 glo, 11
    %ws3 = load f64, %w11
    %w12 = gep f64 glo, 12
    %wt4 = load f64, %w12
    %w13 = gep f64 glo, 13
    %ws4 = load f64, %w13
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
    %wfd = fmul f64 %d, 0.75
    %wfall = fsub f64 1.25, %wfd
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
    %rdt1 = fsub f64 %tf, wt1
    %rrd1 = fmul f64 %rdt1, 0.5
    %rdd1 = fsub f64 %d, %rrd1
    %rdd21 = fmul f64 %rdd1, %rdd1
    %rg01 = fdiv f64 %rdd21, 0.0022
    %rg11 = fsub f64 0.0, %rg01
    %rg1 = call f64 exp(%rg11)
    %rc01 = fmul f64 %rdt1, 0.35
    %rc11 = fsub f64 0.0, %rc01
    %rc1 = call f64 exp(%rc11)
    %rv_1 = fmul f64 ws1, %rg1
    %rv1 = fmul f64 %rv_1, %rc1
    %rdt2 = fsub f64 %tf, wt2
    %rrd2 = fmul f64 %rdt2, 0.5
    %rdd2 = fsub f64 %d, %rrd2
    %rdd22 = fmul f64 %rdd2, %rdd2
    %rg02 = fdiv f64 %rdd22, 0.0022
    %rg12 = fsub f64 0.0, %rg02
    %rg2 = call f64 exp(%rg12)
    %rc02 = fmul f64 %rdt2, 0.35
    %rc12 = fsub f64 0.0, %rc02
    %rc2 = call f64 exp(%rc12)
    %rv_2 = fmul f64 ws2, %rg2
    %rv2 = fmul f64 %rv_2, %rc2
    %rdt3 = fsub f64 %tf, wt3
    %rrd3 = fmul f64 %rdt3, 0.5
    %rdd3 = fsub f64 %d, %rrd3
    %rdd23 = fmul f64 %rdd3, %rdd3
    %rg03 = fdiv f64 %rdd23, 0.0022
    %rg13 = fsub f64 0.0, %rg03
    %rg3 = call f64 exp(%rg13)
    %rc03 = fmul f64 %rdt3, 0.35
    %rc13 = fsub f64 0.0, %rc03
    %rc3 = call f64 exp(%rc13)
    %rv_3 = fmul f64 ws3, %rg3
    %rv3 = fmul f64 %rv_3, %rc3
    %rdt4 = fsub f64 %tf, wt4
    %rrd4 = fmul f64 %rdt4, 0.5
    %rdd4 = fsub f64 %d, %rrd4
    %rdd24 = fmul f64 %rdd4, %rdd4
    %rg04 = fdiv f64 %rdd24, 0.0022
    %rg14 = fsub f64 0.0, %rg04
    %rg4 = call f64 exp(%rg14)
    %rc04 = fmul f64 %rdt4, 0.35
    %rc14 = fsub f64 0.0, %rc04
    %rc4 = call f64 exp(%rc14)
    %rv_4 = fmul f64 ws4, %rg4
    %rv4 = fmul f64 %rv_4, %rc4
    %rbs0 = fadd f64 %rv1, %rv2
    %rbs1 = fadd f64 %rbs0, %rv3
    %rbs = fadd f64 %rbs1, %rv4
    %rbgB = fmul f64 %rbs, 22.0
    %rbgG = fmul f64 %rbs, 8.0
    %rbgR = fmul f64 %rbs, 5.0
    %vg0 = fmul f64 %d2, 0.30
    %vg = fsub f64 1.0, %vg0
    %rr0 = fadd f64 %bgr, %ar
    %rr1 = fadd f64 %rr0, %hr
    %rr2 = fadd f64 %rr1, %str
    %rr3 = fadd f64 %rr2, %rbgR
    %rr = fmul f64 %rr3, %vg
    %gg0 = fadd f64 %bgg, %ag
    %gg1 = fadd f64 %gg0, %hg
    %gg2 = fadd f64 %gg1, %stg
    %gg3 = fadd f64 %gg2, %wag
    %gg4 = fadd f64 %gg3, %rbgG
    %gg = fmul f64 %gg4, %vg
    %bb0 = fadd f64 %bgb, %ab
    %bb1 = fadd f64 %bb0, %hb
    %bb2 = fadd f64 %bb1, %stb
    %bb3 = fadd f64 %bb2, %wab
    %bb4 = fadd f64 %bb3, %rbgB
    %bb = fmul f64 %bb4, %vg
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
    %glo = call ptr malloc(128)
    call void analyze(fr, %glo)
    %frf = sitofp f64 fr
    %totf = sitofp f64 tot
    %ph = fdiv f64 %frf, %totf
    %rot = fmul f64 %ph, 12.566370614359172
    %rots = fmul f64 %ph, -37.69911184307752
    call void seed_pass(%buf, S, %rot, %glo)
    call void spiral_pass(%buf, S, %rots, %glo)
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

path = pathlib.Path(__file__).with_name("fibfilm4.krell")
path.write_text(seed_constants(src.strip() + "\n"))
print("wrote", path, "events embedded:", NEV)
