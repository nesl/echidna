# Installing on windows 64? See http://www.lfd.uci.edu/~gohlke/pythonlibs/
import os
import sys
import time
import logging
import numpy as np
from echidna import Echidna

logger = logging.getLogger("Echidna Client")
hdlr = logging.StreamHandler(sys.stdout)
hdlr.setLevel(logging.DEBUG)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)         
    
numpos = 24
stepsize = 0.5
xinit = 6.0
yinit = 5.0


xs = np.ones(numpos)*xinit
ys = np.arange(yinit,yinit+stepsize*numpos,stepsize)

pos = np.array([np.array(zip(xs,ys))])

if __name__=='__main__':
    ech = Echidna(store_filename="pvcTarget_4-5-2013_2.log")    
    
   
    
    
    