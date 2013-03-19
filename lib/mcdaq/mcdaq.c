#include "mcdaq.h"



static mc_err_t libusb_to_mcdaq_error(int err)
{
    switch(err) 
    {
        case LIBUSB_ERROR_TIMEOUT:
            return MC_ERR_LIBUSB_TIMEOUT;
        case LIBUSB_ERROR_NO_DEVICE:
            return MC_ERR_NO_DEVICE;
        case LIBUSB_ERROR_PIPE:
            return MC_ERR_PIPE;
        default:
            return MC_ERR_UNKNOWN_LIB_USB_ERR;
    }
}


const char *mc_errstring(int err) {    
    switch(err)
    {
    	case MC_ERR_ACCESS:
            return "Insufficient USB permisions";
        case MC_ERR_NO_DEVICE:
            return "No Matching Device Found";
        case MC_ERR_INVALID_ID:
            return "Invalid Device ID";
        case MC_ERR_USB_INIT:
            return "Failed to Init USB";
        case MC_ERR_PIPE:
            return "Libusb Pipe Error, possibly invalid command";
        case MC_ERR_LIBUSB_TIMEOUT:
            return "Transfer Timed Out";
        case MC_ERR_UNKNOWN_LIB_USB_ERR:
            return "Unknown LibUSB Error";
        case MC_ERR_INVALID_BUFFER_SIZE:
            return "Buffer must be and integer multiple of 32";
        case MC_ERR_UNKNOWN:
        default:
            return "Unknown Error\n";
    }
}

char* mc_errorstring_r(int err, char* buf, size_t buflen)
{
  char err_str[5];
  int res;
  buf[0] = '\0';
  strncpy(buf,mc_errstring(err), buflen);
  sprintf(err_str, "-ERRNO:%d", err);
  strncpy(buf, err_str, strlen(err_str));
  return buf;
}

void mc_perror(int err, const char* msg)
{
  DEBUG_PRINT("ERROR:%s:%d:%s\n", mc_errstring(err), err, msg);
}


float mc_scale_and_calibrate_data(unsigned data, 
                                float min_volt, 
                                float max_volt, 
                                float scale, 
                                float offset)
{
  float calibrated_data;
  float scale_calibrate_data;
  float full_scale = max_volt - min_volt;
  
  calibrated_data = (float)data*scale+offset;

  scale_calibrate_data = (calibrated_data/(float)MAX_COUNTS)*full_scale + min_volt;
  return scale_calibrate_data;
}


int mc_init_device(MCDAQ *dev, int vendor_id, int product_id)
{
   
  int i, ret; 
  ssize_t size_of_list;
  int found = 0;
  libusb_device* device;
  struct libusb_device_descriptor desc;
  if(libusb_init(NULL) != 0){
    return MC_ERR_USB_INIT;
  }

  size_of_list = libusb_get_device_list(NULL, &(dev->list));

  DEBUG_PRINT("Looking for %s VENDORID:%x,PRODUCTID:%x\n",DAQ_NAME,vendor_id, product_id);
  for(i=0;(i<size_of_list) && (found==0);i++) {
    device = dev->list[i];

    libusb_get_device_descriptor(device, &desc);
    
    DEBUG_PRINT("VENDORID:%x,PRODUCTID:%x\n",desc.idVendor,desc.idProduct);
    // Check for matching vendor and product id
    if((desc.idVendor == vendor_id) && (desc.idProduct == product_id)) {
      
    
      found = 1;
      DEBUG_PRINT("Found Device %s\n", DAQ_NAME);
      ret = libusb_open(device,&(dev->dev_handle)); 
      if(ret != 0) {
        mc_perror(libusb_to_mcdaq_error(ret),libusb_error_name(ret));
        return libusb_to_mcdaq_error(ret);
      }
      DEBUG_PRINT("Opened Device %s\n", DAQ_NAME);

      // Try to claim the interface      
      ret = libusb_claim_interface(dev->dev_handle,DEFAULT_INTF);
      if(ret != 0) {
        mc_perror(libusb_to_mcdaq_error(ret),libusb_error_name(ret));
        return libusb_to_mcdaq_error(ret);
      }
      DEBUG_PRINT("Claimed interface %d\n", DEFAULT_INTF);
      
      ret = libusb_get_active_config_descriptor(device, &(dev->cfg_desc));
      if(ret!=0) {
        mc_perror(libusb_to_mcdaq_error(ret),libusb_error_name(ret));
        return libusb_to_mcdaq_error(ret);
      }
      DEBUG_PRINT("Got Active Configuration Descriptor\n");
      
      mc_read_endpoints(dev);
      found = 1;
    }
  }
  if(found==0) {
    mc_perror(MC_ERR_NO_DEVICE,"Is it plugged in? Do you have permissions?");
    return MC_ERR_NO_DEVICE;
  }
  return MC_SUCCESS;
}

