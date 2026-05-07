from ctypes import c_int
from turtledemo.penrose import start

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


#     print(mix_rpc_client.rpc_call("mixdevice.reset"))
#     # time.sleep(3)
#     print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_FT232_TO_DUT_FULL_DUPLEX"))
#     # print(mix_rpc_client.rpc_call("mixdevice.relay", "UART_FT232_TO_DUT_HALF_DUPLEX"))

#     # print(mix_rpc_client.rpc_call("mixdevice.relay", "PULL_DOWN_10K_TO_DUT_CW_NTC"))
#     # print(mix_rpc_client.rpc_call("mixdevice.relay", "PULL_DOWN_470K_TO_DUT_AW_NTC"))

#     print(mix_rpc_client.rpc_call("mixdevice.relay", "ODIN_BATT_TO_DUT_TP10_1P05V"))
#     print(mix_rpc_client.rpc_call("mixdevice.battery_output", 500, 1200))


# def power_on_1v2(client):
#     print("power_on_1v2")
#     if not call_rpc(client, "common.reset"):
#         return False
#     if not call_rpc(client, "common.relay", "JLINK_TO_DUT"):
#         return False
#     if not call_rpc(client, "common.relay", "UART_FT232_TO_DUT_HALF_DUPLEX"):
#         return False
#     if not call_rpc(client, "common.relay", "ODIN_BATT_TO_DUT_TP10_1P05V"):
#         return False
#     if not call_rpc(client, "common.battery_output", 500, 1200):
#         return False
#     return True

# def power_off(client):
#     print("power_off")
#     if not call_rpc(client, "common.battery_output", 0, 0):
#         return False

#     return True

# def power_for_jlink(client):

#     if not call_rpc(client, "common.relay", "ODIN_BATT_TO_DUT_TP10_1P05V"):
#         return False
#     if not call_rpc(client, "common.battery_output", 500, 1200):
#         return False
#     time.sleep(1)
#     if not call_rpc(client, "common.relay", "JLINK_TO_DUT"):
#         return False
#     if not call_rpc(client, "common.relay", "PP1V7_LDO_EN"):
#         return False
#     time.sleep(1)
#     if not call_rpc(client, "common.battery_measure", "volt", "5000mv"):
#         return False
#     if not call_rpc(client, "common.battery_measure", "curr", "50ma"):
#         return False
#     if not call_rpc(client, "common.relay", "ODIN_VCHG_TO_DUT_TP40_POGO5V"):
#         return False
#     if not call_rpc(client, "common.charge_output", 500, 5000):
#         return False
#     time.sleep(6)
#     return True



# def fwdl_8300(client):
#     print("fwdl_8300")
#     if not call_rpc(client, "common.restore_8300", timeout=600000):
#         return False
#     return True

# def fwdl_2700(client):
#     print("fwdl_2700")
#     power_off(client)

#     if not call_rpc(client, "common.close_uart"):
#         return False
#     if not call_rpc(client, "common.relay", "UART_FT232_TO_DUT_FULL_DUPLEX"):
#         return False
#     if not call_rpc(client, "common.restore_2700", "D01411205024", timeout=600000):
#         return False
#     return True

# def one_wire_uart(client, double=False):
#     print("one_wire_uart")
#     power_off(client)
#     time.sleep(1)
#     # if not call_rpc(client, "common.open_uart"):
#     #     return False
#     # if not call_rpc(client, "common.relay","UART_FT232_RESET"):
#     #     return False
#     # time.sleep(0.5)
#     # if not call_rpc(client, "common.relay","UART_FT232_RESET", "DISCONNECT"):
#     #     return False
#     # time.sleep(0.5)
#     # if not call_rpc(client, "common.switch_bit1"):
#     #     return False
#     if double:
#         if not call_rpc(client, "common.relay", "UART_FT232_TO_DUT_FULL_DUPLEX"):
#             return False
#         # if not call_rpc(client, "common.relay", "RELAY_RESERVE1"):
#         #     return False
#     else:
#         if not call_rpc(client, "common.relay", "UART_FT232_TO_DUT_HALF_DUPLEX"):
#             return False
#         if not call_rpc(client, "common.relay", "RELAY_RESERVE1"):
#             return False


