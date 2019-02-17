#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ctypes import *
import platform

import time
import cv2
import numpy as np
try:
  from queue import Queue
except ImportError:
  from Queue import Queue
import platform

try:
  if platform.system() == 'Darwin':
    libuvc = cdll.LoadLibrary("libuvc.dylib")
  elif platform.system() == 'Linux':
    libuvc = cdll.LoadLibrary("libuvc.so")
  else:
    libuvc = cdll.LoadLibrary("libuvc")
except OSError:
  print("Error: could not find libuvc!")
  exit(1)

class uvc_context(Structure):
  _fields_ = [("usb_ctx", c_void_p),
              ("own_usb_ctx", c_uint8),
              ("open_devices", c_void_p),
              ("handler_thread", c_ulong),
              ("kill_handler_thread", c_int)]
  
class uvc_device(Structure):
  _fields_ = [("ctx", POINTER(uvc_context)),
              ("ref", c_int),
              ("usb_dev", c_void_p)]
  
class uvc_format_desc(Structure):
  pass

class uvc_frame_desc(Structure):
  pass
  
class uvc_stream_ctrl(Structure):
  _fields_ = [("bmHint", c_uint16),
              ("bFormatIndex", c_uint8),
              ("bFrameIndex", c_uint8),
              ("dwFrameInterval", c_uint32),
              ("wKeyFrameRate", c_uint16),
              ("wPFrameRate", c_uint16),
              ("wCompQuality", c_uint16),
              ("wCompWindowSize", c_uint16),
              ("wDelay", c_uint16),
              ("dwMaxVideoFrameSize", c_uint32),
              ("dwMaxPayloadTransferSize", c_uint32),
              ("dwClockFrequency", c_uint32),
              ("bmFramingInfo", c_uint8),
              ("bPreferredVersion", c_uint8),
              ("bMinVersion", c_uint8),
              ("bMaxVersion", c_uint8),
              ("bInterfaceNumber", c_uint8)]
  
uvc_frame_desc._fields_ = [
              ("parent", POINTER(uvc_format_desc)),
              ("prev", POINTER(uvc_frame_desc)),
              ("next", POINTER(uvc_frame_desc)),
              # /** Type of frame, such as JPEG frame or uncompressed frme */
              ("bDescriptorSubtype", c_uint), # enum uvc_vs_desc_subtype bDescriptorSubtype;
              # /** Index of the frame within the list of specs available for this format */
              ("bFrameIndex", c_uint8),
              ("bmCapabilities", c_uint8),
              # /** Image width */
              ("wWidth", c_uint16),
              # /** Image height */
              ("wHeight", c_uint16),
              # /** Bitrate of corresponding stream at minimal frame rate */
              ("dwMinBitRate", c_uint32),
              # /** Bitrate of corresponding stream at maximal frame rate */
              ("dwMaxBitRate", c_uint32),
              # /** Maximum number of bytes for a video frame */
              ("dwMaxVideoFrameBufferSize", c_uint32),
              # /** Default frame interval (in 100ns units) */
              ("dwDefaultFrameInterval", c_uint32),
              # /** Minimum frame interval for continuous mode (100ns units) */
              ("dwMinFrameInterval", c_uint32),
              # /** Maximum frame interval for continuous mode (100ns units) */
              ("dwMaxFrameInterval", c_uint32),
              # /** Granularity of frame interval range for continuous mode (100ns) */
              ("dwFrameIntervalStep", c_uint32),
              # /** Frame intervals */
              ("bFrameIntervalType", c_uint8),
              # /** number of bytes per line */
              ("dwBytesPerLine", c_uint32),
              # /** Available frame rates, zero-terminated (in 100ns units) */
              ("intervals", POINTER(c_uint32))]

uvc_format_desc._fields_ = [
              ("parent", c_void_p),
              ("prev", POINTER(uvc_format_desc)),
              ("next", POINTER(uvc_format_desc)),
              # /** Type of image stream, such as JPEG or uncompressed. */
              ("bDescriptorSubtype", c_uint), # enum uvc_vs_desc_subtype bDescriptorSubtype;
              # /** Identifier of this format within the VS interface's format list */
              ("bFormatIndex", c_uint8),
              ("bNumFrameDescriptors", c_uint8),
              # /** Format specifier */
              ("guidFormat", c_char * 16), # union { uint8_t guidFormat[16]; uint8_t fourccFormat[4]; }
              # /** Format-specific data */
              ("bBitsPerPixel", c_uint8),
              # /** Default {uvc_frame_desc} to choose given this format */
              ("bDefaultFrameIndex", c_uint8),
              ("bAspectRatioX", c_uint8),
              ("bAspectRatioY", c_uint8),
              ("bmInterlaceFlags", c_uint8),
              ("bCopyProtect", c_uint8),
              ("bVariableSize", c_uint8),
              # /** Available frame specifications for this format */
              ("frame_descs", POINTER(uvc_frame_desc))]

class timeval(Structure):
  _fields_ = [("tv_sec", c_long), ("tv_usec", c_long)]
       
class uvc_frame(Structure):
  _fields_ = [# /** Image data for this frame */
              ("data", POINTER(c_uint8)),
              # /** Size of image data buffer */
              ("data_bytes", c_size_t),
              # /** Width of image in pixels */
              ("width", c_uint32),
              # /** Height of image in pixels */
              ("height", c_uint32),
              # /** Pixel data format */
              ("frame_format", c_uint), # enum uvc_frame_format frame_format
              # /** Number of bytes per horizontal line (undefined for compressed format) */
              ("step", c_size_t),
              # /** Frame number (may skip, but is strictly monotonically increasing) */
              ("sequence", c_uint32),
              # /** Estimate of system time when the device started capturing the image */
              ("capture_time", timeval),
              # /** Handle on the device that produced the image.
              #  * @warning You must not call any uvc_* functions during a callback. */
              ("source", POINTER(uvc_device)),
              # /** Is the data buffer owned by the library?
              #  * If 1, the data buffer can be arbitrarily reallocated by frame conversion
              #  * functions.
              #  * If 0, the data buffer will not be reallocated or freed by the library.
              #  * Set this field to zero if you are supplying the buffer.
              #  */
              ("library_owns_data", c_uint8)]       
       
