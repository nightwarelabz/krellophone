#!/usr/bin/env python3
"""Generator for fib.krell - the extreme Fibonacci compute program.
All numbers printed by the emitted Krell program are computed by it.
"""
import pathlib

STRINGS = []
def S(name, text):
    STRINGS.append((name, text))

S("banner1", "\n================================================================\n")
S("banner2", "FIBONACCI, COMPUTED ENTIRELY IN KRELL\n")
S("banner3", "four algorithms - one sequence - every result cross-checked\n")
S("banner4", "================================================================\n")
S("sec_table", "\n--- THE SEQUENCE: F(0) .. F(92), iterative engine ---\n")
S("fopen", "F(")
S("eq", ") = ")
S("nl", "\n")
S("sec_verify", "\n--- CROSS-VERIFICATION (counts computed by the program) ---\n")
S("v_rec", "naive recursion   vs iterative    n=0..28          : ")
S("v_fast", "fast doubling     vs iterative    n=0..90          : ")
S("v_mat", "matrix power      vs iterative    n=0..90          : ")
S("v_cas", "Cassini identity  F(n-1)F(n+1)-F(n)^2 = (-1)^n  n=1..46 : ")
S("v_sum", "summation         sum F(i) = F(n+2)-1       n=0..88  : ")
S("v_gcd", "gcd identity      gcd(F(m),F(n)) = F(gcd(m,n))  m,n=1..24 : ")
S("v_add", "addition formula  F(m+n)=F(m)F(n+1)+F(m-1)F(n)  m,n=2..30 : ")
S("slash", "/")
S("agree", " agree")
S("sec_phi", "\n--- THE GOLDEN RATIO, FROM THE SEQUENCE ITSELF ---\n")
S("phi_pre", "F(")
S("phi_mid", "+1) / F(")
S("phi_post", ") = ")
S("phi_true", "phi to 15 places                           = 1.618033988749895\n")
S("dot", ".")
S("sec_ops", "\n--- THE COST OF KNOWING: OPERATION COUNTS FOR n = 32 ---\n")
S("ops_rec", "naive recursion : ")
S("ops_rec2", " function calls to learn that F(32) = ")
S("ops_iter", "iterative       : ")
S("ops_iter2", " additions to learn F(32)\n")
S("ops_fast", "fast doubling   : ")
S("ops_fast2", " multiplications across ")
S("ops_fast3", " recursion levels\n")
S("ops_mat", "matrix power    : ")
S("ops_mat2", " matrix multiplications = ")
S("ops_mat3", " scalar multiplications\n")
S("sec_big", "\n--- BEYOND 64 BITS: EXACT BIG FIBONACCI (base 10^9 limbs, in Krell) ---\n")
S("big1_pre", "F(1000)  = ")
S("big2_pre", "F(10000) = ")
S("digits", "    digits        : ")
S("digsum", "    digit sum     : ")
S("last9", "    last 9 digits : ")
S("first", "    leading digits: ")
S("dots", "...")
S("verdict_ok", "\n================================================================\nVERDICT: EVERY CHECK PASSED - ")
S("verdict_bad", "\n================================================================\nVERDICT: FAILURES DETECTED - ")
S("verdict2", " failures out of ")
S("verdict3", " checks\n================================================================\n")

out = []
def emit(line=""):
    out.append(line)
def W(name, indent="    "):
    return f"{indent}call void w_{name}()"

emit("; FIBONACCI, COMPUTED ENTIRELY IN KRELL")
emit("; Four independent engines (naive recursion, iteration, fast doubling,")
emit("; binary matrix power) cross-verify each other and five identities;")
emit("; exact big-integer Fibonacci to F(10000) in base-10^9 limbs; golden-")
emit("; ratio convergence printed digit by digit. Host services: write, malloc.")
emit("")
emit("extern write(i32, ptr, i64) -> i64")
emit("extern malloc(i64) -> ptr")
emit("")
for i, (name, text) in enumerate(STRINGS):
    bs = ", ".join(str(b) for b in text.encode())
    emit(f"data d{i}: i8 = {{ {bs} }}")
emit("")
for i, (name, text) in enumerate(STRINGS):
    emit(f"fn w_{name}() -> void {{")
    emit("  entry():")
    emit(f"    %p = dataptr {i}")
    emit(f"    %r = call i64 write(1, %p, {len(text.encode())})")
    emit("    ret")
    emit("}")
    emit("")

