from rtlib import pyboard
import time
import ast
import re

class Rp2Device(object):

    def __init__(self, port, baudrate, publisher=None):
        print("========rp2 init=========",flush=True)
        self._port = port
        self._baudrate = baudrate
        self._pyb = None
        self._publisher = publisher
        self.isprint = True
        # self.init()

    def init(self):
        if not self._pyb:
            self._pyb = pyboard.Pyboard(self._port, self._baudrate)
            self._pyb.enter_raw_repl()
            self._pyb.exec_("from MixDevice import *")
            # client._pyb.exec_("import micropython")
            # print(client._pyb.exec_("print(micropython.mem_info())"))
            self._pyb.exec_("import gc")
            self._pyb.exec_("gc.collect()")
            # print(client._pyb.exec_("print(micropython.mem_info())"))
            # self._pyb.exec_("from MixDevice import *")
            # self._pyb.exec_("import gc")
            # self._pyb.exec_("gc.collect()")
        return True

    def deinit(self):
        if self._pyb:
            self._pyb.exit_raw_repl()
            self._pyb = None

    def rpc_call(self, *args, **kwargs):
        # start_time = time.time()
        # 检查是否提供了函数名
        if len(args) < 1:
            raise RuntimeError("Missing function name")
        # 提取函数名
        Input = ast.literal_eval(str(args[0]))
        function = Input['function']
        # _timeout = kwargs.get("timeout", None)
        # return function
        # 提取位置参数
        function_args = Input['args']
        # 将位置参数转为字符串表示
        arg_strings = [repr(arg) for arg in function_args]  # 使用 repr 确保参数格式正确
        # kwargs_strings = [f"{key}={repr(value)}" for key, value in kwargs.items()]
        ifpub = kwargs.get("ifpub", True)
        # 拼接所有参数
        # all_args = ", ".join(arg_strings + kwargs_strings)
        all_args = ", ".join(arg_strings)
        # 构造要执行的 Python 代码
        python_code = f"{function}({all_args})"
        # 打印调试信息
        if self._publisher and ifpub:
            self._publisher.publish(f"{python_code}")
        if self.isprint:
            print(f"{python_code}")
        # 执行代码（假设 pyb 是某种执行器对象）
        if hasattr(self, "_pyb") and self._pyb:
            # if _timeout:
            #     print("type: {} ,{}".format(type(_timeout),_timeout))
            #     res, ret_err = self._pyb.exec_raw(python_code, timeout=_timeout)
            #     print("1" * 100)
            # else:
            res = self._pyb.exec_(python_code)
            # print("2"*100)
            res = res.decode('utf-8').strip()
            if self.isprint:
                print(res)
            if self._publisher and ifpub:
                self._publisher.publish(res)
            res = self.parse_result(res)

            # print("durating: {}".format(time.time() - start_time))
            return res
        else:
            raise RuntimeError("No execution engine (_pyb) found!")

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

