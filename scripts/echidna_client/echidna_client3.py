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
N, beta = signal.kaiserord(ripple_db, width)
taps = signal.firwin(N, cutoff/nyquist_rate, window=('kaiser', beta))

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

server_connect_str = "tcp://%s:%d" % (opts.server,opts.port)

print "Connect: %s" % (server_connect_str)

maxs = []

fig = pyplot.figure()
if opts.radar:
    ax = fig.add_axes([0.1,0.1,0.8,0.8], polar=True)
    lines  = ax.get_lines()
    ax.set_rmax(0.2)
else:    
    ax = pyplot.axes(xlim=(0, 8), ylim=(0, .2))
    line, = ax.plot([], [], lw=2)
#ax = pyplot.axes(xlim=(0, 500), ylim=(0, 4.0))
#line, = pyplot.plot([], [], lw=2)

def getrawdata(samples=2):
    datas = [] 
    if not hasattr(getrawdata, "count"):
        getrawdata.count = 0            
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, '')        
    socket.connect(server_connect_str)
    
    for i in range(samples):
        msg = socket.recv_multipart()
        getrawdata.count+=1
        print "Multiparts: %d" % len(msg)
        num_channels = struct.unpack("<I",msg[0])[0]
        print "Number of channels %d" % num_channels
        num_samples = struct.unpack("<I",msg[1])    
        print "Number of Samples %d" % num_samples[0]
        print "Count: %d | Length: %d " % (getrawdata.count, len(msg[2]))        
        data = np.reshape(np.frombuffer(msg[2], dtype=np.float64),(-1,num_channels))
        datas.append(data)
        #data = signal.lfilter(taps, 1.0, data, axis=0)    
        #data = signal.lfilter(b,a,data,axis=0)
    
    return datas

def plotfft(fdata, freq):
    #pyplot.plot(freq[0:fdata.shape[0]/2], fdata[0:fdata.shape[0]/2,0])
    pyplot.plot(fdata[0:fdata.shape[0]/2,0])

def getMaxRange(freq):
    max_idx = np.where(freq==tx_freq)[0][0]
    max_range = np.arange(max_idx-5, max_idx+5)
    return max_range
    
def getPeakPower(fdatas1, freqs):
    max_range = getMaxRange(freqs[0])          
    maxs = np.array([np.array([np.sum(fdata[max_range,i]) for i in range(fdata.shape[1])]) for fdata in fdatas1])
    return maxs

def getMeanPower(fdatas,freqs):
    d = getPeakPower(fdatas,freqs)
    data = np.mean(d,axis=0)
    return data
    
pyplot.ion()
    
def getData():
    datas = getrawdata() 
    fdatas = []
    freqs = []    
    for data in datas:
        fdata = np.abs(fftpack.fft(data,axis=0,n=2000)) / data.shape[0] * 2.0
        freq = fftpack.fftfreq(int(fdata.shape[0]),1.0/sample_rate)    
        fdatas.append(fdata)
        freqs.append(freq)
    maxs = getMeanPower(fdatas,freqs)
    return (maxs,datas,fdatas,freqs)

def sampleData(short_len=10,long_len=250):
    data = getData()[0]
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
    return np.abs(short - long)
    
def animate(i, plotfft=False):    
    if plotfft is True:
        y = getData()
        y = y[2][0][:,0]   
    else:
        y = sampleData() #sampleData()
        print y
    x = np.arange(y.size)                
    #if plotfft is True:            
    line.axes.relim()
    line.axes.autoscale_view(True,True,True)        
    line.set_data(x,y)
    
        
    for val in y:                
        opts.file.write("%3.6f,"% val)
    opts.file.write("\n")     
    return line
    
def animate_radar(i):    
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
            ax.plot([vec[0],vec[0]],[0,vec[1]],linewidth=2.0)    
    ax.set_rmax(0.15)
    return lines
    
    
    
    
if __name__ == "__main__":                           
    if opts.radar:
        anim = animation.FuncAnimation(fig, animate_radar, frames = 200, interval = opts.time)
    else:
        anim = animation.FuncAnimation(fig, animate, frames = 200, interval = opts.time)
    pyplot.show()

    