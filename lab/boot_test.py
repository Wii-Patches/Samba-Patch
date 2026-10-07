import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lab import Lab

os.makedirs('shots', exist_ok=True)
L = Lab('t').setup()
L.start(sys.argv[1], log='shots/boot.log')
try:
    for i in range(6):
        time.sleep(8)
        print(i, 'alive', L.alive(), L.windows())
        L.shot('shots/boot%d.png' % i)
finally:
    L.stop()