emit(r"""
fn fib_rec(i64) -> i64 {
  entry(n: i64):
    %c = icmp.slt i64 n, 2
    condbr %c, base(n), rec(n)
  base(n: i64):
    ret n
  rec(n: i64):
    %n1 = sub i64 n, 1
    %a = call i64 fib_rec(%n1)
    %n2 = sub i64 n, 2
    %b = call i64 fib_rec(%n2)
    %s = add i64 %a, %b
    ret %s
}

fn fib_iter(i64) -> i64 {
  entry(n: i64):
    br loop(0, 0, 1, n)
  loop(i: i64, a: i64, b: i64, n: i64):
    %done = icmp.sge i64 i, n
    condbr %done, fin(a), body(i, a, b, n)
  body(i: i64, a: i64, b: i64, n: i64):
    %nx = add i64 a, b
    %i2 = add i64 i, 1
    br loop(%i2, b, %nx, n)
  fin(a: i64):
    ret a
}

fn fib_iter_ops(i64) -> i64 {
  entry(n: i64):
    br loop(0, 0, 1, n, 0)
  loop(i: i64, a: i64, b: i64, n: i64, ops: i64):
    %done = icmp.sge i64 i, n
    condbr %done, fin(ops), body(i, a, b, n, ops)
  body(i: i64, a: i64, b: i64, n: i64, ops: i64):
    %nx = add i64 a, b
    %i2 = add i64 i, 1
    %o2 = add i64 ops, 1
    br loop(%i2, b, %nx, n, %o2)
  fin(ops: i64):
    ret ops
}

; fast doubling core: (F(n), F(n+1)) -> out[0..1]; per-depth scratch pairs.
fn fib_pair(i64, i64, ptr, ptr, ptr) -> void {
  entry(n: i64, d: i64, out: ptr, scr: ptr, cnt: ptr):
    %z = icmp.eq i64 n, 0
    condbr %z, base(out), rec(n, d, out, scr, cnt)
  base(out: ptr):
    %p0 = gep i64 out, 0
    store i64 %p0, 0
    %p1 = gep i64 out, 1
    store i64 %p1, 1
    ret
  rec(n: i64, d: i64, out: ptr, scr: ptr, cnt: ptr):
    %k = sdiv i64 n, 2
    %d1 = add i64 d, 1
    %s0 = mul i64 d, 2
    %sp = gep i64 scr, %s0
    call void fib_pair(%k, %d1, %sp, scr, cnt)
    %a = load i64, %sp
    %s1 = add i64 %s0, 1
    %sq = gep i64 scr, %s1
    %b = load i64, %sq
    %cv = load i64, %cnt
    %cv2 = add i64 %cv, 3
    store i64 %cnt, %cv2
    %tb = mul i64 %b, 2
    %tba = sub i64 %tb, %a
    %c = mul i64 %a, %tba
    %aa = mul i64 %a, %a
    %bb = mul i64 %b, %b
    %dd = add i64 %aa, %bb
    %odd = and i64 n, 1
    %iso = icmp.eq i64 %odd, 1
    condbr %iso, oddout(%c, %dd, out), evenout(%c, %dd, out)
  evenout(c: i64, dd: i64, out: ptr):
    %p0 = gep i64 out, 0
    store i64 %p0, %c
    %p1 = gep i64 out, 1
    store i64 %p1, %dd
    ret
  oddout(c: i64, dd: i64, out: ptr):
    %e = add i64 %c, %dd
    %p0 = gep i64 out, 0
    store i64 %p0, %dd
    %p1 = gep i64 out, 1
    store i64 %p1, %e
    ret
}

fn fib_fast(i64) -> i64 {
  entry(n: i64):
    %out = call ptr malloc(16)
    %scr = call ptr malloc(4096)
    %cnt = call ptr malloc(8)
    store i64 %cnt, 0
    call void fib_pair(n, 0, %out, %scr, %cnt)
    %p0 = gep i64 %out, 0
    %v = load i64, %p0
    ret %v
}

fn mat_mul(ptr, ptr, ptr) -> void {
  entry(r: ptr, x: ptr, y: ptr):
    %x0p = gep i64 x, 0
    %x0 = load i64, %x0p
    %x1p = gep i64 x, 1
    %x1 = load i64, %x1p
    %x2p = gep i64 x, 2
    %x2 = load i64, %x2p
    %x3p = gep i64 x, 3
    %x3 = load i64, %x3p
    %y0p = gep i64 y, 0
    %y0 = load i64, %y0p
    %y1p = gep i64 y, 1
    %y1 = load i64, %y1p
    %y2p = gep i64 y, 2
    %y2 = load i64, %y2p
    %y3p = gep i64 y, 3
    %y3 = load i64, %y3p
    %a0 = mul i64 %x0, %y0
    %a1 = mul i64 %x1, %y2
    %r0 = add i64 %a0, %a1
    %b0 = mul i64 %x0, %y1
    %b1 = mul i64 %x1, %y3
    %r1 = add i64 %b0, %b1
    %c0 = mul i64 %x2, %y0
    %c1 = mul i64 %x3, %y2
    %r2 = add i64 %c0, %c1
    %d0 = mul i64 %x2, %y1
    %d1 = mul i64 %x3, %y3
    %r3 = add i64 %d0, %d1
    %q0 = gep i64 r, 0
    store i64 %q0, %r0
    %q1 = gep i64 r, 1
    store i64 %q1, %r1
    %q2 = gep i64 r, 2
    store i64 %q2, %r2
    %q3 = gep i64 r, 3
    store i64 %q3, %r3
    ret
}

fn mat_copy(ptr, ptr) -> void {
  entry(dst: ptr, src: ptr):
    br loop(0, dst, src)
  loop(i: i64, dst: ptr, src: ptr):
    %done = icmp.sge i64 i, 4
    condbr %done, fin(), body(i, dst, src)
  body(i: i64, dst: ptr, src: ptr):
    %sp = gep i64 src, i
    %v = load i64, %sp
    %dp = gep i64 dst, i
    store i64 %dp, %v
    %i2 = add i64 i, 1
    br loop(%i2, dst, src)
  fin():
    ret
}

fn fib_matrix_c(i64, ptr) -> i64 {
  entry(n: i64, cnt: ptr):
    %res = call ptr malloc(32)
    %bas = call ptr malloc(32)
    %tmp = call ptr malloc(32)
    %r0 = gep i64 %res, 0
    store i64 %r0, 1
    %r1 = gep i64 %res, 1
    store i64 %r1, 0
    %r2 = gep i64 %res, 2
    store i64 %r2, 0
    %r3 = gep i64 %res, 3
    store i64 %r3, 1
    %b0 = gep i64 %bas, 0
    store i64 %b0, 1
    %b1 = gep i64 %bas, 1
    store i64 %b1, 1
    %b2 = gep i64 %bas, 2
    store i64 %b2, 1
    %b3 = gep i64 %bas, 3
    store i64 %b3, 0
    br loop(n, %res, %bas, %tmp, cnt)
  loop(e: i64, res: ptr, bas: ptr, tmp: ptr, cnt: ptr):
    %done = icmp.sle i64 e, 0
    condbr %done, fin(res), step(e, res, bas, tmp, cnt)
  step(e: i64, res: ptr, bas: ptr, tmp: ptr, cnt: ptr):
    %odd = and i64 e, 1
    %iso = icmp.eq i64 %odd, 1
    condbr %iso, apply(e, res, bas, tmp, cnt), square(e, res, bas, tmp, cnt)
  apply(e: i64, res: ptr, bas: ptr, tmp: ptr, cnt: ptr):
    call void mat_mul(tmp, res, bas)
    call void mat_copy(res, tmp)
    %cv = load i64, %cnt
    %cv2 = add i64 %cv, 1
    store i64 %cnt, %cv2
    br square(e, res, bas, tmp, cnt)
  square(e: i64, res: ptr, bas: ptr, tmp: ptr, cnt: ptr):
    call void mat_mul(tmp, bas, bas)
    call void mat_copy(bas, tmp)
    %cv = load i64, %cnt
    %cv2 = add i64 %cv, 1
    store i64 %cnt, %cv2
    %e2 = lshr i64 e, 1
    br loop(%e2, res, bas, tmp, cnt)
  fin(res: ptr):
    %p = gep i64 res, 1
    %v = load i64, %p
    ret %v
}

fn fib_matrix(i64) -> i64 {
  entry(n: i64):
    %cnt = call ptr malloc(8)
    store i64 %cnt, 0
    %v = call i64 fib_matrix_c(n, %cnt)
    ret %v
}

fn gcd_i64(i64, i64) -> i64 {
  entry(a: i64, b: i64):
    br loop(a, b)
  loop(a: i64, b: i64):
    %z = icmp.eq i64 b, 0
    condbr %z, fin(a), body(a, b)
  body(a: i64, b: i64):
    %r = srem i64 a, b
    br loop(b, %r)
  fin(a: i64):
    ret a
}

; instrumented recursion: returns call count; F(n) stored to vals[d].
fn fib_calls(i64, i64, ptr) -> i64 {
  entry(n: i64, d: i64, vals: ptr):
    %c = icmp.slt i64 n, 2
    condbr %c, base(n, d, vals), rec(n, d, vals)
  base(n: i64, d: i64, vals: ptr):
    %p = gep i64 vals, d
    store i64 %p, n
    ret 1
  rec(n: i64, d: i64, vals: ptr):
    %d1 = add i64 d, 1
    %n1 = sub i64 n, 1
    %cl = call i64 fib_calls(%n1, %d1, vals)
    %pl = gep i64 vals, %d1
    %vl = load i64, %pl
    %n2 = sub i64 n, 2
    %cr = call i64 fib_calls(%n2, %d1, vals)
    %pr = gep i64 vals, %d1
    %vr = load i64, %pr
    %v = add i64 %vl, %vr
    %p = gep i64 vals, d
    store i64 %p, %v
    %t0 = add i64 %cl, %cr
    %t1 = add i64 %t0, 1
    ret %t1
}

fn bitlen(i64) -> i64 {
  entry(x: i64):
    br loop(x, 0)
  loop(x: i64, c: i64):
    %z = icmp.sle i64 x, 0
    condbr %z, fin(c), body(x, c)
  body(x: i64, c: i64):
    %x2 = lshr i64 x, 1
    %c2 = add i64 c, 1
    br loop(%x2, %c2)
  fin(c: i64):
    ret c
}
""")

