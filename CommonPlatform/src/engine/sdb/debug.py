import os
import time
import traceback


from rtrpc.rpc_client import RPCClientWrapper
from rtrpc.tcpClient import TcpClient
from rtrpc.protocols.jsonrpc import JSONRPCServerError, JSONRPCErrorResponse

from rtlib.runShell import runShell

import subprocess
from threading import Timer


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


def run_shell_with_timeout(cmd, timeout=3):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timer = Timer(timeout, lambda process: process.kill(), [p])
    try:
        timer.start()
        stdout, stderr = p.communicate()
        print(stdout)
        return_code = p.returncode
        return return_code, stdout, stderr
    finally:
        timer.cancel()

# rtSerial = SerialPort("COM13",9600)
# rtSerial.send_read("[get_2700_version,]")

def power_reset():
    mix_rpc_client = MixRpc("169.254.1.32", 7801)
    print(mix_rpc_client.rpc_call("mixdevice.reset"))
    time.sleep(3)


def power_on_5v():
    mix_rpc_client = MixRpc("169.254.1.32", 7801)

    print(mix_rpc_client.rpc_call("mixdevice.relay", "ODIN_VCHG_TO_DUT_POGO_PIN_VCC"))
    print(mix_rpc_client.rpc_call("mixdevice.charge_output", 600, 5000))
    time.sleep(6)
    print(mix_rpc_client.rpc_call("mixdevice.psu_measure", "volt", "charger", "5000mv"))
    print(mix_rpc_client.rpc_call("mixdevice.psu_measure", "curr", "charger", "500ma"))

    # print(mix_rpc_client.rpc_call("mixdevice.reset"))


def faul_uart():
    mix_rpc_client = MixRpc("169.254.1.32", 7801)
    print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_FT232_TO_DUT_FULL_DUPLEX"))

def power_on_1p2v():
    mix_rpc_client = MixRpc("169.254.1.32", 7801)

    print(mix_rpc_client.rpc_call("mixdevice.reset"))
    # time.sleep(3)
    print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_FT232_TO_DUT_FULL_DUPLEX"))
    # print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_FT232_TO_DUT_HALF_DUPLEX"))

    # print(mix_rpc_client.rpc_call("mixdevice.relay", "PULL_DOWN_10K_TO_DUT_CW_NTC"))
    # print(mix_rpc_client.rpc_call("mixdevice.relay", "PULL_DOWN_470K_TO_DUT_AW_NTC"))

    print(mix_rpc_client.rpc_call("mixdevice.relay", "ODIN_BATT_TO_DUT_TP10_1P05V"))
    print(mix_rpc_client.rpc_call("mixdevice.battery_output", 500, 1200))


def restore_2700():
    bt_address = "D0141120500E"
    # tool_pth = "C:\\Users\\CTOS\\Desktop\\burn_2700_v1\\burn_2700.exe"
    # port = 13
    # app_bin = "C:\\Users\\CTOS\\Desktop\\burn_2700_v1\\orkatest.bin"
    # ota_bin = ""
    bt_name = "Orka BTE BT"
    ble_name = "Orka BTE BT LE"
    mix_rpc_client = MixRpc("169.254.1.32", 7801)

    print(mix_rpc_client.rpc_call("mixdevice.reset"))
    time.sleep(3)
    print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_FT232_TO_DUT_FULL_DUPLEX"))
    time.sleep(3)
    # cmd = f"{tool_pth} --port 13 --app-file {app_bin} --bt-address 123321123122 --ble-address 321123321122 --bt-name zhang121 --ble-name zhang3212 --timeout 20"
    # cmd = "cd C:\\Users\\CTOS\\Desktop\\burn_2700_v1;C:\\Users\\CTOS\\Desktop\\burn_2700_v1\\burn_2700.exe --port 12 --app-file C:\\Users\\CTOS\Desktop\\burn_2700_v1\\orkatest.bin --bt-address D0141120500E --ble-address D0141120500E --bt-name \"Orka BTE BT\" --ble-name \"Orka BTE LE\" --timeout 20"
    # cmd = """cd C:\\Users\\CTOS\\Desktop\\burn_2700_v1 && C:\\Users\\CTOS\\Desktop\\burn_2700_v1\\burn_2700.exe --port 12 --app-file C:\\Users\\CTOS\\Desktop\\burn_2700_v1\\orkatest.bin --bt-address D0141120500E --ble-address D0141120500E --bt-name "Orka BTE BT" --ble-name "Orka BTE LE" --timeout 20"""
    cmd = "C:/Users/CTOS/Desktop/burn_2700_v1/main.bat"
    with open("restore_2700.bat","w") as f:
        f.write("echo offf\n")
        f.write("cd /d C:\\Users\\CTOS\\Desktop\\burn_2700_v1")
        f.write(f"{cmd}\n")
    try:
        print(cmd)
        run_cmd = ['cmd.exe','\C','restore_2700.bat']
        result, err = runShell.run_shell_with_timeout_power_5v(cmd, mix_rpc_client, 120)
        time.sleep(0.5)
        print(result)
    except Exception as e:
        return "--FAIL--"

