"""Print the raw SI words the hook saw for a few stick positions (channel 0)."""
import os, sys, time, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lab import *
L = Lab('t').setup(); L.start(sys.argv[1], log='shots/boot.log')
try:
    time.sleep(15); g = Gdb(); time.sleep(20)
    for which, x, y in (('C', 0, 0), ('C', -.7, .7), ('C', 0, 1), ('C', 0, 1), ('C', .7, .7), ('C', 0, 1), ('C', 0, -1), ('C', 1, 0), ('C', -1, 0), ('MAIN', 0, 1), ('MAIN', 1, 0)):
        L.stick('gc1', 'MAIN', 0, 0); L.stick('gc1', 'C', 0, 0); L.stick('gc1', which, x, y); time.sleep(1.5)
        g.halt(); d = g.read(0x80002A20, 8); g.resume()
        h, l = struct.unpack('>II', d)
        print(which, x, y, 'main', (h >> 8 & 255) - 128, (h & 255) - 128, 'c', (l >> 24) - 128, (l >> 16 & 255) - 128, flush=True)
finally:
    L.stop()
