# import re
# import threading
import time
import traceback
# from datetime import datetime
from rtrpc.rpc_client import RPCClientWrapper
from rtrpc.tcpClient import TcpClient
from rtrpc.protocols.jsonrpc import JSONRPCServerError, JSONRPCErrorResponse
# from sdb.sdb import client


class MixRpc(object):

    def __init__(self, ip, port, publisher=None):
        # transport = endpoint
        # rpctype = endpoint['type']
        # assert isinstance(transport, dict)
        # assert 'requester' in transport
        # _ip = re.findall("tcp://([0-9\.]+)", endpoint['requester'])[0]
        # _port = re.findall(":([0-9]+)", endpoint['requester'])[0]
        self.client = RPCClientWrapper(TcpClient(ip, int(port), publisher), publisher)
        self._rpc_proxy = self.client.get_proxy()
        self.publisher = publisher
        # self.lock = threading.Lock()

    def rpc_call(self, method, *args, **kwargs):
        """
        this function is the wrapper of rpc call
        :param method: string                   this is the function name of remote server
        :param args:   (string,int,float....)   it's the params of remote function
        :param kwargs: (string,int)             timeout or unit in this dict
        :return: result
        """

        try:
            # print('===================================debug================>')
            # print('method', method)
            # print('===================================debug================>')
            if kwargs and 'description' in kwargs.keys():
                kwargs.pop('description')
            if kwargs and 'timeout_ms' in kwargs.keys():
                kwargs.pop('timeout_ms')
            _strArg = ','.join([str(arg) for arg in args] + ['{}={}'.format(k, v) for k, v in kwargs.items()])
            # self.rpc_log('[rpc send]  {}({})'.format(method, _strArg))
            # print("rpc-call-args:" + str(args))
            # print("rpc-call-kwargs:" + str(kwargs))
            response = getattr(self._rpc_proxy, method)(*args, **kwargs)
            # print('response====', response)

            if response is None:
                raise JSONRPCServerError('Timed out waiting for response from test engine in test: ' + str(method))
            if isinstance(response, JSONRPCErrorResponse):
                raise response.to_exception_obj()

            # self.rpc_log('[rpc recv]  {}({}) <-<<  {} \n'.format(method, _strArg, str(response.result)))

        except JSONRPCServerError as e:
            print(traceback.format_exc())
            print('[rpc recv]  {}({}) <-<<  {} (Code:{}) \n'.format(method, _strArg, e.message, e.jsonrpc_error_code))
            raise e
        except Exception as e:
            print(traceback.format_exc())
            print(
                '[rpc recv]  {}({}) <-<<  {} \n'.format(method, _strArg, e))
            raise e
            # response.error

        result = response.result

        return result

    def get_transport_timeout(self):
        return self._rpc_proxy.transport.timeout_ms

    def set_transport_timeout(self, timeout):
        self._rpc_proxy.transport.timeout_ms = timeout

def odin_test(client, net, volt, current,  _type):
    print("****************{}**************************".format(net))
    print(client.rpc_call("mixdevice.relay", net))
    if _type == "charger":
        # print(client.rpc_call("psu.enable_sense", "charger"))
        # print(client.rpc_call("psu.set_current_limit", "charger", current))
        # print(client.rpc_call("psu.enable_charger_output", volt))
        # print(client.rpc_call("psu.voltage_measure", "charger"))
        # print(client.rpc_call("psu.current_measure", "charger"))

        print(client.rpc_call("mixdevice.charge_output", current, volt))
        print(client.rpc_call("mixdevice.charge_output", current, volt))
        print(client.rpc_call("mixdevice.psu_measure", "volt", "charger"))
        print(client.rpc_call("mixdevice.psu_measure", "curr", "charger"))



    else:
        # print(client.rpc_call("psu.set_current_limit", "battery", current))
        # print(client.rpc_call("psu.enable_battery_output", volt, True))
        # print(client.rpc_call("psu.set_measure_path", "battery", "ch0", "5000mv"))
        # print(client.rpc_call("psu.voltage_measure", "battery"))
        # print(client.rpc_call("psu.set_measure_path", "battery", "ch1", "500ma"))
        # print(client.rpc_call("psu.current_measure", "battery"))

        print(client.rpc_call("mixdevice.battery_output", current, volt))
        print(client.rpc_call("mixdevice.psu_measure", "volt", "battery", "5000mv"))
        print(client.rpc_call("mixdevice.psu_measure", "curr", "battery", "500ma"))