#         # if not call_rpc(client, "common.switch_bit1"):
#         #     return False



#     # output_sg_wave
#     if not call_rpc(client, "common.relay", "AWG811_TO_DUT_TP15_CAL_SQUWAV"):
#         return False
#     if not call_rpc(client, "common.relay", "ODIN_BATT_TO_DUT_TP10_1P05V"):
#         return False
#     # print(mix_rpc_client.rpc_call("mixdevice.battery_output", 500, 3700))
#     if not call_rpc(client, "common.battery_output", 500, 1200):
#         return False
#     if not call_rpc(client, "common.relay", "ODIN_VCHG_TO_DUT_TP40_POGO5V"):
#         return False
#     time.sleep(0.5)
#     if not call_rpc(client, "common.charge_output", 500, 5000):
#         return False

#     # time.sleep(10)
#     # if not call_rpc(client, "common.charger_measure", "volt"):
#     #     return False
#     # if not call_rpc(client, "common.charger_measure", "curr"):
#     #     return False
#     return True


# def one_wire_uart_coreboard(client, double=False):
#     print("one_wire_uart")
#     power_off(client)
#     time.sleep(1)
#     if double:
#         if not call_rpc(client, "common.relay", "UART_FT232_TO_DUT_FULL_DUPLEX"):
#             return False
#         # if not call_rpc(client, "common.relay", "RELAY_RESERVE1"):
#         #     return False
#     else:
#         if not call_rpc(client, "common.relay", "UART_COREBOARD_TO_DUT"):
#             return False
#         # if not call_rpc(client, "common.switch_bit1"):
#         #     return False

#     # output_sg_wave
#     if not call_rpc(client, "common.relay", "AWG811_TO_DUT_TP15_CAL_SQUWAV"):
#         return False
#     if not call_rpc(client, "common.relay", "ODIN_BATT_TO_DUT_TP10_1P05V"):
#         return False
#     # print(mix_rpc_client.rpc_call("mixdevice.battery_output", 500, 3700))
#     if not call_rpc(client, "common.battery_output", 500, 1200):
#         return False
#     if not call_rpc(client, "common.relay", "ODIN_VCHG_TO_DUT_TP40_POGO5V"):
#         return False
#     time.sleep(0.5)
#     if not call_rpc(client, "common.charge_output", 500, 5000):
#         return False

#     # time.sleep(10)
#     # if not call_rpc(client, "common.charger_measure", "volt"):
#     #     return False
#     # if not call_rpc(client, "common.charger_measure", "curr"):
#     #     return False
#     return True



# import time
# def cal8300_power(client):
#     if not call_rpc(client,"common.reset"):
#         return False
#     time.sleep(1)

#     if not call_rpc(client,"common.relay", "UART_FT232_TO_DUT_HALF_DUPLEX"):
#         return False
#     # if not call_rpc(client, "common.switch_bit1"):
#     #     return False
#     if not call_rpc(client,"common.relay", "AWG811_TO_DUT_TP15_CAL_SQUWAV"):
#         return False
#     if not call_rpc(client,"common.relay", "ODIN_BATT_TO_DUT_TP10_1P05V"):
#         return False
#     # print(mix_rpc_client.rpc_call("mixdevice.battery_output", 500, 3700))
#     if not call_rpc(client,"common.battery_output", 500, 1200):
#         return False
#     if not call_rpc(client,"common.relay", "ODIN_VCHG_TO_DUT_TP40_POGO5V"):
#         return False
#     time.sleep(1)
#     if not call_rpc(client,"common.charge_output", 500, 5000):
#         return False
#     time.sleep(5)
#     if not call_rpc(client,"common.charger_measure", "volt"):
#         return False
#     if not call_rpc(client,"common.charger_measure", "curr"):
#         return False
#     return True

