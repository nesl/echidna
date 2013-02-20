#include <iostream>
#include <string>
#include <portaudio.h>
#include <opencv2/opencv.hpp>
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <Eigen/Dense>
#include <opencv2/core/eigen.hpp>
#include <zmq.hpp>
#include "getoptpp/getopt_pp.h"
#include "mcdaq.hpp"
#include "siggen.hpp"

using namespace mcdaq;
using namespace siggen;
using namespace std;
using namespace Eigen;
using namespace cv;
using namespace GetOpt;
using namespace zmq;


unsigned int NUM_SEC = 5;
unsigned int HI_CHAN = 7;
unsigned int LO_CHAN = 0;
unsigned int NUM_SAMPLES = 1000;
unsigned int SAMP_RATE = 60000;
float MAX_VOLT_F = 5.0f;

string server_connection_str;

static void show_usage(char *progname);

int main(int argc, char* argv[]) {    
        


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
        return 0;
    } 

    

    PaStream *stream;
    PaError err;

    SIGGEN_t sig;

    Mat image, big_image;
    Size sz(NUM_SAMPLES,50*(HI_CHAN-LO_CHAN));   

    MCDAQ_t daq;
    MatrixXf m;    
    daq.set_rate(SAMP_RATE);
    daq.set_volt_range(MCDAQ_t::VOLT5);
    daq.set_channels(LO_CHAN,HI_CHAN);
    daq.set_sample_number(NUM_SAMPLES);
    namedWindow("Diplay window", CV_WINDOW_FULLSCREEN); 
    int i = 0;
    sig.start();
    sleep(5);

    for(;;){
        
        m = daq.run_get_data();
        sig.reset_phase();
        m = 1.0/(2.0*MAX_VOLT_F)*m;
        m = (m.array() + 1.0).matrix();        
        eigen2cv(m, image);
        big_image = big_image.zeros(sz,image.type());
        resize(image, big_image, sz);
        //cout << m.transpose() << endl;
        //cout << "Max: " << m.maxCoeff() << endl;
        //cout << "Min: " << m.minCoeff() << endl;
        cerr << "Count: " << i << endl;    
        imshow("Diplay window", big_image);
        i = i+1;
        if(waitKey(10)>=0) {
                break;
        }
    }

    sig.stop();

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