emit(r"""
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

fn print_limb9(i64) -> void {
  entry(x: i64):
    %buf = call ptr malloc(16)
    br loop(8, x, %buf)
  loop(pos: i64, x: i64, buf: ptr):
    %neg = icmp.slt i64 pos, 0
    condbr %neg, dump(buf), body(pos, x, buf)
  body(pos: i64, x: i64, buf: ptr):
    %d = urem i64 x, 10
    %ch = add i64 %d, 48
    %ch8 = trunc i8 %ch
    %pp = gep i8 buf, pos
    store i8 %pp, %ch8
    %x2 = udiv i64 x, 10
    %p2 = sub i64 pos, 1
    br loop(%p2, %x2, buf)
  dump(buf: ptr):
    %w = call i64 write(1, buf, 9)
    ret
}

fn print_phi(i64) -> void {
  entry(n: i64):
    %a1 = add i64 n, 1
    %hi = call i64 fib_iter(%a1)
    %lo = call i64 fib_iter(n)
    %hf = sitofp f64 %hi
    %lf = sitofp f64 %lo
    %r = fdiv f64 %hf, %lf
    %ip = fptosi i64 %r
    call void print_u64(%ip)
    %ipf = sitofp f64 %ip
    %frac = fsub f64 %r, %ipf
""")
emit(W("dot"))
emit(r"""    br loop(0, %frac)
  loop(done: i64, frac: f64):
    %fin = icmp.sge i64 done, 15
    condbr %fin, fin(), body(done, frac)
  body(done: i64, frac: f64):
    %sc = fmul f64 frac, 10.0
    %dg = fptosi i64 %sc
    call void print_u64(%dg)
    %dgf = sitofp f64 %dg
    %nf = fsub f64 %sc, %dgf
    %d2 = add i64 done, 1
    br loop(%d2, %nf)
  fin():
    ret
}
""")

