from abc import ABC, ABCMeta, abstractmethod
import asyncio
from concurrent.futures import ThreadPoolExecutor
import enum
import threading
from cattr import override
import serial
import time
from cobs import cobs


# uint8_t command & frame_type: (command: if it is normal can frame, it is 0x00.)<<4 | is_rtr << 2 | is_extended << 1 | is_error
# uint8_t id[4] : can id
# uint8_t dlc : data length
# uint8_t data[8] : data
class CanFrame:
    def __init__(self, id: int, data: bytes, is_rtr=0, is_extended=0, is_error=0):
        self.command = 0x0  # 0x0 for normal can frame
        self.is_rtr = is_rtr
        self.is_extended = is_extended
        self.is_error = is_error
        self.id = id
        self.data = data
        self.dlc = len(data).to_bytes(1, byteorder="big")

    @staticmethod
    def generate_frame(data: bytes):
        command = (data[0] & 0xF0) >> 4
        is_rtr = (data[0] & 0x04) >> 2
        is_extended = (data[0] & 0x02) >> 1
        is_error = data[0] & 0x01
        id = int.from_bytes(data[1:5], byteorder="big")
        dlc = data[5]
        data = data[6:6+dlc]
        return CanFrame(id, data)

    def generate_bytes(self):
        return bytes([self.command << 4 | self.is_rtr << 2 | self.is_extended << 1 | self.is_error]) + \
            self.id.to_bytes(4, byteorder="big") + \
            self.dlc + \
            self.data

    def __str__(self):
        return "command: " + str(self.command) + "\n" + \
            "is_rtr: " + str(self.is_rtr) + "\n" + \
            "is_extended: " + str(self.is_extended) + "\n" + \
            "is_error: " + str(self.is_error) + "\n" + \
            "id: " + str(self.id.to_bytes(4, byteorder="big")) + "\n" + \
            "dlc: " + str(int.from_bytes(self.dlc, byteorder="big")) + "\n" + \
            "data: " + str(self.data) + "\n"


class USBCAN:
    def __init__(self, port):
        self.ser = serial.Serial(port=port)

    def handshake(self):

        is_return = False
        while not is_return:
            time.sleep(1)
            self.ser.write(HelloUSBCAN)
            data = self.ser.read_all()
            data = cobs_decode(data)
            if data == b'\x10HelloSLCAN':
                is_return = True
                print("Handshake success")
                print("The board has FW_version 2, and it is working")

    def write(self, frame: CanFrame):
        encode = cobs_encode(frame.generate_bytes())
        self.ser.write(encode)

    def read(self):
        u = self.ser.read_until(b'\x00')
        decode = cobs_decode(u)
        return CanFrame.generate_frame(decode)

    def read_raw(self):
        u = self.ser.read_all()
        if u != b'':
            print(u)


class ShirasuMode(enum.Enum):
    desable = 0
    default = 1
    homing = 2
    reversed = 3
    current = 4
    velocity = 5
    position = 6

# abstract class for adaptor. it will be used from usbcan


class Adaptor(ABC):
    def __init__(self) -> None:
        self.serial_write = None

    @ abstractmethod
    def read_handler(self, frame: CanFrame) -> None:
        pass

    def registration(self, write) -> None:
        self.serial_write = write


class ShirasuAdaptor(Adaptor):
    def __init__(self, base_id: int) -> None:
        super().__init__()
        self.base_id = base_id

    def set_mode(self, mode: ShirasuMode) -> None:
        self.serial_write(CanFrame(self.base_id, bytes([mode.value])))

    def send_target(self, target: float) -> None:
        self.serial_write(
            CanFrame(self.base_id + 1, target.to_bytes(4, byteorder="little")))

    @ override
    def read_handler(self, frame: CanFrame) -> None:
        if (frame.id == self.base_id + 2):
            pass  # todo


class RoboMasterAdaptor(Adaptor):
    def __init__(self) -> None:
        super().__init__()

    @ override
    def read_handler(self, frame: CanFrame) -> None:
        pass  # todo

    def send_current(self, currents: list) -> None:
        pass  # todo


def cobs_encode(data: bytes):
    try:
        return cobs.encode(data) + b"\x00"
    except:
        return b""


def cobs_decode(data: bytes):
    try:
        return cobs.decode(data[:-1])
    except:
        return b""


class USBCANContloller:
    def __init__(self, port):
        self.ser = serial.Serial(port=port)
        self.handshake_success = False
        # for reading thread
        self.is_shutdown = False
        self.adaptors = []
        self.thread = threading.Thread(target=self.__read_handle_thread)

    def __delattr__(self, __name: str) -> None:
        self.is_shutdown

    # handshake with board

    async def handshake(self):
        if self.handshake_success:
            return True

        while not self.handshake_success:
            await asyncio.sleep(100)
            self.ser.write(HelloUSBCAN)
        return True

    # write CanFrame to serial
    def write(self, frame: CanFrame):
        encode = cobs_encode(frame.generate_bytes())
        self.ser.write(encode)

    # registrate adaptor.
    def registration(self, adaptor: Adaptor):
        self.adaptors.append(adaptor)
        adaptor.registration(self.write)

    # start communication with usbcan.
    def start(self):
        self.thread.start()

    def stop(self):
        self.is_shutdown = True

    def __read_handle_thread(self):
        for frame in self.__read_stream():
            for adaptor in self.adaptors:
                adaptor.read_handler(frame)

    # generator for read. it will return CanFrame
    def __read_stream(self):
        data_buffer = b''
        while not self.is_shutdown:
            try:
                data_buffer += self.ser.read_all()
            except:
                return
            u = data_buffer.split(b'\x00')

            # if data_buffer is not end with 0x00, it will be stored in data_buffer
            data_buffer = u[-1]
            for i in range(len(u) - 1):
                decode = cobs_decode(u)
                if decode == b'\x10HelloSLCAN':
                    self.handshake_success = True
                    break
                yield CanFrame.generate_frame(decode)


HelloUSBCAN = b'\x02\x10\x00'

if __name__ == '__main__':
    print("It is sample code for USBCAN")
    print("!!!you should change COM port number to your own port number!!!")
    usbcan = USBCAN("COM1")
    usbcan.handshake()
    u = CanFrame(1237, b'\x01\x02\x03\x04\x05\x06\x07\x08')
    while True:
        usbcan.write(u)
        time.sleep(1)
        print(usbcan.read())
