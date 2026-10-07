import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lab import *
L = Lab('t').setup(); L.start(sys.argv[1], log='shots/boot.log')
try:
    for i in range(30):
        time.sleep(4)
        if i >= 6 and i % 3 == 0: L.press('gc1', 'A', 0.15)
        L.shot('shots/p%02d.png' % i)
finally:
    L.stop()