def restore_2700_1():
    bt_address = "D0141120500E"
    # tool_pth = "C:\\Users\\CTOS\\Desktop\\burn_2700_v1\\burn_2700.exe"
    # port = 13
    # app_bin = "C:\\Users\\CTOS\\Desktop\\burn_2700_v1\\orkatest.bin"
    # ota_bin = ""
    bt_name = "Orka BTE BT"
    ble_name = "Orka BTE BT LE"
    mix_rpc_client = MixRpc("169.254.1.32", 7801)

    print(mix_rpc_client.rpc_call("mixdevice.reset"))
    print(mix_rpc_client.rpc_call("mixdevice.charge_output", 600, 0))
    time.sleep(0.5)
    print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_FT232_TO_DUT_FULL_DUPLEX"))
    time.sleep(0.5)
    cmd_list =[]
    # cmd = f"{tool_pth} --port 13 --app-file {app_bin} --bt-address 123321123122 --ble-address 321123321122 --bt-name zhang121 --ble-name zhang3212 --timeout 20"
    # cmd = "cd C:\\Users\\CTOS\\Desktop\\burn_2700_v1;C:\\Users\\CTOS\\Desktop\\burn_2700_v1\\burn_2700.exe --port 12 --app-file C:\\Users\\CTOS\Desktop\\burn_2700_v1\\orkatest.bin --bt-address D0141120500E --ble-address D0141120500E --bt-name \"Orka BTE BT\" --ble-name \"Orka BTE LE\" --timeout 20"
    cmd1 = "C:/Users/CTOS/Desktop/burn_2700_v1/burn_source.exe burn kill"
    cmd2 = "C:/Users/CTOS/Desktop/burn_2700_v1/burn_source.exe burn run"
    cmd3 = "C:/Users/CTOS/Desktop/burn_2700_v1/burn_source.exe burn --port 12 --app-bin C:/Users/CTOS/Desktop/burn_2700_v1/evt_encrypt_1.1.0.1.bin --ota-bin C:/Users/CTOS/Desktop/burn_2700_v1/ota_boot_2700_20211216_5fca0c3e.bin --bt-address D0141120500E --ble-address D0141120500E --bt-name \"Orka BTE BT\" --ble-name \"Orka BTE LE\"  --erase --auto-calib"
    cmd4 = "C:/Users/CTOS/Desktop/burn_2700_v1/burn_source.exe burn kill"
    cmd_list.append(cmd1)
    cmd_list.append(cmd2)
    cmd_list.append(cmd3)
    cmd_list.append(cmd4)
    state = False
    for cmd in cmd_list:
        try:
            return_code, stdout, stderr = runShell.run_shell_with_timeout_power_5v(cmd, mix_rpc_client,120)
            if return_code == 0 and "Burn Success" in stdout.decode():
                state = True
                print("OK")
        except Exception as e:
            return "--FAIL--"
    return state

