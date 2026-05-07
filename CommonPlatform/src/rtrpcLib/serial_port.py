# !/usr/bin/python
# -*- coding: utf-8 -*-

import time
import serial
from datetime import datetime


class SerialPort(object):
    def __init__(self, portName, baudRate=115200, timeout=5, publisher=None):
        self.publisher = publisher
        self._portName = portName
        self._baudRate = baudRate
        self._timeOut = timeout
        self._port = None
        self._debug = True
        self.connect()

    def log(self, msg):
        if self._debug:
            print(str(datetime.now()) + ' ' * 3 + msg)
        if self.publisher:
            self.publisher.publish(msg)
            self.publisher.publish('\n')

    def connect(self):
        """
        no need open cause init Serial means open
        didn't set timeout means block
        :return: True
        """
        if not self.is_open():
            try:
                self._port = serial.Serial(self._portName, self._baudRate)
                self.log("[Port] Open {} Serial Port Success\n".format(self._portName))
            except Exception as e:
                self.log('[Port Exception]' + str(e))
                self.log("[Port] Open {} Serial Port Fail \n".format(self._portName))
                return False
            return True
        return True

    def close(self):
        if self.is_open():
            self._port.flush()
            self._port.close()
            del self._port
            self._port = None
            self.log("[Port] Close {} Serial Port Success\n".format(self._portName))
        return True

    def is_open(self):
        if self._port is None:
            return False
        b_ret = True
        try:
            b_ret = self._port.isOpen()
        except Exception:
            b_ret = False
        finally:
            return b_ret

    def getBaudrate(self):
        return self._port.baudrate

    def setBaudrate(self, baud_rate):
        assert (baud_rate > 0)
        self._port.baudrate = baud_rate
        return True

    def setTimeout(self, timeOut=6):
        self._port.timeout = timeOut
        
    def clear_buff(self):
        self._port.flushInput()
        self._port.flushOutput()

    def send(self, cmd, hex_cmd=None):
        if self.is_open():
            self._port.flushInput()
            self._port.flushOutput()
            self.log('[Send]' + cmd)
            if hex_cmd:
                self.log('[Send hex]' + hex_cmd)
            wdData = (cmd + "\n").encode()
            return self._port.write(wdData)
        else:
            raise RuntimeError("Cmd send error, port not open: %s", self._port.name)

    def send_by_byte(self, cmd, hex_cmd=None, interval=0.005):
        if self.is_open():
            self._port.flushInput()
            self._port.flushOutput()
            self.log('[Send]' + cmd)
            if hex_cmd:
                self.log('[Send hex]' + hex_cmd)
            for byte in cmd:
                self._port.write(byte)
                time.sleep(interval)
            self._port.write("\n")
        else:
            raise RuntimeError("Cmd send error, port not open: %s", self._port.name)

    def send_by_array(self, array_cmd, hex_cmd=None, interval=0.005, byte_count=8):
        if self.is_open():
            self._port.flushInput()
            self._port.flushOutput()
            if not isinstance(array_cmd, (bytes, bytearray)):
                raise RuntimeError('array cmd is correct, must be bytes or bytearray')
            # array_cmd.append(0x0d)
            array_cmd.append(0x0a)
            self.log('[Send]' + array_cmd)
            if hex_cmd:
                self.log('[Send hex]' + hex_cmd)
            self._port.write(array_cmd)
        else:
            raise RuntimeError("Cmd send error, port not open: %s", self._port.name)

    def send_by_hex(self, hex_cmd=None):
        """
        param: hex_cmd must be '05 5a 0d 00 92 0f 41 54'
        param:             or  '055a0d00920f4154'
        """
        if self.is_open():
            self._port.flushInput()
            self._port.flushOutput()
            try:
                basestring
            except NameError:
                basestring = str
            if not isinstance(hex_cmd, basestring):
                raise RuntimeError('Cmd send error, cmd format must be hex cmd')
            hex_cmd = hex_cmd.replace(' ', '')
            array_list = []
            for i in range(0, len(hex_cmd), 2):
                array_list.append(int(hex_cmd[i:i+2], 16))
            tx_array = bytearray(array_list)
            self.log('[Send]' + str(tx_array))
            self.log('[Send hex]' + hex_cmd)
            # tx_array.append(0x0d)
            tx_array.append(0x0a)
            self._port.write(tx_array)
        else:
            raise RuntimeError("Cmd send error, port not open: %s", self._port.name)

    def send_read(self, cmd, terminator=']', hex_cmd=None, timeout=7000):
        self.read_string()
        self.send(cmd, hex_cmd)
        return self.read_until(terminator, timeout)

    def read_until(self, terminator, timeout=5000):
        """
        Read until a termination sequence is found ('\n' by default), the size
        is exceeded or until timeout occurs.
        """
        timeout_happen = False
        recv = ""
        time_out = timeout/1000.0
        begin = time.time()
        try:
            while True:
                temp = self._port.read(self._port.inWaiting())
                if temp:
                    recv += str(temp.decode()) if isinstance(temp, bytes) else temp
                if recv.rfind(str(terminator)) > 0:
                    break
                elif time.time() - begin > time_out:
                    timeout_happen = True
                    break
            if timeout_happen:
                self.log('[Port Timeout]' + recv)
            else:
                self.log('[Recv]' + recv)
            return recv
        except Exception as e:
            self.log('[Port Exception]'+str(e))
            if recv:
                self.log('[Recv]' + recv)
            return ''

    def read_string(self):
        recv = ""
        start = time.time()
        while self._port.inWaiting() > 0:
            if time.time() - start > 2:
                break
            keep_recv = self._port.read(self._port.inWaiting())
            recv += keep_recv
            time.sleep(0.2)
        self.log('[Recv]' + recv)
        return recv


if __name__ == "__main__":
    dev = SerialPort("/dev/cu.usbserial-PRMDUT200", 921600)
    print("Now baudRate:", dev.getBaudrate())
    dev.send_by_hex("00ff")
    startTime = time.time()
    dev.setBaudrate(115200)
    dev.read_until("BROM")
    print("EndTime:%s".format(time.time() - startTime))