def dmm_measure(client, net, socpe="7000mv"):
    print("****************{}**************************".format(net))
    # print(client.rpc_call("mixdevice.relay", net))
    # # print(client.rpc_call("dmm.set_measure_path", "ch0", socpe))
    # # print(client.rpc_call("dmm.measure"))
    # print(client.rpc_call("dmm.set_measure_path", "ch1", socpe))
    # print(client.rpc_call("dmm.voltage_measure_mv"))
    # time.sleep(1)

    print(client.rpc_call("mixdevice.relay", net))
    print(client.rpc_call("mixdevice.dmm_measure", socpe))
    time.sleep(1)

def test1():
    mix_rpc_client = MixRpc("169.254.1.32", 7801)
    print(mix_rpc_client.rpc_call("mixdevice.reset"))
    print(mix_rpc_client.rpc_call("mixdevice.relay", "JLINK_TO_DUT"))
    time.sleep(3)
    print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_FT232_TO_DUT_FULL_DUPLEX"))
    # print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_FT232_TO_DUT_HALF_DUPLEX"))

    # print(mix_rpc_client.rpc_call("mixdevice.relay", "PULL_DOWN_10K_TO_DUT_CW_NTC"))
    # print(mix_rpc_client.rpc_call("mixdevice.relay", "PULL_DOWN_470K_TO_DUT_AW_NTC"))

    # print(mix_rpc_client.rpc_call("mixdevice.relay", "ODIN_BATT_TO_DUT_TP22_BAT_P"))
    print(mix_rpc_client.rpc_call("mixdevice.relay", "ODIN_BATT_TO_DUT_TP10_1P05V"))
    print(mix_rpc_client.rpc_call("mixdevice.battery_output", 500, 1200))

    time.sleep(1)
    print(mix_rpc_client.rpc_call("mixdevice.psu_measure", "volt", "battery", "5000mv"))
    print(mix_rpc_client.rpc_call("mixdevice.psu_measure", "curr", "battery", "500ma"))

    input("pls wating...")
    print(mix_rpc_client.rpc_call("mixdevice.relay", "ODIN_VCHG_TO_DUT_TP40_POGO5V"))
    print(mix_rpc_client.rpc_call("mixdevice.charge_output", 600, 5000))

    time.sleep(3)
    print(mix_rpc_client.rpc_call("mixdevice.psu_measure", "volt", "charger", "5000mv"))
    print(mix_rpc_client.rpc_call("mixdevice.psu_measure", "curr", "charger", "500ma"))

    # print(mix_rpc_client.rpc_call("mixdevice.reset"))



def power_2700():
    mix_rpc_client = MixRpc("169.254.1.32", 7801)
    print(mix_rpc_client.rpc_call("mixdevice.reset"))
    # print(mix_rpc_client.rpc_call("mixdevice.relay", "JLINK_TO_DUT"))

    print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_FT232_TO_DUT_FULL_DUPLEX"))
    # print(mix_rpc_

    # print(mix_rpc_client.rpc_call("mixdevice.relay", "PULL_DOWN_10K_TO_DUT_CW_NTC"))
    # print(mix_rpc_client.rpc_call("mixdevice.relay", "PULL_DOWN_470K_TO_DUT_AW_NTC"))

    input("pls wating...")


    print(mix_rpc_client.rpc_call("mixdevice.relay", "ODIN_VCHG_TO_DUT_TP40_POGO5V"))
    print(mix_rpc_client.rpc_call("mixdevice.charge_output", 600, 5000))

    time.sleep(3)
    print(mix_rpc_client.rpc_call("mixdevice.psu_measure", "volt", "charger", "5000mv"))
    print(mix_rpc_client.rpc_call("mixdevice.psu_measure", "curr", "charger", "500ma"))

    # print(mix_rpc_client.rpc_call("mixdevice.reset"))