# def check_connect(retry_times=1):
#     # input_data = '''connect\r\n
#     #     EZAIRO8300_SPI_FLASH_W25Q16JV\r\n
#     #     s\r\n
#     #     \r\n
#     #     q\r\n
#     #     '''
#     input_data = '''q\r\n
#     '''
#     conn_cmd = ["C:/Program Files/SEGGER/JLink/JLink.exe","-device", "EZAIRO8300_SPI_FLASH_W25Q16JV", "-if", "swd", "-speed", "1000", "-autoconnect", "1"]

#     for i in range(retry_times):
#         p = subprocess.Popen(conn_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#         stdout,stderr = p.communicate(input=input_data.encode())
#         if p.returncode == 0:
#             print("return code: ", p.returncode)
#             print("Standard Output:")
#             print(stdout)
#             if "Cannot connect to target" not in stdout.decode() and "Cortex-M3 identified" in stdout.decode():
#                 return True
#         else:
#             print("Standard Error:")
#             print(stderr)
#             continue
#     return False


# def dmm_measure(client):
#     print("dmm measure DMM_MUX_DUT_TP28_VCODEC_DC")
#     call_rpc(client, "common.dmm_measure_voltage", "DMM_MUX_DUT_TP28_VCODEC_DC")
#     # if not call_rpc(client, "common.dmm_measure_voltage","DMM_MUX_DUT_TP28_VCODEC_DC"):
#     #     return False
#     time.sleep(1)

#     print("dmm measure DMM_MUX_DUT_TP37_VSYS")
#     if not call_rpc(client, "common.dmm_measure_voltage","DMM_MUX_DUT_TP37_VSYS"):
#         return False
#     time.sleep(1)

#     print("dmm measure DMM_MUX_DUT_TP33_VMICON")
#     if not call_rpc(client, "common.dmm_measure_voltage","DMM_MUX_DUT_TP33_VMICON"):
#         return False
#     time.sleep(1)

#     print("dmm measure DMM_MUX_DUT_TP34_VCORE_DC")
#     if not call_rpc(client, "common.dmm_measure_voltage", "DMM_MUX_DUT_TP34_VCORE_DC"):
#         return False
#     time.sleep(1)

#     print("dmm measure DMM_MUX_DUT_TP32_0P6V")
#     if not call_rpc(client, "common.dmm_measure_voltage","DMM_MUX_DUT_TP32_0P6V"):
#         return False
#     time.sleep(1)

#     print("dmm measure DMM_MUX_DUT_TP35_VANA_DC")
#     if not call_rpc(client, "common.dmm_measure_voltage", "DMM_MUX_DUT_TP35_VANA_DC"):
#         return False
#     time.sleep(1)

#     print("dmm measure DMM_MUX_DUT_TP31_VDDIF")
#     if not call_rpc(client, "common.dmm_measure_voltage", "DMM_MUX_DUT_TP31_VDDIF"):
#         return False
#     time.sleep(1)

#     print("dmm measure DMM_MUX_DUT_TP30_VDDA")
#     if not call_rpc(client, "common.dmm_measure_voltage", "DMM_MUX_DUT_TP30_VDDA"):
#         return False
#     time.sleep(1)

# def cal_8300(client):
#     print("one_wire_uart")
#     power_off(client)
#     time.sleep(1)

#     if not call_rpc(client, "common.relay", "AWG811_TO_DUT_TP15_CAL_SQUWAV"):
#         return False
#     if not call_rpc(client, "common.relay", "ODIN_BATT_TO_DUT_TP10_1P05V"):
#         return False
#         # print(mix_rpc_client.rpc_call("mixdevice.battery_output", 500, 3700))
#     if not call_rpc(client, "common.battery_output", 500, 1200):
#         return False
#     if not call_rpc(client, "common.relay", "ODIN_VCHG_TO_DUT_TP40_POGO5V"):
#         return False
#     time.sleep(1)
#     if not call_rpc(client, "common.charge_output", 500, 5000):
#         return False

# def read_string(client):
#     ret = call_rpc(client, "common.read_string")
#     return ret

# def send_read(client, cmd, terminator, timeout_ms=5000):
#     if not call_rpc(client, "common.send_read", cmd, terminator, timeout=timeout_ms):
#         return False
#     return True

