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

logger = logging.getLogger("Echidna Client")
hdlr = logging.StreamHandler(sys.stdout)
hdlr.setLevel(logging.DEBUG)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)

tx_freq = 5000.0
sample_rate = 100000.0
nyquist_rate = sample_rate/2.0
width = 10000.0/nyquist_rate
cutoff = 2000.0/nyquist_rate
ripple_db = 60.0

# Bandpass filter
high_pass = (tx_freq+100.0)/nyquist_rate
low_pass = (tx_freq-100.0)/nyquist_rate
high_cutoff = (tx_freq+300.0)/nyquist_rate
low_cutoff = (tx_freq-300.0)/nyquist_rate
ord, wn = signal.buttord([low_pass, high_pass],[low_cutoff,high_cutoff],1.0,30.0)
b,a = signal.butter(ord,wn, btype="band")

## Low pass filter
#N, beta = signal.kaiserord(ripple_db, width)
#taps = signal.firwin(N, cutoff/nyquist_rate, window=('kaiser', beta))

parser = argparse.ArgumentParser(description="Echidna client")
parser.add_argument('--server', '-s', type=str, default = "localhost",
                    help="select the server to connect to")
parser.add_argument('--port','-p',type=int, default=5555,
                    help="select the port to connect to")

parser.add_argument('--file','-f',type=argparse.FileType('a'),default=sys.stdout,
                    help="file to write to")

parser.add_argument('--time','-t',type=int,default=10,
                    help="experiment duration")
                    

opts = parser.parse_args()

server_connect_str = "tcp://%s:%d" % (opts.server,opts.port)

print "Connect: %s" % (server_connect_str)

maxs = []

fig = pyplot.figure()
ax = pyplot.axes(xlim=(0, 8), ylim=(0, .1))
line, = ax.plot([], [], lw=2)


def getrawdata():
    if not hasattr(getrawdata, "count"):
        getrawdata.count = 0            
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, '')        
    socket.connect(server_connect_str)
    msg = socket.recv_multipart()
    socket.close()
    getrawdata.count+=1
    print "Multiparts: %d" % len(msg)
    num_channels = struct.unpack("<I",msg[0])[0]
    print "Number of channels %d" % num_channels
    num_samples = struct.unpack("<I",msg[1])    
    print "Number of Samples %d" % num_samples[0]
    print "Count: %d | Length: %d " % (getrawdata.count, len(msg[2]))        
    data = np.reshape(np.frombuffer(msg[2], dtype=np.float64),(-1,num_channels))
    #data = signal.lfilter(taps, 1.0, data, axis=0)    
    #data = signal.lfilter(b,a,data,axis=0)
    return data
    
def getdata():
    global maxs    
    data = getrawdata()
    fdata = np.abs(fftpack.fft(data,axis=0)) / data.shape[0] * 2.0
    if not hasattr(getdata, "freqs"):         
        getdata.freqs = fftpack.fftfreq(int(fdata.shape[0]),1.0/sample_rate)
        getdata.max_idx = np.where(getdata.freqs==tx_freq)[0][0]        
    maxs = fdata[getdata.max_idx]
    return maxs
    
def getbaseline():
    data = getdata()
    if not hasattr(getbaseline,'m'):
        getbaseline.n = np.zeros((10,data.size))
        getbaseline.m = np.zeros((100,data.size))
    else:
        getbaseline.m = np.roll(getbaseline.m,1, axis=0)
        getbaseline.n = np.roll(getbaseline.n,1, axis=0)
    getbaseline.m[0,:] = data
    getbaseline.n[0,:] = data
    long = np.mean(getbaseline.m,axis=0)
    short = np.mean(getbaseline.n,axis=0)
    return np.abs(short - long)
    
    
def main():
    data = getrawdata() 
    return data
    while(True):
               
        for val in data:        
            opts.file.write("%3.6f,"% val)
        opts.file.write("\n")        
        time.sleep(opts.time)
    
    

def animate(i):        
    #y = getdata()
    y = getbaseline()
    x = np.arange(y.size)                
    line.set_data(x,y)
    for val in y:        
        opts.file.write("%3.6f,"% val)
    opts.file.write("\n")     
    return line
    # simulate new data coming in
    
#    for rect, h in zip(rects, maxs):
        #rect.set_height(h)
    #fig.canvas.draw()
        
if __name__ == "__main__":                        
    
    anim = animation.FuncAnimation(fig, animate, frames = 200, interval = opts.time)    
    pyplot.show()
    """
    data = main()    
    fdata = np.abs(fftpack.fft(data,axis=0)) / data.shape[0] * 2.0    
    freqs = fftpack.fftfreq(int(fdata.shape[0]),1.0/sample_rate)    
    pyplot.plot(freqs[0:fdata.shape[0]/2], fdata[0:fdata.shape[0]/2,0])
    pyplot.show()
    """