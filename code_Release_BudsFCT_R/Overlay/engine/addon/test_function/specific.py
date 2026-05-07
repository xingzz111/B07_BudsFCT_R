import os
import re
import time
import json

import asyncio

from rtlib.utility import retry_with_delay,ReturnDef
from rtlib.taskScheduler import ConcurrencyAwareAsyncMonitor, SequentialTaskScheduler, InterActiveMonitor


class specific(object):

    rpc_public_api = [
        'restore_2700', 'restore_8300', 'cal_8300', 'get_value_for_key', 'uart_relay', 'check_8300_fw', 'key_test', 'check_8300_fw_flag',
        'compare', 'restore', 'read_fw_version', 'switch_app', 'disablecal8300power', 'send_get_adc'
    ]

    def __init__(self, xobjects):
        self.xobjects = xobjects
        self.site = xobjects.get('site')
        # self.mixrpc = xobjects["mix_dev_rpc"]
        self.rp2_device = xobjects["rp2_device"]
        self.hardware = xobjects.get('hardware', None)
        self.rp2_device = xobjects["rp2_device"]
        self.dutCommand = xobjects.get('dutCommand', None)
        self.sg = xobjects.get('sg', None)
        self.publisher = xobjects.get('cb_pub')
        
        self.restore_2700_dict = {}
        self.restore_8300_dict = {}
        self._taskfinished = asyncio.Event()
        # self._task2700 = asyncio.Event()
        # self._task8300 = asyncio.Event()
        
    def log(self, message):
        if self.publisher:
            print(message)
            msg = '[{}] '.format(message)
            self.publisher.publish(msg)

    def disablecal8300power(self, *args, **kwargs):
        self.rp2_device.rpc_call("mixdevice.batteryDisable")
        self.hardware.relay("ODIN_BATT_TO_DUT_TP10_1P05V","DISCONNECT")
        self.hardware.setStateByName("DUT_TP31_B00TMODE_ON", "GPIO_1V7",0)
        self.hardware.relay("PP1V7_VDDO_TO_DUT_TP41_VDDO", "DISCONNECT")
        time.sleep(1)
        return ReturnDef.PASS_STRING

    def get_value_for_key(self, *args, **kwargs):
        key = str(args[0])
        fw_type = str(args[1])
        _buff_dict = None
        if fw_type == "restore_2700":
            _buff_dict = self.restore_2700_dict
        elif fw_type == "restore_8300":
            _buff_dict = self.restore_8300_dict
        if not _buff_dict:
            return ReturnDef.FAIL_STRING
        value = _buff_dict.get(key, ReturnDef.FAIL_STRING)
        return value


    def uart_relay(self, *args, **kwargs):
        if len(args) != 2:
            return ReturnDef.MISS_PARAMETER
        isSingle = str(args[0])
        isConnect = int(args[1])
        result = self.hardware.uartSwitch(isSingle, isConnect)
        return ReturnDef.PASS_STRING if result else ReturnDef.FAIL_STRING


    def check_8300_fw(self, *args, **kwargs):
        # if fw == expect fw : skip restore 8300 and cal
        # if fw == "00.00.00.00" normal to do restore 8300 and cal
        # if fe != "00.00.00.00" and fw(old fw) to do restore erase 8300 and cal
        expect_fw = str(args[0])
        cmd = "[get_8300_version,]"
        expect_keyword = "Fw1Version"
        # self.dutCommand.send("dummy")
        result = self.dutCommand.send_read(cmd, expect_keyword)
        if result:
            if self.dutCommand.parse_response(expect_fw):
                return "current"
            elif self.dutCommand.parse_response(r"00.00.00"):
                return "00.00.00"
            else:
                return "old"
        return ReturnDef.FAIL_STRING


    def check_8300_fw_flag(self,*args, **kwargs):
        _fw_version = str(args[0])
        if _fw_version == "current":
            return "FALSE"
        else:
            return "TRUE"

    def key_test(self, *args, **kwargs):
        expect_key_word = str(args[0])
        for i in range(2):
            self.hardware.dutKeyPressAndrelease(0.5)
            result = self.dutCommand.read_until(expect_key_word, 5000)
            if result:
                return result
        return ReturnDef.FAIL_STRING


    def switch_app(self, *args, **kwargs):
        cmd, expect_keyword, terminator = str(args[0]).split("@")
        timeout1, timeout2 = str(args[1]).split("@")
        timeout1 = int(timeout1)
        timeout2 = int(timeout2)
        self.dutCommand.read_string()
        try:
            result = self.dutCommand.send_read_key_words_doe(cmd, expect_keyword, terminator, timeout1, timeout2)
            if result:
                return terminator
        except Exception as e:
            self.log(e)
        return ReturnDef.FAIL_STRING

    def send_get_adc(self, *args, **kwargs):
        cmd,expect_keyword = str(args[0]).split("@")
        pattern = str(args[1]) if len(args) ==2 else None
        result = False
        for i in range(3):
            result = self.dutCommand.send_read(cmd, expect_keyword, pattern)
            if result:
                break
            else:
                self.hardware.dutPowerOn()
                self.dutCommand.read_string()
        return result if result else ReturnDef.FAIL_STRING


    
    def compare(self, *args, **kwargs):
        _new,_old = str(args[0]).split("@")
        need_convert = args[1] if len(args) ==2 else None
        self.log("first:{}".format(_new))
        self.log("second:{}".format(_old))
        if need_convert:
            _new = self._transforming_string(_new)
            self.log("transforming first:{}".format(_new))
        return ReturnDef.PASS_STRING if _new == _old else ReturnDef.FAIL_STRING

    def read_fw_version(self,*args, **kwargs):
        self.restore_2700_dict = {}
        self.restore_8300_dict = {}
        fw_2700 = self.dutCommand.send_read("[get_2700_version,]", "Fw0Version", "Fw0Version:([\d.]+)")
        fw_8300 = self.dutCommand.send_read("[get_8300_version,]", "Fw1Version", "Fw1Version:([\d.]+)")
        if not fw_2700:
            fw_2700 = "NULL"
        self.restore_2700_dict["fw_2700"] = fw_2700
        if not  fw_8300:
            fw_8300 = "NULL"
        self.restore_8300_dict["fw_8300"] = fw_8300
        if fw_2700 == fw_8300 == "NULL":
            fw_version = "NULL"
        else:
            fw_version = f"{fw_2700}/{fw_8300}"
        return fw_version

    def restore(self, *args, **kwargs):
        self.restore_2700_dict = {}
        self.restore_8300_dict = {}
        self._taskfinished.clear()
        bt_address = str(args[0])
        fw_2700_bin,fw_8300_bin = str(args[1]).split("@")
        self.restore_2700_dict["result"] = False
        self.restore_2700_dict["complete"] = False

        self.restore_8300_dict["result"] = False
        self.restore_8300_dict["complete"] = False

        self.hardware.chargerShutDownAndUartSwitch()
        time.sleep(3)
        asyncio.run(self._restore(bt_address, fw_2700_bin, fw_8300_bin))
        self.log("restore run ...")

        start_time = time.time()
        while time.time() - start_time < 2:
            # self.log("loop ...")
            if self.restore_2700_dict["complete"] and self.restore_8300_dict["complete"]:
                break
            time.sleep(0.2)
        for i in range(2):
            if self.restore_2700_dict["complete"] and self.restore_2700_dict["result"] == False:
                self.restore_2700_dict = {}
                self.restore_2700_dict["result"] = False
                self.restore_2700_dict["complete"] = False
                self.log("restore 2700 run again...{}".format(i +i))
                self.hardware.chargerShutDownAndUartSwitch()
                time.sleep(3)
                asyncio.run(self._restore2700(bt_address, fw_2700_bin, fw_8300_bin))
               
                start_time = time.time()
                while time.time() - start_time < 2:
                    # self.log("loop ...")
                    if self.restore_2700_dict["complete"] and self.restore_8300_dict["complete"]:
                        break
                    time.sleep(0.2)
        # time.sleep(3)
        self.restore_2700_dict["resrore2700Result"] = ReturnDef.PASS_STRING if self.restore_2700_dict["result"] else ReturnDef.FAIL_STRING
        self.restore_8300_dict["resrore8300Result"] = ReturnDef.PASS_STRING if self.restore_8300_dict["result"] else ReturnDef.FAIL_STRING

        print(self.restore_2700_dict)
        print(self.restore_8300_dict)

        if self.restore_2700_dict["result"] and self.restore_8300_dict["result"]:
            return ReturnDef.PASS_STRING
        return ReturnDef.FAIL_STRING

    async def _restore(self, bt_address,fw_2700_bin, fw_8300_bin):
        # bt_address = "AABBCCDDEEFF"
        # fw_2700_bin,fw_8300_bin = "evt_encrypt_1.1.0.2.bin","PanamaManufacturing_3.2.3.hex"
        # await asyncio.gather(self.restore_2700(bt_address, fw_2700_bin))
        # await asyncio.gather(self.restore_8300(fw_8300_bin))


        await asyncio.gather(self.restore_2700(bt_address, fw_2700_bin), self.restore_8300(fw_8300_bin))


    async def _restore2700(self, bt_address,fw_2700_bin, fw_8300_bin):
        # bt_address = "AABBCCDDEEFF"
        # fw_2700_bin,fw_8300_bin = "evt_encrypt_1.1.0.2.bin","PanamaManufacturing_3.2.3.hex"
        # await asyncio.gather(self.restore_2700(bt_address, fw_2700_bin))
        # await asyncio.gather(self.restore_8300(fw_8300_bin))


        await asyncio.gather(self.restore_2700(bt_address, fw_2700_bin))


