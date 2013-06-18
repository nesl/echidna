# Installing on windows 64? See http://www.lfd.uci.edu/~gohlke/pythonlibs/
import os
import sys
import time
import argparse
import logging
import numpy as np
import tables
from sensor import SampleFactory
from matplotlib import pyplot

logger = logging.getLogger("Echidna Data Parser")
hdlr = logging.StreamHandler(sys.stdout)
hdlr.setLevel(logging.DEBUG)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)         

parser = argparse.ArgumentParser(description="Echidna Data Parser")

parser.add_argument('--file','-f',type=str,
                    help="file to read")

opts = parser.parse_args()

pyplot.ion()

def plotLine(samples):
    a = [s for s in samples if s.pos.x == samples[12].pos.x]
    b = sorted(a, key = lambda o: o.pos.y)
    m = [n.getMeanPower() for n in b]
    pyplot.plot(m)
    
def sortx(samples):
    return sorted(samples, key = lambda o: o.pos.x)

def sorty(samples):
    return sorted(samples, key = lambda o: o.pos.y)
    

#    a = [v.getMeanPower() for v in sorted([s for s in samples if s.pos.y == samples[10].pos.y],key=lambda o :o.pos.x)];pyplot.plot(a)    
if __name__=='__main__':
    db = tables.openFile(opts.file,'r')
    samples = [SampleFactory(node.Samp0) for node in db.root.default]
    #samples = []
    #for node in db.root.default:
        #sample = SampleFactory(node.Samp0)
        #samples.append(sample)
        
   
    
    
    