# ---------------- big integers ----------------
emit(r"""
fn zero_buf(ptr, i64) -> void {
  entry(buf: ptr, slots: i64):
    br loop(0, buf, slots)
  loop(i: i64, buf: ptr, slots: i64):
    %done = icmp.sge i64 i, slots
    condbr %done, fin(), body(i, buf, slots)
  body(i: i64, buf: ptr, slots: i64):
    %p = gep i64 buf, i
    store i64 %p, 0
    %i2 = add i64 i, 1
    br loop(%i2, buf, slots)
  fin():
    ret
}

fn copy_buf(ptr, ptr, i64) -> void {
  entry(dst: ptr, src: ptr, n: i64):
    br loop(0, dst, src, n)
  loop(i: i64, dst: ptr, src: ptr, n: i64):
    %done = icmp.sge i64 i, n
    condbr %done, fin(), body(i, dst, src, n)
  body(i: i64, dst: ptr, src: ptr, n: i64):
    %sp = gep i64 src, i
    %v = load i64, %sp
    %dp = gep i64 dst, i
    store i64 %dp, %v
    %i2 = add i64 i, 1
    br loop(%i2, dst, src, n)
  fin():
    ret
}

; dst = a + b in base 10^9; returns limb count; writes a 0 sentinel at dst[n].
fn big_add(ptr, ptr, i64, ptr, i64) -> i64 {
  entry(dst: ptr, a: ptr, na: i64, b: ptr, nb: i64):
    %gt = icmp.sgt i64 nb, na
    %mx = select i64 %gt, nb, na
    br loop(0, 0, %mx, dst, a, na, b, nb)
  loop(i: i64, carry: i64, mx: i64, dst: ptr, a: ptr, na: i64, b: ptr, nb: i64):
    %done = icmp.sge i64 i, mx
    condbr %done, fin(i, carry, dst), body(i, carry, mx, dst, a, na, b, nb)
  body(i: i64, carry: i64, mx: i64, dst: ptr, a: ptr, na: i64, b: ptr, nb: i64):
    %ap = gep i64 a, i
    %av0 = load i64, %ap
    %ina = icmp.slt i64 i, na
    %av = select i64 %ina, %av0, 0
    %bp = gep i64 b, i
    %bv0 = load i64, %bp
    %inb = icmp.slt i64 i, nb
    %bv = select i64 %inb, %bv0, 0
    %s0 = add i64 %av, %bv
    %s = add i64 %s0, carry
    %ge = icmp.sge i64 %s, 1000000000
    %df = sub i64 %s, 1000000000
    %val = select i64 %ge, %df, %s
    %nc = select i64 %ge, 1, 0
    %dp = gep i64 dst, i
    store i64 %dp, %val
    %i2 = add i64 i, 1
    br loop(%i2, %nc, mx, dst, a, na, b, nb)
  fin(i: i64, carry: i64, dst: ptr):
    %p = gep i64 dst, i
    store i64 %p, carry
    %r = add i64 i, carry
    ret %r
}

; F(target) into res; returns limb count. Buffer roles are FIXED (no
; block-arg rotation: a cyclic permutation of block arguments is not a
; safe idiom). Each body advances three steps in place: C=A+B, A=B+C,
; B=A+C - big_add is index-wise, so dst may alias one operand.
fn big_fib(i64, ptr) -> i64 {
  entry(target: i64, res: ptr):
    %a = call ptr malloc(8192)
    %b = call ptr malloc(8192)
    %c = call ptr malloc(8192)
    call void zero_buf(%a, 1024)
    call void zero_buf(%b, 1024)
    call void zero_buf(%c, 1024)
    %pa = gep i64 %a, 0
    store i64 %pa, 0
    %pb = gep i64 %b, 0
    store i64 %pb, 1
    br loop(0, target, %a, 1, %b, 1, %c, 0, res)
  loop(k: i64, target: i64, pa: ptr, na: i64, pb: ptr, nb: i64, pc: ptr, nc: i64, res: ptr):
    %k3 = add i64 k, 3
    %done = icmp.sgt i64 %k3, target
    condbr %done, tail(k, target, pa, na, pb, nb, pc, nc, res), body(k, target, pa, na, pb, nb, pc, nc, res)
  body(k: i64, target: i64, pa: ptr, na: i64, pb: ptr, nb: i64, pc: ptr, nc: i64, res: ptr):
    %nc1 = call i64 big_add(pc, pa, na, pb, nb)
    %na2 = call i64 big_add(pa, pb, nb, pc, %nc1)
    %nb2 = call i64 big_add(pb, pa, %na2, pc, %nc1)
    %k2 = add i64 k, 3
    br loop(%k2, target, pa, %na2, pb, %nb2, pc, %nc1, res)
  tail(k: i64, target: i64, pa: ptr, na: i64, pb: ptr, nb: i64, pc: ptr, nc: i64, res: ptr):
    %r = sub i64 target, k
    %is0 = icmp.eq i64 %r, 0
    condbr %is0, fina(pa, na, res), tail1(%r, pa, na, pb, nb, pc, nc, res)
  tail1(r: i64, pa: ptr, na: i64, pb: ptr, nb: i64, pc: ptr, nc: i64, res: ptr):
    %is1 = icmp.eq i64 r, 1
    condbr %is1, finb(pb, nb, res), finc(pa, na, pb, nb, pc, res)
  fina(pa: ptr, na: i64, res: ptr):
    call void copy_buf(res, pa, na)
    ret na
  finb(pb: ptr, nb: i64, res: ptr):
    call void copy_buf(res, pb, nb)
    ret nb
  finc(pa: ptr, na: i64, pb: ptr, nb: i64, pc: ptr, res: ptr):
    %nc2 = call i64 big_add(pc, pa, na, pb, nb)
    call void copy_buf(res, pc, %nc2)
    ret %nc2
}

fn print_big(ptr, i64) -> void {
  entry(buf: ptr, n: i64):
    %t = sub i64 n, 1
    %tp = gep i64 buf, %t
    %tv = load i64, %tp
    call void print_u64(%tv)
    %s = sub i64 %t, 1
    br loop(%s, buf)
  loop(i: i64, buf: ptr):
    %neg = icmp.slt i64 i, 0
    condbr %neg, fin(), body(i, buf)
  body(i: i64, buf: ptr):
    %p = gep i64 buf, i
    %v = load i64, %p
    call void print_limb9(%v)
    %i2 = sub i64 i, 1
    br loop(%i2, buf)
  fin():
    ret
}

fn top_digits(i64) -> i64 {
  entry(x: i64):
    br loop(x, 0)
  loop(x: i64, c: i64):
    %z = icmp.sle i64 x, 0
    condbr %z, fin(c), body(x, c)
  body(x: i64, c: i64):
    %x2 = udiv i64 x, 10
    %c2 = add i64 c, 1
    br loop(%x2, %c2)
  fin(c: i64):
    %z = icmp.eq i64 c, 0
    %r = select i64 %z, 1, c
    ret %r
}

fn big_digit_count(ptr, i64) -> i64 {
  entry(buf: ptr, n: i64):
    %t = sub i64 n, 1
    %tp = gep i64 buf, %t
    %tv = load i64, %tp
    %td = call i64 top_digits(%tv)
    %m = mul i64 %t, 9
    %r = add i64 %m, %td
    ret %r
}

fn limb_dsum(i64) -> i64 {
  entry(x: i64):
    br loop(0, x, 0)
  loop(i: i64, x: i64, s: i64):
    %done = icmp.sge i64 i, 9
    condbr %done, fin(s), body(i, x, s)
  body(i: i64, x: i64, s: i64):
    %d = urem i64 x, 10
    %s2 = add i64 s, %d
    %x2 = udiv i64 x, 10
    %i2 = add i64 i, 1
    br loop(%i2, %x2, %s2)
  fin(s: i64):
    ret s
}

fn big_digit_sum(ptr, i64) -> i64 {
  entry(buf: ptr, n: i64):
    br loop(0, buf, n, 0)
  loop(i: i64, buf: ptr, n: i64, s: i64):
    %done = icmp.sge i64 i, n
    condbr %done, fin(s), body(i, buf, n, s)
  body(i: i64, buf: ptr, n: i64, s: i64):
    %p = gep i64 buf, i
    %v = load i64, %p
    %d = call i64 limb_dsum(%v)
    %s2 = add i64 s, %d
    %i2 = add i64 i, 1
    br loop(%i2, buf, n, %s2)
  fin(s: i64):
    ret s
}
""")