def test2():
    mix_rpc_client = MixRpc("169.254.1.32", 7801)
    print(mix_rpc_client.rpc_call("mixdevice.reset"))

    # print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_FT232_TO_DUT_FULL_DUPLEX"))
    # print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_COREBOARD_TO_DUT"))
    # print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_FT232_TO_DUT_HALF_DUPLEX"))

    # print(mix_rpc_client.rpc_call("mixdevice.relay", "PULL_DOWN_10K_TO_DUT_CW_NTC"))
    # print(mix_rpc_client.rpc_call("mixdevice.relay", "PULL_DOWN_470K_TO_DUT_AW_NTC"))

    # print(mix_rpc_client.rpc_call("mixdevice.relay", "ODIN_BATT_TO_DUT_TP22_BAT_P"))
    # print(mix_rpc_client.rpc_call("mixdevice.battery_output", 500, 3700))

    print(mix_rpc_client.rpc_call("mixdevice.relay", "ODIN_VCHG_TO_DUT_TP40_POGO5V"))
    print(mix_rpc_client.rpc_call("mixdevice.charge_output", 600, 5000))
    time.sleep(3)
    print(mix_rpc_client.rpc_call("mixdevice.psu_measure", "volt", "charger", "5000mv"))
    print(mix_rpc_client.rpc_call("mixdevice.psu_measure", "curr", "charger", "500ma"))

    print(mix_rpc_client.rpc_call("mixdevice.reset"))

    # print(mix_rpc_client.rpc_call("mixdevice.switch_mode", True))
    # time.sleep(1)
    # # print(mix_rpc_client.rpc_call("com.read_until", ":::)))"))
    # info = mix_rpc_client.rpc_call("com.read_by_byte")
    # print(info)
    # info_str = ''.join(chr(x) for x in info)
    # print(info_str)
    # time.sleep(1)


    # info = mix_rpc_client.rpc_call("com.read_by_byte")
    # print("readBuff",info)
    #
    # info = mix_rpc_client.rpc_call("com.read_by_byte")
    # print("readBuff",info)
    #
    # info = mix_rpc_client.rpc_call("com.read_by_byte")
    # print("readBuff",info)
    #
    # print(mix_rpc_client.rpc_call("com.write", "[get_2700_version,]\n"))
    # time.sleep(1)
    # info = mix_rpc_client.rpc_call("com.read_by_byte")
    # print(info)
    # info_str = ''.join(chr(x) for x in info)
    # print(info_str)
    #
    # print(mix_rpc_client.rpc_call("com.write", "[get_2700_version,]\n"))
    # time.sleep(1)
    # info = mix_rpc_client.rpc_call("com.read_by_byte")
    # print(info)
    # info_str = ''.join(chr(x) for x in info)
    # print(info_str)
    #
    #
    # print(mix_rpc_client.rpc_call("com.write", "[get_2700_version,]\n"))
    # time.sleep(1)
    # info = mix_rpc_client.rpc_call("com.read_by_byte")
    # print(info)
    # info_str = ''.join(chr(x) for x in info)
    # print(info_str)



