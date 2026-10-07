import os,sys,time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lab import *
L=Lab('t').setup()
L.start(sys.argv[1], log='shots/boot.log')
try:
    t0=time.time()
    for i in range(24):
        time.sleep(5)
        if i>=4 and i%2==0: L.press('wm1','A',0.3)
        L.shot('shots/q%02d.png'%i)
finally:
    L.stop()