def check_oqc(client, num=1):
    for i in range(num):
        print("*************************{}************************".format(i))
        client.rpc_call("mixdevice.reset")
        time.sleep(0.5)
        # test charge
        client.rpc_call("mixdevice.chargeEnable", 5000, 500)
        time.sleep(0.1)
        client.rpc_call("mixdevice.measureVoltageByOdin", "charger")

        client.rpc_call("mixdevice.chargeDisable")
        time.sleep(0.1)
        client.rpc_call("mixdevice.measureVoltageByOdin", "charger")

        #test battery
        client.rpc_call("mixdevice.batteryEnable", 3800, 500)
        time.sleep(0.1)
        client.rpc_call("mixdevice.measureVoltageByOdin", "battery")        
        client.rpc_call("mixdevice.odin_datalogger", "ch0", 500, 25000)
        client.rpc_call("mixdevice.odin_datalogger", "ch0", 500, 25000)
        client.rpc_call("mixdevice.odin_datalogger2", "ch0", 1000, 25000)

        client.rpc_call("mixdevice.batteryDisable")
        time.sleep(0.1)
        client.rpc_call("mixdevice.measureVoltageByOdin", "battery")

        # # test dmm 3v3
        # client.rpc_call('mixdevice.relay', 'DMM_MUX_PP3V3_SYS')
        # time.sleep(0.1)
        client.rpc_call("mixdevice.measureByDMM", "ch1", "7000mv")
        client.rpc_call("mixdevice.dmm_datalogger", "ch1", 500, 25000)
        client.rpc_call("mixdevice.dmm_datalogger", "ch1", 1000, 25000)

        # client.rpc_call('mixdevice.relay', 'DMM_MUX_PP3V3_SYS', 'DISCONNECT')
        time.sleep(0.1)
        client.rpc_call("mixdevice.measureByDMM", "ch1", "7000mv")
        client.rpc_call("mixdevice.dmm_datalogger", "ch1", 500, 25000)
        client.rpc_call("mixdevice.dmm_datalogger", "ch1", 1000, 25000)

        # test dmm 5V
        client.rpc_call("mixdevice.chargeEnable", 5000, 500)
        # client.rpc_call('mixdevice.relay', 'ODIN_VCHG_TO_DUT_POGO_PIN_VCC', 'CONNECT')
        # client.rpc_call('mixdevice.relay', 'DMM_MUX_DUT_POGO_PIN_VCC', 'CONNECT')
        time.sleep(0.5)
        client.rpc_call("mixdevice.measureByDMM", "ch1", "7000mv")
        client.rpc_call("mixdevice.dmm_datalogger", "ch1", 500, 25000)
        client.rpc_call("mixdevice.dmm_datalogger", "ch1", 1000, 25000)
        client.rpc_call("mixdevice.chargeDisable")
        # time.sleep(0.5)
        # client.rpc_call('mixdevice.relay', 'ODIN_VCHG_TO_DUT_POGO_PIN_VCC', 'DISCONNECT')
        # client.rpc_call('mixdevice.relay', 'DMM_MUX_DUT_POGO_PIN_VCC', 'DISCONNECT')
        time.sleep(0.1)
        client.rpc_call("mixdevice.measureByDMM", "ch1", "7000mv")
        client.rpc_call("mixdevice.dmm_datalogger", "ch1", 500, 25000)
        client.rpc_call("mixdevice.dmm_datalogger", "ch1", 1000, 25000)

        # odin output 3v8
        client.rpc_call("mixdevice.batteryEnable", 3800, 500)
        time.sleep(0.1)
        client.rpc_call("mixdevice.measureVoltageByOdin", "battery")
        client.rpc_call("mixdevice.odin_datalogger", "ch0", 500, 25000)
        client.rpc_call("mixdevice.odin_datalogger", "ch0", 500, 25000)
        client.rpc_call("mixdevice.odin_datalogger2", "ch0", 1000, 25000)
        # client.rpc_call('mixdevice.relay', 'ODIN_BATT_TO_DUT_TP10_1P05V', 'CONNECT')
        # client.rpc_call('mixdevice.relay', 'DMM_MUX_DUT_TP10_1P05V', 'CONNECT')
        # time.sleep(0.1)
        client.rpc_call("mixdevice.measureByDMM", "ch1", "7000mv")
        client.rpc_call("mixdevice.dmm_datalogger", "ch1", 500, 25000)
        client.rpc_call("mixdevice.dmm_datalogger", "ch1", 1000, 25000)
        client.rpc_call("mixdevice.batteryDisable")
        time.sleep(0.1)
        client.rpc_call("mixdevice.measureByDMM", "ch1", "7000mv")
        client.rpc_call("mixdevice.dmm_datalogger", "ch1", 500, 25000)
        client.rpc_call("mixdevice.dmm_datalogger", "ch1", 1000, 25000)

        # test adg2128
        client.rpc_call("mixdevice.relay", "PP1V7_LDO_EN")
        client.rpc_call("mixdevice.setState", 0, 3, 1, 1)
        client.rpc_call("mixdevice.setState", 0, 3, 0, 1)
        client.rpc_call("mixdevice.relay", "PP1V7_LDO_EN", "DISCONNECT")

        client.rpc_call("mixdevice.setDac", 0, 1000)
        client.rpc_call("mixdevice.setDac", 0, 0)

        client.rpc_call("mixdevice.setDac", 1, 1000)
        client.rpc_call("mixdevice.setDac", 0, 1000)


        client.rpc_call("mixdevice.setStateByName","DUT_TP38_FW_RX", "GPIO_1V7", 1)
        client.rpc_call("mixdevice.setStateByName","DUT_TP39_FW_TX", "GPIO_1V7", 1)
        client.rpc_call("mixdevice.setStateByName","DUT_TP38_FW_RX", "GPIO_1V7", 0)
        client.rpc_call("mixdevice.setStateByName","DUT_TP39_FW_TX", "GPIO_1V7", 0)

        client.rpc_call('mixdevice.relay', 'PP1V7_LDO_EN', 'CONNECT')
        client.rpc_call('mixdevice.relay', 'ODIN_VCHG_TO_DUT_TP40_POGO5V', 'CONNECT')
        client.rpc_call('mixdevice.relay', 'ODIN_BATT_TO_DUT_TP22_BAT_P', 'CONNECT')
        client.rpc_call('mixdevice.relay', 'ODIN_BATT_TO_DUT_TP10_1P05V', 'CONNECT')
        client.rpc_call('mixdevice.relay', 'PP1V7_VDDO_TO_DUT_TP41_VDDO', 'CONNECT')
        client.rpc_call('mixdevice.relay', 'ODIN_BATT_OVP_RESET', 'CONNECT')
        client.rpc_call('mixdevice.relay', 'ODIN_VCHG_OVP_RESET', 'CONNECT')
        client.rpc_call('mixdevice.relay', 'UART_FT232_RESET', 'CONNECT')
        client.rpc_call('mixdevice.relay', 'UART_FT232_TO_DUT_FULL_DUPLEX', 'CONNECT')
        client.rpc_call('mixdevice.relay', 'UART_FT232_TO_DUT_HALF_DUPLEX', 'CONNECT')
        client.rpc_call('mixdevice.relay', 'UART_COREBOARD_TO_DUT', 'CONNECT')
        client.rpc_call('mixdevice.relay', 'CCS_CURRENT_OUTPUT_RANG_100K', 'CONNECT')
        client.rpc_call('mixdevice.relay', 'CCS_CURRENT_OUTPUT_RANG_1K', 'CONNECT')
        client.rpc_call('mixdevice.relay', 'CCS_OUTPUT_POSITIVE_POLARITY', 'CONNECT')
        client.rpc_call('mixdevice.relay', 'CCS_OUTPUT_NEGATIVE_POLARITY', 'CONNECT')
        client.rpc_call('mixdevice.relay', 'CCS_CURRENT_MEASURE_RANG_101K', 'CONNECT')
        client.rpc_call('mixdevice.relay', 'CCS_CURRENT_MEASURE_RANG_1K', 'CONNECT')
        client.rpc_call('mixdevice.relay', 'EDGE_TRIGGER_RESET', 'CONNECT')
        client.rpc_call('mixdevice.relay', 'BES_BOARD_POWER_ON', 'CONNECT')

        client.rpc_call('mixdevice.relay', 'PP1V7_LDO_EN', 'DISCONNECT')
        client.rpc_call('mixdevice.relay', 'ODIN_VCHG_TO_DUT_TP40_POGO5V', 'DISCONNECT')
        client.rpc_call('mixdevice.relay', 'ODIN_BATT_TO_DUT_TP22_BAT_P', 'DISCONNECT')
        client.rpc_call('mixdevice.relay', 'ODIN_BATT_TO_DUT_TP10_1P05V', 'DISCONNECT')
        client.rpc_call('mixdevice.relay', 'PP1V7_VDDO_TO_DUT_TP41_VDDO', 'DISCONNECT')
        client.rpc_call('mixdevice.relay', 'ODIN_BATT_OVP_RESET', 'DISCONNECT')
        client.rpc_call('mixdevice.relay', 'ODIN_VCHG_OVP_RESET', 'DISCONNECT')
        client.rpc_call('mixdevice.relay', 'UART_FT232_RESET', 'DISCONNECT')
        client.rpc_call('mixdevice.relay', 'UART_FT232_TO_DUT_FULL_DUPLEX', 'DISCONNECT')
        client.rpc_call('mixdevice.relay', 'UART_FT232_TO_DUT_HALF_DUPLEX', 'DISCONNECT')
        client.rpc_call('mixdevice.relay', 'UART_COREBOARD_TO_DUT', 'DISCONNECT')
        client.rpc_call('mixdevice.relay', 'CCS_CURRENT_OUTPUT_RANG_100K', 'DISCONNECT')
        client.rpc_call('mixdevice.relay', 'CCS_CURRENT_OUTPUT_RANG_1K', 'DISCONNECT')
        client.rpc_call('mixdevice.relay', 'CCS_OUTPUT_POSITIVE_POLARITY', 'DISCONNECT')
        client.rpc_call('mixdevice.relay', 'CCS_OUTPUT_NEGATIVE_POLARITY', 'DISCONNECT')
        client.rpc_call('mixdevice.relay', 'CCS_CURRENT_MEASURE_RANG_101K', 'DISCONNECT')
        client.rpc_call('mixdevice.relay', 'CCS_CURRENT_MEASURE_RANG_1K', 'DISCONNECT')
        client.rpc_call('mixdevice.relay', 'EDGE_TRIGGER_RESET', 'DISCONNECT')
        client.rpc_call('mixdevice.relay', 'BES_BOARD_POWER_ON', 'DISCONNECT')


