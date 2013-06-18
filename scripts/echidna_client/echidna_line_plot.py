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
ax = pyplot.axes(xlim=(0, 8), ylim=(-.15, .15))
line, = ax.plot([], [], lw=2)    

ech = Echidna(store_filename="temp.log")  

def sampleData_roll(short_len=20,long_len=250):
    sample = ech.sensor.getSample(1)
    data = sample.getMeanPower()    
    if not hasattr(sampleData,'m'):
        sampleData.n = np.zeros((short_len,data.size))
        sampleData.m = np.zeros((long_len,data.size))        
        sampleData.m.fill(data[0])
    else:
        sampleData.m = np.roll(sampleData.m,1, axis=0)
        sampleData.n = np.roll(sampleData.n,1, axis=0)
    sampleData.m[0,:] = data
    sampleData.n[0,:] = data
    long = np.mean(sampleData.m,axis=0)
    short = np.mean(sampleData.n,axis=0)
    return short - long

def sampleData(short_len=20,long_len=250):
    if not hasattr(sampleData,'sample_baseline'):
        sampleData.sample_baseline = ech.sensor.getSample(long_len)
        sampleData.baseline = sampleData.sample_baseline.getMeanPower()
        
    sample = ech.sensor.getSample(short_len)
    data = sample.getMeanPower()    
    
    return data - sampleData.baseline

    
def animate(i, plotfft=False):    

    y = sampleData() #sampleData()
    x = np.arange(y.size)                
    #if plotfft is True:            
    line.axes.relim()
    line.axes.autoscale_view(True,True,True)        
    line.set_data(x,y)
    
        
    for val in y:                
        opts.file.write("%3.6f,"% val)
    opts.file.write("\n")     
    return line

    
if __name__=='__main__':
    
    anim = animation.FuncAnimation(fig, animate, frames = 200, interval = opts.time)
    pyplot.show()    
    
   
    
    
    