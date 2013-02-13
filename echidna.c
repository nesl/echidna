#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <limits.h>
#include <libusb.h>
#include "mcdaq.h"

MCDAQ daq;

void close_dev();

int main()
{
    int ret;
    int ii;
    CTRL_MSG outmsg;
    CTRL_MSG inmsg;
    SAMPLE sample;
    
    sample.sample_rate = 10000;
    sample.high_channel=6;
    sample.low_channel=0;
    sample.sample_range=V5;
    sample.num_samples=100;


    ret = mc_init_device(&daq, VENDOR_ID, PRODUCT_ID);
    if(ret!=MC_SUCCESS) {
      //mc_perror(ret, "Could not initialize device");
      exit(ret);  
    }

    for(ii=0;ii<2;ii=ii+1) {
      printf("%d:",ii);
      mc_msg_load(&outmsg,"DEV:FLASHLED/1");
      ret = mc_send_msg(&daq, &outmsg, &inmsg);
      if(ret!=MC_SUCCESS) {
          mc_perror(ret, "Huh?");
          close_dev();
      }
      printf("OUTMSG:%s\tINMSG:%s\n",outmsg.msg,inmsg.msg);
      //sleep(1);
    }
    mc_get_calibration(&daq);
    mc_init_sample(&daq, &sample);
    mc_sample_single(&daq, &sample);
    mc_print_data(&daq,&sample);
    mc_free_sample(&sample); 
    exit(EXIT_SUCCESS);

}

void close_dev() 
{   int ret;
    ret = mc_close_device(&daq);
    if(ret!=MC_SUCCESS) {
      //mc_perror(ret, "Could not close device");
      exit(ret);
    }
}