int mc_close_device(MCDAQ *dev) 
{ int ret;
  ret = libusb_release_interface(dev->dev_handle,0);
  if(ret!=0) {
    mc_perror(ret, "Could not release interface");
  }

  libusb_close(dev->dev_handle);
  libusb_free_device_list(dev->list, 1);
  libusb_exit(NULL);
  DEBUG_PRINT( "Device closed\n");
  return MC_SUCCESS;
}


int mc_read_endpoints(MCDAQ *dev)
{
  int i,j,k;
  int num_intf;
  int num_intf_desc;
  int num_eps;
  struct libusb_interface *intf;
  struct libusb_interface_descriptor *intf_desc;
  struct libusb_endpoint_descriptor *ep_desc;

  // Corresponds to control endpoint
  dev->endpoint_out=0;

  num_intf = dev->cfg_desc->bNumInterfaces;
  DEBUG_PRINT( "Number of interfaces: %d\n", num_intf);
  
  if(num_intf > 1) {
    mc_perror(MC_ERR_UNKNOWN, "To mant interface descriptors, expexted 1");
    return MC_ERR_UNKNOWN;
  }

  for(i = 0;i<num_intf;i++){
    intf = (struct libusb_interface *) dev->cfg_desc->interface+i;
    num_intf_desc = intf->num_altsetting;
    DEBUG_PRINT( "Number of alternate settings for interface %d -> %d\n", num_intf, num_intf_desc);
    
    if(num_intf_desc >1) {
      mc_perror(MC_ERR_UNKNOWN, "To many alternate settings descriptors, expected 1");
      return MC_ERR_UNKNOWN;
    }
    
    for(j=0;j<num_intf_desc;j++) {
      intf_desc = (struct libusb_interface_descriptor *)intf->altsetting+j;
      num_eps = intf_desc->bNumEndpoints;
      DEBUG_PRINT( "Number of endpoints for alternate setting %d -> %d\n", num_intf_desc, num_eps);
      
      if(num_eps>1) {
        mc_perror(MC_ERR_UNKNOWN, "To many endpoint descriptors, expected 1");
      }

      for(k=0;k<num_eps;k++){
        ep_desc = (struct libusb_endpoint_descriptor *)intf_desc->endpoint+k;
        DEBUG_PRINT( "Endpoint Address: %x\n", ep_desc->bEndpointAddress);
        DEBUG_PRINT( "Max Packet Size: %d\n", ep_desc->wMaxPacketSize);
        dev->endpoint_in=ep_desc->bEndpointAddress;
        dev->bulk_packet_sz=ep_desc->wMaxPacketSize;
      }
    }
  }

  return MC_SUCCESS;  
}


int mc_send_ctrl_msg(MCDAQ *dev, CTRL_MSG *msg)
{
  int bytes_transfered;
  DEBUG_PRINT( "Sending: %s\n", msg->msg);
  
  bytes_transfered = libusb_control_transfer(dev->dev_handle, LIBUSB_REQUEST_TYPE_VENDOR + LIBUSB_ENDPOINT_OUT,
                                                  STRINGMESSAGE, 0, 0, msg->msg, MAX_MSG_LEN, CTRL_TIMEOUT);

  if(bytes_transfered<0) {
    mc_perror(libusb_to_mcdaq_error(bytes_transfered),libusb_error_name(bytes_transfered));
    return libusb_to_mcdaq_error(bytes_transfered);
  }

  return MC_SUCCESS;
}

