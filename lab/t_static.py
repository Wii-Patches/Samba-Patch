"""Boot a statically patched disc and check the pad hook is live and driven by a GC pad."""
import os, sys, time, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lab import *
os.makedirs('shots', exist_ok=True)
L = Lab('t').setup()
L.start(sys.argv[1], log='shots/boot.log')
def state(g, ch=0):
    g.halt(); st = struct.unpack('>16I', g.read(0x80002A00 + 0x40 * ch, 0x40)); g.resume(); return st
try:
    time.sleep(20)
    g = Gdb()
    for i in range(10):
        s = state(g); print(i*5, 'magic %08x frames %d' % (s[0], s[10]), flush=True)
        if s[0]: break
        time.sleep(5)
    L.shot('shots/st0.png')
    for label, act in (('A', lambda: L.send('gc1', 'PRESS A')), ('A up', lambda: L.send('gc1', 'RELEASE A')),
                       ('stick right', lambda: L.stick('gc1', 'MAIN', 1, 0)), ('stick 0', lambda: L.stick('gc1', 'MAIN', 0, 0))):
        act(); time.sleep(1.5); s = state(g)
        print(label, 'hold %08x ptr(%d,%d) frames %d' % (s[1], struct.unpack('>i', struct.pack('>I', s[2]))[0], struct.unpack('>i', struct.pack('>I', s[3]))[0], s[10]))
    L.shot('shots/st1.png')
finally:
    L.stop()
