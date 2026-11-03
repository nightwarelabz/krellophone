import json, math

SR = 44100
BPM = 76.0
SPT = SR * 60.0 / (BPM * 384)          # samples per tick = 90.6667
BAR = 768                               # ticks per 2/4 bar

d = json.load(open('score.json'))
notes = []
for tr in d['tracks']:
    for (s, e, n, v, ch) in tr:
        notes.append({'s': s, 'e': e, 'n': n, 'ch': ch})
notes.sort(key=lambda x: (x['s'], x['ch'], x['n']))

def base_vel(bar1):
    if bar1 <= 16: return 64
    if bar1 <= 24: return 70
    if bar1 <= 32: return 88
    if bar1 <= 40: return 68
    if bar1 <= 48: return 72
    if bar1 <= 56: return 76
    if bar1 <= 64: return 90
    if bar1 <= 80: return 66
    if bar1 <= 88: return 72
    if bar1 <= 96: return 90
    if bar1 <= 108: return 86
    if bar1 <= 116: return 92
    return 88

FORTE_BARS = set(range(25, 33)) | set(range(57, 65)) | set(range(89, 97)) | set(range(109, 117))
BIG_BARS = {27, 31, 59, 63, 91, 95, 116}

def h2(i, k):
    x = (i * 2654435761 + k * 40503) & 0xffffffff
    x ^= x >> 13; x = (x * 1103515245) & 0xffffffff; x ^= x >> 16
    return x

events = []
for i, nt in enumerate(notes):
    bar1 = nt['s'] // BAR + 1
    bv = base_vel(bar1)
    if bar1 in BIG_BARS: bv += 7
    pos = nt['s'] % BAR
    if pos == 0: bv += 4
    elif pos == 384: bv += 1
    elif pos % 192 == 96: bv -= 3
    bv += [0, 2, 4, 1][(bar1 - 1) % 4]
    if nt['ch'] == 1 and bar1 not in FORTE_BARS: bv -= 6
    bv += (h2(i, 1) % 7) - 3
    vel = max(30, min(112, bv))
    st = nt['s'] + (h2(i, 2) % 5) - 2
    if nt['s'] == 0: st = 0
    start = int(round(st * SPT))
    dur = max(1, int(round((nt['e'] - nt['s']) * SPT)))
    events.append((start, dur, nt['n'], vel))

events.sort(key=lambda x: x[0])
NEV = len(events)
piece_samples = math.ceil(255 * SR * 60.0 / BPM)
TOTAL = piece_samples + int(2.5 * SR)
print('events', NEV, 'piece_samples', piece_samples, 'TOTAL', TOTAL,
      'duration', round(TOTAL / SR, 2), 's')

def decl(name, ty, vals, per=16):
    out = [f'data {name}: {ty} = {{']
    for i in range(0, len(vals), per):
        out.append('  ' + ', '.join(str(v) for v in vals[i:i+per]) + (',' if i + per < len(vals) else ''))
    out.append('}')
    return '\n'.join(out)

with open('tables.inc', 'w') as f:
    f.write(decl('evstart', 'i32', [e[0] for e in events]) + '\n')
    f.write(decl('evdur', 'i32', [e[1] for e in events]) + '\n')
    f.write(decl('evnote', 'i8', [e[2] for e in events]) + '\n')
    f.write(decl('evvel', 'i8', [e[3] for e in events]) + '\n')
    f.write(decl('evpreset', 'i8', [0] * len(events)) + '\n')
    f.write(decl('evcount', 'i32', [len(events)]) + '\n')

# music-energy envelope at 24 fps for the visual program
FPS = 24
nframes = math.ceil(TOTAL / SR * FPS)
spf = SR / FPS
level = [0.0] * nframes
tau_f = 0.30 * FPS
for (start, dur, n, vel) in events:
    f0 = int(start / spf)
    w = vel * vel
    f = f0
    while f < nframes:
        level[f] += w * math.exp(-(f - f0) / tau_f)
        if f - f0 > 90: break
        f += 1
mx = sorted(level)[int(len(level) * 0.995)]
env = [max(0, min(255, int(round(255 * (l / mx) ** 0.7)))) for l in level]
with open('envelope.inc', 'w') as f:
    f.write(decl('env24', 'i8', env) + '\n')
print('envelope frames', nframes, 'env max', max(env), 'env mean', round(sum(env) / len(env), 1))
json.dump({'total': TOTAL, 'nev': NEV, 'events': events}, open('events.json', 'w'))
