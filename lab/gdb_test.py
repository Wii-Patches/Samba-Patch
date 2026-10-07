import os,sys,time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lab import *
L=Lab('t').setup()
L.start(sys.argv[1], log='shots/boot.log')
try:
    time.sleep(12)
    g=Gdb()
    print('connected')
    print(g.read(0x80000000,8))
    g.resume(); time.sleep(10)
    g.halt()
    st=g.read(0x8056ad78,0x538)
    print(st[:64].hex())
    print(g.read(0x803f8508,16).hex())
    g.resume()
    time.sleep(1)
    L.shot('shots/g.png')
finally:
    L.stop()