###################################restore_2700#####################################################
    async def restore_2700(self, bt_address, app_bin):
        bt_address = self._transforming_string(bt_address)
        port = 90 + self.site

        _response = False
        # 初始化任务列表
        task_sequence = list()
        # _cmd = "D:/RestorePackage/burn_2700_v{}/burn_source.exe kill".format(self.site)
        # _sub_config = self._sub_task_config(_cmd)
        # task_sequence.append(_sub_config)
        # task_sequence.append(_sub_config)
        # task_sequence.append(_sub_config)
        # _cmd = "D:/RestorePackage/burn_2700_v{}/burn_source.exe run".format(self.site)
        # _sub_config = self._sub_task_config(_cmd)
        # task_sequence.append(_sub_config)
        # _cmd = ["D:/RestorePackage/burn_2700_v{}/burn_source.exe".format(self.site), "burn", "--port", f"{port}",
        #         "--app-bin", f"D:/RestorePackage/burn_2700_v1/{app_bin}", "--ota-bin",
        #         "D:/RestorePackage/burn_2700_v1/ota_boot_2700_20211216_5fca0c3e.bin", "--bt-address", bt_address,
        #         "--ble-address", bt_address, "--bt-name", "Orka BTE BT", "--ble-name", "Orka BTE LE", "--erase",
        #         "--auto-calib"]

        _cmd = ["D:/RestorePackage/burn_2700_v{}/burn_cli_v0.5.exe".format(self.site),
                "--app-bin", f"D:/RestorePackage/burn_2700_v1/{app_bin}",
                "--bt-address", bt_address,
                "--ble-address", bt_address, "--bt-name", "Orka BTE BT", "--ble-name", "Orka BTE LE",
                "--port", f"{port}",
                "--auto-calib"]

        _sub_task_config = self._sub_task_config(_cmd, timeout_s=120.0)
        _sub_task_config['filters'] = [("", self._restore_2700_callback)]
        task_sequence.append(_sub_task_config)

        try:
            # self.hardware.chargerShutDownAndUartSwitch()
            asyncio.gather(self._restore_2700_task(task_sequence))
        except Exception as e:
            self.log("restore 2700 exit")
        finally:
            self.log("restore 2700 finally ...")
        # while True:
        #     if self._task8300.is_set():
        #         break
        #     asyncio.sleep(1)
    
    def _restore_2700_callback(self, line):
        isResult = False
        if "EvWmPortOpenFailed" in line:
            self.log("burn 2700 PortOpenFailed")
            self.restore_2700_dict["result"] = False
            self.restore_2700_dict["complete"] = True
        if "EvWmSyncWait" in line:
            self.restore_2700_dict["SyncWait"] = True
            # power on 5V
            dt = self.hardware.chargerPowerOn(5000, 500, 3)
            volt = dt["chargerVolt"]
            curr = dt["chargerCurr"]
            self.restore_2700_dict.update(dt)
            if volt > 5020 or volt < 4980:
                self.log("2700 burn--power on 5v failed")
                self.log("2700 burn--power target volt limit is [4980,5020]mV, curr limit is [20,40]mA")
                isResult = True
                self.restore_2700_dict["result"] = False
                self.restore_2700_dict["complete"] = True
                self.log("Power On 5V failed all show exit")
        elif "Burn Success" in line:
            # success
            self.log("Burn Success***********************")
            self.restore_2700_dict["result"] = True
            # self.restore_2700_dict["complete"] = True
            # isResult = True
        elif "Calibration" in line:
            self.log("Calibrated Value***********************")
            cal_value = re.findall(r"Calibration:\s*(\d+)", line)
            cal_value = cal_value[0] if cal_value else "--FAIL--"
            self.restore_2700_dict["calibrated_value"] = cal_value
            self.restore_2700_dict["complete"] = True
            isResult = True
        elif "EvWmExitInvalid" in line:
            self.log("ExitInvalid :***********************")
            self.restore_2700_dict["result"] = False
            self.restore_2700_dict["complete"] = True
            isResult = True
        else:
            pass
        # self.restore_2700_dict["complete"] = isResult
        return isResult


    async def _restore_2700_task(self, task_sequence):

        # 初始化调度器
        scheduler = SequentialTaskScheduler(publisher=self.publisher)

        
        # 添加任务到队列
        for task_config in task_sequence:
            await scheduler.add_task(task_config)

        # 启动调度器
        scheduler_task = asyncio.create_task(scheduler.run())

        try:
            # 等待所有任务完成
            await scheduler.task_queue.join()
        except KeyboardInterrupt:
            self.log("\nKeyboardInterrupt...")
            await scheduler.stop()
        finally:
            # await scheduler_task
            asyncio.gather(scheduler_task)
            self._taskfinished.set()
            # self._task2700.set()
            await scheduler.stop()
            self.log("all task finished")