class uvc_device_handle(Structure):
  _fields_ = [("dev", POINTER(uvc_device)),
              ("prev", c_void_p),
              ("next", c_void_p),
              ("usb_devh", c_void_p),
              ("info", c_void_p),
              ("status_xfer", c_void_p),
              ("status_buf", c_ubyte * 32),
              ("status_cb", c_void_p),
              ("status_user_ptr", c_void_p),
              ("button_cb", c_void_p),
              ("button_user_ptr", c_void_p),
              ("streams", c_void_p),
              ("is_isight", c_ubyte)]
       
PT_USB_VID = 0x1e4e
PT_USB_PID = 0x0100

UVC_FRAME_FORMAT_Y16 = 13

VS_FMT_GUID_Y16 = create_string_buffer(
    b"Y16 \x00\x00\x10\x00\x80\x00\x00\xaa\x00\x38\x9b\x71", 16
)
  
BUF_SIZE = 2
q = Queue(BUF_SIZE)

libuvc.uvc_get_format_descs.restype = POINTER(uvc_format_desc)

def uvc_get_frame_formats_by_guid(devh, vs_fmt_guid):
  # for format_desc in uvc_iter_formats(devh):
  p_format_desc = libuvc.uvc_get_format_descs(devh)
  while p_format_desc:
    format_desc = p_format_desc.contents 
    if vs_fmt_guid[0:4] == format_desc.guidFormat[0:4]:
      # import pdb; pdb.set_trace()
      fmt = []
      p_frame_desc = format_desc.frame_descs
      while p_frame_desc:
        fmt.append(p_frame_desc.contents)
        p_frame_desc = p_frame_desc.contents.next
      return fmt
    p_format_desc = p_format_desc.contents.next
  return []

def py_frame_callback(frame, userptr):

  array_pointer = cast(frame.contents.data, POINTER(c_uint16 * (frame.contents.width * frame.contents.height)))
  data = np.frombuffer(
    array_pointer.contents, dtype=np.dtype(np.uint16)
  ).reshape(
    frame.contents.height, frame.contents.width
  ) 

  if frame.contents.data_bytes != (2 * frame.contents.width * frame.contents.height):
    return

  if not q.full():
    q.put(data)

PTR_PY_FRAME_CALLBACK = CFUNCTYPE(None, POINTER(uvc_frame), c_void_p)(py_frame_callback)

def ktoc(val):
  return (val - 27315) / 100.0

def raw_to_8bit(data):
  cv2.normalize(data, data, 0, 65535, cv2.NORM_MINMAX)
  np.right_shift(data, 8, data)
  return cv2.cvtColor(np.uint8(data), cv2.COLOR_GRAY2RGB)

def display_temperature(img, val_k, loc, color):
  val = ktoc(val_k)
  cv2.putText(img,"{0:.1f} degC".format(val), loc, cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
  x, y = loc
  cv2.line(img, (x - 2, y), (x + 2, y), color, 1)
  cv2.line(img, (x, y - 2), (x, y + 2), color, 1)

def main():
  ctx = POINTER(uvc_context)()
  dev = POINTER(uvc_device)()
  devh = POINTER(uvc_device_handle)()
  ctrl = uvc_stream_ctrl()

  res = libuvc.uvc_init(byref(ctx), 0)
  if res < 0:
    print("uvc_init error")
    exit(1)

  try:
    res = libuvc.uvc_find_device(ctx, byref(dev), PT_USB_VID, PT_USB_PID, 0)
    if res < 0:
      print("uvc_find_device error")
      exit(1)

    try:
      res = libuvc.uvc_open(dev, byref(devh))
      if res < 0:
        print("uvc_open error")
        exit(1)

      print("device opened!")

      #print_device_info(devh)
      #print_device_formats(devh)

      frame_formats = uvc_get_frame_formats_by_guid(devh, VS_FMT_GUID_Y16)
      if len(frame_formats) == 0:
        print("device does not support Y16")
        exit(1)

      libuvc.uvc_get_stream_ctrl_format_size(devh, byref(ctrl), UVC_FRAME_FORMAT_Y16,
        frame_formats[0].wWidth, frame_formats[0].wHeight, int(1e7 / frame_formats[0].dwDefaultFrameInterval)
      )

      res = libuvc.uvc_start_streaming(devh, byref(ctrl), PTR_PY_FRAME_CALLBACK, None, 0)
      if res < 0:
        print("uvc_start_streaming failed: {0}".format(res))
        exit(1)

      try:
        while True:
          data = q.get(True, 500)
          if data is None:
            break
          data = cv2.resize(data[:,:], (640, 480))
          minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(data)
          img = raw_to_8bit(data)
          display_temperature(img, minVal, minLoc, (255, 0, 0))
          display_temperature(img, maxVal, maxLoc, (0, 0, 255))
          cv2.imshow('Lepton Radiometry', img)
          cv2.waitKey(1)

        cv2.destroyAllWindows()
      finally:
        libuvc.uvc_stop_streaming(devh)

      print("done")
    finally:
      libuvc.uvc_unref_device(dev)
  finally:
    libuvc.uvc_exit(ctx)

if __name__ == '__main__':
  main()
