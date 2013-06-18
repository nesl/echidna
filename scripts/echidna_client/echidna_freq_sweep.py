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
    
if __name__=='__main__':
    ech = Echidna(store_filename="freqsweep_4-17-2013_0.log")
    #ech.robot.moveAndWait(12,12,60)
    #ech.learn_baseline()
    ech.robot.moveAndWait(0,0,60)
    
    