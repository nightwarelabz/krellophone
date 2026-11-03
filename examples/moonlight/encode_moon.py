#!/usr/bin/env python3
"""Encode the Mutopia Moonlight Sonata (mvt 1) score into Krell engine
tables, with editorial dynamics (the score MIDI is uniformly vel 127):
melody sings, triplets murmur, bass is the floor; one long phrase arch
over the movement, light humanization. Also exports the event list for
the film program's in-Krell audio analysis."""
import json, math

SR = 44100
DIV = 384
TEMPO_US = 1000000                      # MIDI tempo meta: 60 quarters/min
SPT = SR * (TEMPO_US / 1e6) / DIV       # 114.84375 samples per tick
BAR = 4 * DIV                           # 4/4

d = json.load(open('score.json'))
notes = []
for tr in d['tracks']:
    for (s, e, n, v, ch) in tr:
        notes.append({'s': s, 'e': e, 'n': n, 'ch': ch})
notes.sort(key=lambda x: (x['s'], x['ch'], x['n']))
print('notes', len(notes))

def h2(i, k):
    x = (i * 2654435761 + k * 40503) & 0xffffffff
    x ^= x >> 13; x = (x * 1103515245) & 0xffffffff; x ^= x >> 16
    return x

events = []
for i, nt in enumerate(notes):
    bar1 = nt['s'] // BAR + 1
    dur_ticks = nt['e'] - nt['s']
    if nt['ch'] == 2:
        role, base = 'bass', 62
    elif dur_ticks >= 300:
        role, base = 'melody', 88
    else:
        role, base = 'triplet', 52
    # one long arch over 69 bars + gentle 8-bar breathing
    arch = 1.0 + 0.17 * math.sin(math.pi * (bar1 - 1) / 68.0) ** 2
    arch *= 1.0 + 0.04 * math.sin(2 * math.pi * (bar1 - 1) / 8.0)
    if bar1 <= 4:
        arch *= 0.92                      # the opening murmur
    if bar1 >= 65:
        arch *= 0.94                      # receding close
    vel = base * arch
    if role == 'triplet' and (nt['s'] % 384) == 0:
        vel += 3                          # beat-head triplet breathes
    vel += (h2(i, 1) % 5) - 2
    vel = int(round(max(28, min(114, vel))))
    st = nt['s'] + ((h2(i, 2) % 3) - 1)   # +-1 tick humanization
    if nt['s'] == 0:
        st = 0
    start = int(round(st * SPT))
    dur_s = dur_ticks * SPT
    if role == 'bass':
        dur_s *= 1.5                      # pedal resonance
    dur = max(1, int(round(dur_s)))
    events.append((start, dur, nt['n'], vel))

events.sort(key=lambda x: x[0])
NEV = len(events)
last_tick = max(nt['e'] for nt in notes)
piece_samples = int(round(last_tick * SPT))
TOTAL = piece_samples + int(3.0 * SR)
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

json.dump({'total': TOTAL, 'sr': SR, 'nev': NEV, 'events': events},
          open('events.json', 'w'))
print('tables.inc + events.json written')