# def send(client, cmd):
#     if not call_rpc(client, "common.send", cmd):
#         return False
#     return True


# def send_read_key_words(client, args1, args2, timeout_ms=5000):
#     ret = call_rpc(client, "common.send_read_key_words", args1, args2, timeout=timeout_ms)
#     if ret:
#         return ret
#     return "-- read util Fail--"

# def read_until(client, terminator, timeout=5000):
#     return  call_rpc(client, "common.read_until", terminator, timeout, timeout=timeout + 5000)





# # res = client.rpc("common.test", timeout=1000)
# # if isinstance(res, JSONRPCSuccessResponse):
# #     print(res.result)
# #     print("done")
# # else:
# #     print(res.error)

# # res = client.rpc("common.end_test", timeout=1000)
# # if isinstance(res, JSONRPCSuccessResponse):
# #     print(res.result)
# #     print("done")
# # else:
# #     print(res.error)


# # 'reset', 'fw_version', 'relay', 'fixture_eeprom_write', 'fixture_eeprom_read',
# #         'switch_mode', 'sendrecv', 'sendrecv_by_byte', 'charge_output', 'battery_output',
# #         'psu_measure', 'dmm_measure'

# # bRet =  client.rpc("common.reset", timeout=1000)
# # print("common.reset",bRet)
# #
# # bRet =  client.rpc("common.fw_version", timeout=1000)
# # print("common.fw_version",bRet)
# #
# #
# # bRet =  client.rpc("common.relay","xxx", "CONNECT:25",timeout=1000)
# # print("common.relay",bRet)
# #
# #
# # bRet =  client.rpc("common.switch_mode",True,timeout=1000)
# # print("common.switch_mode",bRet)
# #
# #
# # bRet =  client.rpc("common.charge_output",200,5000,timeout=1000)
# # print("common.charge_output",bRet)
# #
# # bRet =  client.rpc("common.battery_output",200,3800,timeout=1000)
# # print("common.battery_output",bRet)
# #
# #
# # bRet =  client.rpc("common.psu_measure","5000mv","battery",timeout=1000)
# # print("common.psu_measure",bRet)
# #
# # bRet =  client.rpc("common.dmm_measure","7000mv",timeout=1000)
# # print("common.psu_measure",bRet)
# #
# #
# # bRet =  client.rpc("common.sendrecv","DUMMY","\n",timeout=1000)
# # print("common.sendrecv",bRet)
# import subprocess
# from threading import Timer
# def run_shell_with_timeout1(cmd, timeout=10):
#     p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     timer = Timer(timeout, lambda process: process.kill(), [p])
#     try:
#         timer.start()
#         # print("4" * 100)
#         # for line in iter(p.stdout.readline, b''):
#         #     t = line
#         #     print(t)
#         stdout, stderr = p.communicate(input="q\r\n")

#         return_code = p.returncode
#         print("return_code", return_code)
#         print("stdout", stdout)
#         print("stderr: ",stderr)
#         return return_code, stdout, stderr
#     finally:
#         timer.cancel()

# def cal_8300_sqw(client):
#     one_wire_uart(client)
#     time.sleep(10)
#     read_string(client)

#     send_read(client, "[get_8300_version,]", "Fw1Version:00.00.00")

#     # send_read(client, "[stop_trim,]", "CLK trim stop")

#     send_read_key_words(client, "[start_trim,]@CLK trim start@8300 CLK trim SUCCESS!", "2000@40000", timeout_ms=50000)
#     send_read(client, "[stop_trim,]", "CLK trim stop")
#     send_read_key_words(client, "[switch_app,]@switch panama SUCCESS!@Rst8300", "20000@2000", timeout_ms=50000)

#     send_read(client, "[get_8300_version,]", "Fw1Version:03.02.02")

