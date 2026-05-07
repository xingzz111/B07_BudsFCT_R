import os
import re
import time
import json
import subprocess
from threading import Timer
from rtlib.utility import Unit
from rtlib.utility import ReturnDef
from rtlib.utility import handle_response
from rtlib.ictmes import MesSN, UploadMES


class common(object):

    rpc_public_api = [
        'start_test', 'end_test', 'reset', 'delay', 'get_scan_sn', 'query_mac_by_sn', 'station_name', 'fw_version',
        'slot_id', 'fixture_id', 'vendor_id', 'get_value_for_key', 'relay', 'check_uop', 'send_data', 'charge_output',
        'battery_output', 'charger_measure', 'battery_measure', 'dmm_measure','dmm_measure_voltage', 'set_io_switch',
        'mult_measure_bat_curr', 'disable_battery_output', 'disable_charge_output'
    ]

    def __init__(self, xobjects):
        self.xobjects = xobjects
        self.mixrpc = xobjects["mix_dev_rpc"]
        self.site = xobjects.get('site')
        self.publisher = xobjects.get('cb_pub')
        self.buff_dict = {}
        
    def log(self, message):
        if self.publisher:
            print(message)
            msg = '[{}] '.format(message)
            self.publisher.publish(msg)

    def start_test(self, *args, **kwargs):
        return ""

    def end_test(self, *args, **kwargs):
        self.reset()
        return ""

    def delay(self, *args, **kwargs):
        if len(args) != 1:
            return ReturnDef.MISS_PARAMETER
        time.sleep(float(args[0]) / 1000)
        return ReturnDef.PASS_STRING

    def rpc_call(self, *args, **kwargs):
        if len(args) < 1:
            return "ReturnDef.MISS_PARAMETER"
        method = args[0]
        rpc_args = args[1].split(":") if len(args) == 2 else None
        bRet = self.mixrpc.rpc_call(method, rpc_args)
        if isinstance(bRet,(int,float,str,bool)):
            return bRet
        else:
            print(bRet)
            return False

    def station_name(self, *args, **kwargs):
        station_name = args[0]
        return station_name

    def fixture_id(self, *args, **kwargs):
        fixture_id = self.mixrpc.rpc_call("baseboard.fixtureID")
        if fixture_id:
            return fixture_id
        return ReturnDef.FAIL_STRING


    def slot_id(self, *args, **kwargs):
        slot_id = "slot" + str(self.site + 1)
        return slot_id

    def vendor_id(self, *args, **kwargs):
        return "OSSNS"


    def reset(self, *args, **kwargs):
        bRet = self.mixrpc.rpc_call("mixdevice.reset")
        self.dis_charge()
        return bRet

    def loadIoMap(self, *args, **kwargs):
        bRet = self.mixrpc.rpc_call("mixdevice.loadIoMap")
        return bRet

    def fw_version(self, *args, **kwarg):
        """
        return: dict "MIX_FW_PACKAGE":"xxx",
        """
        bRet = self.mixrpc.rpc_call("mixdevice.fw_version")
        return bRet

    def relay(self, *args, **kwargs):
        """
        set io bit by iomap
        org:
            relay(self, net, switch="CONNECT")
        Args:
            net:         string; net of io table.
            switch:      string; switch name; CONNECT/DISCONNECT
            duration:    float; delay for millisecond
        Returns:    
            bool;        True/False
        Examples:
                mixdevice.relay("I2C_PMU_TO_XAVIER","CONNECT")
        """
        if len(args) < 1:
            return ReturnDef.MISS_PARAMETER
        netName = str(args[0])
        switch = str(args[1]) if len(args) == 2 else "CONNECT"
        bRet = self.mixrpc.rpc_call("mixdevice.relay", netName, switch)
        if "True" in bRet:
            return ReturnDef.PASS_STRING
        return ReturnDef.FAIL_STRING

   
    def set_io_switch(self, *args, **kwargs):
        io_list = json.dumps(args[0])
        bRet = self.mixrpc.rpc_call("baseboard.set_io_switch", io_list)
        return bRet


    def charge_output(self, *args, **kwargs):
        if len(args) != 2:
            return ReturnDef.MISS_PARAMETER
        curr_limit = float(args[0])
        volt = float(args[1])
        bRet = self.mixrpc.rpc_call("mixdevice.charge_output", curr_limit, volt)
        return bRet
    

    def battery_output(self, *args, **kwargs):
        if len(args) != 2:
            return ReturnDef.MISS_PARAMETER
        curr_limit = float(args[0])
        volt = float(args[1])
        bRet = self.mixrpc.rpc_call("mixdevice.battery_output", curr_limit, volt)
        return bRet


    # def psu_measure(self, _type, _module, scope=None):
    def psu_measure(self, *args, **kwargs):
        if len(args)!=2:
            return ReturnDef.MISS_PARAMETER
        measure_type, measure_modle = str(args[0]).split(":")
        scope = str(args[1]) if len(args) == 2 else None
        assert(measure_type in ("curr", "volt"))
        assert(measure_modle in ("battery" ,"charger"))
        bRet = self.mixrpc.rpc_call("mixdevice.psu_measure", measure_type, measure_modle, scope)
        if isinstance(bRet,list):
            value, unit = bRet
            final_unit = kwargs.get("unit")
            if not final_unit:
                if measure_type == "curr":
                    final_unit = 'mA'
                else:
                    final_unit = 'mV'
            return Unit.convert_unit(value, unit, str(final_unit))
        else:
            return ReturnDef.FAIL_STRING
    
    @handle_response
    def charger_measure(self, *args, **kwargs):
        if len(args) != 1:
            return ReturnDef.MISS_PARAMETER
        measure_type = str(args[0]) 
        assert(measure_type in ("curr", "volt"))
        bRet = self.mixrpc.rpc_call("mixdevice.psu_measure", measure_type, "charger")
        if isinstance(bRet, list):
            value, unit = bRet
            final_unit = kwargs.get("unit")
            if not final_unit:
                if measure_type == "curr":
                    final_unit = 'mA'
                else:
                    final_unit = 'mV'
            return Unit.convert_unit(value, unit, str(final_unit))
        else:
            return ReturnDef.FAIL_STRING
        

    def battery_measure(self, *args, **kwargs):
        if len(args) != 2:
            return ReturnDef.MISS_PARAMETER
        measure_type = str(args[0]) 
        scope = str(args[1])
        assert(measure_type in ("curr", "volt"))
        bRet = self.mixrpc.rpc_call("mixdevice.psu_measure", measure_type, "battery",scope)
        if isinstance(bRet, list):
            value, unit = bRet
            final_unit = kwargs.get("unit")
            if not final_unit:
                if measure_type == "curr":
                    final_unit = 'mA'
                else:
                    final_unit = 'mV'
            return Unit.convert_unit(value, unit, str(final_unit))
        else:
            return ReturnDef.FAIL_STRING


    def dmm_measure(self, *args, **kwargs):
        scope = "7000mv"
        if len(args) == 1:
            scope = str(args[0])
        assert(scope in ("10mv", "100mv", "1000mv","7000mv"))
        bRet = self.mixrpc.rpc_call("mixdevice.dmm_measure", scope)
        if isinstance(bRet, list):
            volt, unit = bRet
            final_unit = kwargs.get("unit")
            if not final_unit:
                final_unit = 'mV'
            return Unit.convert_unit(volt, unit, str(final_unit))
        else:
            return ReturnDef.FAIL_STRING


    def query_mac_by_sn(self, *args, **kwargs):
        sn = str(args[0])
        mes_sn = MesSN()
        mac, error_msg = mes_sn.get_mac(sn)
        self.log("GET: MAC:{} by SN:{}".format(mac, sn))
        if not mac:
            return ReturnDef.FAIL_STRING
        return mac

    def get_scan_sn(self, *args, **kwargs):
        sn = str(args[0])
        return sn

    def fixture_eeprom_write(self, *args, **kwargs):
        return "Not implement"


    def fixture_eeprom_read(self, *args, **kwargs):
        return "Not implement"

 
    def dmm_measure_voltage(self, *args, **kwargs):
        netName = str(args[0])
        scope = "7000mv"
        assert(scope in ("10mv", "100mv", "1000mv","7000mv"))

        self.mixrpc.rpc_call("mixdevice.relay", netName, "CONNECT")
        time.sleep(0.1)
        bRet = self.mixrpc.rpc_call("mixdevice.dmm_measure", scope)
        self.mixrpc.rpc_call("mixdevice.relay", netName, "DISCONNECT")
        time.sleep(0.1)
        self.mixrpc.rpc_call("mixdevice.relay", "DMM_MUX_DISCHARGE", "CONNECT")
        self.mixrpc.rpc_call("mixdevice.relay", "DMM_CH1_DIV2", "CONNECT")
        time.sleep(0.1)
        self.mixrpc.rpc_call("mixdevice.relay", "DMM_MUX_DISCHARGE", "DISCONNECT")
        self.mixrpc.rpc_call("mixdevice.relay", "DMM_CH1_DIV2", "DISCONNECT")
        time.sleep(0.1)
        if isinstance(bRet, list):
            volt, unit = bRet
            unit = "mV" if unit.lower() == "mv" else "mV"
            if volt:
                volt = float(volt)
            else:
                return "--FAIL-- measure voltage failed"
            final_unit = kwargs.get("unit", None)
            if not final_unit:
                final_unit = 'mV'
            return Unit.convert_unit(volt, unit, str(final_unit))
        else:
            return ReturnDef.FAIL_STRING

 
    def get_value_for_key(self, *args, **kwargs):
        key = str(args[0])
        if not self.buff_dict:
            return ReturnDef.FAIL_STRING
        value = self.buff_dict.get(key, ReturnDef.FAIL_STRING)
        return value



    def check_uop(self, *args, **kwargs):
        sn = str(args[0])
        mes = UploadMES()
        state, resp = mes.check_data(sn)
        if not state:
            self.log("check uop failed,get data from MES failed")
            return ReturnDef.FAIL_STRING
        uop_result = resp.get("RESULT")
        result_info = resp.get("RESULT_INFO")
        if uop_result == "OK":
            return  ReturnDef.PASS_STRING
        else:
            self.log("MES data:{}".format(json.dumps(resp)))
            return "--FAIL--{}".format(result_info)


    def send_data(self, *args, **kwargs):
        sn = args[0]
        fixture_id = "OSED6120241107001"
        mes = UploadMES()
        # sn, test_data, test_result, fixture_id
        state, resp = mes.send_data(sn,[],"PASS", fixture_id)
        if not state:
            self.log("check uop failed,get data from MES failed")

        uop_result = resp.get("RESULT")
        result_info = resp.get("RESULT_INFO")
        if uop_result == "OK":
            return ReturnDef.PASS_STRING
        else:
            self.log("MES data:{}".format(json.dumps(resp)))
            return "--FAIL--{}".format(result_info.replace(",",";"))

    def mult_measure_bat_curr(self, *args, **kwargs):
        count = int(args[0])
        sample_rate = int(args[1])
        self.mixrpc.rpc_call("psu.set_measure_path","battery", "ch1", "50ma")
        curr = self.mixrpc.rpc_call("psu.get_raw_samples_cal", "ch1", count, sample_rate, timeout_ms=20000)
        final_unit = kwargs.get("unit")
        if not final_unit:
            final_unit = 'mA'
        return Unit.convert_unit(curr, "mA", str(final_unit))

    def disable_battery_output(self, *args, **kwargs):
        self.mixrpc.rpc_call("psu.disable_battery_output")
        return ReturnDef.PASS_STRING

    def disable_charge_output(self, *args, **kwargs):
        self.mixrpc.rpc_call("psu.disable_charger_output")
        return ReturnDef.PASS_STRING

    def dis_charge(self):
        self.mixrpc.rpc_call("mixdevice.relay", "CURRENT_SOURCE_TO_DISCHARGE", "CONNECT")
        self.mixrpc.rpc_call("mixdevice.relay", "DMM_CH1_DIV2", "CONNECT")
        time.sleep(0.1)
        self.mixrpc.rpc_call("mixdevice.relay", "CURRENT_SOURCE_TO_DISCHARGE", "DISCONNECT")
        self.mixrpc.rpc_call("mixdevice.relay", "DMM_CH1_DIV2", "DISCONNECT")
        time.sleep(0.1)


    