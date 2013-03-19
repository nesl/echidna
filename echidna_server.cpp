#include <iostream>
#include <fstream>
#include <sstream>
#include <cstring>
#include <cmath>
#include <complex>
#include <zmq.hpp>
#include <Eigen/Dense>
#include <opencv2/opencv.hpp>
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/core/eigen.hpp>
#include "getoptpp/getopt_pp.h"
#include "mcdaq.hpp"
#include <fftw3.h>

using namespace mcdaq;
using namespace std;
using namespace Eigen;
using namespace cv;
using namespace GetOpt;
using namespace zmq;


bool bDisplay = false;
bool bfft = false;
unsigned int NUM_SEC = 5;
unsigned int HI_CHAN = 7;
unsigned int LO_CHAN = 0;
unsigned int NUM_SAMPLES = 500;
unsigned int SAMP_RATE = 100000;
unsigned int GAIN = 1;
float MAX_VOLT_F = 5.0f;
string server_connection_str("*");
int server_port = 5555;

MCDAQ_t daq;
MatrixXd m;
context_t context(1);
socket_t socket(context, ZMQ_PUB);

static void show_usage(char *progname);
void scale_data(void);
void send_matrix(MatrixXd mat);
MatrixXd dft_mag_data(void);




int main(int argc, char* argv[]) 
{    
        


    GetOpt_pp ops(argc, argv);

    if (ops >> OptionPresent('h',"help")) {
        show_usage(argv[0]);
        return 0;
    }

    if (ops >> OptionPresent('D',"display")) {
        cout << "Display Result" << endl;
        bDisplay = true;
    }

    if (ops >> OptionPresent('F',"fft")) {
        cout << "Calculate FFT" << endl;
        bfft = true;
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
    if(SAMP_RATE>100000){
        show_usage(argv[0]);
        return 1;
    }

    if(ops >> Option('S',"server",server_connection_str)) {
        cout << "Connect to server: " << server_connection_str << endl;
    }

   if(ops >> Option('P',"port",server_port)) {
        cout << "Connect to port: " << server_port << endl;
   } 

   if(ops >> Option('G',"gain", GAIN)) {       
        cout << "Gain:" << GAIN << endl;
   }

   switch(GAIN) {
       case 10:
           cout << "10!" << endl;
           daq.set_gain_10();
           break;
       case 100:
           daq.set_gain_100();
           cout << "100!" << endl;
           break;
       case 1000:
           daq.set_gain_1000();
           cout << "1000!" << endl;
           break;
       case 1:           
       default:
           daq.set_gain_1();
           cout << "1!" << endl;
           break;
   }
  
   stringstream server_connection;
   server_connection << "tcp://" << server_connection_str << ":" << server_port;

   cout << "Server started as: " << server_connection.str()<<endl;
   
   
    namedWindow("Display window", CV_WINDOW_FULLSCREEN);
  

    socket.bind((char *)server_connection.str().c_str());


    Mat image, big_image;
    Size sz(NUM_SAMPLES,50*(HI_CHAN-LO_CHAN+1));   

    
    daq.set_rate(SAMP_RATE);
    daq.set_volt_range(MCDAQ_t::VOLT5);
    daq.set_channels(LO_CHAN,HI_CHAN);
    daq.set_sample_number(NUM_SAMPLES);

    long i = 0;

    for(;;){
       
        daq.run();        
        m = daq.get_data();

        if(bfft) {
            MatrixXd fftm = dft_mag_data();
            send_matrix(fftm);
        } else {
            send_matrix(m);
        }


        scale_data();

        if (bDisplay) {
            eigen2cv(m, image);
            big_image = big_image.zeros(sz,image.type());
            resize(image, big_image, sz);
            imshow("Display window", big_image);
        }
        cout << "Sent: " << i++ << endl;    
        if(waitKey(1)>=0) {
                break;
        }
    }


    return 0;
}

MatrixXd dft_mag_data(void)
{
    int N = m.cols()/2+1;
    MatrixXcd fftm(m.rows(), N);
    fftw_complex *out;
    fftw_plan p;
    out = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * N);
    double *in;
    for(int i=0; i < m.rows();i++) {
        in = m.row(i).data();
        p = fftw_plan_dft_r2c_1d(N, in, out, 0);
        fftw_execute(p);        
        memcpy((void *)fftm.row(i).data(),(void *)out, N);
    }
    fftw_free(out);

    MatrixXd fftm_mag = fftm.array().abs().matrix();

    return fftm_mag;
}

void scale_data(void)
{
    m = 1.0/(2.0*MAX_VOLT_F)*m;
    m = (m.array() + 1.0).matrix(); 
}

void send_matrix(MatrixXd mat) 
{
    message_t data_msg;

    uint32_t rows = mat.rows();
    uint32_t cols = mat.cols();
    
    data_msg.rebuild(sizeof(rows));
    memcpy((void*) data_msg.data(), (void*)&rows, sizeof(rows));
    socket.send(data_msg,ZMQ_SNDMORE);
    
    data_msg.rebuild(sizeof(cols));
    memcpy((void*) data_msg.data(), (void*)&cols, sizeof(cols));
    socket.send(data_msg,ZMQ_SNDMORE);

    data_msg.rebuild(mat.size()*sizeof(double));
    memcpy((void*) data_msg.data(), (void*)mat.data(), mat.size()*sizeof(double));        
    socket.send(data_msg,0);
}

void show_usage(char* progname) 
{
    cout << "Usage: " << progname << " [OPTION]" << endl;
    cout << "Read data from the USB-1608FS Data Acquisition\n"
            "-G, --gain\t\t"
            "Set the gain. Valid options 1,10,100,100"
            "-s, --samples\t\t"
            "set the number of samples\n"
            "-r, --rate\t\t"
            "set the sample rate (default 100kSps)\n" << endl;    
}

