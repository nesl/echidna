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
    
numpos = 36
stepsize = 0.25
xinit = 7.0
yinit = 15.5


xs = np.ones(numpos)*xinit
ys = np.arange(yinit-stepsize*numpos,yinit,stepsize)

pos = np.array([np.array(zip(xs,ys))])

if __name__=='__main__':
    ech = Echidna(store_filename="alumTarget_3in_4-7-2013_5.log")    
    
   
    
    
    