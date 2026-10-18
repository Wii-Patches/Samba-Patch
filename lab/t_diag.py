"""Boot the patched disc; check the hook's left-hand vector for neutral / diagonal / cardinal sticks."""
import os, sys, time, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lab import *
L = Lab('t').setup(); L.start(sys.argv[1], log='shots/boot.log')
def vecs(g):
    g.halt(); d = g.read(0x803F8A50, 0x2200); g.resume()
    out = set()
    for o in range(0, len(d) - 0x74, 4):
        out.add(struct.unpack('>3f', d[o + 0x68 - 0:o + 0x68 + 12]))
    return d
def left_acc(g):
    g.halt(); d = g.read(0x803F8A50, 0x84); g.resume()
    return struct.unpack('>3f', d[0x68:0x74]), struct.unpack('>3f', d[0x0C:0x18])
try:
    time.sleep(70)
    g = Gdb()
    for label, x, y in (('neutral', 0, 0), ('up', 0, 1), ('left', -1, 0), ('up-left', -.7, .7), ('down-right', .7, -.7), ('up shallow', -.3, .9)):
        L.stick('gc1', 'MAIN', x, y); time.sleep(3)
        print(label, 'left acc / right acc', left_acc(g), flush=True)
finally:
    L.stop()