# def power_on(client, double=False):
#     print("power_on")
#     power_off(client)
#     time.sleep(1)
#     if not call_rpc(client, "common.open_uart"):
#         return False
#     # if not call_rpc(client, "common.relay","UART_FT232_RESET"):
#     #     return False
#     # time.sleep(0.5)
#     # if not call_rpc(client, "common.relay","UART_FT232_RESET", "DISCONNECT"):
#     #     return False
#     # time.sleep(0.5)
#     # if not call_rpc(client, "common.switch_bit1"):
#     #     return False
#     if double:
#         if not call_rpc(client, "common.relay", "UART_FT232_TO_DUT_FULL_DUPLEX"):
#             return False
#         # if not call_rpc(client, "common.relay", "RELAY_RESERVE1"):
#         #     return False
#     else:
#         if not call_rpc(client, "common.relay", "UART_FT232_TO_DUT_HALF_DUPLEX"):
#             return False
#         if not call_rpc(client, "common.relay", "RELAY_RESERVE1"):
#             return False


#         # if not call_rpc(client, "common.switch_bit1"):
#         #     return False



#     # output_sg_wave
#     # if not call_rpc(client, "common.relay", "AWG811_TO_DUT_TP15_CAL_SQUWAV"):
#     #     return False
#     if not call_rpc(client, "common.relay", "ODIN_BATT_TO_DUT_TP10_1P05V"):
#         return False
#     # print(mix_rpc_client.rpc_call("mixdevice.battery_output", 500, 3700))
#     if not call_rpc(client, "common.battery_output", 500, 1200):
#         return False
#     if not call_rpc(client, "common.relay", "ODIN_VCHG_TO_DUT_TP40_POGO5V"):
#         return False
#     time.sleep(0.5)
#     if not call_rpc(client, "common.charge_output", 500, 5000):
#         return False

#     # time.sleep(10)
#     # if not call_rpc(client, "common.charger_measure", "volt"):
#     #     return False
#     # if not call_rpc(client, "common.charger_measure", "curr"):
#     #     return False
#     return True

# def check_DUT_state(client):
#     one_wire_uart(client)
#     power_on(client)
#     time.sleep(600000)
#     read_string(client)
#     sn = "KSBBMBEVB1000Q"
#     # print("set_prod_sn")
#     # send_read(client, "[set_prod_sn,{}]".format(sn), "PROD SN")  #[set_prod_sn,KSBBMBEVB1000Q]
#     #
#     # print("get_prod_sn")
#     # send_read(client, "[get_prod_sn,]".format(sn), "PROD SN")
#     #
#     # send_read(client, "[2700_status,]", "BLE", timeout_ms=5000)
#     #
#     # send_read(client, "[init_status,]", "]]", timeout_ms=5000)

#     # --key
#     # print("key test")
#     # if not call_rpc(client, "common.relay", "PULL_UP_DUT_TP6_KEY"):
#     #     print("key test 111")
#     #     return False
#     # if not call_rpc(client, "common.relay", "PULL_UP_DUT_TP6_KEY","DISCONNECT"):
#     #     print("key test 222")
#     #     return False
#     # print("33333")
#     # time.sleep(1)
#     # read_string(client)



#     # key power
#     # print("power off key check")
#     # if not call_rpc(client, "common.relay", "PULL_UP_DUT_TP6_KEY"):
#     #     return False
#     # time.sleep(3)
#     # if not call_rpc(client, "common.relay", "PULL_UP_DUT_TP6_KEY", "DISCONNECT"):
#     #     return False
#     # time.sleep(10)
#     # read_string(client)
#     #
#     # print("power on key check")
#     # if not call_rpc(client, "common.relay", "PULL_UP_DUT_TP6_KEY"):
#     #     return False
#     # time.sleep(3)
#     # if not call_rpc(client, "common.relay", "PULL_UP_DUT_TP6_KEY", "DISCONNECT"):
#     #     return False
#     # time.sleep(10)
#     # read_string(client)

#     print("get_adc0")
#     send_read(client, "[get_adc0,],", "Adc0", timeout_ms=5000)

#     print("measure_curr")
#     if not call_rpc(client, "common.battery_measure", "curr", "500ma"):
#         return False

#     if not call_rpc(client, "common.relay", "ODIN_BATT_TO_DUT_TP22_BAT_P"):
#         return False

#     if not call_rpc(client, "common.battery_output", 500, 3700):
#         return False