def restore_8300():
    # tool_pth = ""
    # device = ""
    # jink_config_path = "download.jlink"
    # conn_cmd = "\"C:\\Program Files\\SEGGER\\JLink\\JLink.exe\" -autoconnect 1 -device EZAIRO8300_SPI_FLASH_W25Q16JV -if swd -speed 4000"
    cmd = "\"C:\\Program Files\\SEGGER\\JLink\\JLink.exe\" -autoconnect 1 -device EZAIRO8300_SPI_FLASH_W25Q16JV -if swd -speed 4000   -commandfile C:\\Users\\CTOS\Desktop\\JlinkTools\config.txt"
    try:
        mix_rpc_client = MixRpc("169.254.1.32", 7801)
        print(mix_rpc_client.rpc_call("mixdevice.relay", "JLINK_TO_DUT"))
        time.sleep(3)
        # power_on_5v()
        # result, err = runShell.run_shell_with_timeout_power_5v_for_8300(cmd, mix_rpc_client, 600)
        for i in range(3):
            connect_flag, result, err = runShell.run_shell_with_timeout_power_5v_for_8300(cmd, mix_rpc_client,600)
            time.sleep(0.5)
            if connect_flag:
                break
        print("error",err)
        # with open("C:\\Users\\CTOS\\Desktop\\log.txt.txt","a+") as f:
        #     f.write(result.decode())
        print("result",result)
    except Exception as e:
        print(str(e))


def restore_8300_doe():
    # tool_pth = ""
    # device = ""
    # jink_config_path = "download.jlink"
    conn_cmd = "\"C:\\Program Files\\SEGGER\\JLink\\JLink.exe\" -autoconnect 1 -device EZAIRO8300_SPI_FLASH_W25Q16JV -if swd -speed 4000"
    cmd = "\"C:\\Program Files\\SEGGER\\JLink\\JLink.exe\" -autoconnect 1 -device EZAIRO8300_SPI_FLASH_W25Q16JV -if swd -speed 4000   -commandfile C:\\Users\\CTOS\Desktop\\JlinkTools\config.txt"
    # cmd_list = []
    try:
        mix_rpc_client = MixRpc("169.254.1.32", 7801)
        print(mix_rpc_client.rpc_call("mixdevice.relay", "JLINK_TO_DUT"))
        time.sleep(3)
        # power_on_5v()
        # result, err = runShell.run_shell_with_timeout_power_5v_for_8300(cmd, mix_rpc_client, 600)
        for i in range(3):
            # print("run-----")
            # return_code, stdout, stderr = runShell.run_shell_with_timeout_for_8300_connect(conn_cmd,10)
            # print(stdout.decode())
            # if return_code:
            #     break
            # os.system(conn_cmd)
            out = os.popen(conn_cmd)
            print("-----")
            # print(out.readlines())
        time.sleep(3)
        mix_rpc_client.rpc_call("mixdevice.relay", "ODIN_VCHG_TO_DUT_POGO_PIN_VCC")
        mix_rpc_client.rpc_call("mixdevice.charge_output", 500, 5000)
        time.sleep(1)
        print("--- power on 5v")
        print("run")
        code, result, err = runShell.run_shell_with_timeout_power_5v_for_8300(cmd, mix_rpc_client,600)
        time.sleep(0.5)
        print("error",err)
        # with open("C:\\Users\\CTOS\\Desktop\\log.txt.txt","a+") as f:
        #     f.write(result.decode())
        print("result",result)
    except Exception as e:
        print(str(e))

def restore_8300_v1():
    # tool_pth = ""
    # device = ""
    # jink_config_path = "download.jlink"
    connect_cmd = "\"C:\\Program Files\\SEGGER\\JLink\\JLink.exe\" -autoconnect 1 -device EZAIRO8300_SPI_FLASH_W25Q16JV -if swd -speed 4000"
    cmd = "\"C:\\Program Files\\SEGGER\\JLink\\JLink.exe\" -autoconnect 1 -device EZAIRO8300_SPI_FLASH_W25Q16JV -if swd -speed 4000   -commandfile C:\\Users\\CTOS\Desktop\\JlinkTools\config.txt"
    try:
        # print("1111")
        # # result, err ,_ = run_shell_with_timeout(connect_cmd,5)
        # print("1111")
        # time.sleep(0.5)
        # print("error",err)
        # print("result",result)
        # power_on_5v()
        result, err, _ = run_shell_with_timeout(cmd, 500)
        print("error", err)
        print("result", result.decode())
    except Exception as e:
        print(str(e))

if __name__ == "__main__":
    # restore 2700
    power_reset()
    restore_2700_1()
    # power_reset()
    # faul_uart()
    # power_on_5v()
    # restore_2700()

    # power_on_1p2v()
    # time.sleep(3)
    # restore_8300_doe()
    # test1()







