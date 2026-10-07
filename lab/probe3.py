import os,sys,time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lab import *
L=Lab('t').setup()
L.start(sys.argv[1], log='shots/boot.log')
try:
    time.sleep(10)
    g=Gdb()
    for i in range(6):
        g.halt()
        r=gdb_regs(g); print(i, hex(r['pc'] or 0), 'sp',hex(r['r1']))
        g.resume()
        L.shot('shots/r%d.png'%i)
        time.sleep(8)
finally:
    L.stop()
