

#ifndef _MCDAQ_HPP_
#define _MCDAQ_HPP_

#include <iostream>
#include <climits>
#include <Eigen/Dense>
#include "mcdaq.h"

using namespace Eigen;
using namespace std;

namespace mcdaq {
    class error_t : public std::exception {
        int _errnum;
        public:
                inline error_t(int errnum) {
                    _errnum = errnum;
                }

                virtual const char *what() const throw()
                {
                    return mc_errstring(_errnum);
                }

                int num() const
                {
                    int _errnum;
                }
    };

    class MCDAQ_t {

        MCDAQ dev;
        SAMPLE sample; 
        bool dirty;       

        public:
 
            enum VOLT_RANGE {
                VOLT1=V1,
                VOLT2=V2,
                VOLT5=V5,
                VOLT10=V10
            };

            MCDAQ_t();
            ~MCDAQ_t();
            
                         
                       
            void set_rate(int rate);
            void set_sample_number(int num);
            void set_channels(int lo, int hi);
            void set_volt_range(VOLT_RANGE range);
            void set_dio_out_dir();
            void set_gain_1();
            void set_gain_10();
            void set_gain_100();
            void set_gain_1000();
            void run();
            MatrixXd run_get_data();
            MatrixXd get_data();

    };
    
    inline MCDAQ_t::MCDAQ_t(){
                int ret;
                dirty = true;
                ret = mc_init_device(&dev, VENDOR_ID, PRODUCT_ID);
                if(ret != MC_SUCCESS)
                    throw error_t(ret);                
                set_dio_out_dir();
                set_gain_1();
                ret = mc_get_calibration(&dev);                
                if(ret != MC_SUCCESS)
                    throw error_t(ret);
                sample.sample_rate=1000;
                sample.high_channel=0;
                sample.low_channel=0;
                sample.sample_range=V5;
                sample.num_samples=100;
    }

    inline MCDAQ_t::~MCDAQ_t() {        
        int ret;
        mc_free_sample(&sample);
        ret = mc_close_device(&dev);
        if(ret!=MC_SUCCESS)
            throw error_t(ret);
    }

   inline void MCDAQ_t::set_rate(int rate) {
        dirty=true;
        sample.sample_rate = rate;
   }
   
   inline void MCDAQ_t::set_sample_number(int num) {
        int ret;
        dirty = true;
        sample.num_samples = num;
   }

   inline void MCDAQ_t::set_channels(int lo, int hi) {
        int ret;
        dirty = true;
        sample.high_channel = hi;
        sample.low_channel = lo;
   } 
   
   inline void MCDAQ_t::set_volt_range(MCDAQ_t::VOLT_RANGE range) {
       dirty = true;
       sample.sample_range = range;
   }

   inline void MCDAQ_t::set_dio_out_dir() {
       int ret; 
       ret = mc_set_dio_out(&dev);
       if(ret!=MC_SUCCESS)
           throw error_t(ret);
   }
   
   inline void MCDAQ_t::set_gain_1() {
       
        int ret;
        ret = mc_set_dio_val(&dev, 1);
        if(ret!=MC_SUCCESS)
            throw error_t(ret);
        ret = mc_set_dio_val(&dev, 0);
        if(ret!=MC_SUCCESS)
            throw error_t(ret);
   }

   inline void MCDAQ_t::set_gain_10() {
        int ret;
        ret = mc_set_dio_val(&dev, 3);
        if(ret!=MC_SUCCESS)
            throw error_t(ret);
        ret = mc_set_dio_val(&dev, 2);
        if(ret!=MC_SUCCESS)
            throw error_t(ret);
   }

   inline void MCDAQ_t::set_gain_100() {
        int ret;
        ret = mc_set_dio_val(&dev, 5);
        if(ret!=MC_SUCCESS)
            throw error_t(ret);
        ret = mc_set_dio_val(&dev, 4);
        if(ret!=MC_SUCCESS)
            throw error_t(ret);
   }

   inline void MCDAQ_t::set_gain_1000() {
        int ret;
        ret = mc_set_dio_val(&dev, 7);
        if(ret!=MC_SUCCESS)
            throw error_t(ret);
        ret = mc_set_dio_val(&dev, 6);
        if(ret!=MC_SUCCESS)
            throw error_t(ret);

   }

   inline void MCDAQ_t::run() {
        int ret;

        if(dirty) {        
                ret = mc_init_sample(&dev, &sample);
                if(ret!=MC_SUCCESS)
                        throw error_t(ret);
                dirty = false;
        }

        ret = mc_start_sampling(&dev);
        if(ret!=MC_SUCCESS)
            throw error_t(ret);
   }

   MatrixXd MCDAQ_t::run_get_data() {
        run();
        return get_data();
   }

   MatrixXd MCDAQ_t::get_data() {  
        int ret;  
        uint16_t data;
        double fdata;
        ret = mc_recv_samples(&dev, &sample);
        if(ret!=MC_SUCCESS)
            throw error_t(ret);        
        MatrixXd m(sample.num_channels,sample.num_samples); 
        for(int i=0;i<sample.num_samples;i++) {
            for(int j=0;j<sample.num_channels;j++) {
                data=((uint16_t *)sample.buf)[i*sample.num_channels + j];
                fdata=mc_scale_data(data, sample.min_val,
                        sample.max_val,
                        dev.calibration[j].slope,
                        dev.calibration[j].offset);
                m(j,i) = fdata;
            }
        }
        return m;
   }
   
}

#endif
