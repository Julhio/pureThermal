# pureThermal UVC Capture Test With C++

This reporitory was created to test the PureThermal 1 with C++ programming.
The code was based on:

The [PureThermal 1 FLIR Lepton development board](https://groupgets.com/manufacturers/groupgets-labs/products/pure-thermal-1-flir-lepton-dev-kit)
by GroupGets supports the USB video class (UVC), and this makes it very easy to capture thermal imaging data
from a host PC using standard tools and libraries. If you want to prototype quickly, your application demands
increasing processing power, or you simply don't want to hack on the firmware, check out these examples to get started.

### uvc-radiometry_mod.py

This example is a simplification of the [uvc-radiometry.py](https://github.com/groupgets/purethermal1-uvc-capture/blob/master/python/uvc-radiometry.py) 

This example uses ctypes to hook into `libuvc` and circumvents the troubles associated with using OS camera
capture drivers, particularly on Mac OS X, whose standard capture drivers do not support the Y16 data type
for grabbing raw sensor data.

This example leverages the Radiometric Lepton 2.5. The same approach can of course modified to support other Leptons as well.

You'll need the modified version of `libuvc` from [groupgets/libuvc](https://github.com/groupgets/libuvc).

    git clone https://github.com/groupgets/libuvc
    cd libuvc
    mkdir build
    cd build
    cmake ..
    make && sudo make install

If you don't want to install this system-wide, you can copy the shared library to your working directory.

Then run the example:

    ./uvc-radiometry_mod.py
