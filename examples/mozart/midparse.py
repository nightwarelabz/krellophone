import struct, json, sys

def read_vlq(b, i):
    v = 0
    while True:
        x = b[i]; i += 1
        v = (v << 7) | (x & 0x7f)
        if not (x & 0x80):
            return v, i

def parse(path):
    b = open(path, 'rb').read()
    assert b[:4] == b'MThd'
    fmt, ntrk, div = struct.unpack('>HHH', b[8:14])
    i = 14
    tracks = []
    tempos = []
    for _ in range(ntrk):
        assert b[i:i+4] == b'MTrk'
        ln = struct.unpack('>I', b[i+4:i+8])[0]
        i += 8
        end = i + ln
        t = 0
        running = None
        notes = []
        open_notes = {}
        while i < end:
            delta, i = read_vlq(b, i)
            t += delta
            st = b[i]
            if st & 0x80:
                running = st; i += 1
            else:
                st = running
            hi = st & 0xf0
            ch = st & 0x0f
            if st == 0xff:
                mt = b[i]; i += 1
                ml, i = read_vlq(b, i)
                data = b[i:i+ml]; i += ml
                if mt == 0x51:
                    tempos.append((t, int.from_bytes(data, 'big')))
                running = None
            elif st in (0xf0, 0xf7):
                ml, i = read_vlq(b, i)
                i += ml
                running = None
            elif hi == 0x90 or hi == 0x80:
                note, vel = b[i], b[i+1]; i += 2
                if hi == 0x90 and vel > 0:
                    open_notes.setdefault((ch, note), []).append((t, vel))
                else:
                    lst = open_notes.get((ch, note), [])
                    if lst:
                        st0, v0 = lst.pop(0)
                        notes.append((st0, t, note, v0, ch))
            elif hi in (0xa0, 0xb0, 0xe0):
                i += 2
            elif hi in (0xc0, 0xd0):
                i += 1
            else:
                raise ValueError(f'bad status {st:#x} at {i}')
        tracks.append(notes)
    return fmt, div, tempos, tracks

if __name__ == '__main__':
    fmt, div, tempos, tracks = parse('rondo.mid')
    allnotes = [n for tr in tracks for n in tr]
    print('format', fmt, 'division', div, 'tempos', tempos)
    print('tracks with notes:', [len(tr) for tr in tracks])
    print('total notes:', len(allnotes))
    pitches = [n[2] for n in allnotes]
    print('pitch range:', min(pitches), 'to', max(pitches))
    last = max(n[1] for n in allnotes)
    print('last tick:', last, 'quarter beats:', last / div)
    tempo = tempos[0][1] if tempos else 500000
    secs = last / div * tempo / 1e6
    print('duration at tempo', tempo, 'us/beat:', round(secs, 1), 's')
    names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    def nm(m): return names[m % 12] + str(m // 12 - 1)
    first = sorted([n for n in allnotes if n[0] < div * 2], key=lambda n: (n[0], -n[2]))
    print('first 2 beats:')
    for n in first[:20]:
        print('  tick', n[0], nm(n[2]), 'vel', n[3], 'dur', n[1] - n[0], 'ch', n[4])
    # bar count in 2/4: beats/2
    print('bars (2/4):', last / div / 2)
    json.dump({'div': div, 'tempos': tempos,
               'tracks': tracks}, open('score.json', 'w'))
    print('score.json written')
