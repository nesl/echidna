# Installing on windows 64? See http://www.lfd.uci.edu/~gohlke/pythonlibs/
import sys
import os
import time
import argparse
import logging
import datetime
import zmq
import struct
import numpy as np
import scipy
from scipy import fftpack
from scipy import signal
from matplotlib import pyplot
from matplotlib import animation
from echidna import Echidna


logger = logging.getLogger("Echidna Client")
hdlr = logging.StreamHandler(sys.stdout)
hdlr.setLevel(logging.DEBUG)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)         


parser = argparse.ArgumentParser(description="Echidna client")
parser.add_argument('--server', '-s', type=str, default = "localhost",
                    help="select the server to connect to")
parser.add_argument('--port','-p',type=int, default=5555,
                    help="select the port to connect to")

parser.add_argument('--file','-f',type=argparse.FileType('a'),default=sys.stdout,
                    help="file to write to")

parser.add_argument('--time','-t',type=int,default=10,
                    help="experiment duration")

parser.add_argument('--radar','-r',action="store_true",default=False,
                    help="radar plot")
                                        

opts = parser.parse_args()


fig = pyplot.figure()

ax = fig.add_axes([0.1,0.1,0.8,0.8], polar=True)
lines  = ax.get_lines()
ax.set_rmax(0.1)

ech = Echidna(store_filename="temp.log")  


def sampleData(short_len=10,long_len=250):
    if not hasattr(sampleData,'sample_baseline'):
        sampleData.sample_baseline = ech.sensor.getSample(long_len)
        sampleData.baseline = sampleData.sample_baseline.getMeanPower()
        
    sample = ech.sensor.getSample(short_len)
    data = sample.getMeanPower()    
    
    return data - sampleData.baseline


def animate(i):    
    y = sampleData()
    
    for val in y:                
        opts.file.write("%3.6f,"% val)
    opts.file.write("\n")
    
    x = np.arange(y.size)/np.float(y.size)*np.pi*2.0
    data = zip(x,y)
    lines = ax.get_lines()
    if lines:
        for line in zip(data, lines):
            line[1].set_data([line[0][0],line[0][0]], [0, line[0][1]])
    else:
        for vec in data:
            ax.set_rmax(0.15)
            ax.plot([vec[0],vec[0]],[0,vec[1]],linewidth=3.0)    
    ax.set_rmax(0.1)
    return lines
    
    
if __name__=='__main__':
        
    ech.robot.moveAndWait(12.0,12.0)
    anim = animation.FuncAnimation(fig, animate, frames = 200, interval = opts.time)
    pyplot.show()    
    
   
    
    
    