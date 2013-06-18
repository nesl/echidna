import os
import sys
import time
import telnetlib
import logging
import numpy as np

logger = logging.getLogger("Echidna Robot")
hdlr = logging.StreamHandler(sys.stdout)
hdlr.setLevel(logging.DEBUG)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)

class Gantry(object):    
    timeout = 1
    def __init__(self, host="172.17.5.100", port=5007):
        self.host = host
        self.port = port
        self.con = telnetlib.Telnet(host, port, self.timeout)
        self.con.set_debuglevel(9999)
        self.verbose = False
        #self.con.open()
        time.sleep(1.0)
        self.send_command("hello EMC 1 1")        
        self.send_command("set enable EMCTOO")
        self.set_verbose()
        self.send_command("set mode manual")
        self.send_command("set home 0")
        self.send_command("set home 1")
        self.send_command("set home 2")
        self.send_command("set mode mdi")
        self._x = 0.0
        self._y = 0.0
        
    
    def set_verbose(self):
        self.verbose = True
        self.send_command("set verbose on")
        
    def home(self):
        self.send_command("set mode manual")
        self.send_command("set home 0")
        self.send_command("set home 1")
        self.send_command("set home 2")
        self.send_command("set mode mdi")
    
    def send_command(self,msg):
        logger.info("SENT: %s" % msg)
        self.con.write("%s\r\n" % msg)
        if self.verbose:
            resp_v = self.con.read_until("\n", self.timeout)
            logger.info("RECV: %s" % resp_v)
        resp = self.con.read_until("\n", self.timeout)
        logger.info("RECV: %s" % resp)
        
        return resp
            
    def check_pos(self,x,y):
        resp = self.send_command("get abs_act_pos")        
        #import pdb; pdb.set_trace()
        vals = resp.split(" ")
        x_ = np.round(float(vals[1]),3)
        y_ = np.round(float(vals[2]),3)
        logger.info("XPOS:%3.3f|YPOS:%3.3f" %(x,y))
        if np.abs(x_-x)<0.06 and np.abs(y_-y)<0.06:
            return True
        else:
            return False
        
        
    def busy(self):
        logger.info("Waiting for XPOS:%3.3f|YPOS:%3.3f" %(self._x,self._y))
        return not self.check_pos(np.round(self._x,2),np.round(self._y,2))
        
    
    def move(self, x, y, speed=8.0, wait=False, limit=True):
        self._x = x
        self._y = y
        if limit:
            if x > 25 or x < 0:
                logger.info("Out of bounds")
                return
            if y > 25 or y < 0:
                logger.info("Out of bounds")
                return
            if speed > 80.0:
                logger.info("Too fast!")
                return
        self.send_command("set mdi G01 X%2.2f Y%2.2f Z0 F%2.2f" % (x,y,speed))
        while(wait and (not self.check_pos(x,y))):
            time.sleep(0.2)

    def moveAndWait(self,x,y,speed=60):
        self.move(x,y,speed)
        while(self.busy()):
            time.sleep(0.125) 
        
    def goHome(self,speed=60):
        self.moveAndWait(0,0, speed)        
        
    def stop_move(self):
        self.send_command("set mdi G80")
if __name__ == '__main__':
    robot = Gantry()
    