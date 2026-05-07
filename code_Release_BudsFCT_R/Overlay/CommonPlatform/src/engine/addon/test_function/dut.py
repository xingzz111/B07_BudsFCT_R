import os
import re
import time
import json

import subprocess
from threading import Timer


DEFAULT_TIMEOUT = 3000
MSH_MODE = "msh()"
TERMINATOR = "msh >"
SUCCESS = "success"
DUT_PARSER_PATH = "D:/Overlay/engine/addon/config/dut_paser.json"



class dut(object):

    rpc_public_api = [
        "open_uart", "close_uart","send_read", "detect_msh_mode", "write_bsn", "read_bsn", "led_control",
        "diags_parse", "read_until", "uart_slave_diags"
    ]

    def __init__(self, xobjects):
        self.xobjects = xobjects
        self.mixrpc = xobjects["mix_dev_rpc"]
        self.site = xobjects.get('site')
        self.publisher = xobjects.get('cb_pub')
        self.serial = xobjects.get('uart0', None)
        self.config = self._load_parse_file()

        # ctx = zmq.Context().instance()
        # self.publisher = ZmqPublisher(ctx,'tcp://127.0.0.1:6850','UART_0'.encode())
        # self.serial = SerialPort("COM12",9600)

    def log(self, message):
        # if not message.endswith('\n'):
        #     message += '\n'
        if self.publisher:
            # print("------DEBUG------")
            print(message)
            msg = '[{}] '.format(message)
            self.publisher.publish(msg)

    def _load_parse_file(self):
        f = open(DUT_PARSER_PATH, 'r')
        config = json.load(f)
        f.close()
        return config

    def _case_communicate(self, *args, **kwarg):
        self._read_all()

    def _send_read_by_key_word(self, cmd, key, terminator):
        self.serial.send(cmd)
        tmp = self.serial.read_until_by_key(key, terminator, 5000)
        return tmp if tmp else None

    def _read_all(self):
        return self.serial.read_all()
    
    def read_until(self, *arg, **kwargs):
        key = str(arg[0])
        if self.serial.read_until(key, 8000):
            return "--PASS--"
        return "--FAIL--"

    def open_uart(self, *args, **kwargs):
        self.serial.connect()
        return '--PASS--'

    def close_uart(self, *args, **kwargs):
        self.serial.close()
        return '--PASS--'

    def send_read(self, *args, **kwarg):
        cmd = str(args[0])
        key = TERMINATOR
        if len(args) == 2:
            key = str(args[1])
        if self._send_read_by_key_word(cmd, key, TERMINATOR):
            return key
        return "--FAIL--"

    def diags_parse(self, *args, **kwarg):
        cmd = str(args[0])
        res = self._send_read_by_key_word(cmd, TERMINATOR, TERMINATOR)
        if res:
            _pattern = self.config.get(cmd, None)
            if _pattern:
                print("res: ", res)
                print("config: ", self.config)
                print("_pattern: ",_pattern)
                match = re.search(_pattern, res)
                if match:
                    return match.group(1)
            else:
                return "--FAIL--ERROR-NO-PATTERN"
        return "--FAIL--"

    def detect_msh_mode(self, *args, **kwarg):
        self.serial.read_until_by_key("FUEL_GAUGE_BATTERY_LOW", "DEFAULT_BATTERY_LOW_EVT", 10000)
        if self._send_read_by_key_word(MSH_MODE, TERMINATOR, TERMINATOR):
            return "--PASS--"
        return "--FAIL--"

    def write_bsn(self, *args, **kwarg):
        sn = str(args[0])
        if self._send_read_by_key_word("write_bsn {}".format(sn), "success", TERMINATOR):
            return "--PASS--"
        return "--FAIL--"

    def read_bsn(self, *args, **kwarg):
        t = self._send_read_by_key_word("read_bsn", "msh >", TERMINATOR)
        if t:
            import  re
            match = re.search("smt_bsn:(.*)", t)
            if match:
                return match.group(1).strip()
        return "--FAIL--"

    def led_control(self, *args, **kwarg):
        assert len(args) == 2
        color = str(args[0]).lower()
        status = str(args[1]).lower()
        assert color in ("red", "green", "blue", "rgb")
        assert status in ("close", "open")
        self._send_read_by_key_word("led_{} {}".format(color, status), SUCCESS, TERMINATOR)
        return True

    def uart_slave_diags(self, *args, **kwarg):
        print("&"*100)
        cmd,key = str(args[0]).split("@")
        response = [0x02, 0x00, 0x00]
        self.serial.send(cmd)
        timeout = 20
        start_time = time.time()
        isFound = False
        t = [1, 0, 0]
        while True:
            res = self.mixrpc.rpc_call("com.read_by_byte")
            print("res: {}".format(res))
            if res:
                if len(res) < 3:
                    continue
                for index, value in enumerate(res):
                    if t[0] == value:
                        if t[1] == res[index + 1] and t[2] == res[index + 2]:
                            isFound = True
                            break
                if isFound:
                    break
            if time.time() - start_time > timeout:
                break
            time.sleep(1)
        if isFound:
            self.mixrpc.rpc_call("com.write_by_byte", response)
            print("&" * 100)
            if self.serial.read_until(key, 20000):
                self.serial.read_all()
                return key
        return "--FAIL--"