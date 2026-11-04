#!/usr/bin/env python3
"""Generator for livecount_audio.krell - the Live Count soundtrack.

A Krell synth: a slow Dm - Bb - F - C pad under an arpeggio whose
note density ramps exponentially over 72 s (one pluck every 0.42 s at
the start, one every ~18 ms at the end), mirroring the film's
particle-count climb. 8 voices, sine + 2nd harmonic, exp decay.
Output: raw f64le PCM on stdout at 22050 Hz. Arg: [seconds].
"""
import pathlib, re

SRC = r"""
extern write(i32, ptr, i64) -> i64
extern malloc(i64) -> ptr
extern atoi(ptr) -> i32
extern sin(f64) -> f64
extern exp(f64) -> f64

data chords: i64 = { 146830, 174610, 220000, 293660, 349230, 440000, 116540, 146830, 174610, 233080, 293660, 349230, 174610, 220000, 261630, 349230, 440000, 523250, 130810, 164810, 196000, 261630, 329630, 392000 }

fn zero8(ptr) -> void {
  entry(a: ptr):
    br loop(0, a)
  loop(i: i64, a: ptr):
    %done = icmp.sge i64 i, 8
    condbr %done, fin(), body(i, a)
  body(i: i64, a: ptr):
    %p = gep f64 a, i
    store f64 %p, 0.0
    %i2 = add i64 i, 1
    br loop(%i2, a)
  fin():
    ret
}

; sum all sounding voices, advancing phases and decays in place.
fn voices_sum(ptr, ptr, ptr) -> f64 {
  entry(fa: ptr, pa: ptr, ea: ptr):
    br loop(0, 0.0, fa, pa, ea)
  loop(v: i64, sum: f64, fa: ptr, pa: ptr, ea: ptr):
    %done = icmp.sge i64 v, 8
    condbr %done, fin(sum), body(v, sum, fa, pa, ea)
  body(v: i64, sum: f64, fa: ptr, pa: ptr, ea: ptr):
    %ep = gep f64 ea, v
    %env = load f64, %ep
    %act = fcmp.ogt f64 %env, 0.0005
    condbr %act, on(v, sum, fa, pa, ea, %env), off(v, sum, fa, pa, ea)
  on(v: i64, sum: f64, fa: ptr, pa: ptr, ea: ptr, env: f64):
    %fp = gep f64 fa, v
    %f = load f64, %fp
    %pp = gep f64 pa, v
    %ph0 = load f64, %pp
    %dph = fmul f64 %f, 0.000045351473922902494
    %ph = fadd f64 %ph0, %dph
    store f64 %pp, %ph
    %a1 = fmul f64 %ph, 6.283185307179586
    %s1 = call f64 sin(%a1)
    %a2 = fmul f64 %ph, 12.566370614359172
    %s2 = call f64 sin(%a2)
    %h2 = fmul f64 %s2, 0.3
    %tone = fadd f64 %s1, %h2
    %c0 = fmul f64 %tone, env
    %contrib = fmul f64 %c0, 0.22
    %sum2 = fadd f64 sum, %contrib
    %env2 = fmul f64 env, 0.99987
    %ep2 = gep f64 ea, v
    store f64 %ep2, %env2
    br next(v, %sum2, fa, pa, ea)
  off(v: i64, sum: f64, fa: ptr, pa: ptr, ea: ptr):
    br next(v, sum, fa, pa, ea)
  next(v: i64, sum: f64, fa: ptr, pa: ptr, ea: ptr):
    %v2 = add i64 v, 1
    br loop(%v2, sum, fa, pa, ea)
  fin(sum: f64):
    ret sum
}

fn clamp1(f64) -> f64 {
  entry(v: f64):
    %lo = fcmp.olt f64 v, -0.92
    %a = select f64 %lo, -0.92, v
    %hi = fcmp.ogt f64 %a, 0.92
    %b = select f64 %hi, 0.92, %a
    ret %b
}

fn main(i32, ptr) -> i32 {
  entry(argc: i32, argv: ptr):
    %h1 = icmp.sge i32 argc, 2
    condbr %h1, a1(argc, argv), setup(72)
  a1(argc: i32, argv: ptr):
    %p1 = gep ptr argv, 1
    %s1 = load ptr, %p1
    %av1 = call i32 atoi(%s1)
    %sec = sext i64 %av1
    br setup(%sec)
  setup(sec: i64):
    %total = mul i64 sec, 22050
    %fa = call ptr malloc(64)
    %pa = call ptr malloc(64)
    %ea = call ptr malloc(64)
    call void zero8(%fa)
    call void zero8(%pa)
    call void zero8(%ea)
    %buf = call ptr malloc(32768)
    br loop(0, %total, 0, 0, %fa, %pa, %ea, %buf, 0, 0.0, 0.0)
  loop(i: i64, total: i64, nextev: i64, evc: i64, fa: ptr, pa: ptr, ea: ptr, buf: ptr, bidx: i64, pph1: f64, pph2: f64):
    %done = icmp.sge i64 i, total
    condbr %done, fin(buf, bidx), body(i, total, nextev, evc, fa, pa, ea, buf, bidx, pph1, pph2)
  body(i: i64, total: i64, nextev: i64, evc: i64, fa: ptr, pa: ptr, ea: ptr, buf: ptr, bidx: i64, pph1: f64, pph2: f64):
    %ch0 = udiv i64 i, 132300
    %chord = urem i64 %ch0, 4
    %cbase = mul i64 %chord, 6
    %cp = dataptr 0
    %tf = sitofp f64 i
    %ttf = sitofp f64 total
    %prog = fdiv f64 %tf, %ttf
    %trig = icmp.sge i64 i, nextev
    condbr %trig, trig(i, total, nextev, evc, fa, pa, ea, buf, bidx, pph1, pph2, %cp, %cbase, %prog), mix(i, total, nextev, evc, fa, pa, ea, buf, bidx, pph1, pph2, %cp, %cbase, %prog)
  trig(i: i64, total: i64, nextev: i64, evc: i64, fa: ptr, pa: ptr, ea: ptr, buf: ptr, bidx: i64, pph1: f64, pph2: f64, cp: ptr, cbase: i64, prog: f64):
    %slot = urem i64 evc, 8
    %pat0 = mul i64 evc, 5
    %nidx = urem i64 %pat0, 6
    %ni = add i64 cbase, %nidx
    %np = gep i64 %cp, %ni
    %freqi = load i64, %np
    %freqf = sitofp f64 %freqi
    %freq = fdiv f64 %freqf, 1000.0
    %fp = gep f64 fa, %slot
    store f64 %fp, %freq
    %pp = gep f64 pa, %slot
    store f64 %pp, 0.0
    %var0 = mul i64 evc, 37
    %var1 = urem i64 %var0, 10
    %varf = sitofp f64 %var1
    %amp0 = fmul f64 %varf, 0.03
    %amp = fadd f64 %amp0, 0.55
    %ep = gep f64 ea, %slot
    store f64 %ep, %amp
    %ex0 = fmul f64 prog, -3.1780538303479458
    %ex = call f64 exp(%ex0)
    %isec = fmul f64 %ex, 0.42
    %isamp0 = fmul f64 %isec, 22050.0
    %isamp = fptosi i64 %isamp0
    %lo = icmp.slt i64 %isamp, 380
    %step = select i64 %lo, 380, %isamp
    %next2 = add i64 i, %step
    %evc2 = add i64 evc, 1
    br mix(i, total, %next2, %evc2, fa, pa, ea, buf, bidx, pph1, pph2, cp, cbase, prog)
  mix(i: i64, total: i64, nextev: i64, evc: i64, fa: ptr, pa: ptr, ea: ptr, buf: ptr, bidx: i64, pph1: f64, pph2: f64, cp: ptr, cbase: i64, prog: f64):
    %vs = call f64 voices_sum(fa, pa, ea)
    %rp = gep i64 cp, cbase
    %rooti = load i64, %rp
    %rootf = sitofp f64 %rooti
    %root = fdiv f64 %rootf, 1000.0
    %fi0 = add i64 cbase, 2
    %fp2 = gep i64 %cp, %fi0
    %fifthi = load i64, %fp2
    %fifthf = sitofp f64 %fifthi
    %fifth = fdiv f64 %fifthf, 1000.0
    %root2 = fmul f64 %root, 0.5
    %fifth2 = fmul f64 %fifth, 0.5
    %dp1 = fmul f64 %root2, 0.000045351473922902494
    %np1 = fadd f64 pph1, %dp1
    %dp2 = fmul f64 %fifth2, 0.000045351473922902494
    %np2 = fadd f64 pph2, %dp2
    %sw0 = fmul f64 prog, 6.283185307179586
    %sw1 = fmul f64 %sw0, 3.0
    %sw = call f64 sin(%sw1)
    %pamp0 = fmul f64 %sw, 0.012
    %pamp1 = fmul f64 prog, 0.045
    %pamp2 = fadd f64 %pamp1, 0.038
    %pamp = fadd f64 %pamp2, %pamp0
    %pa1 = fmul f64 %np1, 6.283185307179586
    %ps1 = call f64 sin(%pa1)
    %pa2 = fmul f64 %np2, 6.283185307179586
    %ps2 = call f64 sin(%pa2)
    %pad0 = fmul f64 %ps1, 0.6
    %pad1 = fmul f64 %ps2, 0.4
    %pad2 = fadd f64 %pad0, %pad1
    %pad = fmul f64 %pad2, %pamp
    %tot0 = fadd f64 %vs, %pad
    %val = call f64 clamp1(%tot0)
    %bp = gep f64 buf, bidx
    store f64 %bp, %val
    %bidx2 = add i64 bidx, 1
    %full = icmp.sge i64 %bidx2, 4096
    condbr %full, flush(i, total, nextev, evc, fa, pa, ea, buf, %np1, %np2), step(i, total, nextev, evc, fa, pa, ea, buf, %bidx2, %np1, %np2)
  flush(i: i64, total: i64, nextev: i64, evc: i64, fa: ptr, pa: ptr, ea: ptr, buf: ptr, np1: f64, np2: f64):
    %w = call i64 write(1, buf, 32768)
    br step(i, total, nextev, evc, fa, pa, ea, buf, 0, np1, np2)
  step(i: i64, total: i64, nextev: i64, evc: i64, fa: ptr, pa: ptr, ea: ptr, buf: ptr, bidx: i64, np1: f64, np2: f64):
    %i2 = add i64 i, 1
    br loop(%i2, total, nextev, evc, fa, pa, ea, buf, bidx, np1, np2)
  fin(buf: ptr, bidx: i64):
    %has = icmp.sgt i64 bidx, 0
    condbr %has, tail(buf, bidx), done()
  tail(buf: ptr, bidx: i64):
    %bytes = mul i64 bidx, 8
    %w = call i64 write(1, buf, %bytes)
    br done()
  done():
    ret 0
}
"""

def seed_constants(text):
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

path = pathlib.Path(__file__).with_name("livecount_audio.krell")
path.write_text(seed_constants(SRC.strip() + "\n"))
print("wrote", path)
