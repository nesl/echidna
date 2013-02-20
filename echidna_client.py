import sys
import os
import argparse
import logging
import datetime
import zmq
import numpy as np

logger = logging.getLogger("Echidna Client")
hdlr = logging.StreamHandler(sys.stdout)
hdlr.setLevel(logging.DEBUG)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)



parser = argparse.ArgumentParser(description="Echidna client")

parser.add_argument('--high_channel', '-H', type=int, default=7,
                    help='highest channel  to sample')
parser.add_argument('--low_channel', '-L', type=int, default=0,
                    help='lowest channel to sample')
parser.add_argument('--number_samples', '-N',type=int, default=1000,
                    help='number of sample per buffer')
parser.add_argument('--server', '-s', type=str, default = "localhost",
                    help="select the server to connect to")
parser.add_argument('--port','-p',type=int, default=5555,
                    help="select the port to connect to")


opts = parser.parse_args()

if opts.high_channel > 7 and \
        opts.high_channel>opts.low_channel \
        and opts.high_channel >=0:
    parser.error("High channel must be less than 7 and greater than low channel.")

if opts.low_channel > 7 and \
        opts.high_channel>opts.low_channel\
        and opts.low_channel >= 0:
    parser.error("Low channel must be less than 7 and greater than low channel.")

if opts.number_samples > 60000 or \
        opts.number_samples < 0:
            parser.error("Number of samples should be between 0 and 60000")

server_connect_str = "tcp://%s:%d" % (opts.server,opts.port)
num_chans = opts.high_channel - opts.low_channel + 1

print "Connect: %s | Number of samples: %d | Number of channels: %d" % (server_connect_str, 
                                                                       opts.number_samples,
                                                                       num_chans)

def main():
    
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, '')

    socket.connect(server_connect_str)

    count = 0;
    while True:
        msg = socket.recv()
        print "Count: %d | Length: %d" % (count, len(msg))
        data = np.reshape(np.frombuffer(msg, dtype=np.float32),(-1,num_chans))
        print data[0:2,:]
        count = count + 1


if __name__ == "__main__":
    data = main()


