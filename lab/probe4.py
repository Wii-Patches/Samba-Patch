import os,sys,time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lab import *
from PIL import Image
L=Lab('t').setup()
L.start(sys.argv[1], log='shots/boot.log')
def dump(g,addr,n):
    d=g.read(addr,n)
    for i in range(0,n,16): print('%08x  %s'%(addr+i,d[i:i+16].hex(' ',4)))
try:
    time.sleep(10)
    g=Gdb()
    shots=[]
    for i in range(30):
        g.halt(); g.resume(); time.sleep(0.3)
        p='shots/s%02d.png'%i; L.shot(p); shots.append(p)
        if i>=3: L.press('wm1','A',0.25)
        time.sleep(4.5)
    g.halt()
    print('status ch0'); dump(g,0x803f8a50,0x84)
    print('cfg'); dump(g,0x803f8508,16)
    print('kpad0'); dump(g,0x8056ad78,0x60)
    g.resume()
    ims=[Image.open(f).convert('RGB').resize((256,203)) for f in shots]
    W=Image.new('RGB',(256*6,203*5))
    for i,im in enumerate(ims): W.paste(im,((i%6)*256,(i//6)*203))
    W.save('shots/sheet.png')
finally:
    L.stop()
