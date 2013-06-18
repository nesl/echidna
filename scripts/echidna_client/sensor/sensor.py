
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
import matplotlib.gridspec as gridspec
import matplotlib.mlab as mlab
import tables

logger = logging.getLogger("Echidna Sensor")
hdlr = logging.StreamHandler(sys.stdout)
hdlr.setLevel(logging.DEBUG)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)

pyplot.ion()

class SensorException(Exception):
    pass

class Pos(object):
    def __init__(self, x, y, coord=(0,0)):
        self.x = x
        self.y = y
        self.coord = coord
            
    def asarray(self):
        return np.array([self.x, self.y])
        
    def astuple(self):
        return (self.x, self.y)
     
    def __str__(self):
        #Stored in mils (gantry is in inches)
        return "POSX%d_POSY%d" % (int(self.x*1000.0), int(self.y*1000.0))
        
class DataStorage(object):
    def __init__(self, filename, title="Experiment"):
        self.db = tables.openFile(filename, 'w', title=title)
        self.addExperiment("default")        
        
    def addExperiment(self,title,description="None"):
        if not hasattr(self.db.root, title):
            self.experiment = self.db.createGroup('/', title)
        else:
            self.experiment = getattr(self.db.root, title)
        self._currentExp = '/' + title
        
    def setExperiment(self, title):
        
        self._currentExp = "/" + title
        self.experiment = getattr(self.db.root, title)
    
    def getCurrentExp(self):
        return str(self.experiment).split(" ")[0]
        
    currentExp = property(getCurrentExp)
        
    def addSample(self, title):
        if not hasattr(self.experiment, title):        
            self.sample = self.db.createGroup(self.currentExp, title)
        else:
            self._currentSample = title
            self.sample = getattr(self.experiment, title)
        
    def getCurrentSample(self):
        return str(self.sample).split(" ")[0]
                
    currentSample = property(getCurrentSample)
    
    def save(self,sample):
        self.addSample(str(sample.pos))
        count = 0        
        while(1):
            if not hasattr(self.sample, "Samp%d" % count):
                break
            else:
                count = count + 1
        
        arr = self.db.createArray(self.currentSample, "Samp%d" % count, sample.data)
        arr._v_attrs.sample_rate = sample.sample_rate
        arr._v_attrs.tx_freq = sample.tx_freq
        arr._v_attrs.pos = sample.pos.asarray()
        arr._v_attrs.coord = sample.pos.coord
        logger.info("Storing %s" % sample.pos)
    
    def fileToSample(self,arr):        
        return DataSample(np.array(arr), arr._v_attrs.sample_rate, arr._v_attrs.tx_freq, arr._v_attrs.pos)
    
    def close(self):
        self.db.close()

def SampleFactory(arr):        
        return DataSample(np.array(arr), arr._v_attrs.sample_rate, arr._v_attrs.tx_freq, arr._v_attrs.pos)
        
