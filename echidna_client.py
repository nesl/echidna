import sys
import os
import argparse
import logging
import datetime
import zmq
import struct
import numpy as np

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


opts = parser.parse_args()

server_connect_str = "tcp://%s:%d" % (opts.server,opts.port)

print "Connect: %s" % (server_connect_str)

def main():
    
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, '')

    socket.connect(server_connect_str)

    count = 0;
    while True:
        msg = socket.recv_multipart()
        print "Multiparts: %d" % len(msg)
        num_channels = struct.unpack("<I",msg[0])[0]
        print "Number of channels %d" % num_channels
        num_samples = struct.unpack("<I",msg[1])
        print "Number of Samples %d" % num_samples[0]
        print "Count: %d | Length: %d " % (count, len(msg[2]))
        data = np.reshape(np.frombuffer(msg[2], dtype=np.float64),(-1,num_channels))

        print data[0:2,:]
        count = count + 1


if __name__ == "__main__":
    data = main()


