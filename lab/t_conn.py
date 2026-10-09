"""GC pad only (no Wii Remote): are the game's own connection bits set?

USA values; for Europe the same, for Japan CONNOFF=-22415 CONNST=0x803F9B70 R13=<its r13>.
Prints the two bit bytes (Wii Remote byte, then Nunchuk/remote byte), connected[0], and the hook's claim/quiet/frame counters.
"""
import os, sys, time, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lab import *
os.makedirs('shots', exist_ok=True)
OFF = int(os.environ.get('CONNOFF', '-22479')); ST = int(os.environ.get('CONNST', str(0x803F8518)), 0)
L = Lab('t').setup(wiimotes=int(os.environ.get('WM', '0'))); L.start(sys.argv[1], log='shots/boot.log')
def look(g):
    g.halt(); g.drain(); r13 = int(os.environ.get('R13', '0x8057c560'), 0)
    m = g.read(r13 + OFF - 1, 2); c0 = struct.unpack('>I', g.read(ST, 4))[0]
    h = struct.unpack('>16I', g.read(0x80002A00, 0x40))
    g.resume(); return r13, m.hex(), c0, h[11], h[12], h[10]
try:
    time.sleep(25); g = Gdb()
    for i in range(6):
        print('r13 %08x  [remote-byte, mask-byte]=%s  connected[0]=%d  claim=%d quiet=%d frames=%d' % look(g), flush=True)
        time.sleep(4)
finally:
    try: L.stop()
    except Exception as e: print('stop', e)
