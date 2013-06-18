# Installing on windows 64? See http://www.lfd.uci.edu/~gohlke/pythonlibs/
import os
import sys
import time
import logging
import numpy as np
from gantry import Gantry
from sensor import Sensor, DataStorage, Pos
from transmitter import siggen
from matplotlib import pyplot as plt
from matplotlib import animation
import logging

logger = logging.getLogger("Echidna Device")
hdlr = logging.StreamHandler(sys.stdout)
hdlr.setLevel(logging.DEBUG)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)

class Echidna(object):
    
    def __init__(self, sensor_server="172.17.5.180", 
                       sensor_port=5555,
                       sensor_sample_rate=100000,
                       sensor_tx_freq=1000,
                       gantry_server="172.17.5.100", 
                       gantry_port=5007,
                       store_filename="data.log"):
        
        self.robot = Gantry(host=gantry_server,port=gantry_port)
        self.sensor = Sensor(server=sensor_server,
                        port=sensor_port,
                        sample_rate=sensor_sample_rate,
                        tx_freq=sensor_tx_freq)
                        
        self.transmitter = siggen
        self.transmitter.setFrequency(sensor_tx_freq)
        self.transmitter.setVoltage(-2,2)
        self.transmitter.turnOn()
        self._tx_freq = sensor_tx_freq
        
        self.store = DataStorage(store_filename)
        self.pos = Pos(0,0)
    
    def setStore(self,fname):
        if self.store.db.isopen:
            self.store.close()
        self.store = DataStorage(fname)
        
    def setTxFreq(self,freq):
        self._tx_freq = freq
        self.transmitter.setFrequency(freq)
        self.sensor.tx_freq = freq
        
    def stepOverTank(self,fname="tank"):
        self.pos = self.discretizeTank()
        x_size = self.pos.shape[0]
        y_size = self.pos.shape[1]
        for x in range(x_size):            
            for y in range(y_size):
                p = self.pos[x,y]                
                logger.info("Moving to (%f, %f)" % (p[0],p[1]))
                self.robot.moveAndWait(p[0],p[1], 60)
                d = self.sensor.getSample(100)
                fig, samp = self.plotRadar(5)
                fig.savefig(fname + "-x%3.2f-y%3.2f(x%d,y%d).tiff" % (p[0],p[1],x,y))
                plt.close(fig)
                d.setPos(p, (x,y))
                self.store.save(d)                
                    
    def stepOverPos(self,pos,fname="target"):
        self.count = 0
        self.pos = pos
        x_size = self.pos.shape[0]
        y_size = self.pos.shape[1]
        for x in range(x_size):            
            for y in range(y_size):
                p = self.pos[x,y]                
                logger.info("Moving to (%f, %f)" % (p[0],p[1]))
                self.robot.move(p[0],p[1], 70)
                #d = self.sensor.getSample(25)
                fig, d = self.plotRadar()
                d.setPos(p)
                self.store.save(d)                            
                fig.savefig("%d-" % self.count + fname + "-x%3.2f-y%3.2f.tiff" % (p[0],p[1]))
                plt.close(fig)                
                while(self.robot.busy()):
                    time.sleep(0.5)                
                self.count = self.count + 1
                        
    def freqSweep(self,start,stop,step=1, nsamps=100):
        self.count = 0                
        range = np.arange(start,stop,step)   
        samples = []
        for freq in range:
            logger.info("%d | Sampling frequency: %f" % (self.count,freq))
            self.setTxFreq(freq)
            d = self.sensor.getSample(nsamps)            
            d.setPos(self.pos.astuple())
            self.store.save(d)                                                                    
            self.count = self.count + 1
            samples.append(d)
        
        return samples     
        
    def discretizeTank(self, width=23.5, length=23.5, steps=50.0):
        x_steps = np.round(np.arange(0,width,width/steps),2)
        y_steps = np.round(np.arange(0,length,length/steps),2)
        pos = np.zeros((x_steps.size,y_steps.size, 2))
        for i in range(x_steps.size):
            for j in range(y_steps.size):
                pos[i][j][0] = x_steps[i]
                pos[i][j][1] = y_steps[j]
        
        return pos
         

    def learn_baseline(self, samples=250):
        self.sample_baseline = self.sensor.getSample(samples)
        
    def getDiffSignal(self, samples=10, baseline_samples=250):
        if not hasattr(self,"sample_baseline"):
            self.learn_baseline(baseline_samples)
        sample = self.sensor.getSample(samples)
        data = sample.getMeanPower()
        return (data - self.sample_baseline.getMeanPower()), sample
                
    def plotRadar(self, samples=15, baseline_samples=250):
     
        fig = plt.figure()
        ax = fig.add_axes([0.1,0.1,0.8,0.8], polar=True)
        lines  = ax.get_lines()
        ax.set_rmax(0.1)
        y, samp = self.getDiffSignal(samples, baseline_samples)
        for val in y:                
            sys.stdout.write("%3.6f,"% val)
        sys.stdout.write("\n")
                
        x = np.arange(y.size)/np.float(y.size)*np.pi*2.0
        data = zip(x,y)
        lines = ax.get_lines()
        for vec in data:
            ax.set_rmax(0.15)
            ax.plot([vec[0],vec[0]],[0,vec[1]],linewidth=3.0)    
        ax.set_rmax(0.1)
        plt.show()
        return fig, samp

        
    def __del__(self):
        self.store.close()
    
if __name__=='__main__':
    ech = Echidna()
    
    