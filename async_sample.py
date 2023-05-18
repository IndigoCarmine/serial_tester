import time
import serialtester


shirasuAdaptor = serialtester.ShirasuAdaptor(0x1)
robomasterAdaptor = serialtester.RoboMasterAdaptor()


if __name__ == "__main__":
    # it communicates usbcan and handle adaptor callback
    controller = serialtester.USBCANContloller("COM3")

    # registrate Adaptor
    controller.registration(shirasuAdaptor)
    controller.registration(robomasterAdaptor)

    # communication
    controller.start()

    shirasuAdaptor.set_mode(serialtester.ShirasuMode.velocity)
    while True:
        shirasuAdaptor.set_mode(serialtester.ShirasuMode.velocity)
        shirasuAdaptor.send_target(10)
        time.sleep(1)
        print("send")