int mc_recv_ctrl_msg(MCDAQ *dev, CTRL_MSG *inmsg)
{
    
    mc_msg_init(inmsg);
    inmsg->msg_sz = libusb_control_transfer(dev->dev_handle,  LIBUSB_REQUEST_TYPE_VENDOR + LIBUSB_ENDPOINT_IN,
				                               STRINGMESSAGE, 0, 0, inmsg->msg, MAX_MSG_LEN, CTRL_TIMEOUT);

    if(inmsg->msg_sz<0){
      mc_perror(libusb_to_mcdaq_error(inmsg->msg_sz),libusb_error_name(inmsg->msg_sz));
      return libusb_to_mcdaq_error(inmsg->msg_sz);
    }

    DEBUG_PRINT( "Received Control Transfer: %s\n", inmsg->msg);
    return MC_SUCCESS;
}

int mc_send_msg(MCDAQ *dev, CTRL_MSG* outmsg, CTRL_MSG* inmsg)
{
  int ret;
  ret = mc_send_ctrl_msg(dev, outmsg);
  if(ret!=MC_SUCCESS) {
    return ret;
  }

  ret = mc_recv_ctrl_msg(dev,inmsg); 
  if(ret!=MC_SUCCESS) {
    return ret;
  }
  return MC_SUCCESS;
}


int mc_recv_scan_data(MCDAQ *dev, unsigned short *data, int length, int rate)
{

  return MC_SUCCESS;
}

int mc_msg_init(CTRL_MSG *msg)
{
  int i;
  msg->msg_sz = 0;
  for(i=0;i<MAX_MSG_LEN;i++){
    msg->msg[i]='\0';
  }
  return MC_SUCCESS;
}

int mc_msg_load(CTRL_MSG *msg, char *message)
{
  mc_msg_init(msg);
  strncpy(msg->msg, message, MAX_MSG_LEN-1);
  msg->msg[MAX_MSG_LEN-1] = '\0';
  msg->msg_sz = strlen(msg->msg);
  return MC_SUCCESS;
}

int mc_flush_input_data(MCDAQ *dev)
{
  int byte_recv = 0;
  int ret = 0;

  mc_msg_init(&in_msg);
  while(byte_recv > 0 && ret == 0) {
  
    ret = libusb_bulk_transfer(dev->dev_handle, 
                               dev->endpoint_in, 
                               in_msg.msg,dev->bulk_packet_sz, 
                               &(in_msg.msg_sz),
                               TIMEOUT); 
  }
  mc_msg_init(&in_msg);
  return MC_SUCCESS;
}

int mc_set_transfer_mode_block_io(MCDAQ *dev)
{
  int ret;
  mc_msg_load(&out_msg,"AISCAN:XFRMODE=BLOCKIO");
  ret = mc_send_msg(dev, &out_msg, &in_msg);
  return ret;
}

int mc_set_voltage_range(MCDAQ *dev, int VOLTRANGE)
{

  int ret;
  char buf[MAX_MSG_LEN];
#ifdef __APPLE__  
  sleep(1);  // Delay add
#endif 
  switch(VOLTRANGE) {
    case V2:
      strcpy(buf, "AISCAN:RANGE=BIP2V");
      break;
     case V5:
      strcpy(buf, "AISCAN:RANGE=BIP5V");
      break;
     case V10:
      strcpy(buf, "AISCAN:RANGE=BIP10V");
      break;
     case V1:
     default:
      strcpy(buf, "AISCAN:RANGE=BIP1V");
      break;
  }

  mc_msg_load(&out_msg,buf);
  ret = mc_send_msg(dev, &out_msg, &in_msg);
  if(ret!=MC_SUCCESS) 
  return ret;
}

int mc_set_chan_range(MCDAQ *dev, int low_chan, int hi_chan)
{
  int ret;
  char buf[MAX_MSG_LEN];
  sprintf(buf, "AISCAN:LOWCHAN=%d",low_chan);
  mc_msg_load(&out_msg,buf);
  ret = mc_send_msg(dev, &out_msg, &in_msg);
  if(ret!=MC_SUCCESS) {
    return ret;
  }
  sprintf(buf, "AISCAN:HIGHCHAN=%d",hi_chan);
  mc_msg_load(&out_msg,buf);
  ret = mc_send_msg(dev, &out_msg, &in_msg);
  return ret;
}