#     send_read(client, "[[get_charging_status,]", "]]", timeout_ms=5000)

#     send_read(client, "[get_batt_curr,]", "]]", timeout_ms=5000)

#     if not call_rpc(client, "common.battery_measure", "volt", "5000mv"):
#         return False

#     time.sleep(0.5)
#     if not call_rpc(client, "common.battery_measure", "curr", "500ma"):
#         return False

#     time.sleep(0.5)
#     print("charge_output 0")
#     if not call_rpc(client, "common.charge_output", 0, 0):
#         return False
#     if not call_rpc(client, "common.relay", "ODIN_VCHG_TO_DUT_TP40_POGO5V", "DISCONNECT"):
#         return False

#     dmm_measure(client)

#     print("ship Mode")
#     send_read(client, "[enter_shipmode,]", "]]", timeout_ms=5000)

#     time.sleep(0.5)
#     if not call_rpc(client, "common.battery_measure", "curr", "500ma"):
#         return False

#     if not call_rpc(client, "common.relay", "ODIN_BATT_TO_DUT_TP22_BAT_P", "DISCONNECT"):
#         return False

#     print("Power off curr")
#     if not call_rpc(client, "common.battery_measure", "curr", "500ma"):
#         return False

# # check_DUT_state(client)
# # power_off(client)
# # one_wire_uart_coreboard(client)

# # assert power_on_1v2(client)
# # assert check_connect(5)
# # fwdl_2700(client)

# #
# # power_off(client)
# # power_for_jlink(client)
# # one_wire_uart(client)

# # dmm_measure(client)

# # time.sleep(10)
# # read_string(client)

# # for i in range(10):
# #     send_read(client, "[get_8300_version,]", "Fw1Version:00.00.00")

# # assert power_off(client)
# # assert power_on_1v2(client)
# # assert fwdl_8300(client)

# # one_wire_uart(client, False)
# # cal_8300_sqw(client)


# # device = "EZAIRO8300_SPI_FLASH_W25Q16JV"
# # conn_cmd = f"\"C:\\Program Files\\SEGGER\\JLink\\JLink.exe\" -autoconnect 1 -device EZAIRO8300_SPI_FLASH_W25Q16JV -if swd -speed 1000"
# # conn_cmd = f"C:/Program Files/SEGGER/JLink/JLink.exe -device EZAIRO8300_SPI_FLASH_W25Q16JV -if swd -speed 1000 -autoconnect 1"



# # for i in range(10):
# #     assert power_off(client)
# #     assert power_on_1v2(client)
# #     assert fwdl_8300(client)

# # assert power_off(client)
# # assert power_on_1v2(client)
# # assert fwdl_8300(client)

# #
# # assert(cal8300_power(client))
# # dmm_measure(client)

# # import pexpect
# # child = pexpect.spawn("C:/Program Files/SEGGER/JLink/JLink.exe", args=["-device", "EZAIRO8300_SPI_FLASH_W25Q16JV", "-if", "swd", "-speed", "1000", "-autoconnect", "1"])
# # child.expect("Cortex-M3 identified.")
# # child.sendline("q")

# print(call_rpc(client, "fwdl.restore_2700", "AABBCCDDEEFF", "evt_encrypt_1.1.0.2.bin", timeout=20000))


client = RPCClientWrapper("tcp://127.0.0.1:6100", pub)

# call_rpc(client, "specific.restore", "AABBCCDDEEFF", "evt_encrypt_1.1.0.2.bin@PanamaManufacturing_3.2.3.hex")
# call_rpc(client,'common.dut_power_on', {'netName_list':['CCS_CURRENT_OUTPUT_RANG_100MA', 'CCS_CURRENT_MEASURE_RANG_100MA', 'EXT_DUT_GND_TO_SYS_GND', 'CCS_P_TO_DUT_MUX_SEL_DUT_VDD_1V8'], 'curr_ma':10, 'volt_mv':1800})

call_rpc(client, 'common.run_shell_cmd', "{'cmd':'mode', 'expect_keyword':'COM30', 'Timeout':30000}")