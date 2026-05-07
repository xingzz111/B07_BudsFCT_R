import os
import time
import json
import ast
import re
import shutil
import platform
import ctypes
import wave
import threading

import requests
import queue
import psutil

from winpty import PtyProcess
from random import sample

import numpy as np
from scipy.io import wavfile
from scipy import signal

from rtlib.utility import ReturnDef
from rtlib.ictmes import STATION_ID, get_mes_status
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional, Union, Dict

from rtlib.ictmes import MesSN, UploadMES
from rtlib.runShell import runShell
from rtlib.utility import Unit
from pylink.jlink import JLink
from setuptools.command.egg_info import overwrite_arg

class common(object):

    rpc_public_api = [
        'start_test', 'end_test', 'delay', 'station_id' ,'rpc_call','slot_id', 'fixture_id', 'vendor_id', 'check_uop',
        'query_mac_by_sn', 'dut_power_on', 'curr_test', 'volt_test', 'led_curr_test', 'powerOn',
        'usb_test', 'scan_device', 'run_bmt_cmd', 'run_shell_cmd', 'init_rp2', 'parse_response',
        "compare_sn", "generate_device_name", "get_value_by_key", "detect_seq", "run_cmd_admin",
        "free_mem", "calculate_a_weight", "save_raw_wav", "audio_record_and_analyse", "check_fw_config", "start_bmt_server",
        "bmt_client_send", "close_bmt_server", "bmt_client_mutil_send", "parse_client_resp", "get_test_result", "query_mac_by_sn_tmp",
        "audio_enable", "audio_disable", "pio_enable", "pio_measure_stop", "measure_shipmode_current", 'write_station_flag',
        "measure_volt_uvp_ovp", "measure_vcharge", "qcc_sys_ctrl_test", "measure_ship_mode", "fixture_power_off", "measure_voltage"
    ]

    def __init__(self, xobjects):
        self.xobjects = xobjects
        self.site = xobjects.get('site')
        self._slot_status = xobjects.get("slot_status_manager")
        self.rp2_device = xobjects["rp2_device"]
        self.dutCommand = xobjects.get('dutCommand', None)
        self.publisher = xobjects.get('format_pub')
        self.publisher_common = xobjects.get('bmt_pub')
        self.buff_dict = None
        self._usb_sw_flag = False
        self._parse_response = None
        self._sn = ""
        self._bd_address = ""
        self.run_shell = runShell()
        self.bmt_cmd_dict = {}
        self._bmt_queue = queue.Queue()
        self._close_windows_flag = True
        # bmt usb server 变量：
        self._port = None
        self._monitor = None
        self._pty_proc = None
        self._bmt_client_resp = {}
        self._if_passthrough_stop_server = False
        # bmt ble server 变量：
        self._ble_port = None
        self._ble_monitor = None
        self._if_passthrough_stop_ble_server = False

        if platform.system() == "Windows":
            with open(os.path.dirname(os.path.abspath(__file__))+"\\BMT.json", "r") as f:
                self.bmt_cmd_dict = json.load(f)
            with open(os.path.dirname(os.path.abspath(__file__))+"\\port_config.json", "r") as f:
                self.usb_port_config = json.load(f).get("usb_port_config")
        else:
            with open(os.path.dirname(os.path.abspath(__file__))+"/BMT.json", "r") as f:
                self.bmt_cmd_dict = json.load(f)

        user_home = os.path.expanduser('~')
        mes_path = f"{user_home}/testerconfig/mes_config.json"
        with open(mes_path, "r") as f:
            self._clear_core_dump = json.load(f).get("clear_core_dump", True)

        mes_log_config_path = f"{user_home}/testerconfig/mes_config_for_logger.json"
        with open(mes_log_config_path, "r") as f:
            self.mes_cfg = json.load(f).get("mes_config", {})

    def log(self, message):
        if self.publisher:
            # print(message)
            msg = '{} \n'.format(message)
            self.publisher_common.publish(msg)

    def test_item_logger(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if result != 0 and result == False:
                    result = ReturnDef.FAIL_STRING
                if str(result) == "True" or result == "done":
                    result = ReturnDef.PASS_STRING
            except Exception as e:
                result = f"--FAIL--{e}"
            if type(result) is float:
                result = format(result,".2f")
            return result
        return wrapper

    def start_test(self, *args, **kwargs):
        self.rp2_device.init()
        self.rp2_device.rpc_call("mixdevice.reset", None)
        self._port = None
        self._slot_status.update_test_status(self.site)
        self._if_passthrough_stop_server = False
        try:
            for path in ("D:\\BMT\\server_pass.txt", "D:\\BMT\\server_fail.txt"):
                if os.path.exists(path):
                    os.remove(path)
        except:
            pass
        time.sleep(0.2)
        return ""

    def end_test(self, *args, **kwargs):
        self._slot_status.update_finish_status(self.site)
        try:
            if self._slot_status.check_other_slot_finish(int(self.site)):
                if not self._if_passthrough_stop_server:
                    self._kill_daemon(self._sn, False)
            self._get_server_info()
            for path in ("D:\\BMT\\server_pass.txt", "D:\\BMT\\server_fail.txt"):
                if os.path.exists(path):
                    os.remove(path)
        except:
            pass
        self.rp2_device.rpc_call("mixdevice.reset", None)
        self.rp2_device.deinit()
        time.sleep(0.2)
        return ""

    def init_rp2(self, *args, **kwargs):
        self.rp2_device.init()
        return ""

    @test_item_logger
    def rpc_call(self, *args, **kwargs):
        _args = args[0]
        function_name = _args.get("func", None)
        if not function_name:
            return ReturnDef.MISS_PARAMETER
        args_list = _args.get("args", None)
        result = self.rp2_device.rpc_call(function_name, args_list)
        if type(result) is float:
            result = round(result,2)
        return result

    @test_item_logger
    def measure_shipmode_current(self, *args, **kwargs):
        final_unit = kwargs.get("units")
        result_list = []
        for i in range(3):
            result = self.rp2_device.rpc_call("mixdevice.measureCurrentByOdin", ['battery', '1ua'])
            result_list.append(result)
        result = sum(result_list) / len(result_list)
        result = round(Unit.convert_unit(result, "mA", final_unit), 3)
        return abs(result)

    @test_item_logger
    def write_station_flag(self, *args, **kwargs):
        args_dict = args[0]
        except_result = None
        test_result = args_dict.get("test_result", None)[0]
        cmd_key = args_dict.get("cmd_key", None)
        if not test_result:
            return ReturnDef.FAIL_STRING
        if test_result == "True":
            if not cmd_key:
                args_dict["cmd_key"] = "WRITE_STATION_FLAG_FCT"
            except_result = "Station2Status=Pass"
        else:
            if not cmd_key:
                args_dict["cmd_key"] = "WRITE_STATION_FLAG_FCT_FAIL"
            except_result = "Station2Status=None"
        for i in range(3):
            result = self._run_bmt_cmd(args_dict, **kwargs)
            if "Status" in result:
                break
        if result == except_result:
            return ReturnDef.PASS_STRING
        else:
            return ReturnDef.FAIL_STRING

    @test_item_logger
    def qcc_sys_ctrl_test(self, *args, **kwargs):
        args_dict = args[0]
        action = args_dict.get("action", None)
        self.rp2_device.rpc_call("mixdevice.relay", [f"BUD_TP32_QCC_SYS_CTRL_TO_{action}"])
        time.sleep(0.5)
        for i in range(3):
            result = self._bmt_client_send(*args, **kwargs)
            if "FAIL" not in str(result):
                break
            time.sleep(0.5)
        return result

    @test_item_logger
    def measure_ship_mode(self, *args, **kwargs):
        self.rp2_device.rpc_call("mixdevice.relay", ["VOLT_MEAS_MUX_SEL_BUD_TP34_QCC_BAT_STB"])
        time.sleep(0.5)
        # result = self._run_bmt_cmd(*args, **kwargs)
        # time.sleep(5)
        self.log(f"log_in@Start_Measure: {str(datetime.now())}")
        start_time = time.time()
        volt = 0
        while True:
            volt = self.rp2_device.rpc_call("mixdevice.measureByDMM", ["ch1", "7000mv", None, 0])
            if volt > 1700:
                time.sleep(0.2)
                volt = self.rp2_device.rpc_call("mixdevice.measureByDMM", ["ch1", "7000mv", None, 0])
                break
            time.sleep(1)
            time_now = time.time()
            if time_now - start_time > 15:
                break
        self.log(f"log_in@Finish_Measure: {str(datetime.now())}")
        return volt

    @test_item_logger
    def measure_voltage(self, *args, **kwargs):
        gain_list = [0.694, 0.556, 0.675, 0.7]
        gain_index = int(self.site)
        _args = args[0]
        function_name = _args.get("func", None)
        if not function_name:
            return ReturnDef.MISS_PARAMETER
        args_list = _args.get("args", None)
        result = self.rp2_device.rpc_call(function_name, args_list)
        result = round(result * gain_list[gain_index], 2)
        self.log(f"log_in@mixdevice.measureByDMM('ch1', '7000mv', 'VOLT_MEAS_MUX_SEL_BUD_TP34_QCC_BAT_STB', 0.2)")
        self.log(f"log_out@{result}")
        return result


    @test_item_logger
    def detect_seq(self, *args, **kwargs):
        self._global_dict = {}
        final_unit = kwargs.get("units")
        result = {"qcc_sys": 0, "case_detect":0}
        if not final_unit:
            final_unit = 'mS'
        for i in range(3):
            self.rp2_device.rpc_call("pio1.load_program_high_low", None)
            self.log("log_out@done")
            self.rp2_device.rpc_call("pio2.load_program_high_low", None)
            self.log("log_out@done")
            self.rp2_device.rpc_call("pio1.measure_start", None)
            self.log("log_out@done")
            self.rp2_device.rpc_call("mixdevice.chargeEnable", [1625, 100])
            time.sleep(0.4)
            self.rp2_device.rpc_call("mixdevice.chargeEnable", [400, 100])
            time.sleep(0.4)
            self.rp2_device.rpc_call("mixdevice.chargeEnable", [1625, 100])
            time.sleep(1)
            self.rp2_device.rpc_call("pio2.measure_start", None)
            time.sleep(0.5)
            self.rp2_device.rpc_call("mixdevice.chargeDisable", None)
            self.log("log_out@done")
            time.sleep(0.1)
            self.rp2_device.rpc_call("mixdevice.chargeEnable", [1625, 100])
            # self.rp2_device.rpc_call("baseboard.set_io_switch", [[[0,1]]])

            time.sleep(2)

            qcc_rst_width = self.rp2_device.rpc_call("pio2.measure_stop", None)
            qcc_sys_ctrl_width = self.rp2_device.rpc_call("pio1.measure_stop", None)

            if qcc_sys_ctrl_width and qcc_sys_ctrl_width > 5:
                qcc_sys_ctrl_width = round(Unit.convert_unit(qcc_sys_ctrl_width, "uS", final_unit), 3)
                result["qcc_sys"] = qcc_sys_ctrl_width
            if qcc_rst_width and qcc_rst_width > 5:
                qcc_rst_width = round(Unit.convert_unit(qcc_rst_width, "uS", final_unit), 3)
                result["case_detect"] = qcc_rst_width

            self.rp2_device.rpc_call("mixdevice.chargeEnable", [5000, 500])

            if result["qcc_sys"] and result["case_detect"]:
                time.sleep(8)
                try:
                    mfg_result = self._run_bmt_cmd({'cmd_key': 'MFG_MV_GET_USB', 'cmd_args':[self._sn], 'parse_pattern': 'Variable is: (\d+)', 'Timeout': 2000, 'if_log_print': False})
                    if mfg_result == "0":
                        break
                    continue
                except:
                    continue
            else:
                if i < 2:
                    time.sleep(2)
                else:
                    time.sleep(8)
                continue


            # gpio_result = self._run_bmt_cmd({'cmd_key':'GET_GPIO7', 'parse_pattern':'GPIONum=7 Level=(\w+)', 'Timeout':5000, 'if_log_print': False})
            # try:
            #     connect_result = self._run_bmt_cmd({'cmd_key': 'Connect_DUT_BT', 'parse_pattern': '(Connected):', 'Timeout': 10000, 'if_log_print': True})
            #     if connect_result=="Connected":
            #         break
            # except Exception as e:
            #     continue

        self._global_dict = result
        return result["qcc_sys"]

    @test_item_logger
    def pio_measure_stop(self, *args, **kwargs):
        final_unit = kwargs.get("units")
        if not final_unit:
            final_unit = 'mS'
        pulse_width = self.rp2_device.rpc_call("pio1.measure_stop", None)
        if pulse_width:
            result = round(Unit.convert_unit(pulse_width, "uS", final_unit), 3)
        else:
            result = 0
        return result

    @test_item_logger
    def pio_enable(self, *args, **kwargs):
        self.rp2_device.rpc_call("pio1.load_program_low_high", None)
        self.rp2_device.rpc_call("pio1.measure_start", None)
        return ReturnDef.PASS_STRING

    @test_item_logger
    def audio_record_and_analyse(self, *args, **kwargs):
        record_type, sample_rate, raw_data_flag, need_cal = args
        log_key = kwargs.get("SubSubTestName")
        result = "--FAIL--"
        raw_data_flag = False if not int(raw_data_flag) else True
        for i in range(1):
            if record_type == "pcm":
                result = self.rp2_device.rpc_call(f"mixdevice.audio_record", [sample_rate, raw_data_flag])[0]
                # print(result)
                if need_cal:
                    cal_resp = self.rp2_device.rpc_call("mixdevice.read_calibration_cell", ["audio_measure"])
                    result['rms'] = result['rms'] * cal_resp['gain'] + cal_resp['offset']
                    # print(result)
            else:
                result = self.rp2_device.rpc_call(f"mixdevice.pdm_record", [])
            if not result:
                continue
            time.sleep(1)

        frequency = result.get("frequency", 0)
        rms = float(abs(result["rms"])) * 1000
        if "Noise_Vrms" in log_key:
            result = rms
        self.log(f"log_in@mixdevice.audio_record({sample_rate}, {raw_data_flag})")
        self.log(f"log_out@{result}")
        return result

    @test_item_logger
    def audio_enable(self, *args, **kwargs):
        freq, volt = args
        result = self.rp2_device.rpc_call("mixdevice.read_calibration_cell", ["audio_output"])
        offset = result["offset"]
        volt = float(volt) + offset
        self.rp2_device.rpc_call("mixdevice.dds_enable", [float(freq), volt, 0.2])
        time.sleep(1)
        return ReturnDef.PASS_STRING

    @test_item_logger
    def audio_disable(self, *args, **kwargs):
        self.rp2_device.rpc_call("mixdevice.dds_disable", [])
        time.sleep(0.1)
        return ReturnDef.PASS_STRING

    @test_item_logger
    def free_mem(self, *args, **kwargs):
        self.rp2_device.rpc_call("mixdevice.get_free_mem", None)
        self.rp2_device.rpc_call("mixdevice.delete_reocrder", None)
        self.rp2_device.rpc_call("mixdevice.get_free_mem", None)
        return ReturnDef.PASS_STRING

    @test_item_logger
    def delay(self, *args, **kwargs):
        if len(args) != 1:
            return ReturnDef.MISS_PARAMETER
        delay_time = float(args[0]) / 1000
        time.sleep(delay_time)
        self.log(f"log_out@Delay {delay_time}s")
        return ReturnDef.PASS_STRING

    @test_item_logger
    def get_test_result(self, *args, **kwargs):
        if len(args) != 1:
            return ReturnDef.MISS_PARAMETER
        test_result = args[0].strip('\'')
        self.log(f"get_test_result: {test_result}")
        result = "PASS" if test_result == "True" else "FAIL"
        return result

    @test_item_logger
    def copyFile(self, *args, **kwargs):
        wave = args[0]
        self.log(f"[wave] wave to {wave}...\n")
        cmd = "mpremote connect " + "COM3" + str(self.site) + " fs cp :/sdcard/" + wave + " C:\\Users\\Admin\Desktop\\test\\" + str(self.site)
        self.log(f"[cmd] cmd to {cmd}...\n")
        try:
            rescode, result, err = runShell.run_shell_with_timeout(cmd, 15)
            self.log(f"[copyFile] copyFile to {result}...\n")
        except Exception as e:
            return ReturnDef.FAIL_STRING
        return ReturnDef.PASS_STRING

    @test_item_logger
    def run_shell_cmd(self, *args, **kwargs):
        print('run shell command')
        args_dict = args[0]
        expect_keyword = args_dict.get("expect_keyword", None)
        expect_keyword = expect_keyword + str(self.site)
        parse_pattern = args_dict.get("parse_pattern", None)
        timeout = float(args_dict.get("Timeout", 5000))/1000
        cmd = args_dict.get("cmd", None)
        if not cmd:
            return ReturnDef.MISS_PARAMETER
        self.log(f"Send Shell cmd:{cmd}")
        return_code, resp, error = self.run_shell.run_shell_with_timeout(cmd, timeout)
        self.log(f"Return Code:{return_code}")
        self.log(f"BMT CMD Response:{resp}")
        self.log(f"Error:{error}")
        if return_code != 0:
            return "--FAIL--CMD Run Fail"
        if expect_keyword:
            if expect_keyword not in resp:
                return "--FAIL--NO Expect key Words Found"
            else:
                return resp
        if parse_pattern:
            parse_result = re.search(parse_pattern, resp)
            if not parse_result:
                return "--FAIL--Parse Fail"
            else:
                return parse_result.group(1)
        return ReturnDef.PASS_STRING


    def _prepare_write_sn(self, sn_type, sn):
        if sn_type not in ("WRITE_PCBA_SN", "WRITE_USB_SN"):
            return False
        if sn_type == "WRITE_PCBA_SN":
            list_device_cmd = "wmic path Win32_PnPEntity where \"PNPClass='HIDClass'\" get Name, DeviceID"
            self._usb_sw_flag = True
            self.rp2_device.rpc_call("mixdevice.relay", ["USB_SEL_SW"])
            time_start = time.time()
            while True:
                time_now = time.time()
                return_code, resp, error = self.run_shell.run_shell_with_timeout(list_device_cmd)
                self.log(f"List USB Device:{resp}")
                if "USB\VID_05A7&PID_4089" in resp:
                    time.sleep(3)
                    break
                if time_now - time_start > 20:
                    return False
                time.sleep(0.5)
            return [sn]
        else:
            sn_hex = ""
            for item in sn.encode("utf-8"):
                sn_hex += ((hex(item).replace("0x", "")))
            return [sn_hex]

    def _pre_handle_bmt_cmd(self, cmd_key, cmd, format_string=None):
        bmt_cmd = cmd
        bmt_cmd_key = cmd_key
        bmt_format_strings = format_string
        if "--port" in bmt_cmd:
            port_id = self.usb_port_config.get("slot" + str(self.site + 1), None)
            if not port_id:
                return "--FAIL--No Port id Found"
            bmt_cmd = bmt_cmd.replace("--port {}", f"--port {port_id}")

        if cmd_key in ("WRITE_PCBA_SN", "WRITE_USB_SN"):
            bmt_format_strings = self._prepare_write_sn(bmt_cmd_key, bmt_format_strings[0])
        # elif bmt_cmd_key in ("READ_PCBA_SN", "READ_USB_SN"):
        #     self._prepare_read_sn()
        if cmd_key in ("Connect_DUT_BT", "GET_GPIO7", "GET_GPIO0", "MFG_MV_GET", "MFG_MV_SET_99", "Disconnect_DUT_BT"):
            bmt_cmd = bmt_cmd.format(self._bd_address, 50+int(self.site))
            time.sleep(1)

        if bmt_format_strings:
            if not len(re.findall("{}", bmt_cmd)) == len(bmt_format_strings):
                return "--FAIL--Wrong Format Strings"
            if cmd_key in ("READ_BATTERY_VOLT", "GET_BATTERY_TEMPERATURE"):
                bmt_cmd = bmt_cmd.replace("{}", bmt_format_strings[0])
            else:
                bmt_cmd = bmt_cmd.format(*bmt_format_strings)
        if "{}" in bmt_cmd:
            return "--FAIL--BMT CMD Format Fail"
        return bmt_cmd

    def _close_window_by_title(self, title, timeout=10):
        start_time = time.time()
        while self._close_windows_flag:
            time.sleep(2)
            current_time = time.time()
            if current_time - start_time > timeout:
                break
        if self._close_windows_flag:
            hwnd = ctypes.windll.user32.FindWindowW(None, title)
            if hwnd:
                ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
        return True

    def _handle_core_status(self, resp):
        self._close_windows_flag = True
        core_dump_path = f"D:\\vault\\StationLog\\Core_Dump"
        if not os.path.exists(core_dump_path):
            os.makedirs(core_dump_path, exist_ok=True)
        core_dump_file = f"{core_dump_path}\\core_dump_record.txt"

        status = re.search("status = (\d)", resp).group(1)
        if status != "4":
            if not self._clear_core_dump:
                ctypes.windll.user32.MessageBoxW(0, f"Slot{self.site + 1} DUT CoreDump Status不等于4，请联系TE处理！！", "Warning", 0x1000 | 0x30)
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                record_message = f"Slot{self.site + 1}; {self._sn}; {timestamp}; {resp}; Not Clear Core Dump\r"
                with open(core_dump_file, "a+") as f:
                    f.write(record_message)
                return "--PASS--"
            else:
                windows_title = f"Clear Warning Slot{self.site + 1}"
                t = threading.Thread(target=self._close_window_by_title, args=(windows_title, 30), daemon=True)
                t.start()
                ctypes.windll.user32.MessageBoxW(0, f"Slot{self.site + 1} DUT CoreDump Status不等于4，请联系TE处理！！", windows_title, 0x1000 | 0x30)
                self._close_windows_flag = False
                t.join()

                kwargs = {}
                args = [{'cmd_key':'Clear_Core_Dump', 'cmd_args':[self._sn], 'expect_keyword': 'CORE_FILE_RC_SUCCESS', 'Timeout':10000}]
                clr_resp = self._run_bmt_cmd(*args, **kwargs)
                args = [{'cmd_key':'Get_Core_Dump', 'cmd_args':[self._sn], 'expect_keyword': 'Debug.TAP.Result TapCommandStatus=OK','parse_pattern':'crashlog info->status = (\d)', 'Timeout':10000}]
                cmd_resp = self._run_bmt_cmd(*args, **kwargs)
                if cmd_resp == "4":
                    clear_message = "Clear Core Dump Pass"
                else:
                    clear_message = "Clear Core Dump Fail"
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                record_message = f"Slot{self.site + 1}; {self._sn}; {timestamp}; {resp}; {clear_message}\r"
                with open(core_dump_file, "a+") as f:
                    f.write(record_message)
                return clr_resp
        return "--PASS--"

    @test_item_logger
    def run_bmt_cmd(self, *args, **kwargs):
        resp = "--FAIL--"
        args_dict = args[0]
        bmt_cmd_key = args_dict.get("cmd_key", None)
        for i in range(2):
            try:
                resp = self._run_bmt_cmd(*args, **kwargs)
                if bmt_cmd_key == "Get_Core_Dump":
                    if "status" in resp:
                        resp = self._handle_core_status(resp)
            except Exception as e:
                resp == f"--FAIL--Exception Error {e}"
                self.log(f"log_out@Exception Error:[{e}]")
                continue
            if "FAIL" not in str(resp):
                if bmt_cmd_key == "READ_USB_SN_2":
                    resp = self._get_scan_sn(resp)
                break
        return resp

    def _run_bmt_cmd(self, *args, **kwargs):
        self._parse_response = None

        args_dict = args[0]
        expect_keyword = args_dict.get("expect_keyword", None)
        parse_pattern = args_dict.get("parse_pattern", None)
        if_need_resp = int(args_dict.get("if_need_resp", 0))
        if_need_tonumber = int(args_dict.get("if_need_tonumber", 0))
        if_log_print = args_dict.get("if_log_print", True)
        compare_str = args_dict.get("compare_str", None)
        timeout = float(args_dict.get("Timeout", 5000))/1000
        bmt_cmd_key = args_dict.get("cmd_key", None)
        bmt_cmd = self.bmt_cmd_dict.get(bmt_cmd_key, None)
        if not bmt_cmd:
            return ReturnDef.MISS_PARAMETER
        bmt_format_strings = args_dict.get("cmd_args", None)

        bmt_cmd = self._pre_handle_bmt_cmd(bmt_cmd_key, bmt_cmd, bmt_format_strings)
        if "--FAIL--" in bmt_cmd:
            self.log(f"Pre handle BMT cmd Fail: {bmt_cmd}")
            return "--FAIL--Pre_Handle_CMD_Fail"

        path = "D:\\BMT\\BoseManufacturingTool-5.3.0-1384+a170927\\BoseManufacturingTool\\BoseManufacturingTool.exe"
        if "BoseManufacturingTool" in bmt_cmd:
            bmt_cmd = bmt_cmd.replace("BoseManufacturingTool", path)

        if if_log_print:
            self.log(f"log_in@Send cmd:[{bmt_cmd}] with timeout {timeout}s")

        return_code, resp, error = self.run_shell.run_shell_with_timeout(bmt_cmd, timeout)
        resp = error + resp

        if if_log_print:
            self.log(f"log_out@CMD Response:[{resp}]")

        if if_need_resp:
            self._parse_response = resp
        self.log(f"Return Code:[{return_code}]")
        # time.sleep(1)

        if self._usb_sw_flag:
            self.rp2_device.rpc_call("mixdevice.relay", ["USB_SEL_SW", "DISCONNECT"])
            self._usb_sw_flag = False
            time.sleep(3)

        if return_code != 0 and return_code != 12:
            return "--FAIL--CMD Run Fail"
        else:
            if "BlueSuite" in bmt_cmd and "BoseManufacturingTool" in bmt_cmd:
                time.sleep(0.5)

        if expect_keyword:
            if expect_keyword not in resp:
                return "--FAIL--NO Expect key Words Found"
        if parse_pattern:
            parse_result = re.search(parse_pattern, resp)
            if not parse_result:
                return "--FAIL--Parse Fail"
            else:
                parse_result = parse_result.group(1)
                if if_need_tonumber:
                    parse_result = float(parse_result)
                else:
                    if compare_str:
                        if compare_str == parse_result:
                            self.log(f"log_out@|Result = PASS")
                            return ReturnDef.PASS_STRING
                        else:
                            return "--FAIL--Compare String Failed"
                return parse_result
        # if expect_keyword:
        #     self.log(f"log_out@|Result = PASS")
        return ReturnDef.PASS_STRING

    @test_item_logger
    def bmt_client_send(self, *args, **kwargs):
        resp = "--FAIL--"
        args_dict = args[0]
        bmt_cmd_key = args_dict.get("cmd_key", None)
        for i in range(2):
            try:
                resp = self._bmt_client_send(*args, **kwargs)
            except Exception as e:
                resp == f"--FAIL--Exception Error {e}"
                self.log(f"log_out@Exception Error:[{e}]")
                continue
            if "FAIL" not in str(resp):
                break
            else:
                time.sleep(1)
        return resp

    @test_item_logger
    def bmt_client_mutil_send(self, *args, **kwargs):
        args_dict = args[0]

        timeout = float(args_dict.get("Timeout", 5000)) / 1000
        cmd_list = args_dict.get("cmd_list", None)
        if_ble = args_dict.get("if_ble", 0)
        
        if not cmd_list:
            return ReturnDef.MISS_PARAMETER

        port = self._port if not if_ble else self._ble_port
        dev = self._sn
        client_path = "D:\\BMT\\BoseManufacturingTool-5.3.0-1384+a170927\\BoseManufacturingTool\\bmt_client.exe"
        bmt_cmd = f"{client_path} --host 127.0.0.1 --port {port} --dev {dev} "

        for item in cmd_list:
            bmt_cmd += f"--cmd {item} "

        for i in range(2):
            try:
                self.log(f"log_in@{str(datetime.now())} Send cmd:[{bmt_cmd}] with timeout {timeout}s")
                return_code, resp, error = self.run_shell.run_shell_with_timeout(bmt_cmd, timeout)
                resp = error + resp
                self.log(f"log_out@{str(datetime.now())} CMD Response:[{resp}]")
                if "No messages seen" in resp:
                    continue
                else:
                    break
            except Exception as e:
                self.log(f"log_out@{str(datetime.now())} CMD Response Error:[{e}]")
                time.sleep(2)
                continue

        time.sleep(0.25)
        server_resp = self._get_server_info()
        self.log(f"log_out@{str(datetime.now())} Server Response:[{server_resp}]")

        sent_list = re.findall("(Sent: .*)", resp)
        recevie_list = re.findall("(Received: .*)", resp)
        if len(cmd_list) != len(sent_list) and len(cmd_list) != len(recevie_list):
            return "--FAIL--Response not match cmd list"
        else:
            self._bmt_client_resp = {}
            for i in range(len(cmd_list)):
                self._bmt_client_resp[cmd_list[i]] = [sent_list[i], recevie_list[i]]
        return ReturnDef.PASS_STRING

    @test_item_logger
    def parse_client_resp(self, *args, **kwargs):
        args_dict = args[0]

        expect_keyword = args_dict.get("expect_keyword", None)
        parse_pattern = args_dict.get("parse_pattern", None)
        if_need_tonumber = int(args_dict.get("if_need_tonumber", 0))
        compare_str = args_dict.get("compare_str", None)
        bmt_cmd_key = args_dict.get("cmd_key", None)
        bmt_resp = self._bmt_client_resp.get(bmt_cmd_key, None)
        if not bmt_resp:
            return "--FAIL--NO CMD Resp Found"
        sent_info = bmt_resp[0]
        resp = bmt_resp[1]
        self.log(f"log_in@BMT Client sent:[{sent_info}]")
        self.log(f"log_out@BMT Client Response:[{resp}]")
        time.sleep(0.03)

        if expect_keyword:
            if expect_keyword not in resp:
                return "--FAIL--NO Expect key Words Found"
        if parse_pattern:
            parse_result = re.search(parse_pattern, resp)
            if not parse_result:
                return "--FAIL--Parse Fail"
            else:
                parse_result = parse_result.group(1)
                if if_need_tonumber:
                    parse_result = float(parse_result)
                else:
                    if compare_str:
                        if compare_str == parse_result:
                            self.log(f"log_out@|Result = PASS")
                            return ReturnDef.PASS_STRING
                        else:
                            return "--FAIL--Compare String Failed"
                return parse_result
        # if expect_keyword:
        #     self.log(f"log_out@|Result = PASS")
        return ReturnDef.PASS_STRING

    def _bmt_client_send(self, *args, **kwargs):
        self._parse_response = None

        args_dict = args[0]
        expect_keyword = args_dict.get("expect_keyword", None)
        parse_pattern = args_dict.get("parse_pattern", None)
        if_need_resp = int(args_dict.get("if_need_resp", 0))
        if_need_tonumber = int(args_dict.get("if_need_tonumber", 0))
        if_log_print = args_dict.get("if_log_print", True)
        if_ble = args_dict.get("if_ble", 0)
        compare_str = args_dict.get("compare_str", None)
        timeout = float(args_dict.get("Timeout", 5000))/1000
        bmt_cmd_key = args_dict.get("cmd_key", None)
        if not bmt_cmd_key:
            return ReturnDef.MISS_PARAMETER

        port = self._port if not if_ble else self._ble_port
        dev = self._sn
        client_path = "D:\\BMT\\BoseManufacturingTool-5.3.0-1384+a170927\\BoseManufacturingTool\\bmt_client.exe"
        bmt_cmd = f"{client_path} --host 127.0.0.1 --port {port} --dev {dev} --cmd {bmt_cmd_key}"

        if if_log_print:
            self.log(f"log_in@{str(datetime.now())} Send cmd:[{bmt_cmd}] with timeout {timeout}s")
        return_code, resp, error = self.run_shell.run_shell_with_timeout(bmt_cmd, timeout)
        resp = error + resp
        if if_log_print:
            self.log(f"log_out@{str(datetime.now())} CMD Response:[{resp}]")

        if if_need_resp:
            self._parse_response = resp
        self.log(f"Return Code:[{return_code}]")

        time.sleep(0.25)
        # server_resp = self._get_server_info()
        # if if_log_print:
        #     self.log(f"log_out@{str(datetime.now())} Server Response:[{server_resp}]")

        if self._usb_sw_flag:
            self.rp2_device.rpc_call("mixdevice.relay", ["USB_SEL_SW", "DISCONNECT"])
            self._usb_sw_flag = False
            time.sleep(3)

        if return_code != 0 and return_code != 12:
            return "--FAIL--CMD Run Fail"
        else:
            if "BlueSuite" in bmt_cmd and "BoseManufacturingTool" in bmt_cmd:
                time.sleep(1)

        if expect_keyword:
            if expect_keyword not in resp:
                return "--FAIL--NO Expect key Words Found"
        if parse_pattern:
            parse_result = re.search(parse_pattern, resp)
            if not parse_result:
                return "--FAIL--Parse Fail"
            else:
                parse_result = parse_result.group(1)
                if if_need_tonumber:
                    parse_result = float(parse_result)
                else:
                    if compare_str:
                        if compare_str == parse_result:
                            self.log(f"log_out@|Result = PASS")
                            return ReturnDef.PASS_STRING
                        else:
                            return "--FAIL--Compare String Failed"
                return parse_result
        # if expect_keyword:
        #     self.log(f"log_out@|Result = PASS")
        return ReturnDef.PASS_STRING

    @test_item_logger
    def run_cmd_admin(self, *args, **kwargs):
        resp = "--FAIL--"
        for i in range(3):
            try:
                resp = self._run_cmd_admin(*args, **kwargs)
                if "Device Disconnect Over BLE" in resp:
                    self._run_cmd_admin({'cmd_key': 'Connect_DUT_BT', 'parse_pattern': '(Connected):', 'Timeout': 5000, 'if_log_print': True})
                    time.sleep(2)
            except Exception as e:
                resp == f"--FAIL--Exception Error {e}"
                self.log(f"log_out@Exception Error:[{e}]")
                continue
            if "FAIL" not in str(resp):
                break
        return resp

    def _bmt_server_monitor(self, cmd):
        if self._pty_proc:
            self._pty_proc.terminate(True)
            self._pty_proc.close()
            time.sleep(0.5)
        self._pty_proc = None
        self._pty_proc = PtyProcess.spawn("cmd.exe", dimensions=(24, 800))
        self._pty_proc.fileobj.setblocking(False)
        self._pty_proc.write(cmd + "\r\n")
        while self._pty_proc.isalive():
            try:
                content = self._pty_proc.fileobj.recv(2048)
                if content:
                    content = content.decode("utf-8")
                    content = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', content)
                    content = re.sub(r'[\x08\x07\x1b]', '', content)
                    self._bmt_queue.put(content.strip())
                time.sleep(0.05)
            except Exception as e:
                if "[WinError 10035]" in str(e):
                    time.sleep(0.05)
                else:
                    self._bmt_queue.put(str(e))
                    break
        return

    def _bmt_ble_server_monitor(self, cmd):
        self._pty_proc_ble = None
        self._pty_proc_ble = PtyProcess.spawn("cmd.exe", dimensions=(24, 800))
        self._pty_proc_ble.fileobj.setblocking(False)
        self._pty_proc_ble.write(cmd + "\r\n")
        while self._pty_proc_ble.isalive():
            try:
                content = self._pty_proc_ble.fileobj.recv(2048)
                if content:
                    content = content.decode("utf-8")
                    content = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', content)
                    content = re.sub(r'[\x08\x07\x1b]', '', content)
                    self._bmt_queue.put(content.strip())
                time.sleep(0.05)
            except Exception as e:
                if "[WinError 10035]" in str(e):
                    time.sleep(0.05)
                else:
                    self._bmt_queue.put(str(e))
                    break
        return

    def _get_server_info(self):
        try:
            content = ""
            while not self._bmt_queue.empty():
                elem = self._bmt_queue.get(timeout=1)
                content = content + elem + "\r"
                # time.sleep(0.01)
            return content
        except Exception as e:
            return f"Error: {e}"

    @test_item_logger
    def start_bmt_server(self, *args, **kwargs):
        args_dict = args[0]
        sn = args_dict.get("sn", None)
        if not sn:
            return ReturnDef.MISS_PARAMETER
        self._port = None
        result = "--FAIL--"
        content = " "

        client_path = "D:\\BMT\\BoseManufacturingTool-5.3.0-1384+a170927\\BoseManufacturingTool\\bmt_client.exe"
        path = "D:\\BMT\\BoseManufacturingTool-5.3.0-1384+a170927\\BoseManufacturingTool\\BoseManufacturingTool.exe"
        server_pass_path = "D:\\BMT\\server_pass.txt"
        server_fail_path = "D:\\BMT\\server_fail.txt"
        if os.path.exists(server_pass_path):
            self.log(f"log_in@Detect BMT Server Exist")
            with open(server_pass_path, "r") as f:
                content = f.read()
            parse_port = re.search(f"Server listening on 127.0.0.1:(\d+) - Expecting device: {sn}", content)
            if parse_port:
                self._port = parse_port.group(1)
                result = "--PASS--"
            else:
                result = "--FAIL--No parsed port found"
        elif os.path.exists(server_fail_path):
            self.log(f"log_in@BMT Server Start Fail]")
            with open(server_fail_path, "r") as f:
                content = f.read()
            result = "--FAIL--Found fail txt"
        else:
            for i in range(2):
                start_cmd = f"{path} start_daemon --transport USB --devices 4 --file D:\\BMT\\BUDS_CMD.json --print_response --debug --time_stamp"
                self.log(f"log_in@Start daemon: [{start_cmd}]")
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                self._monitor = threading.Thread(target=self._bmt_server_monitor, args=(start_cmd,),
                                                    name=f"bmt_monitor_{timestamp}", daemon=True)
                self._monitor.start()
                time.sleep(5)
                content = self._get_server_info()
                if "Server listening on 127.0.0.1" not in content:
                    time.sleep(3)
                    content = content + "\r\n" + self._get_server_info()

                self.log(f"Server Response: [{content}]")
                if "Server listening on 127.0.0.1" in content:
                    with open(server_pass_path, "w") as f:
                        f.write(content)
                    parse_content = re.search("Starting Daemon.*", content, flags=re.DOTALL)
                    if parse_content:
                        content = parse_content.group()
                    parse_port = re.search(f"Server listening on 127.0.0.1:(\d+) - Expecting device: {sn}", content)
                    if parse_port:
                        self._port = parse_port.group(1)
                        result = "--PASS--"
                        break
                    else:
                        result = "--FAIL--No parsed port found"
                else:
                    continue

        if "--FAIL--" in result:
            if not os.path.exists(server_fail_path):
                with open(server_fail_path, "w") as f:
                    f.write(content)
        self.log(f"log_out@Server Response: [{content}]")
        time.sleep(0.1)
        return result


    def _list_thread(self):
        for i, thread in enumerate(threading.enumerate()):
            self.log(f"log_out@thread: [{i}]")
            self.log(f"log_out@name: [{thread.name}]")
            self.log(f"log_out@ident: [{thread.ident}]")
            self.log(f"log_out@isalive: [{thread.is_alive}]")
            self.log(f"log_out@daemon: [{thread.daemon}]")

    def _check_memory(self):
        process = psutil.Process()
        mem_mb = process.memory_info().rss / (1024 ** 2)
        self.log(f"log_out@RSS: {mem_mb} MB")
        mem_mb = process.memory_full_info().uss / (1024 ** 2)
        self.log(f"log_out@USS: {mem_mb} MB")

    def _list_bmt_pid(self):
        task_list_cmd = "tasklist /fi \"imagename eq BoseManufacturingTool.exe\""
        self.log(f"log_in@Send CMD: [{task_list_cmd}] with timeout 8s")
        return_code, resp, error = self.run_shell.run_shell_with_timeout(task_list_cmd, 8)
        resp = error + resp
        self.log(f"log_out@CMD Response: [{resp}]")
        pid_list = re.findall("BoseManufacturingTool.exe\s+(\d+)", resp)
        return pid_list

    @test_item_logger
    def close_bmt_server(self, *args, **kwargs):
        if self._slot_status.check_other_slot_finish(self.site):
            resp = self._kill_daemon(self._sn)
            if "Bye for now" in resp:
                time.sleep(0.5)
                # self._check_memory()
                result = ReturnDef.PASS_STRING
            elif "Connection to server failed" in resp:
                result = ReturnDef.PASS_STRING
            else:
                result = ReturnDef.FAIL_STRING
        else:
            result = ReturnDef.PASS_STRING
        self._slot_status.update_finish_status(self.site)
        time.sleep(0.1)
        return result

    def _kill_daemon(self, sn, log_print = True):
        client_path = "D:\\BMT\\BoseManufacturingTool-5.3.0-1384+a170927\\BoseManufacturingTool\\bmt_client.exe"
        kill_cmd = f"{client_path} --host 127.0.0.1 --port {self._port} --dev {sn} --cmd kill_daemon"

        if log_print:
            self.log(f"log_in@Send CMD: [{kill_cmd}] with timeout 5s")
        self._if_passthrough_stop_server = True
        return_code, resp, error = self.run_shell.run_shell_with_timeout(kill_cmd, 5)
        resp = error + resp
        if log_print:
            self.log(f"log_out@CMD Response: [{resp}]")
        return resp

    def _run_cmd_admin(self, *args, **kwargs):
        args_dict = args[0]
        output_path = "C:\\CmdOut"
        if not os.path.exists(output_path):
            os.makedirs(output_path, exist_ok=True)
        output_file = f"C:\\CmdOut\\slot{self.site}.txt"
        # if os.path.exists(output_file):
        #     os.remove(output_file)
        #     time.sleep(0.5)
        if_log_print = args_dict.get("if_log_print", True)
        expect_keyword = args_dict.get("expect_keyword", None)
        parse_pattern = args_dict.get("parse_pattern", None)
        timeout = float(args_dict.get("Timeout", 5000)) / 1000
        bmt_cmd_key = args_dict.get("cmd_key", None)
        bmt_cmd = self.bmt_cmd_dict.get(bmt_cmd_key, None)
        if not bmt_cmd:
            return ReturnDef.MISS_PARAMETER

        if "ble_address" in bmt_cmd and "bluespeak_port" in bmt_cmd:
            bmt_cmd = bmt_cmd.format(self._bd_address, 50 + int(self.site))
        else:
            bmt_cmd = bmt_cmd.format(50 + int(self.site))

        path = "D:\\BMT\\BoseManufacturingTool-5.0.0-1263+568c02b\\BoseManufacturingTool\\BoseManufacturingTool.exe"
        if "BoseManufacturingTool" in bmt_cmd:
            bmt_cmd = bmt_cmd.replace("BoseManufacturingTool", path)

        if if_log_print:
            self.log(f"log_in@Send cmd:[{bmt_cmd}] with timeout {timeout}s")
        cmd = f'cmd /c "{bmt_cmd} > "{output_file}" 2>&1"'
        ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", f"/c{cmd}", None, 0)
        time.sleep(1)
        start = time.time()
        resp = ""
        while True:
            try:
                with open(output_file, "r") as f:
                    resp = f.read()
            except:
                time.sleep(0.5)
                continue
            if resp:
                break
            time.sleep(0.5)
            now = time.time()
            if now - start > timeout:
                break

        with open(output_file, "r") as f:
            resp = f.read()
        if if_log_print:
            self.log(f"log_out@CMD Response:[{resp}]")
        if "No devices connected over BLE" in resp:
            return "--FAIL--Device Disconnect Over BLE"

        if expect_keyword:
            if expect_keyword not in resp:
                return "--FAIL--NO Expect key Words Found"
        if parse_pattern:
            parse_result = re.search(parse_pattern, resp)
            if not parse_result:
                return "--FAIL--Parse Fail"
            else:
                parse_result = parse_result.group(1)
                return parse_result
        # if expect_keyword:
        #     self.log(f"log_out@|Result = PASS")
        return ReturnDef.PASS_STRING

    @test_item_logger
    def parse_response(self, *args, **kwargs):

        parse_pattern = args[0]
        # if len(args_list) != 1:
        #     return ReturnDef.MISS_PARAMETER
        string_to_parse = self._parse_response
        parse_result = re.search(parse_pattern, string_to_parse)
        if not parse_result:
            return "--FAIL--Parse Fail"
        else:
            return parse_result.group(1)

    @test_item_logger
    def compare_sn(self, *args, **kwargs):
        if len(args) == 2:
            _from_mes, _from_dut = args
        else:
            _from_mes, _from_dut = args[0], args[1]
            _from_dut = _from_dut.replace(" ", "")
        # if len(args_list) != 1:
        #     return ReturnDef.MISS_PARAMETER
        self.log(f"log_in@Scanned SN is {_from_mes}; Read SN is {_from_dut}")
        self.log(f"mes: {_from_mes}")
        self.log(f"dut: {_from_dut}")
        if _from_dut == _from_mes:
            self.log(f"log_out@|Result = PASS")
            return ReturnDef.PASS_STRING
        else:
            return ReturnDef.FAIL_STRING

    @test_item_logger
    def station_id(self, *args, **kwargs):
        return STATION_ID

    @test_item_logger
    def fixture_id(self, *args, **kwargs):
        return "fixturexxx"

    @test_item_logger
    def slot_id(self, *args, **kwargs):
        slot_id = "slot" + str(self.site + 1)
        return slot_id

    @test_item_logger
    def vendor_id(self, *args, **kwargs):
        return "OSENS"

    @test_item_logger
    def check_uop(self, *args, **kwargs):
        if not get_mes_status():
            return "--SKIP--"
        sn = str(args[0])
        mes = UploadMES()
        mes_cmd = {"COMMAND": "CheckData", "SERIAL_NUMBER": sn, "VERSION": "V1.0", "TERMINAL_NAME": STATION_ID}
        self.log(f"log_in@Send to MES: {mes_cmd}")
        state, resp = mes.check_data(sn)
        self.log(f"log_out@MES Response: {resp}")
        if not state:
            self.log("check uop failed,get data from MES failed")
            return ReturnDef.FAIL_STRING
        if state and state == "--SKIP--":
            return resp
        uop_result = resp.get("RESULT")
        result_info = resp.get("RESULT_INFO")
        if uop_result == "OK":
            return  ReturnDef.PASS_STRING
        else:
            self.log("MES data:{}".format(json.dumps(resp)))
            return "--FAIL--{}".format(result_info)

    @test_item_logger
    def query_mac_by_sn(self, *args, **kwargs):
        sn = str(args[0]).strip("\'")
        mes_sn = MesSN()
        info_dict = {}
        self._bd_address = ""
        info, msg = mes_sn.get_mac(sn)
        # self.log("GET: MAC:{} by SN:{}".format(info, sn))
        if not info:
            return ReturnDef.FAIL_STRING
        self.log(f"log_in@Send to MES: [{msg}]")
        self.log(f"log_out@MES Response: [{info}]")
        mac_code_raw = re.findall(r"MACCODE=(\w+)", info)[0]
        info_dict["MAC_RAW"] = mac_code_raw.strip()
        # license_key_raw = re.findall(r"LICENSE_KEY=(\w+)", info)[0]
        MACCODE = ""
        # LICENSE_KEY = ""

        for i in range(0, int(len(mac_code_raw)), 2):
            self._bd_address += ":" + mac_code_raw[i:i+2]
        for i in range(int(len(mac_code_raw)), 0, -2):
            MACCODE += " " + mac_code_raw[i - 2:i]
        # for i in range(0, int(len(license_key_raw)), +4):
        #     tmp_str = (license_key_raw[i:i + 4])
        #     LICENSE_KEY += tmp_str[2:4] + " " + tmp_str[:2] + " "

        self._bd_address = self._bd_address.strip(":")
        info_dict["MACCODE"] = MACCODE.strip()
        # info_dict["LICENSE_KEY"] = LICENSE_KEY.strip()
        # info_dict["APTX_LICENSE_KEY"] = re.findall(r"APTX_LICENSE_KEY=([\w\s]+)", info)[0]
        return info_dict

    @test_item_logger
    def query_mac_by_sn_tmp(self, *args, **kwargs):
        sn = str(args[0]).strip("\'")
        self._bd_address = ""
        info_dict = {}
        dict_mes = {"R5265000928900276S20010": "SN=R5265000928900276S20010;MACCODE=68F21F16B228;LICENSE_KEY=2DB75A53EDB853FDD9710172;APTX_LICENSE_KEY=54 B6 F2 5F 10 7D CF 3C 2B E0 4D D9 32 D8 5C 4A CE 14 BB 39 8A 36 D6 4E 79 E5 28 74 E8 CE 27 4D 70 FC FD A0 36 43 4B C6 6F 41 05 22 DC 62 CD 81 05 8F 86 D2 EC EC 98 73 84 6D 17 0D A8 7E 43 86",
                "R5266000407900276S30010": "SN=R5266000407900276S30010;MACCODE=68F21F16A95E;LICENSE_KEY=2DB75A53EDB853FDD9710172;APTX_LICENSE_KEY=54 B6 F2 5F 10 7D CF 3C 2B E0 4D D9 32 D8 5C 4A CE 14 BB 39 8A 36 D6 4E 79 E5 28 74 E8 CE 27 4D 70 FC FD A0 36 43 4B C6 6F 41 05 22 DC 62 CD 81 05 8F 86 D2 EC EC 98 73 84 6D 17 0D A8 7E 43 86",
                "R5266000411900276S30010": "SN=R5266000411900276S30010;MACCODE=68F21F16B485;LICENSE_KEY=2DB75A53EDB853FDD9710172;APTX_LICENSE_KEY=54 B6 F2 5F 10 7D CF 3C 2B E0 4D D9 32 D8 5C 4A CE 14 BB 39 8A 36 D6 4E 79 E5 28 74 E8 CE 27 4D 70 FC FD A0 36 43 4B C6 6F 41 05 22 DC 62 CD 81 05 8F 86 D2 EC EC 98 73 84 6D 17 0D A8 7E 43 86",
                "R5266000410900276S30010": "SN=R5266000410900276S30010;MACCODE=68F21F16B2AA;LICENSE_KEY=2DB75A53EDB853FDD9710172;APTX_LICENSE_KEY=54 B6 F2 5F 10 7D CF 3C 2B E0 4D D9 32 D8 5C 4A CE 14 BB 39 8A 36 D6 4E 79 E5 28 74 E8 CE 27 4D 70 FC FD A0 36 43 4B C6 6F 41 05 22 DC 62 CD 81 05 8F 86 D2 EC EC 98 73 84 6D 17 0D A8 7E 43 86"
        }
        info = dict_mes[sn]
        self.log(f"log_out@MES Response: [{info}]")

        mac_code_raw = re.findall(r"MACCODE=(\w+)", info)[0]
        info_dict["MAC_RAW"] = mac_code_raw.strip()
        license_key_raw = re.findall(r"LICENSE_KEY=(\w+)", info)[0]
        MACCODE = ""
        LICENSE_KEY = ""

        for i in range(0, int(len(mac_code_raw)), 2):
            self._bd_address += ":" + mac_code_raw[i:i + 2]
        for i in range(int(len(mac_code_raw)), 0, -2):
            MACCODE += " " + mac_code_raw[i - 2:i]
        for i in range(0, int(len(license_key_raw)), +4):
            tmp_str = (license_key_raw[i:i + 4])
            LICENSE_KEY += tmp_str[2:4] + " " + tmp_str[:2] + " "

        self._bd_address = self._bd_address.strip(":")
        info_dict["MACCODE"] = MACCODE.strip()
        info_dict["LICENSE_KEY"] = LICENSE_KEY.strip()
        info_dict["APTX_LICENSE_KEY"] = re.findall(r"APTX_LICENSE_KEY=([\w\s]+)", info)[0]
        return info_dict

    @test_item_logger
    def check_fw_config(self, *args, **kwargs):
        check_list = {"une": "otp_none", "dev": "otp_deve", "pro": "otp_prod"}
        args_dict = args[0]
        sn = args_dict.get("sn", None)
        otp_type = args_dict.get("otp", None)

        url = f"http://10.32.23.128:8091/api/Mes/CheckFWVersion?SN={sn}"
        mes_cmd = {"COMMAND": "GET", "SERIAL_NUMBER": sn, "URL": url}
        self.log(f"log_in@Send to MES: {mes_cmd}")
        response = requests.get(url)
        resp_code = response.status_code
        resp_text = response.text
        resp_dict = json.loads(resp_text)
        self.log(f"log_out@MES Response: {resp_text}")
        if resp_code == 200:
            result = resp_dict.get("Msg", "None").lower()
            if result in ("une", 'dev', 'pro'):
                self.log(f"log_in@Dut OTP type is: {otp_type}; FW Config from MES is {result}")
                if otp_type == check_list.get(result, None):
                    self.log("log_out@|Result = PASS")
                    return result
                else:
                    self.log("log_out@|Result = FAIL")
                    return "--FAIL--OTP Type compare failed"
            else:
                return "--FAIL--Invalid config"
        else:
            return "--FAIL--Return Code Error"

    @test_item_logger
    def generate_device_name(self, *args, **kwargs):
        station_id = STATION_ID
        buds_type = re.search("FCT_(\w)_", station_id).group(1)
        bd_address = str(args[0]).strip("\'")
        bd_list = bd_address.split(" ")
        device_name = "SPI_C2_" + buds_type + "_" +bd_list[1] + bd_list[0]
        self.log(f"log_in@DeviceName string is ‘{device_name}’")
        device_name_ascii = ""
        for item in device_name.encode("utf-8"):
            device_name_ascii += ' ' + (hex(item).replace("0x", ""))
        device_name_ascii = device_name_ascii.strip()
        self.log(f"log_out@DeviceName ASCII is '{device_name_ascii}'")
        return device_name_ascii


    # @test_item_logger
    def _get_scan_sn(self, *args, **kwargs):
        self._sn = ""
        sn = str(args[0]).strip("'")
        sn_limit = re.search("\w{11}(\d+)\w{6}", self.mes_cfg.get('scan_sn_limit')).group(1)
        sn_scanned = re.search("\w{11}(\d+)\w{6}", sn).group(1)
        if not sn_limit == sn_scanned:
            return "--FAIL--SCAN Wrong SN"
        self._sn = sn
        return sn

    @test_item_logger
    def get_value_by_key(self, *args, **kwargs):
        log_dict = {"@MIC_Noise_Vrms": "ANALYSE_MIC_Noise", "@MIC_Frequency": "Run_MIC_1000Hz_Test",
                    "@MIC_Vrms": "Run_MIC_1000Hz_Test", "@MIC_THD+N": "Run_MIC_1000Hz_Test",
                    "@VPU_Noise_Vrms": "ANALYSE_VPU_Noise", "@VPU_Frequency": "Run_VPU_1000Hz_Test",
                    "@VPU_Vrms": "Run_VPU_1000Hz_Test", "@VPU_THD+N": "Run_VPU_1000Hz_Test", 
                    "@CASE_DETECT_L_Pulse_Width": "QCC_SYS_CTRL_Pulse_Width" 
                    }
        log_key = kwargs.get("SubSubTestName")
        key = kwargs.get("SubTestName")
        from_item = log_dict.get(log_key, None)
        if from_item:
            self.log(f"log_in@Get value from item [{from_item}]")
        # if "@" in key:
        #     key = key.replace("@", "")
        key = key.split("@")[1]
        # self.log(f"key: {key}")
        if len(args) == 0:
            self.log(f"log_out@{self._global_dict[key]}")
            return self._global_dict[key]
        # self.log(f"args: {args}")
        input_table = ast.literal_eval(args[0].strip("'"))
        # self.log(f"arg_list: {input_table}")
        # input_table = ast.literal_eval(arg_list[1])
        if key == "dBV":
            dbv = round(20 * np.log10(float(input_table["rms"])), 4)
            self.log(f"log_in@Transfer RMS to dBV: 20 * log10({float(input_table['rms'])}/1)")
            self.log(f"log_out@{dbv} dBV")
            return dbv
        if key == "rms":
            rms = input_table["rms"]
            self.log(f"log_out@{rms}")
            rms = float(abs(rms)) * 1000
            return rms
        if key == "thdn":
            thdn = input_table["thdn"]
            self.log(f"log_out@{thdn}")
            thdn = round(10 ** (float(thdn)/20) * 100, 4)
            return thdn
        result = input_table[key]
        self.log(f"log_out@{result}")
        return result


    @test_item_logger
    def _filter_batt_curr(self, data_list):
        data_len = len(data_list)
        target_data = [round(i, 1) for i in data_list]
        self.log("batt_curr_handle_data:{}".format(target_data))
        filter_dict = {}
        for value in target_data:
            count = target_data.count(value)
            filter_dict[value] = count
        print(filter_dict)
        max_count = max(filter_dict.values())
        for k, v in filter_dict.items():
            if v == max_count:
                rate = float(v) / data_len
                return k, v, rate
        return False, None, None

    @test_item_logger
    def dut_power_on(self, *args, **kwargs):
        delay_time = float(args[0])/1000
        self.rp2_device.rpc_call("mixdevice.relay", ['PSU_VCHG_TO_DUT'])
        self.rp2_device.rpc_call("mixdevice.relay", ['PSU_BATT_TO_DUT'])
        self.rp2_device.rpc_call("mixdevice.relay", ['USB_SEL_SW'])
        self.rp2_device.rpc_call("mixdevice.batteryEnable", [3800, 500])
        time.sleep(0.2)
        self.rp2_device.rpc_call("mixdevice.chargeEnable", [5000, 500])
        time.sleep(delay_time)
        result = self.rp2_device.rpc_call("mixdevice.measureVoltageByOdin", ["charger"])
        self.log(f"log_out@Delay {delay_time}s")
        return result

    @test_item_logger
    def fixture_power_off(self, *args, **kwargs):
        if_off = int(args[0])
        if if_off:
            self.rp2_device.rpc_call("mixdevice.reset")
        else:
            time.sleep(0.1)
        return ReturnDef.PASS_STRING


    @test_item_logger
    def measure_vcharge(self, *args, **kwargs):
        battery_volt = float(args[0])
        delay_time = float(args[1])/1000
        self.rp2_device.rpc_call("mixdevice.batteryEnable", [battery_volt, 500])
        time.sleep(delay_time)
        curr = self.rp2_device.rpc_call("mixdevice.measureCurrentByOdin", ['battery', '500ma'])
        return curr

    @test_item_logger
    def measure_volt_uvp_ovp(self, *args, **kwargs):
        volt = 0
        for i in range(3):
            volt = self.rp2_device.rpc_call("mixdevice.measureVoltageByOdin", ['battery'])
            if 90 <= volt <= 110:
                break
        return volt

    @test_item_logger
    def powerOn(self, *args, **kwargs):
        self.rp2_device.rpc_call("mixdevice.batteryEnable", [3800, 500])
        # 调用rpc_call函数，测量电池电流
        time.sleep(2)
        # 调用rpc_call函数，打开DUT电源
        self.rp2_device.rpc_call("mixdevice.measureCurrentByOdin", ['battery'])
        # 调用rpc_call函数，打开充电
        self.rp2_device.rpc_call("mixdevice.relay", ['PSU_VCHG_TO_DUT'])
        # 调用rpc_call函数，选择DMM_VIN1_SEL_SW
        self.rp2_device.rpc_call("mixdevice.chargeEnable", [5000, 500])
        self.rp2_device.rpc_call("mixdevice.measureCurrentByOdin", ['charger'])
        return ReturnDef.PASS_STRING

    @test_item_logger
    def usb_test(self, *args, **kwargs):
        print("****************************usb_test**********************************")
        self.rp2_device.rpc_call("mixdevice.relay", ['USB_SEL_SW'])
        time.sleep(1)
        # return_code, stdout, stderr = runShell.run_shell_with_timeout("diskutil list external")
        # print("return_code: {}\nstdout: {}\n stderr: {}\n".format(return_code, stdout, stderr))
        total = 0
        start_time = time.time()
        while True:
            if (time.time() - start_time) > 10:
                return False
            try:
                total, _, _ = shutil.disk_usage("/Volumes/RTTECH")
                print("USB Storage total Size: {}GB".format(round(total / 1024 / 1024 / 1024, 3)))
                break
            except Exception as e:
                print(e)
                pass
            time.sleep(1)
        assert total >= 15029999360
        return True

    @test_item_logger
    def scan_device(self, *args, **kwargs):
        from rtRP2.rp2Device import Rp2Device
        print("****************************scan_device**********************************")
        self.rp2_device.rpc_call("mixdevice.batteryEnable", [3800, 500])
        self.rp2_device.rpc_call("mixdevice.relay", ['PSU_BATT_TO_DUT'])
        self.rp2_device.rpc_call("mixdevice.relay", ['DUT_PCM_SEL_SW'])
        time.sleep(1)
        iicDev = Rp2Device("/dev/cu.usbmodemiic1", 11500, None, True)
        iicDev.init()
        iicDev._pyb.exec_("from MixDevice import *")
        time.sleep(1)
        print("*" * 50)
        res = iicDev._pyb.exec_("print(base_i2c_ch0.scan())")
        print(res)
        assert '85' in str(res)
        print("*" * 50)
        iicDev.deinit()
        return True
		
    @test_item_logger
    def curr_test(self, *args, **kwargs):
        return self.rp2_device.rpc_call("mixdevice.current_measure", [])

    @test_item_logger
    def volt_test(self, *args, **kwargs):
        netName_list = args[0]['netName_list']
        delay_ms = args[0]['delay_ms']

        for net in netName_list:
            self.rp2_device.rpc_call("mixdevice.relay", [net])
        time.sleep(delay_ms / 1000)
        voltage = self.rp2_device.rpc_call("mixdevice.voltage_measure", [])
        for net in netName_list:
            self.rp2_device.rpc_call("mixdevice.relay", [net, 'DISCONNECT'])
        return  voltage

    @test_item_logger
    def led_curr_test(self, *args, **kwargs):
        netName_list = args[0]['netName_list']
        curr_ma = args[0]['curr_ma']
        volt_mv = args[0]['volt_mv']
        netName = args[0]['netName']
        delay_ms = args[0]['delay_ms']
        for net in netName_list:
            self.rp2_device.rpc_call("mixdevice.relay", [net])
        self.rp2_device.rpc_call("mixdevice.ccs_svs_setup", [curr_ma, volt_mv])
        self.rp2_device.rpc_call("mixdevice.relay", [netName])
        time.sleep(delay_ms / 1000)
        current = self.rp2_device.rpc_call("mixdevice.current_measure", [])
        self.rp2_device.rpc_call("mixdevice.ccs_svs_setup", [0, 10])
        for net in netName_list:
            self.rp2_device.rpc_call("mixdevice.relay", [net, 'DISCONNECT'])
        self.rp2_device.rpc_call("mixdevice.relay", [netName, 'DISCONNECT'])
        return current

    def _pull_and_transfer_rawwav(self, type, dir_name):
        try:
            self.rp2_device.deinit()
            ori_path = f"D:\\vault\\{dir_name}"
            if not os.path.exists(ori_path):
                os.makedirs(ori_path, exist_ok=True)
            slot_path = f"D:\\vault\\{dir_name}\\slot{self.site}"
            if not os.path.exists(slot_path):
                os.makedirs(slot_path, exist_ok=True)

            raw_path = f"{slot_path}\\{type}_raw.wav"
            pull_cmd = f"mpremote connect com{100+int(self.site)} cp :/sdcard/raw.wav {raw_path}"

            self.log(f"Send Shell cmd:{pull_cmd}")
            return_code, resp, error = self.run_shell.run_shell_with_timeout(pull_cmd, 20)
            self.log(f"Return Code:{return_code}")
            self.log(f"BMT CMD Response:{resp}")
            self.log(f"Error:{error}")
            self.rp2_device.init()
            self.rp2_device.rpc_call("baseboard.set_calibration_mode", ['cal'])
            if not os.path.exists(raw_path):
                return False
            return raw_path
        except Exception as e:
            self.log(f"FAIL: {e}")
            return False

    @test_item_logger
    def save_raw_wav(self, *args, **kwargs):
        type, rms, thdn = args
        rms = round(rms, 1)
        thdn = round(thdn, 1)
        raw_path = self._pull_and_transfer_rawwav(type, "mic_wav")
        if not raw_path:
            return "--FAIL--Get raw wav Fail"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        file_name = f"{timestamp}_{type}_{rms}_{thdn}_{self._sn}_raw"
        if type == "VPU":
            sample_rate = 96000
        else:
            sample_rate = 48000
        resp = self._over_write_rawwav(raw_path, type, sample_rate, file_name)
        if not resp:
            return "--FAIL--Overwrite raw wav Fail"
        return ReturnDef.PASS_STRING

    def _over_write_rawwav(self, file_input, type, sample_rate=48000, file_name=None):
        try:
            with wave.open(file_input, 'rb') as wav_file:
                params = wav_file.getparams()
                n_frames = params.nframes  # 总帧数
                frames = wav_file.readframes(n_frames)

            if not file_name:
                file_output = os.path.dirname(file_input) + f"\\{type}_noise.wav"
            else:
                file_output = os.path.dirname(file_input) + f"\\{file_name}.wav"

            with wave.open(file_output, 'wb') as wav_out:
                wav_out.setnchannels(1)
                wav_out.setsampwidth(2)
                wav_out.setframerate(sample_rate)
                wav_out.setcomptype("NONE", "not compressed")
                wav_out.writeframes(frames)

            if not os.path.exists(file_output):
                return False
            return file_output
        except Exception as e:
            self.log(f"FAIL: {e}")
            return False

    def _calculate_a_weighting(self, frequencies):
        f = frequencies
        f_sq = f ** 2
        numerator = (12194 ** 2) * f_sq ** 2
        denominator = (f_sq + 20.6 ** 2) * np.sqrt((f_sq + 107.7 ** 2) * (f_sq + 737.9 ** 2)) * (f_sq + 12194 ** 2)
        a_db = 20 * np.log10(numerator / denominator) + 2.0
        a_linear = 10 ** (a_db / 20.0)
        a_linear = np.nan_to_num(a_linear, nan=0.0, posinf=0.0, neginf=0.0)
        return a_linear

    def _compute_a_weighted_spl(self, file_path):
        try:
            sample_rate, data = wavfile.read(file_path)
            if data.ndim > 1:
                data = data.mean(axis=1)
            if data.dtype == np.int16:
                data = data / 32768.0
            elif data.dtype == np.int32:
                data = data / 2147483648.0
            elif data.dtype == np.uint8:
                data = (data - 128) / 128.0

            data = data - np.mean(data)

            nperseg = 4096  # 分段长度
            freqs, psd = signal.welch(data, fs=sample_rate, window='hann', nperseg=nperseg, average='mean')
            a_weights = self._calculate_a_weighting(freqs)
            weighted_psd = psd * (a_weights ** 2)
            total_power = np.trapz(weighted_psd, freqs)

            # vrms_volts = np.sqrt(total_power) * 1000
            # self.log(f"log_out@vrms_volts: {vrms_volts} mV")
            # square = np.square(data)
            # mean_square = np.mean(square)
            # vrms = np.sqrt(mean_square) * 1000
            # self.log(f"log_out@vrms: {vrms} mV")

            reference_pressure = 20e-6  # 20微帕
            spl = 10 * np.log10(total_power / (reference_pressure ** 2))
            return round(spl, 3)
        except Exception as e:
            self.log(f"FAIL: {e}")
            return False

    @test_item_logger
    def calculate_a_weight(self, *args, **kwargs):
        type = args[0]
        if type not in ("VPU", "MIC1"):
            return "--FAIL--Wrong audio type"
        raw_path = self._pull_and_transfer_rawwav(type, "audio_wav")
        if not raw_path:
            return "--FAIL--Get raw wav Fail"
        noise_path = self._over_write_rawwav(raw_path, type, 48000)
        if not noise_path:
            return "--FAIL--Overwrite raw wav Fail"
        spl = self._compute_a_weighted_spl(noise_path)
        if not spl:
            return "--FAIL--Calculate A-Weight spl Fail"
        self.log(f"log_in@Compute Noise Data in path '{noise_path}' with A-Weight filter...")
        self.log(f"log_out@Result = {spl} dB(A)")
        return spl