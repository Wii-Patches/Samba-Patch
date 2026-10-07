import os,sys,time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lab import *
L=Lab('t').setup()
L.start(sys.argv[1], log='shots/boot.log')
try:
    time.sleep(40)
    g=Gdb()
    for label,act in (('idle',None),('A',lambda:L.send('gc1','PRESS A')),('stick up',lambda:(L.send('gc1','RELEASE A'),L.stick('gc1','MAIN',0,1))),('Cstick right + L',lambda:(L.stick('gc1','MAIN',0,0),L.stick('gc1','C',1,0),L.send('gc1','PRESS L'))),('p2 A',lambda:(L.send('gc1','RELEASE L'),L.stick('gc1','C',0,0),L.send('gc2','PRESS A')))):
        if act: act()
        time.sleep(1.5)
        g.halt()
        for port in (0,1):
            d=g.read(0xCD006404+12*port,8)
            print(label,'port',port,d.hex(' ',4))
        g.resume()
    g.halt(); print('SIPOLL',g.read(0xCD006430,4).hex(),'SICOMCSR',g.read(0xCD006434,4).hex(),'SISR',g.read(0xCD006438,4).hex())
    g.resume()
finally:
    L.stop()