# ---------------- verification sections ----------------
def verify_fn(name, label, kind, **kw):
    """Emits a verify function printing 'label passed/total agree' and
    returning checks*10000+fails."""
    lines = [f"fn {name}() -> i64 {{"]
    if kind == "pair_range":
        lo, hi, fa, fb = kw["lo"], kw["hi"], kw["fa"], kw["fb"]
        lines += [
            "  entry():",
            f"    br loop({lo}, 0, 0)",
            "  loop(n: i64, checks: i64, fails: i64):",
            f"    %done = icmp.sgt i64 n, {hi}",
            "    condbr %done, report(checks, fails), body(n, checks, fails)",
            "  body(n: i64, checks: i64, fails: i64):",
            f"    %a = call i64 {fa}(n)",
            f"    %b = call i64 {fb}(n)",
            "    %eq = icmp.eq i64 %a, %b",
            "    %inc = select i64 %eq, 0, 1",
            "    %f2 = add i64 fails, %inc",
            "    %c2 = add i64 checks, 1",
            "    %n2 = add i64 n, 1",
            "    br loop(%n2, %c2, %f2)",
        ]
    elif kind == "cassini":
        lines += [
            "  entry():",
            "    br loop(1, 0, 0)",
            "  loop(n: i64, checks: i64, fails: i64):",
            "    %done = icmp.sgt i64 n, 46",
            "    condbr %done, report(checks, fails), body(n, checks, fails)",
            "  body(n: i64, checks: i64, fails: i64):",
            "    %nm = sub i64 n, 1",
            "    %np = add i64 n, 1",
            "    %fm = call i64 fib_iter(%nm)",
            "    %fp = call i64 fib_iter(%np)",
            "    %fn = call i64 fib_iter(n)",
            "    %p0 = mul i64 %fm, %fp",
            "    %p1 = mul i64 %fn, %fn",
            "    %lhs = sub i64 %p0, %p1",
            "    %odd = and i64 n, 1",
            "    %iso = icmp.eq i64 %odd, 1",
            "    %exp = select i64 %iso, -1, 1",
            "    %eq = icmp.eq i64 %lhs, %exp",
            "    %inc = select i64 %eq, 0, 1",
            "    %f2 = add i64 fails, %inc",
            "    %c2 = add i64 checks, 1",
            "    %n2 = add i64 n, 1",
            "    br loop(%n2, %c2, %f2)",
        ]
    elif kind == "sumid":
        lines += [
            "  entry():",
            "    br loop(0, 0, 0, 0)",
            "  loop(n: i64, cum: i64, checks: i64, fails: i64):",
            "    %done = icmp.sgt i64 n, 88",
            "    condbr %done, report(checks, fails), body(n, cum, checks, fails)",
            "  body(n: i64, cum: i64, checks: i64, fails: i64):",
            "    %f = call i64 fib_iter(n)",
            "    %c2v = add i64 cum, %f",
            "    %np = add i64 n, 2",
            "    %rhs0 = call i64 fib_iter(%np)",
            "    %rhs = sub i64 %rhs0, 1",
            "    %eq = icmp.eq i64 %c2v, %rhs",
            "    %inc = select i64 %eq, 0, 1",
            "    %f2 = add i64 fails, %inc",
            "    %c2 = add i64 checks, 1",
            "    %n2 = add i64 n, 1",
            "    br loop(%n2, %c2v, %c2, %f2)",
        ]
    elif kind == "gcdid":
        lines += [
            "  entry():",
            "    br oloop(1, 0, 0)",
            "  oloop(m: i64, checks: i64, fails: i64):",
            "    %done = icmp.sgt i64 m, 24",
            "    condbr %done, report(checks, fails), obody(m, checks, fails)",
            "  obody(m: i64, checks: i64, fails: i64):",
            "    br iloop(m, 1, checks, fails)",
            "  iloop(m: i64, n: i64, checks: i64, fails: i64):",
            "    %done = icmp.sgt i64 n, 24",
            "    condbr %done, idone(m, checks, fails), ibody(m, n, checks, fails)",
            "  ibody(m: i64, n: i64, checks: i64, fails: i64):",
            "    %fm = call i64 fib_iter(m)",
            "    %fn = call i64 fib_iter(n)",
            "    %lhs = call i64 gcd_i64(%fm, %fn)",
            "    %g = call i64 gcd_i64(m, n)",
            "    %rhs = call i64 fib_iter(%g)",
            "    %eq = icmp.eq i64 %lhs, %rhs",
            "    %inc = select i64 %eq, 0, 1",
            "    %f2 = add i64 fails, %inc",
            "    %c2 = add i64 checks, 1",
            "    %n2 = add i64 n, 1",
            "    br iloop(m, %n2, %c2, %f2)",
            "  idone(m: i64, checks: i64, fails: i64):",
            "    %m2 = add i64 m, 1",
            "    br oloop(%m2, checks, fails)",
        ]
    elif kind == "addid":
        lines += [
            "  entry():",
            "    br oloop(2, 0, 0)",
            "  oloop(m: i64, checks: i64, fails: i64):",
            "    %done = icmp.sgt i64 m, 30",
            "    condbr %done, report(checks, fails), obody(m, checks, fails)",
            "  obody(m: i64, checks: i64, fails: i64):",
            "    br iloop(m, 2, checks, fails)",
            "  iloop(m: i64, n: i64, checks: i64, fails: i64):",
            "    %done = icmp.sgt i64 n, 30",
            "    condbr %done, idone(m, checks, fails), ibody(m, n, checks, fails)",
            "  ibody(m: i64, n: i64, checks: i64, fails: i64):",
            "    %mn = add i64 m, n",
            "    %lhs = call i64 fib_iter(%mn)",
            "    %fm = call i64 fib_iter(m)",
            "    %np = add i64 n, 1",
            "    %fnp = call i64 fib_iter(%np)",
            "    %t0 = mul i64 %fm, %fnp",
            "    %mm = sub i64 m, 1",
            "    %fmm = call i64 fib_iter(%mm)",
            "    %fn = call i64 fib_iter(n)",
            "    %t1 = mul i64 %fmm, %fn",
            "    %rhs = add i64 %t0, %t1",
            "    %eq = icmp.eq i64 %lhs, %rhs",
            "    %inc = select i64 %eq, 0, 1",
            "    %f2 = add i64 fails, %inc",
            "    %c2 = add i64 checks, 1",
            "    %n2 = add i64 n, 1",
            "    br iloop(m, %n2, %c2, %f2)",
            "  idone(m: i64, checks: i64, fails: i64):",
            "    %m2 = add i64 m, 1",
            "    br oloop(%m2, checks, fails)",
        ]
    lines += [
        "  report(checks: i64, fails: i64):",
        W(label, "    "),
        "    %ok = sub i64 checks, fails",
        "    call void print_u64(%ok)",
        W("slash", "    "),
        "    call void print_u64(checks)",
        W("agree", "    "),
        W("nl", "    "),
        "    %pk = mul i64 checks, 10000",
        "    %r = add i64 %pk, fails",
        "    ret %r",
        "}",
        "",
    ]
    return lines