###################################restore_8300#####################################################
    async def restore_8300(self, app_bin):
        user_home = os.path.expanduser('~')
        _path = f"{user_home}/testerconfig/fixture_config.json"
        device = None
        with open(_path, 'r') as f:
            file = f.read()
            device = json.loads(file)
        device_sn_list = device.get("sn")
        if not device_sn_list:
            self.restore_8300_dict["result"] = False
            self.restore_8300_dict["complete"] = True
            return False
        usb_device = device_sn_list[self.site]
        # erase_cmd = ["C:/Program Files/SEGGER/JLink/JLink.exe", "-SelectEmuBySN", usb_device ,"-autoconnect", "1", "-device", "EZAIRO8300_SPI_FLASH_W25Q16JV", "-if", "swd", "-speed", "4000", "-commandfile", "D:/RestorePackage/JlinkTools/erase_flash.jlink"]
        program_cmd = ["C:/Program Files/SEGGER/JLink/JFlash.exe",f"-usb{usb_device}" ,"-jlinkdevicesxmlpathC:/Program Files/SEGGER/JLink/JLinkDevices", "-openprjC:/Program Files/SEGGER/JLink/barista_bringup.jflash", f"-openD:/RestorePackage/JlinkTools/{app_bin}", "-auto", "-exit"]
        # program_cmd =["D:/RestorePackage/JlinkTools/jlink_command.bat"]
        await asyncio.sleep(5)
        # power on for 8300 restore
        self.hardware.disconnect8300Power()
        await asyncio.sleep(2)
        _dt = self.hardware.jlinkPowerOn()
        self.restore_8300_dict.update(_dt)
        await asyncio.sleep(2)
        # if _dt and isinstance(_dt,dict):
        #     tp10Volt = _dt["TP10Volt"]
        #     tp10Curr = _dt["TP10Curr"]
        #     tp31Volt = _dt["TP10Volt"]
        #     tp41Volt = _dt["TP10Volt"]
        #     if not (1180 < tp10Volt < 1220 and 1.9 < tp10Curr < 10 and 1650 < tp31Volt < 1720 and 1680 < tp41Volt < 1720):
        #         self.log("Jlink power on failed")
        #         self.restore_8300_dict["result"] = False
        #         self.restore_8300_dict["complete"] = True
        #         return False
        # else:
        #     self.log("Jlink power on failed")
        #     self.restore_8300_dict["result"] = False
        #     self.restore_8300_dict["complete"] = True
        #     return False

        # 8300 restore
        start_time = time.time()
        self.log("8300 cmd: {}".format(program_cmd))
        monitor = InterActiveMonitor(program_cmd, None, 100, publisher=self.publisher)
        proc, stdout, stderr = await monitor.run()
        # self.log(proc, stdout, stderr)
        self.log("proc: {}, stdout: {}, stderr: {}".format(proc, stdout, stderr))

        ex_time = time.time() - start_time
        self.log("--restore 8300 ex_time: {}".format(ex_time))
        self.restore_8300_dict["resrore8300Time"] = ex_time
        if ex_time > 20:
            self.restore_8300_dict["result"] = True
        # self.log("abc"*100)
        # while True:
        #     if self._task2700.is_set():
        #         self.log("_task2700 is set")
        #         break
        #     asyncio.sleep(1)

        self.hardware.disconnect8300Power()
        await asyncio.sleep(0.5)
        self.hardware.cal8300PowerOn()
        await asyncio.sleep(3)

        while not self._taskfinished.is_set():
            await asyncio.sleep(1)

        # start_time = time.time()
        # while time.time() - start_time < 40:
        #     if self._task8300.set() and self._task2700.set():
        #         break

        cal_8300_flag = True
        time1 = time2 = time3 = "--FAIL--"

        self.rp2_device.rpc_call("mixdevice.measure_pulse", 1, 3)
        r = self.rp2_device.rpc_call("mixdevice.measure_pulse", 50, 5)
        if r and isinstance(r,dict):
            time1 = r.get(1, 0)
            time2 = r.get(2, 0)
            time3 = r.get(3, 0)
            if 3000 < time1 < 3300 and 3000 < time1 < 3300 and 3000 < time1 < 3300:
                cal_8300_flag = False

        if cal_8300_flag:
            for i in range(2):
                self.hardware.disconnect8300Power()
                await asyncio.sleep(0.5)
                self.hardware.cal8300PowerOn()
                await asyncio.sleep(0.5)
                self.rp2_device.rpc_call("mixdevice.measure_pulse", 1, 3)
                r = self.rp2_device.rpc_call("mixdevice.measure_pulse", 50, 5)
                if r and isinstance(r,dict):
                    time1 = r.get(1, 0)
                    time2 = r.get(2, 0)
                    time3 = r.get(3, 0)
                    if 3000 < time1 < 3300 and 3000 < time1 < 3300 and 3000 < time1 < 3300:
                        break
            # self._task8300.set()
            
        self.restore_8300_dict["delay1"] = time1
        self.restore_8300_dict["delay2"] = time2
        self.restore_8300_dict["delay3"] = time3



        self.restore_8300_dict["complete"] = True

    
    def cal_8300(self, *args, **kwargs):
        _fw_version = args[0]
        self.dutCommand.open_uart()
        self.hardware.relay("UART_FT232_TO_DUT_HALF_DUPLEX")
        # if need cal, 
        if _fw_version == "current":
            time.sleep(1)
            return "--SKIP--8300 has been calibrated"
        # 'output_sg_wave', 'disable_sg_wave'
        self.hardware.setStateByName("DUT_TP15_CAL_SQUWAV", "SIGNAL_GENERATOR", 1)
        self._output_sg_wave()
        time.sleep(1)

        # self.dutCommand.send("dummy")
        check_8300_version_before_cal = self.dutCommand.send_read("[get_8300_version,]", "Fw1Version", r"Fw1Version:([\d.]+)")
        self.restore_8300_dict["check_8300_version_before_cal"] = check_8300_version_before_cal
        start_trim = self.dutCommand.send_read_key_words(cmd="[start_trim,]",expect_keyword="CLK trim start",terminator="8300 CLK trim SUCCESS!",timeout1=2000, timeout2=60000)
        self.dutCommand.send_read("[stop_trim,]","CLK trim stop")
        if not start_trim or "8300 CLK trim SUCCESS" not in start_trim:
            return "--FAIL--start_trim fail"
        
        self.dutCommand.send_read_key_words(cmd="[switch_app,]", expect_keyword="switch panama SUCCESS!", terminator="Rst8300",timeout1=20000, timeout2=2000)
        
        # self.dutCommand.send("dummy")
        check_8300_version_after_cal = self.dutCommand.send_read("[get_8300_version,]", "Fw1Version", r"Fw1Version:([\d.]+)")
        self.restore_8300_dict["check_8300_version_after_cal"] = check_8300_version_after_cal
        self._disable_sg_wave()
        self.hardware.setStateByName("DUT_TP15_CAL_SQUWAV", "SIGNAL_GENERATOR", 0)
        if "8300 CLK trim SUCCESS" in start_trim:
            return "8300 CLK trim SUCCESS"
        return ReturnDef.FAIL_STRING        

    async def _restore_8300_check_connect(self, usb_device):
        conn_cmd = ["C:/Program Files/SEGGER/JLink/JLink.exe", "-SelectEmuBySN", usb_device ,"-device", "EZAIRO8300_SPI_FLASH_W25Q16JV", "-if", "swd",
                    "-speed", "4000", "-autoconnect", "1"]
        input_data = '''q\r\n
        '''
        monitor = InterActiveMonitor(conn_cmd, input_data, 10, publisher=self.publisher)
        for i in range(3):
            _dt = self.hardware.jlinkPowerOn1V2()
            self.restore_8300_dict.update(_dt)
            if _dt["batVolt"] > 1180 and _dt["batVolt"] < 1220 and _dt["batCurr"] > 1.9 and _dt["batCurr"] < 3:
                # success
                # _success = asyncio.run(self._restore_8300_check_connect())
                for j in range(3):
                    proc, stdout, stderr = await monitor.run()
                    if proc.returncode == 0:
                        response = stdout.decode().strip()
                        if "Cannot connect to target" not in response and "Cortex-M3 identified" in response:
                            return True
                        else:
                            _dt2 = self.hardware.chargerPowerOn(5000, 500, 6)
                            self.restore_8300_dict.update(_dt2)
                            continue
            else:
                continue
        return False
    
    async def _restore_8300_exe_cmd(self, cmd, timeout_s):
        monitor = InterActiveMonitor(cmd, None, timeout_s, publisher=self.publisher)
        return await monitor.run()
    

    def _output_sg_wave(self, *args, **kwargs):
        try:
            self.sg.open_device()
            self.sg.reset_device()
            self.sg.output_wave(1, 128, 1.8, 0.9, "SQUARE")
        except:
            return ReturnDef.FAIL_STRING
        return ReturnDef.PASS_STRING

    def _disable_sg_wave(self, *args, **kwargs):
        try:
            if not self.sg.is_open:
                self.sg.open_device()
            self.sg.reset_device()
            self.sg.close_device()
        except Exception as e:
            return ReturnDef.FAIL_STRING
        return ReturnDef.PASS_STRING

###################################Common function#####################################################

    def _transforming_string(self, input_str):
        bytes_list = [input_str[i:i +2] for i in range(0, len(input_str), 2)]
        swapped_bytes = [byte[0] + byte[1] for byte in bytes_list]

        swapped_bytes.reverse()
        return ''.join(swapped_bytes)

    def _sub_task_config(self, cmd, timeout_s=5):
        # task_sequence = list()
        sub_taks_config = dict()
        if isinstance(cmd, str):
            sub_taks_config.setdefault("command", cmd.split(" "))
        elif isinstance(cmd, list):
            sub_taks_config.setdefault("command", cmd)
        sub_taks_config.setdefault("timeout", timeout_s)
        return sub_taks_config


# s = specific({})
# ret = s.restore("AABBCCDDEEFF","evt_encrypt_1.1.0.2.bin@PanamaManufacturing_3.2.3.hex")
# print(ret)