def test3():
    mix_rpc_client = MixRpc("169.254.1.32", 7801)
    print(mix_rpc_client.rpc_call("mixdevice.reset"))
    print(mix_rpc_client.rpc_call("mixdevice.switch_mode", True))
    time.sleep(1)
    # print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_FT232_TO_DUT_FULL_DUPLEX"))
    print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_COREBOARD_TO_DUT"))

    # print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_FT232_TO_DUT_HALF_DUPLEX"))

    # print(mix_rpc_client.rpc_call("mixdevice.relay", "PULL_DOWN_10K_TO_DUT_CW_NTC"))
    # print(mix_rpc_client.rpc_call("mixdevice.relay", "PULL_DOWN_470K_TO_DUT_AW_NTC"))

    # print(mix_rpc_client.rpc_call("mixdevice.relay", "ODIN_BATT_TO_DUT_TP22_BAT_P"))
    # print(mix_rpc_client.rpc_call("mixdevice.battery_output", 500, 3700))

    print(mix_rpc_client.rpc_call("mixdevice.relay", "ODIN_VCHG_TO_DUT_TP40_POGO5V"))
    time.sleep(1)
    print(mix_rpc_client.rpc_call("mixdevice.charge_output", 500, 5000))
    time.sleep(10)
    print(mix_rpc_client.rpc_call("mixdevice.psu_measure", "volt", "charger", "5000mv"))
    print(mix_rpc_client.rpc_call("mixdevice.psu_measure", "curr", "charger", "500ma"))



    # print(mix_rpc_client.rpc_call("com.read_until", "Mode fog: 0"))

    info = mix_rpc_client.rpc_call("com.read_by_byte")
    # info = mix_rpc_client.rpc_call("com.read_until","fog: 0", 5)
    # print(info)
    info_str = ''.join(chr(x) for x in info)
    print(info_str)
    time.sleep(1)

    # print(mix_rpc_client.rpc_call("com.write", "\r\n[2700_status,]\r\n"))
    # # info = mix_rpc_client.rpc_call("com.read_until", "fog: 0", 5)
    # time.sleep(5)
    # info = mix_rpc_client.rpc_call("com.read_by_byte")
    # print("readBuff",info)
    # info_str = ''.join(chr(x) for x in info)
    # print(info_str)


    # while True:
    #     info = mix_rpc_client.rpc_call("com.read_by_byte")
    #     # info = mix_rpc_client.rpc_call("com.read_until","fog: 0", 5)
    #     print(info)
    #     info_str = ''.join(chr(x) for x in info)
    #     print(info_str)
    #     time.sleep(5)



    # print(mix_rpc_client.rpc_call("com.write", "[get_2700_version,]\r"))
    # # info = mix_rpc_client.rpc_call("com.read_until", "fog: 0", 5)
    # time.sleep(5)
    # info = mix_rpc_client.rpc_call("com.read_by_byte")
    # print("readBuff", info)
    # info_str = ''.join(chr(x) for x in info)
    # print(info_str)

    while True:

        print(mix_rpc_client.rpc_call("com.write", "[get_8300_version,]"))
        # print(mix_rpc_client.rpc_call("com.write", "[get_2700_version,]"))
        # print(mix_rpc_client.rpc_call("com.write", "\r\n"))

        time.sleep(5)

        info = mix_rpc_client.rpc_call("com.read_by_byte")
        print("readBuff", info)
        info_str = ''.join(chr(x) for x in info)
        print(info_str)
