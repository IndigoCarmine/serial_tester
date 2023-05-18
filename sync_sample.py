import serialtester
import time


def change_target(ampere, can_frame):
    ampere = int(ampere)
    if ampere > 16384:
        ampere = 16384
    elif ampere < -16384:
        ampere = -16384
    can_frame.data = bytes(ampere.to_bytes(
        2, byteorder="big", signed=True) + bytes([0, 0, 0, 0, 0, 0]))
    return can_frame


if __name__ == '__main__':
    usbc = serialtester.USBCAN("COM9")
    # usbc.handshake()
    target = 5000
    P_gain = 0.0001
    D_gain = 0.7
    previous_current = 0
    previous_error = 0
    can_frame = serialtester.CanFrame(
        0x200, bytes([0x0F, 0xFF, 0, 0, 0, 0, 0, 0]))

    while True:
        print("Sending frame")
        can = usbc.read()
        velocity = int.from_bytes(
            can.data[2:4], byteorder="big", signed=True)
        current = int.from_bytes(
            can.data[0:2], byteorder="big", signed=True)
        print("current: " + str(current))
        print("velocity:" + str(velocity))
        error = (target - velocity)

        send = error*P_gain+(error-previous_error)*D_gain+previous_current
        previous_error = error
        previous_current = send
        print("send: " + str(send))

        # can_frame = change_target(1000, can_frame)
        can_frame.data = bytes((10000).to_bytes(
            2, byteorder="big", signed=True) + bytes([0, 0, 0, 0, 0, 0]))
        usbc.write(can_frame)
