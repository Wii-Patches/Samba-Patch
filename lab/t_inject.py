import os,sys,time,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','src'))
from lab import *
import gen_pads
L=Lab('t').setup()
L.start(sys.argv[1], log='shots/boot.log')
def dump(g,addr,n):
    d=g.read(addr,n)
    for i in range(0,n,16): print('%08x  %s'%(addr+i,d[i:i+16].hex(' ',4)))
try:
    time.sleep(8)
    g=Gdb(); g.halt()
    inject(g, gen_pads.make('R3BE8P',0x80116DAC,0x802F5948))
    print('injected'); g.resume()
    # sit through boot; poll the frame counter of channel 0 state
    for i in range(40):
        time.sleep(3)
        g.halt()
        st=g.read(0x80002A00,0x40)
        w=struct.unpack('>16I',st)
        print(i,'magic %08x frames %d prevhold %x h=%08x l=%08x'%(w[0],w[10],w[1],w[8],w[9]))
        g.resume()
        if i>=3: L.press('wm1','A',0.25)
    g.halt(); dump(g,0x803f8a50,0x84); g.resume()
finally:
    L.stop()