out += verify_fn("v_rec", "v_rec", "pair_range", lo=0, hi=28, fa="fib_rec", fb="fib_iter")
out += verify_fn("v_fast", "v_fast", "pair_range", lo=0, hi=90, fa="fib_fast", fb="fib_iter")
out += verify_fn("v_mat", "v_mat", "pair_range", lo=0, hi=90, fa="fib_matrix", fb="fib_iter")
out += verify_fn("v_cas", "v_cas", "cassini")
out += verify_fn("v_sum", "v_sum", "sumid")
out += verify_fn("v_gcd", "v_gcd", "gcdid")
out += verify_fn("v_add", "v_add", "addid")

# ---------------- presentation sections ----------------
emit(r"""
fn sec_table() -> void {
  entry():
    br loop(0)
  loop(n: i64):
    %done = icmp.sgt i64 n, 92
    condbr %done, fin(), body(n)
  body(n: i64):
""")
emit(W("fopen"))
emit(r"""    call void print_u64(n)
""")
emit(W("eq"))
emit(r"""    %v = call i64 fib_iter(n)
    call void print_u64(%v)
""")
emit(W("nl"))
emit(r"""    %n2 = add i64 n, 1
    br loop(%n2)
  fin():
    ret
}

fn phi_row(i64) -> void {
  entry(n: i64):
""")
emit(W("phi_pre"))
emit(r"""    call void print_u64(n)
""")
emit(W("phi_mid"))
emit(r"""    call void print_u64(n)
""")
emit(W("phi_post"))
emit(r"""    call void print_phi(n)
""")
emit(W("nl"))
emit(r"""    ret
}

fn sec_phi() -> void {
  entry():
    br loop(10)
  loop(n: i64):
    %done = icmp.sgt i64 n, 90
    condbr %done, fin(), body(n)
  body(n: i64):
    call void phi_row(n)
    %n2 = add i64 n, 10
    br loop(%n2)
  fin():
""")
emit(W("phi_true"))
emit(r"""    ret
}

fn sec_ops() -> void {
  entry():
    %vals = call ptr malloc(4096)
    %calls = call i64 fib_calls(32, 0, %vals)
    %vp = gep i64 %vals, 0
    %v32 = load i64, %vp
""")
emit(W("ops_rec"))
emit(r"""    call void print_u64(%calls)
""")
emit(W("ops_rec2"))
emit(r"""    call void print_u64(%v32)
""")
emit(W("nl"))
emit(W("ops_iter"))
emit(r"""    %adds = call i64 fib_iter_ops(32)
    call void print_u64(%adds)
""")
emit(W("ops_iter2"))
emit(r"""    %out = call ptr malloc(16)
    %scr = call ptr malloc(4096)
    %cnt = call ptr malloc(8)
    store i64 %cnt, 0
    call void fib_pair(32, 0, %out, %scr, %cnt)
    %muls = load i64, %cnt
    %lv = call i64 bitlen(32)
""")
emit(W("ops_fast"))
emit(r"""    call void print_u64(%muls)
""")
emit(W("ops_fast2"))
emit(r"""    call void print_u64(%lv)
""")
emit(W("ops_fast3"))
emit(r"""    %mcnt = call ptr malloc(8)
    store i64 %mcnt, 0
    %mv = call i64 fib_matrix_c(32, %mcnt)
    %mm = load i64, %mcnt
    %sm = mul i64 %mm, 8
""")
emit(W("ops_mat"))
emit(r"""    call void print_u64(%mm)
""")
emit(W("ops_mat2"))
emit(r"""    call void print_u64(%sm)
""")
emit(W("ops_mat3"))
emit(r"""    ret
}

fn print_big_stats(ptr, i64) -> void {
  entry(buf: ptr, n: i64):
    %dc = call i64 big_digit_count(buf, n)
""")
emit(W("digits"))
emit(r"""    call void print_u64(%dc)
""")
emit(W("nl"))
emit(W("digsum"))
emit(r"""    %ds = call i64 big_digit_sum(buf, n)
    call void print_u64(%ds)
""")
emit(W("nl"))
emit(W("last9"))
emit(r"""    %l0p = gep i64 buf, 0
    %l0 = load i64, %l0p
    call void print_limb9(%l0)
""")
emit(W("nl"))
emit(W("first"))
emit(r"""    %t = sub i64 n, 1
    %tp = gep i64 buf, %t
    %tv = load i64, %tp
    call void print_u64(%tv)
    %t2 = sub i64 %t, 1
    %tp2 = gep i64 buf, %t2
    %tv2 = load i64, %tp2
    call void print_limb9(%tv2)
""")
emit(W("dots"))
emit(W("nl"))
emit(r"""    ret
}

fn sec_big() -> void {
  entry():
    %res = call ptr malloc(8192)
    %n1 = call i64 big_fib(1000, %res)
""")
emit(W("big1_pre"))
emit(r"""    call void print_big(%res, %n1)
""")
emit(W("nl"))
emit(r"""    call void print_big_stats(%res, %n1)
    %n2 = call i64 big_fib(10000, %res)
""")
emit(W("big2_pre"))
emit(r"""    call void print_big(%res, %n2)
""")
emit(W("nl"))
emit(r"""    call void print_big_stats(%res, %n2)
    ret
}

fn main(i32, ptr) -> i32 {
  entry(argc: i32, argv: ptr):
""")
for nm in ["banner1", "banner2", "banner3", "banner4", "sec_table"]:
    emit(W(nm))
