import serialtester
import time

if __name__ == '__main__':
    usbc = serialtester.USBCAN("COM18")
    usbc.handshake()
    while True:
        usbc.write(serialtester.CanFrame(0x01,b'\x01\x02\x03\x04\x05\x06\x07\x08'))
        print(usbc.read())
        time.sleep(1)