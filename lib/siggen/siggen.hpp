

#ifndef _SIGGEN_HPP_
#define _SIGGEN_HPP_

#include <iostream>
#include <portaudio.h>
#include <cmath>



using namespace Eigen;
using namespace std;


namespace siggen {

const unsigned int TABLE_SZ = 200;
const unsigned int SAMPLE_RATE = 44100;

static int paCallback(const void *inputBuffer, void *outputBuffer,
                      unsigned long framesPerBuffer,
                      const PaStreamCallbackTimeInfo * timeInfo,
                      PaStreamFlags statusFlags,
                      void *userData);
    
typedef struct {
    float sine[TABLE_SZ];
    int left_phase;
    int right_phase;
    char message[20];
}paData;


    class error_t : public std::exception {
        PaError _errnum;
        public:
                inline error_t(PaError err) {
                    _errnum = err;
                }

                virtual const char *what() const throw()
                {
                    return Pa_GetErrorText(_errnum);
                }

                int num() const
                {
                    return _errnum;
                }
    };

    class SIGGEN_t {
        
        PaStream *stream;        
        paData data;


        public:

        SIGGEN_t();
        ~SIGGEN_t();
        void start(void);
        void stop(void);
        void reset_phase(void);
 
        void setup_sine_wave(void);
    };

    inline SIGGEN_t::SIGGEN_t() {
       PaError err;

       setup_sine_wave();
       
       cout << "PortAudio Library Version:" << Pa_GetVersionText() << endl; 
       
       err = Pa_Initialize();        
       if(err!=paNoError)
            throw error_t(err);

        err = Pa_OpenDefaultStream( &stream,
                                    0, // No input
                                    2, // Stereo
                                    paFloat32,
                                    SAMPLE_RATE,
                                    8, // Frames per buffer
                                    paCallback,
                                    &data);
       if(err!=paNoError)
          throw error_t(err);
        
    }

    inline SIGGEN_t::~SIGGEN_t() {
        PaError err;
        
        err = Pa_CloseStream(stream);
        if(err!=paNoError) 
            throw error_t(err);

        err = Pa_Terminate();
        if(err!=paNoError)
            throw error_t(err);            
    }

    inline void SIGGEN_t::start() {
        PaError err;
        err = Pa_StartStream(stream);
        if(err!=paNoError)
            throw error_t(err);
    }

    inline void SIGGEN_t::stop() {
        PaError err;
        err = Pa_StopStream(stream);
        if(err!=paNoError) 
            throw error_t(err);            
    }

    inline void SIGGEN_t::reset_phase() {
 
       data.left_phase =  0;
       data.right_phase = 0;

    }
    
    inline void SIGGEN_t::setup_sine_wave(void) {

       data.left_phase =  0;
       data.right_phase = 0;

       for(int i=0;i<TABLE_SZ;i++)
           data.sine[i] = (float) sin( (double)i/(double)TABLE_SZ*M_PI*2.0f);
    }

    inline static int paCallback(const void *inputBuffer, void *outputBuffer,
                      unsigned long framesPerBuffer,
                      const PaStreamCallbackTimeInfo * timeInfo,
                      PaStreamFlags statusFlags,
                      void *userData) 
    {
        paData *data = (paData *)userData;
        float *out = (float *)outputBuffer;
        unsigned int i;
        (void) inputBuffer;

        for(i=0;i<framesPerBuffer;i++) {
            *out++= data->sine[data->left_phase];
            *out++= data->sine[data->right_phase];
            data->left_phase  += 1; 
            data->right_phase += 5;
            if(data->left_phase>=TABLE_SZ) data->left_phase =  0;
            if(data->right_phase>TABLE_SZ) data->right_phase = 0;
        }       
        return 0;
    }

}

#endif