class DataSample(object):
    def __init__(self, data, sample_rate=100000, tx_freq=5000, pos=(0,0)):        
        self.data = data
        self.sample_rate = sample_rate        
        self.tx_freq = tx_freq
        self.pos = Pos(*pos)
        (self.fftfreq,self.fftdata) = self.getFFT()       

        
    def setPos(self, pos, coord=(0,0)):
        self.pos = Pos(*pos,coord=coord)
        
    def getFFT(self):
        freqs = []
        fdatas = np.abs(fftpack.rfft(self.data,axis=1))/self.data.shape[1]*2.0               
        for fdata in fdatas:                    
            freq = fftpack.rfftfreq(int(fdata.shape[0]),1.0/self.sample_rate)                
            freqs.append(freq)
        return (np.array(freqs), fdatas)
    
    
    
    
    fdata = property(getFFT)    
        
    
    def getMaxRange(self, range = 0):
    
        freq = self.fftfreq[0]
        max_idx = np.where(freq==self.tx_freq)[0][0]
        max_range = np.arange(max_idx-range, max_idx+range)
        if range == 0:
            max_range=np.array([max_idx])
        return max_range

    def getPeakPower(self):
        #max_range = self.getMaxRange()     
        maxs = np.abs(fftpack.fft(self.data,axis=1)).max(axis=1)/self.data.shape[1]*2.0
        return maxs        
        
    def getMeanPower(self):
        return (np.abs(fftpack.fft(self.data,axis=1)).max(axis=1)/1000.0*2.0).mean(axis=0)       

    def plotPowerHist(self, bins=25):
        powers = self.getPeakPower()        
        sensor_range = np.arange(0,powers.shape[1])        
        sensor_count = len(sensor_range)
        number_of_cols = 4.0
        number_of_rows = np.int(np.ceil((len(sensor_range))/number_of_cols))
        gs = gridspec.GridSpec(int(number_of_cols), int(number_of_rows))        
        fig = pyplot.figure()
        
        axs = [ pyplot.subplot(gs[i]) for i in sensor_range]
        for i in range(len(axs)):
            axs[i].set_ylabel("Count")
            axs[i].set_xlabel("Power")
            axs[i].set_title("Sensor %d" % (i+1))
            label = "Sensor %d" % (i+1)
            mu = np.mean(powers[:,i])
            sigma = np.std(powers[:,i])
            n, bins, patches = axs[i].hist(powers[:,i],bins=bins, normed=True, label=label)
            bincenters = 0.5*(bins[1:]+bins[:-1])
            y = mlab.normpdf( bincenters, mu, sigma)
            l = axs[i].plot(bincenters, y, 'r--', linewidth=1)
        #fig.tight_layout()    
        return fig
        
    def plotRawData(self, idx=0):
        data = self.data[idx].transpose()
        t = np.arange(0,data.shape[1])*1/np.float(self.sample_rate)
        sensor_range = np.arange(0,data.shape[0])        
        sensor_count = len(sensor_range)
        number_of_cols = 4.0
        number_of_rows = np.int(np.ceil((len(sensor_range))/number_of_cols))
        gs = gridspec.GridSpec(int(number_of_cols), int(number_of_rows))        
        logger.debug("ROWS:%d, COLS:%d" % (number_of_rows, number_of_cols))
        fig = pyplot.figure()        
        axs = [ pyplot.subplot(gs[i]) for i in sensor_range]
        for i in range(len(axs)):
            axs[i].set_ylabel("Voltage (volts)")
            axs[i].set_xlabel("Time (sec)")
            axs[i].set_title("Sensor %d" % (i+1))
            axs[i].plot(t, data[i,:])
        #fig.tight_layout()
        return fig
        
    def plotFFTData(self, idx):
        fftdata = self.fftdata[idx].transpose()
        freq = self.fftfreq[idx]
        N = fftdata.shape[1]
        sensor_range = np.arange(0,fftdata.shape[0])
        sensor_count = len(sensor_range)
        number_of_cols = 4.0
        number_of_rows = np.int(np.ceil((len(sensor_range))/number_of_cols))
        gs = gridspec.GridSpec(int(number_of_cols), int(number_of_rows))        
        fig = pyplot.figure()
        
        axs = [ pyplot.subplot(gs[i]) for i in sensor_range]
        for i in range(len(axs)):
            axs[i].set_ylabel("Voltage (volts)")
            axs[i].set_xlabel("Freq (Hertz)")
            axs[i].set_title("Sensor %d" % (i+1))
            axs[i].plot(freq, fftdata[i])
        #fig.tight_layout()
        return fig

    
    def __repr__(self):
        return "Sample(x:%2.3f,y:%2.3f)" % (self.pos.astuple())

