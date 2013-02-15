#include <iostream>
#include <portaudio.h>
#include <opencv2/opencv.hpp>
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <Eigen/Dense>
#include <opencv2/core/eigen.hpp>
#include "mcdaq.hpp"
#include "siggen.hpp"

using namespace mcdaq;
using namespace siggen;
using namespace std;
using namespace Eigen;
using namespace cv;


const unsigned int NUM_SEC = 5;
const unsigned int HI_CHAN = 7;
const unsigned int LO_CHAN = 0;
const unsigned int NUM_SAMPLES = 1000;
const unsigned int SAMP_RATE = 20000;
const float MAX_VOLT_F = 5.0f;


int main() {    
        
    PaStream *stream;
    PaError err;

    SIGGEN_t sig;

    Mat image, big_image;
    Size sz(NUM_SAMPLES,80); 


    MCDAQ_t daq;
    MatrixXf m;    
    daq.set_rate(SAMP_RATE);
    daq.set_volt_range(MCDAQ_t::VOLT5);
    daq.set_channels(0,7);
    daq.set_sample_number(NUM_SAMPLES);
    namedWindow("Diplay window", CV_WINDOW_FULLSCREEN); 
    int i = 0;
    //for(i=0;i<100;i++) {
    sig.start();
    sleep(5);

    for(;;){
        sig.reset_phase();
        m = daq.get_data();
        m = 1.0/(2.0*MAX_VOLT_F)*m;
        m = (m.array() + 1.0).matrix();        
        eigen2cv(m, image);
        big_image = big_image.zeros(sz,image.type());
        resize(image, big_image, sz);
        //cout << m.transpose() << endl;
        cout << "Max: " << m.maxCoeff() << endl;
        cout << "Min: " << m.minCoeff() << endl;
        cout << "Count: " << i+1 << endl;    
        imshow("Diplay window", big_image); 
        if(waitKey(10)>=0) {
                break;
        }
    }

    sig.stop();

    return 0;
}

