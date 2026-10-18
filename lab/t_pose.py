"""Sweep both sticks and print, per hand, the game's hand type, the vector it classifies and the pose id (channel 0)."""
import os, sys, time, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lab import *
L = Lab('t').setup(); L.start(sys.argv[1], log='shots/boot.log')
HANDS = 0x803FCC60          # per channel 1016 bytes, two hands of 508: +0 type, +8 pose, +60 normalised vector
def read(g):
    g.halt(); d = g.read(HANDS, 1016); src = g.read(0x803F8508, 8); g.resume()
    out = []
    for h in range(2):
        b = d[508 * h:]
        out.append((struct.unpack('>I', b[0:4])[0], struct.unpack('>i', b[8:12])[0],
                    tuple(round(v, 2) for v in struct.unpack('>3f', b[60:72]))))
    return src.hex(), out
dirs = [('up-left',-.7,.7),('up',0,1),('up-right',.7,.7),('left',-1,0),('neutral',0,0),('right',1,0),('down-left',-.7,-.7),('down',0,-1),('down-right',.7,-.7)]
# rings: 0-2 left column top to bottom, 3-5 right column
WANT = {'MAIN': [0, 0, 3, 1, 1, 4, 2, 2, 5], 'C': [0, 3, 3, 1, 4, 4, 2, 5, 5]}
bad = 0
try:
    time.sleep(15)
    g = Gdb()
    t0 = time.time()
    while time.time() - t0 < 240:
        s, o = read(g)
        if any(p for _, p, _ in o) or any(v != (0, 0, 0) for _, _, v in o):
            break
        time.sleep(5)
    print('ready after', int(time.time() - t0), 's', flush=True)
    for which in ('MAIN', 'C'):
        for name, x, y in dirs:
            L.stick('gc1', 'MAIN', 0, 0); L.stick('gc1', 'C', 0, 0)
            L.stick("gc1", which, x, y); time.sleep(3)
            src, hands = read(g)
            h = 0 if which == 'MAIN' else 1
            got, want = hands[h][1], WANT[which][dirs.index((name, x, y))]
            bad += got != want
            print(which, name, src, hands, 'ring', got, 'want', want, '' if got == want else 'MISMATCH', flush=True)
        L.stick('gc1', which, 0, 0)
    print('mismatches:', bad)
finally:
    L.stop()
