#ifndef _MCDAQ_H
#define _MCDAQ_H


#ifdef __cplusplus
extern "C" {
#endif
//#define DEBUG  1
#ifdef DEBUG
#define DEBUG_PRINT(fmt, args...)    fprintf(stderr, fmt, ## args)
#else
#define DEBUG_PRINT(fmt, args...)    /* Don't do anything in release builds */
#endif
 
#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <libusb.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>
#include <libusb.h>
#include <math.h>

#define VENDOR_ID               0x09db
#define PRODUCT_ID              0x00ea
#define DEFAULT_INTF            0
#define DAQ_NAME                "USB-1608-FS-PLUS"
#define MAX_MSG_LEN             64
#define STRINGMESSAGE           0x80
#define CTRL_TIMEOUT            1000
#define MAX_COUNTS              0xFFFF
#define TIMEOUT                 200


#define MAX_CHANNELS            8
#define V10                     10
#define V5                      5
#define V2                      2
#define V1                      1

#define ADC_RESOLUTION          pow(2, 16)
#define PRINTERROR(RET)         mc_perror(libusb_to_mcdaq_error(RET), \
                                libusb_error_name(RET))

typedef struct {
    float slope;
    float offset;
} MCCAL;

typedef struct {
    int product_id;
    int vendor_id;
    unsigned char endpoint_in;
    unsigned char endpoint_out;
    unsigned short bulk_packet_sz;

    libusb_device *dev;
    libusb_device_handle* dev_handle;
    libusb_device** list;
    struct libusb_config_descriptor* cfg_desc;
    MCCAL calibration[MAX_CHANNELS];
} MCDAQ;


typedef struct {
    int msg_sz;
    char msg[MAX_MSG_LEN];
} CTRL_MSG;


typedef struct {
    /* User Configured Values */
    int num_samples;
    int sample_rate;
    int sample_range;
    int low_channel;
    int high_channel;

    /* Software set values */    
    int num_channels;
    int num_bytes;
    int total_samples;
    float max_val;
    float min_val;    
    uint16_t *buf;
} SAMPLE;

typedef enum mc_err {
    MC_SUCCESS,
    MC_ERR_NO_DEVICE,
    MC_ERR_INVALID_ID,
    MC_ERR_USB_INIT,
    MC_ERR_PIPE,
    MC_ERR_LIBUSB_TIMEOUT,
    MC_ERR_TRANSFER_FAILED,
    MC_ERR_LIBUSB_TRANSFER_STALL,
    MC_ERR_LIBUSB_TRANSFER_OVERFLOW,
    MC_ERR_UNKNOWN_LIB_USB_ERR,
    MC_ERR_INVALID_BUFFER_SIZE,
    MC_ERR_ACCESS,
    MC_ERR_UNKNOWN,
} mc_err_t;


CTRL_MSG in_msg;
CTRL_MSG out_msg;


static mc_err_t libusb_to_mcdaq_error(int err);
const char *mc_errstring(int err);
char * mc_errorstring_r(int err, char* buf, size_t buflen);
void mc_perror(int err, const char* msg);

float mc_scale_and_calibrate_data(unsigned data, 
                                float min_volt, 
                                float max_volt, 
                                float scale, 
                                float offset);

int mc_init_device(MCDAQ *dev, int vendor_id, int product_id);
int mc_close_device(MCDAQ *dev);
int mc_read_endpoints(MCDAQ *dev);

int mc_send_ctrl_msg(MCDAQ *dev, CTRL_MSG *msg);
int mc_recv_ctrl_msg(MCDAQ *dev, CTRL_MSG *inmsg);
int mc_send_msg(MCDAQ *dev, CTRL_MSG* outmsg, CTRL_MSG* inmsg);

int mc_recv_scan_data(MCDAQ *dev, unsigned short *data, int length, int rate);

int mc_msg_init(CTRL_MSG *msg);
int mc_msg_load(CTRL_MSG *msg, char * message);

int mc_flush_input_data(MCDAQ *dev);
int mc_set_transfer_mode_block_io(MCDAQ *dev);
int mc_set_pacer(MCDAQ *dev);
int mc_set_voltage_range(MCDAQ *dev, int VOLTRANGE);
int mc_set_chan_range(MCDAQ *dev, int low_chan, int hi_chan);
int mc_set_dio_out(MCDAQ *dev);
int mc_set_dio_val(MCDAQ *dev, uint8_t val);
int mc_set_dio_bit(MCDAQ *dev, uint8_t bit, uint8_t val);
int mc_set_samp_rate(MCDAQ *dev, int samp_rate);
int mc_set_num_samp(MCDAQ *dev, int num_samp);

int mc_sample_setup_n(MCDAQ *dev, SAMPLE *sample);

int mc_start_sampling(MCDAQ *dev);

int mc_recv_samples(MCDAQ *dev, SAMPLE *sample);
int mc_sample_single(MCDAQ *dev, SAMPLE *sample);

int mc_init_sample(MCDAQ *dev,SAMPLE *sample);

int mc_free_sample(SAMPLE *sample);

double mc_scale_data(uint16_t data,float min_volt, \
                    float max_volt,float scale, \
                    float offset);

int mc_get_calibration(MCDAQ *dev);
float mc_print_data(MCDAQ *dev, SAMPLE *sample);

#ifdef __cplusplus
}
#endif


#endif