def cal8300():
    mix_rpc_client = MixRpc("169.254.1.32", 7801)
    print(mix_rpc_client.rpc_call("mixdevice.reset"))
    print(mix_rpc_client.rpc_call("mixdevice.switch_mode", True))
    time.sleep(1)
    # print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_FT232_TO_DUT_FULL_DUPLEX"))
    print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_COREBOARD_TO_DUT"))

    # print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_FT232_TO_DUT_HALF_DUPLEX"))

    # print(mix_rpc_client.rpc_call("mixdevice.relay", "PULL_DOWN_10K_TO_DUT_CW_NTC"))
    # print(mix_rpc_client.rpc_call("mixdevice.relay", "PULL_DOWN_470K_TO_DUT_AW_NTC"))

    # print(mix_rpc_client.rpc_call("mixdevice.relay", "ODIN_BATT_TO_DUT_TP22_BAT_P"))
    # print(mix_rpc_client.rpc_call("mixdevice.battery_output", 500, 3700))

    print(mix_rpc_client.rpc_call("mixdevice.relay", "ODIN_VCHG_TO_DUT_TP40_POGO5V"))
    time.sleep(1)
    print(mix_rpc_client.rpc_call("mixdevice.charge_output", 500, 5000))
    time.sleep(5)
    print(mix_rpc_client.rpc_call("mixdevice.psu_measure", "volt", "charger", "5000mv"))
    print(mix_rpc_client.rpc_call("mixdevice.psu_measure", "curr", "charger", "500ma"))


    info = mix_rpc_client.rpc_call("com.read_by_byte")
    # info = mix_rpc_client.rpc_call("com.read_until","fog: 0", 5)
    # print(info)
    info_str = ''.join(chr(x) for x in info)
    print(info_str)
    time.sleep(1)
    for i in range(1):
        print(mix_rpc_client.rpc_call("com.write", "[start_trim,]"))
        time.sleep(5)
        info = mix_rpc_client.rpc_call("com.read_by_byte")
        print("readBuff", info)
        info_str = ''.join(chr(x) for x in info)
        print(info_str)

    time.sleep(50)
    # input("[8300_reset,]")
    for i in range(3):
        print(mix_rpc_client.rpc_call("com.write", "[8300_reset,]"))
        time.sleep(5)
        info = mix_rpc_client.rpc_call("com.read_by_byte")
        print("readBuff", info)
        info_str = ''.join(chr(x) for x in info)
        print(info_str)
        if "Rst8300" in info_str:
            break

    # input("[stop_trim,]")


    for i in range(3):
        print(mix_rpc_client.rpc_call("com.write", "[stop_trim,]"))
        time.sleep(5)
        info = mix_rpc_client.rpc_call("com.read_by_byte")
        print("readBuff", info)
        info_str = ''.join(chr(x) for x in info)
        print(info_str)
        if "Rst8300" in info_str:
            break

    # input("[switch_app,]")
    for i in range(3):
        print(mix_rpc_client.rpc_call("com.write", "[switch_app,]"))
        time.sleep(5)
        info = mix_rpc_client.rpc_call("com.read_by_byte")
        print("readBuff", info)
        info_str = ''.join(chr(x) for x in info)
        print(info_str)


    # input("[get_8300_version,]")
    for i in range(3):
        print(mix_rpc_client.rpc_call("com.write", "[get_8300_version,]"))
        time.sleep(5)
        info = mix_rpc_client.rpc_call("com.read_by_byte")
        print("readBuff", info)
        info_str = ''.join(chr(x) for x in info)
        print(info_str)



def power_off():
    mix_rpc_client = MixRpc("169.254.1.32", 7801)
    print(mix_rpc_client.rpc_call("mixdevice.charge_output", 500, 0))
    print(mix_rpc_client.rpc_call("mixdevice.reset"))
    time.sleep(0.5)

    # print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_FT232_TO_DUT_HALF_DUPLEX"))
    #
    # print(mix_rpc_client.rpc_call("mixdevice.relay", "ODIN_VCHG_TO_DUT_TP40_POGO5V"))
    # time.sleep(1)
    # print(mix_rpc_client.rpc_call("mixdevice.charge_output", 500, 5000))
    # time.sleep(6)
    # print(mix_rpc_client.rpc_call("mixdevice.psu_measure", "volt", "charger", "5000mv"))
    # print(mix_rpc_client.rpc_call("mixdevice.psu_measure", "curr", "charger", "500ma"))


if __name__ == "__main__":
    power_off()
