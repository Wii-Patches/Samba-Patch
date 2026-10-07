import os,sys,time,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lab import *
L=Lab('t').setup()
L.start(sys.argv[1], log='shots/boot.log')
def dump(g,addr,n):
    d=g.read(addr,n)
    for i in range(0,n,16):
        print('%08x  %s'%(addr+i,d[i:i+16].hex(' ',4)))
try:
    time.sleep(25)
    L.press('wm1','A',0.3)
    time.sleep(6)
    g=Gdb(); g.halt()
    print('status ch0'); dump(g,0x803f8a50,0x84*2)
    print('cfg'); dump(g,0x803f8508,16)
    print('counts'); dump(g,0x803fcc50,16)
    g.resume(); time.sleep(0.5); L.shot('shots/p1.png')
finally:
    L.stop()
