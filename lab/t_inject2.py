import os,sys,time,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','src'))
from lab import *
import gen_pads
L=Lab('t').setup()
L.start(sys.argv[1], log='shots/boot.log')
try:
    time.sleep(8)
    g=Gdb(); g.halt()
    inject(g, gen_pads.make('R3BE8P',0x80116DAC,0x802F5948,-22479,0x803F8518))
    g.resume()
    for i in range(8):
        time.sleep(4)
        g.halt()
        r=gdb_regs(g)
        st=struct.unpack('>16I',g.read(0x80002A00,0x40))
        print(i,'pc %s lr? sp %08x frames %d'%(hex(r['pc'] or 0),r['r1'],st[10]))
        g.resume(); time.sleep(0.2); L.shot('shots/i%d.png'%i)
finally:
    L.stop()