def power_on(client):

    client.rpc_call('mixdevice.relay', 'UART_FT232_TO_DUT_FULL_DUPLEX', 'CONNECT')

    client.rpc_call('mixdevice.setStateByName', 'DUT_TP38_FW_RX', 'UART_FT232_TO_DUT_1V7', 1)
    client.rpc_call('mixdevice.setStateByName', 'DUT_TP39_FW_TX', 'UART_DUT_TO_FT232_1V7', 1)
    time.sleep(0.1)
    client.rpc_call('mixdevice.relay', 'ODIN_VCHG_TO_DUT_TP40_POGO5V', 'CONNECT')
    client.rpc_call("mixdevice.chargeEnable", 5000, 500)
    time.sleep(1)
    client.rpc_call("mixdevice.measureVoltageByOdin", "charger")
    client.rpc_call("mixdevice.measureCurrentByOdin", "charger")

def power_on_1v2(client):

    # client.rpc_call('mixdevice.relay', 'ODIN_BATT_TO_DUT_TP22_BAT_P', 'CONNECT')
    client.rpc_call('mixdevice.relay', 'ODIN_BATT_TO_DUT_TP10_1P05V', 'CONNECT')
    time.sleep(0.1)
    client.rpc_call("mixdevice.batteryEnable", 1200, 50)
    time.sleep(1)
    client.rpc_call("mixdevice.measureVoltageByOdin", "battery")
    client.rpc_call("mixdevice.odin_datalogger", "ch0", 100, 1000)
    client.rpc_call("mixdevice.odin_datalogger2", "ch0", 1000, 1000)



    client.rpc_call("mixdevice.measureCurrentByOdin", "battery", "50ma")
    client.rpc_call("mixdevice.odin_datalogger", "ch1", 100, 1000)
    client.rpc_call("mixdevice.odin_datalogger2", "ch1", 100, 1000)
    client.rpc_call("mixdevice.odin_datalogger2", "ch1", 200, 1000)
    client.rpc_call("mixdevice.odin_datalogger2", "ch1", 300, 1000)
    client.rpc_call("mixdevice.odin_datalogger2", "ch1", 400, 1000)
    client.rpc_call("mixdevice.odin_datalogger2", "ch1", 500, 1000)
    client.rpc_call("mixdevice.odin_datalogger2", "ch1", 600, 1000)
    client.rpc_call("mixdevice.odin_datalogger2", "ch1", 700, 1000)
    client.rpc_call("mixdevice.odin_datalogger2", "ch1", 800, 1000)
    client.rpc_call("mixdevice.odin_datalogger2", "ch1", 900, 1000)
    client.rpc_call("mixdevice.odin_datalogger2", "ch1", 1000, 1000)








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