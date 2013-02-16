#include <iostream>
#include <string>
#include <zmq.hpp>
#include <Eigen/Dense>
#include "getoptpp/getopt_pp.h"


using namespace zmq;
using namespace std;
using namespace Eigen;
using namespace GetOpt;


unsigned int NUM_SEC = 5;
unsigned int HI_CHAN = 7;
unsigned int LO_CHAN = 0;
unsigned int NUM_SAMPLES = 1000;
unsigned int SAMP_RATE = 60000;
float MAX_VOLT_F = 5.0f;
string server_connection_str("localhost");
int server_port = 5555;

static void show_usage(char *progname);

int main(int argc, char* argv[]) 
{

    GetOpt_pp ops(argc, argv);

    if (ops >> OptionPresent('h',"help")) {
        show_usage(argv[0]);
        return 0;
    }
    ops >> Option('H',"high_channel",HI_CHAN);
    if(HI_CHAN > 7) {
        show_usage(argv[0]);
        return 1;
    }

    ops >> Option('L',"low_channel",LO_CHAN);
    if(LO_CHAN > 7) {
        show_usage(argv[0]);
        return 1;
    }
    ops >> Option('s',"samples",NUM_SAMPLES);
    if(NUM_SAMPLES>10000){
        show_usage(argv[0]);
        return 1;
    }    
    ops >> Option('r',"rate",SAMP_RATE);
    if(SAMP_RATE>60000){
        show_usage(argv[0]);
        return 1;
    }

    if(ops >> Option('S',"server",server_connection_str)) {
        cout << "Connect to server: " << server_connection_str << endl;
    }

   if(ops >> Option('P',"port",server_port)) {
        cout << "Connect to port: " << server_port << endl;
   } 

   stringstream server_connection;
   server_connection << "tcp://" << server_connection_str << ":" << server_port;

   cout << "Connect to server at: " << server_connection.str()<<endl;


    context_t context(1);
    socket_t socket(context, ZMQ_SUB);
    socket.setsockopt(ZMQ_SUBSCRIBE, "", 0);

    cout << "Connecting to Hello World server" << endl;
    
    socket.connect("tcp://localhost:5555");
    long count = 0;
    for(;;) {
        float *pf;
        message_t data_msg;
        socket.recv(&data_msg);
        pf = (float*) data_msg.data(); 
        Map<MatrixXf> mf(pf,(HI_CHAN-LO_CHAN+1),NUM_SAMPLES);
        cout << count << " Received:  " << endl << mf << endl;
    }
    return 0;
}

void show_usage(char* progname) 
{
    cout << "Usage: " << progname << " [OPTION]" << endl;
    cout << "Read data from the USB-1608FS Data Acquisition\n"
            "Use the sound card to generate a sine wave\n"
            "-H, --high_channel\t\t"
            "select the highest channel on the USB DAQ to sample (0-7)\n"            
            "-L, --low_channel\t\t"
            "select the lowest channel o nthe USB DAQ to sample (0-7)\n"
            "-s, --sample\t\t"
            "choose the number of samples to per image\n"
            "-r, --rate\t\t"
            "choose the ADC sample rate" << endl;    
}