class Sensor(object):
    def __init__(self, server, port, sample_rate, tx_freq):
        self.count = 0
        self.server = server
        self.port = port
        self.sample_rate = sample_rate
        self.nyquist_rate = sample_rate/2.0
        self.tx_freq = tx_freq        
        self.server_connect_str = "tcp://%s:%d" % (self.server,self.port)
        logger.info("Connect: %s" % (self.server_connect_str))
        self.calculate_bandpass()
        
    def calculate_bandpass(self):
        # Bandpass filter
        #self.width = 10000.0/self.nyquist_rate
        #self.cutoff = 2000.0/self.nyquist_rate
        self.ripple_db = 60.0
        self.high_pass = (self.tx_freq+1000.0)/self.nyquist_rate
        self.low_pass = (self.tx_freq-1000.0)/self.nyquist_rate
        self.high_cutoff = (self.tx_freq+1500.0)/self.nyquist_rate
        self.low_cutoff = (self.tx_freq-1500.0)/self.nyquist_rate
        ord, wn = signal.buttord([self.low_pass, self.high_pass],[self.low_cutoff,self.high_cutoff],1.0,30.0)
        self.b,self.a = signal.butter(ord,wn, btype="band")

        ## Low pass filter
        #self.N, self.beta = signal.kaiserord(self.ripple_db, self.width)
        #taps = signal.firwin(N, self.cutoff/self.nyquist_rate, window=('kaiser', self.beta))
        
    def getMaxRange(self,freq):
        max_idx = np.where(freq==self.tx_freq)[0][0]
        max_range = np.arange(max_idx-10, max_idx+10)
        return max_range
        
    def getRawData(self,samples=1):
        datas = []         
        context = zmq.Context()
        self.socket = context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.SUBSCRIBE, '')        
        self.socket.connect(self.server_connect_str)
        
        for i in range(samples):
            msg = self.socket.recv_multipart()
            
            logger.info("Multiparts: %d" % len(msg))
            num_channels = struct.unpack("<I",msg[0])[0]
            logger.info("Number of channels %d" % num_channels)
            num_samples = struct.unpack("<I",msg[1])    
            logger.info("Number of Samples %d" % num_samples[0])
            logger.info("Count: %d | Length: %d " % (self.count, len(msg[2])))
            data = np.reshape(np.frombuffer(msg[2], dtype=np.float64),(-1,num_channels))
            #data = signal.lfilter(self.b,self.a,data,axis=0)
            datas.append(data)
            self.count+=1
        return np.array(datas)
    
    def getData(self,samples=1):
        datas = self.getRawData(samples)          
        return datas
    
    def getSample(self, samples=1):
        d =  self.getData(samples)
        return DataSample(d, self.sample_rate, self.tx_freq)
        

    def sampleData(self, short_len=40,long_len=1000):
        data = getData()
        if not hasattr(self,'m'):
            self.n = np.zeros((short_len,data.size))
            self.m = np.zeros((long_len,data.size))        
            self.m.fill(data)
        else:
            self.m = np.roll(self.m,1, axis=0)
            self.n = np.roll(self.n,1, axis=0)
        self.m[0,:] = data
        self.n[0,:] = data
        long = np.mean(self.m,axis=0)
        short = np.mean(self.n,axis=0)
        return np.abs(short - long)
    
    def getPeakPower(self, fdatas, freqs):
        max_range = self.getMaxRange(freqs[0])          
        maxs = np.array([np.array([np.sum(fdata[max_range,i]) for i in \
                        range(fdata.shape[1])]) for fdata in fdatas])
        return maxs

    def getMeanPower(self, fdatas, freqs):
        d = self.getPeakPower(fdatas,freqs)
        data = np.mean(d,axis=0)
        return data
        
    def plotfft(self, sensor_id = 0):
        #pyplot.plot(freq[0:fdata.shape[0]/2], fdata[0:fdata.shape[0]/2,0])
        data = getData()
        fdata = data[2]
        freq = data[3]
        pyplot.plot(freq[0:fdata.shape[0]/2],fdata[0:fdata.shape[0]/2,0])
        
        
if __name__ == "__main__":
    s = Sensor("172.17.5.180", 5555, 100000,1000)
    d = s.getSample()
    