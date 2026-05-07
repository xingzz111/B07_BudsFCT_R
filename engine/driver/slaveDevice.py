from rtlib import pyboard
import time
import ast
import re
from rtRP2.rp2Device import Rp2Device

class sDevice(object):

    def __init__(self, port, baudrate, publisher=None):
        self._port = port
        self._baudrate = baudrate
        # self._pyb = None
        self._publisher = publisher
        # self.isprint = True
        # self.init()
        self._client = None

    def init(self):
        if not self._client:
            self._client = Rp2Device(self._port, self._baudrate, self._publisher)
            self._client.init()
            self._client._pyb.exec_("from MixDevice import *")
        return True

    def deinit(self):
        self._client._pyb.exec_("del mixdevice")
        # self._client._pyb.exec_("import gc;gc.mem_free()")
        self._client.deinit()
        self._client = None
        
        return True

    def rpc_call(self, func_name, args_list, **kwargs):
        assert(isinstance(func_name, str), "Wrong function name type")
        assert(isinstance(args_list, list) or args_list==None, "Wrong function args type")
        _args = []
        _args.append(func_name)
        if args_list:
            _args.extend(args_list)
        return self._client.rpc_call(*_args, **kwargs)

    def parse_result(self, response):

        """
        通用解析方法：解析返回值并转换为对应的Python类型。
        
        Args:
            response (bytes): 返回的字节数据，例如 b'xxx\r\nxxxx\r\nxxxx\r\n'
        
        Returns:
            Any: 转换后的Python对象（float, int, str, list, dict, array.array等）
        """
        try:
            # 解码为字符串

            last_line = response.split('\r\n')[-1].strip()
            match = re.search(r"array\('[a-zA-Z]', \[(.*)\]\)", last_line)
            if match:
                numbers_str = match.group(1)
                last_line = f"[{numbers_str}]"
            return ast.literal_eval(last_line)
        except (ValueError, SyntaxError):
            # 如果无法解析为Python原生类型，返回字符串本身
            return last_line





if __name__ == "__main__":
    client = Rp2Device("COM100", 115200)

    client.init()
    # check_oqc(client)
    # client._pyb.exec_("from MixDevice import *")
    # client._pyb.exec_("import micropython")
    # print(client._pyb.exec_("print(micropython.mem_info())"))
    # client._pyb.exec_("import gc")
    # client._pyb.exec_("gc.collect()")
    # print(client._pyb.exec_("print(micropython.mem_info())"))

    client.rpc_call('mixdevice.measure_pulse', 50,3)

    # # client.rpc_call('mixdevice.setStateByName','VREFOUT_2V5', "DMM_VINA", 1)
    # # client.rpc_call('mixdevice.measureByDMM_Matrix', 'ch1', '7000mv', 'VREFOUT_2V5')
    # # client.rpc_call('mixdevice.measureByDMM_Matrix', 'ch0', '7000mv', 'VREFOUT_2V5')

    # power_on(client)
    # power_on_1v2(client)
    # client.deinit()