emit(r"""    call void sec_table()
""")
emit(W("sec_verify"))
emit(r"""    %p1 = call i64 v_rec()
    %p2 = call i64 v_fast()
    %p3 = call i64 v_mat()
    %p4 = call i64 v_cas()
    %p5 = call i64 v_sum()
    %p6 = call i64 v_gcd()
    %p7 = call i64 v_add()
    %c1 = sdiv i64 %p1, 10000
    %f1 = srem i64 %p1, 10000
    %c2 = sdiv i64 %p2, 10000
    %f2 = srem i64 %p2, 10000
    %c3 = sdiv i64 %p3, 10000
    %f3 = srem i64 %p3, 10000
    %c4 = sdiv i64 %p4, 10000
    %f4 = srem i64 %p4, 10000
    %c5 = sdiv i64 %p5, 10000
    %f5 = srem i64 %p5, 10000
    %c6 = sdiv i64 %p6, 10000
    %f6 = srem i64 %p6, 10000
    %c7 = sdiv i64 %p7, 10000
    %f7 = srem i64 %p7, 10000
    %ca = add i64 %c1, %c2
    %cb = add i64 %ca, %c3
    %cc = add i64 %cb, %c4
    %cd = add i64 %cc, %c5
    %ce = add i64 %cd, %c6
    %checks = add i64 %ce, %c7
    %fa = add i64 %f1, %f2
    %fb = add i64 %fa, %f3
    %fc = add i64 %fb, %f4
    %fd = add i64 %fc, %f5
    %fe = add i64 %fd, %f6
    %fails = add i64 %fe, %f7
""")
emit(W("sec_phi"))
emit(r"""    call void sec_phi()
""")
emit(W("sec_ops"))
emit(r"""    call void sec_ops()
""")
emit(W("sec_big"))
emit(r"""    call void sec_big()
    %ok = icmp.eq i64 %fails, 0
    condbr %ok, good(%fails, %checks), bad(%fails, %checks)
  good(fails: i64, checks: i64):
""")
emit(W("verdict_ok"))
emit(r"""    call void print_u64(fails)
""")
emit(W("verdict2"))
emit(r"""    call void print_u64(checks)
""")
emit(W("verdict3"))
emit(r"""    ret 0
  bad(fails: i64, checks: i64):
""")
emit(W("verdict_bad"))
emit(r"""    call void print_u64(fails)
""")
emit(W("verdict2"))
emit(r"""    call void print_u64(checks)
""")
emit(W("verdict3"))
emit(r"""    %fi = trunc i32 fails
    ret %fi
}
""")

def seed_constants(text):
    """Krell hash-conses every pure op per function: a literal first
    materialized in a non-dominating block poisons sibling uses. Seed every
    literal used in a function as an explicit const in its entry block
    (entry dominates the whole function), so all later literal uses in
    that function resolve to the entry definition."""
    import re
    lines = text.split("\n")
    res = []
    i = 0
    while i < len(lines):
        line = lines[i]
        res.append(line)
        if line.startswith("fn "):
            # collect function body until closing brace at col 0
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
            # insert seeds right after the entry block header (search res back)
            if seeds:
                for j in range(len(res) - 1, -1, -1):
                    if re.match(r"\s+entry\(.*\):\s*$", res[j]):
                        res[j + 1:j + 1] = seeds
                        break
        i += 1
    return "\n".join(res)

path = pathlib.Path(__file__).with_name("fib.krell")
text = seed_constants("\n".join(out) + "\n")
path.write_text(text)
print("wrote", path, "lines", len(text.splitlines()), "strings", len(STRINGS))
