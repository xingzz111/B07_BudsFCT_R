from ctypes import c_int
from turtledemo.penrose import start
import time
from rtSque.tinyrpc import RPCClientWrapper
from rtSque.tinyrpc.publisher import NoOpPublisher
from rtSque.tinyrpc.protocols.jsonrpc import JSONRPCSuccessResponse, JSONRPCErrorResponse
from rtrpc.transports.transport import PRMClientTransport

# from sdb.debug import run_shell_with_timeout

TEST_ENGINE_PORT = 6100
bind_url = 'tcp://*'
transport = bind_url + ":" + str(TEST_ENGINE_PORT)
pub = NoOpPublisher()

client = RPCClientWrapper("tcp://127.0.0.1:6100", pub)


def call_rpc(client, cmd, *args, timeout=5000):
    res = client.rpc(cmd, *args, timeout=timeout)
    if isinstance(res, JSONRPCSuccessResponse):
        print(res.result)
        return True
    else:
        print("ERROR: {}".format(res.error))
    return False


def power_off(client):
    print("power_off")
    if not call_rpc(client, "common.reset"):
        return False
    if not call_rpc(client, "common.battery_output", 500, 0):
        return False
    return True


def battery_power_on(client, curr=500, volt=3700):

    if not call_rpc(client, "common.relay", "DUT_TP32_BAT_NTC_PULLDOWN_10K"):
            return False

    if not call_rpc(client, "common.relay", "ODIN_BATT_TO_DUT_TP30_V_BAT"):
            return False

    if not call_rpc(client, "common.battery_output", curr, volt):
        return False
    time.sleep(1)
    if not call_rpc(client, "common.relay", "LDO_PP3V0_EN"):
        return False
    if not call_rpc(client, "common.relay", "JLINK_TO_DUT"):
            return False

    if not call_rpc(client, "common.battery_measure", "volt", "5000mv"):
        return False
    time.sleep(0.5)
    if not call_rpc(client, "common.battery_measure", "curr", "500ma"):
        return False
    return True

def charge_power_on(client, curr=500, volt=5000):

    # if not call_rpc(client, "common.relay", "DUT_TP32_BAT_NTC_PULLDOWN_10K"):
    #         return False

    if not call_rpc(client, "common.relay", "ODIN_VCHG_TO_DUT_TP24_VBUS"):
            return False

    if not call_rpc(client, "common.charge_output", curr, volt):
        return False


    time.sleep(1)
    if not call_rpc(client, "common.relay", "LDO_PP3V0_EN"):
        return False
    if not call_rpc(client, "common.relay", "JLINK_TO_DUT"):
            return False

    if not call_rpc(client, "common.charger_measure", "volt"):
        return False
    if not call_rpc(client, "common.charger_measure", "curr"):
        return False

def power_cycle(client):
    power_off(client)
    battery_power_on(client, 500, 3700)

def uart_ftdi(client):
    if not call_rpc(client, "common.relay", "UART_FT232_TO_DUT_MCU_PP3V0"):
        return False

def uart_coreboard_l(client):
    if not call_rpc(client, "common.relay", "UART_CORE_BOARD_TO_DUT_TP53_HI_DATA_L_ONEWIRE_PP1V7"):
        return False


def uart_coreboard_r(client):
    if not call_rpc(client, "common.relay", "UART_CORE_BOARD_TO_DUT_TP54_HI_DATA_R_ONEWIRE_PP1V7"):
        return False


def button_test(client):
    if not call_rpc(client, "common.relay", "PULL_DOWN_DUT_TP45_BUTTON"):
        return False
    time.sleep(3)
    if not call_rpc(client, "common.relay", "PULL_DOWN_DUT_TP45_BUTTON", "DISCONNECT"):
        return False
    return True



#1
power_off(client)
# # call_rpc(client, "dut.open_uart")
# # # #
battery_power_on(client)
# time.sleep(50)
# charge_power_on(client)
# # # # # #
# # # # # # #2
# # # # # # power_cycle(client)
# uart_ftdi(client)
# button_test(client)
# call_rpc(client, "dut.close_uart")
# # #
# # # #
# call_rpc(client, "dut.detect_msh_mode")
# uart_coreboard_l(client)
# uart_coreboard_r(client)
# # #
# # #
# call_rpc(client, "dut.uart_slave_diags", "L_loop_back_test@success")
# call_rpc(client, "dut.led_control", "red", "close")
#
# call_rpc(client, "dut.write_bsn", "1234rde2312")
#
# call_rpc(client, "dut.read_bsn")
# call_rpc(client, "dut.send_read", "write_bsn 1231111111", "success")
# call_rpc(client, "dut.read_bsn")
    # print(mix_rpc_client.rpc_call("mixdevice.reset"))
    # # time.sleep(3)
    # print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_FT232_TO_DUT_FULL_DUPLEX"))
    # # print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_FT232_TO_DUT_HALF_DUPLEX"))

    # # print(mix_rpc_client.rpc_call("mixdevice.relay", "PULL_DOWN_10K_TO_DUT_CW_NTC"))
    # # print(mix_rpc_client.rpc_call("mixdevice.relay", "PULL_DOWN_470K_TO_DUT_AW_NTC"))

    # print(mix_rpc_client.rpc_call("mixdevice.relay", "ODIN_BATT_TO_DUT_TP10_1P05V"))
    # print(mix_rpc_client.rpc_call("mixdevice.battery_output", 500, 1200))