int mc_set_dio_out(MCDAQ *dev)
{
  int ret;
  mc_msg_load(&out_msg,"DIO{0}:DIR=OUT");
  ret = mc_send_msg(dev, &out_msg, &in_msg);
  if(ret!=MC_SUCCESS)
     return ret;
   mc_msg_load(&out_msg,"?DIO{0}:DIR");
  ret = mc_send_msg(dev, &out_msg, &in_msg);
  if(ret!=MC_SUCCESS)
     return ret; 
  mc_msg_load(&out_msg,"DIO{0}:VALUE=0");
  ret = mc_send_msg(dev, &out_msg, &in_msg);
  if(ret!=MC_SUCCESS)
     return ret;
  mc_msg_load(&out_msg,"?DIO{0}:VALUE");
  ret = mc_send_msg(dev, &out_msg, &in_msg);
  if(ret!=MC_SUCCESS)
     return ret;
  mc_msg_load(&out_msg,"DIO{0}:LATCH=0");
  ret = mc_send_msg(dev, &out_msg, &in_msg);
  return ret;
}

int mc_set_dio_val(MCDAQ *dev, uint8_t val)
{
  int ret;
  char buf[MAX_MSG_LEN];
  sprintf(buf, "DIO{0}:LATCH=%d",val);
  mc_msg_load(&out_msg,buf);
  ret = mc_send_msg(dev, &out_msg, &in_msg);
  return ret;
}


int mc_set_samp_rate(MCDAQ *dev, int samp_rate)
{
  char buf[MAX_MSG_LEN];
  sprintf(buf, "AISCAN:RATE=%d",samp_rate);
  mc_msg_load(&out_msg,buf);
  return mc_send_msg(dev, &out_msg, &in_msg);
}

int mc_set_num_samp(MCDAQ *dev, int num_samp)
{
  char buf[MAX_MSG_LEN];
  sprintf(buf, "AISCAN:SAMPLES=%d",num_samp);
  mc_msg_load(&out_msg,buf);
  return mc_send_msg(dev, &out_msg, &in_msg);
}


int mc_sample_setup_n(MCDAQ *dev, SAMPLE *sample)
{
  
  int ret;
  ret = mc_set_transfer_mode_block_io(dev);
  if(ret!=MC_SUCCESS){
    return ret;
  }
  ret = mc_set_num_samp(dev, sample->num_samples);
  if(ret!=MC_SUCCESS){
    return ret;
  }
  ret = mc_set_samp_rate(dev, sample->sample_rate);
  if(ret!=MC_SUCCESS){
    return ret;
  }
  ret = mc_set_voltage_range(dev, sample->sample_range);
  if(ret!=MC_SUCCESS){
    return ret;
  }
  ret = mc_set_chan_range(dev, sample->low_channel, sample->high_channel);
  if(ret!=MC_SUCCESS){
    return ret;
  } 
  return MC_SUCCESS;

}

int mc_start_sampling(MCDAQ *dev)
{
  char buf[MAX_MSG_LEN];
  sprintf(buf, "AISCAN:START");
  mc_msg_load(&out_msg, buf);
  return mc_send_msg(dev, &out_msg, &in_msg);

}


int mc_recv_samples(MCDAQ *dev, SAMPLE *sample)
{
  int ret;
  int bytes_received=0;
  int total_bytes_received=0;
  uint8_t *pbuf;
  int cur_idx=0;
  pbuf=(uint8_t *)sample->buf;

  DEBUG_PRINT( "Expecting %d bytes\n", sample->num_bytes);         

  while(total_bytes_received<sample->num_bytes) {
    ret =  libusb_bulk_transfer(dev->dev_handle, dev->endpoint_in, \
                                &pbuf[cur_idx], MAX_MSG_LEN,\
                                &bytes_received, TIMEOUT);
    DEBUG_PRINT( "Received %d byte...\n", bytes_received);
    
    total_bytes_received = total_bytes_received + bytes_received;
    if( ret==LIBUSB_ERROR_TIMEOUT && bytes_received<=0) {
      mc_perror(libusb_to_mcdaq_error(ret),libusb_error_name(ret));
      return libusb_to_mcdaq_error(ret);
    }
    cur_idx = cur_idx + bytes_received;
    DEBUG_PRINT( "Total Received Bytes:%d\n", total_bytes_received);
  }
  DEBUG_PRINT( "Total Received Samples:%lu\n", total_bytes_received/sizeof(uint16_t));
  return MC_SUCCESS;
}


