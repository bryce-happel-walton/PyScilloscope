# boot.py -- run on boot-up
# can run arbitrary Python, but best to keep it minimal

import machine
import pyb

pyb.freq(168000000)
#pyb.main('main.py') # main script to run after this one
#pyb.usb_mode('VCP+MSC') # act as a serial and a storage device
#pyb.usb_mode('VCP+HID') # act as a serial device and a mouse
