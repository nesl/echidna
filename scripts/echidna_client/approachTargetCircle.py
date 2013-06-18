# Installing on windows 64? See http://www.lfd.uci.edu/~gohlke/pythonlibs/
import os
import sys
import time
import logging
import argparse
import numpy as np
from echidna import Echidna

logger = logging.getLogger("Echidna Client")
hdlr = logging.StreamHandler(sys.stdout)
hdlr.setLevel(logging.DEBUG)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)         
    
    
    
#fname= "alumTarget_2in_circle_x12in_y12in_4.5in_radius_4-7-2013_5"

parser = argparse.ArgumentParser(description="Echidna client")
parser.add_argument('--file','-f',type=str,default="experiment",
                    help="file to write to")

opts = parser.parse_args()    

numpos = 36
numsteps = 32.0
xinit = 12.0
yinit = 12.0
radius = 8.0

xs = radius*np.cos(np.arange(0, 1, 1.0/numsteps)*2*np.pi)+xinit
ys = radius*np.sin(np.arange(0, 1, 1.0/numsteps)*2*np.pi)+yinit


pos = np.array([np.array(zip(xs,ys))])


def demo(ech):
    ech.robot.moveAndWait(6,6,70)
    ech.plotRadar()
    ech.robot.moveAndWait(22,0,70)
    #for p in pos[0]:
    #    ech.robot.moveAndWait(p[0],p[1],70)   
    #ech.robot.moveAndWait(22,0,70)

if __name__=='__main__':    
    
    ech = Echidna(store_filename=opts.file)            
    demo(ech)
    ech.stepOverPos(pos,opts.file)
    ech.store.close()
    ech.robot.moveAndWait(14,6,70)
    ech.robot.goHome()
    