int mc_sample_single(MCDAQ *dev, SAMPLE *sample)
{
    int ret;
    ret = mc_set_num_samp(dev,sample->num_samples);
    if(ret!=MC_SUCCESS) return ret;
    ret = mc_set_samp_rate(dev,sample->sample_rate);
    if(ret!=MC_SUCCESS) return ret;
    ret = mc_set_voltage_range(dev, sample->sample_range);
    if(ret!=MC_SUCCESS) return ret;
    ret = mc_set_chan_range(dev,sample->low_channel, \
                            sample->high_channel);
    if(ret!=MC_SUCCESS) return ret;

    ret = mc_start_sampling(dev);
    if(ret!=MC_SUCCESS) return ret;
    ret = mc_recv_samples(dev,sample);
    if(ret!=MC_SUCCESS) return ret;
}


int mc_init_sample(MCDAQ *dev, SAMPLE *sample) 
{
   int len;
   int ret;
   DEBUG_PRINT( "Setting up sampling routine\n");

   sample->num_channels = sample->high_channel-sample->low_channel+1;
   sample->total_samples = sample->num_samples * sample->num_channels;
   sample->num_bytes = sample->total_samples*sizeof(uint16_t);
   
   switch(sample->sample_range) {
        case V1:
            sample->max_val=1.0;
            sample->min_val=-1.0;
            break;
        case V2:
            sample->max_val=2.0;
            sample->min_val=-2.0;
            break;            
        case V5:
            sample->max_val=5.0;
            sample->min_val=-5.0;
            break;
        case V10:
            sample->max_val=10.0;
            sample->min_val=-10.0;
            break;
        default:
           sample->max_val=5.0;
           sample->min_val=-5.0;
           break;
   }

   sample->buf = (uint16_t *)malloc(sizeof(uint8_t)*sample->num_bytes);
   if(sample->buf == NULL) {
    printf("Out of memory, could not allocate sample buffer");
    return MC_ERR_UNKNOWN;
   }
   ret = mc_sample_setup_n(dev, sample);
   return ret;
}

int mc_free_sample(SAMPLE *sample)
{
    free(sample->buf);
    return MC_SUCCESS;
}


double mc_scale_data(uint16_t data, float min_volt,\
                    float max_volt, float scale, \
                    float offset)
{
    double scaled_data;
    double range = max_volt - min_volt;

    scaled_data = (double)data*scale + offset;
    scaled_data = scaled_data / (double)ADC_RESOLUTION * range + min_volt;
    return scaled_data;
}


int mc_get_calibration(MCDAQ *dev)
{ 
  int ret, chan_id;
  char buf[MAX_MSG_LEN];
  int dummy;
 
  for(chan_id = 0;chan_id<MAX_CHANNELS;chan_id++) {
        
    sprintf(buf, "?AI{%d}:SLOPE",chan_id);  
    mc_msg_load(&out_msg,buf);
    
    ret = mc_send_msg(dev, &out_msg, &in_msg);
    
    if(ret!=MC_SUCCESS) {
        PRINTERROR(ret);
        return ret;
    }
    else {
        sscanf(in_msg.msg, "AI{%*d}:SLOPE=%f", &(dev->calibration[chan_id].slope));
        DEBUG_PRINT("Chan %d Slope: %f\n",chan_id,dev->calibration[chan_id].slope);
    } 
    sprintf(buf, "?AI{%d}:OFFSET",chan_id);  
    mc_msg_load(&out_msg,buf);
    
    ret = mc_send_msg(dev, &out_msg, &in_msg);
    
    if(ret!=MC_SUCCESS) {
        PRINTERROR(ret);
        return ret;
    } else {
        sscanf(in_msg.msg, "AI{%*d}:OFFSET=%f", &(dev->calibration[chan_id].offset));
        DEBUG_PRINT("Chan %d Offset: %f\n",chan_id,dev->calibration[chan_id].offset);
    }
  }
  return MC_SUCCESS;
}


float mc_print_data(MCDAQ *dev, SAMPLE *sample)
{
    int i,j;
    uint16_t data;
    float fdata;    

    DEBUG_PRINT("Number of channels: %d\n", sample->num_channels);
    DEBUG_PRINT("Number of sample: %d\n", sample->num_samples);    
    for(i=0;i<sample->num_samples;i++) {
        for(j=0;j<sample->num_channels;j++) {
                data=((uint16_t *)sample->buf)[i*sample->num_channels + j];
                fdata=mc_scale_data(data, sample->min_val,
                        sample->max_val,
                        dev->calibration[j].slope,
                        dev->calibration[j].offset);
                printf("%2.3f,", fdata);
        }
        printf("\n");
    }
    printf("\n");
}

