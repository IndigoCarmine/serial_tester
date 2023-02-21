# serialtester
A simple USBCAN　adapter tester for Windows, Linux and Mac OS X.
USBCAN should install my firmware 
[USBCAN firmware](https://github.com/IndigoCarmine/usbcan_fw_v2)
## Usage
Use pip to install the dependencies. You should run the following commands in the terminal.

'''bash
pip install pyserial
pip install cobs
'''

Check the serial port name, and replace the port name in the code.
e.g.
Linux: /dev/serial/by-id/usb-FTD...
(if you set udev rules, you can use /dev/usbcan)
Windows: COM...

'''python
usbc = serialtester.USBCAN("COM18")  # replace the port name
'''