import os
import re
import time
import json

import subprocess
from threading import Timer

from rtlib.utility import Unit
from rtlib.utility import ReturnDef
from rtlib.utility import handle_response

class specific(object):
    rpc_public_api = [
        'check_hall', 'check_button', 'check_led','check_esd','check_esd_specific'
    ]

    def __init__(self, xobjects):
        self.xobjects = xobjects
        self.mixrpc = xobjects["mix_dev_rpc"]
        self.site = xobjects.get('site')
        self.publisher = xobjects.get('cb_pub')
        self.common = xobjects.get('common', None)
        self.fixture_ctrl = xobjects.get('fixture_ctrl')
        self.buff_dict = {}
       

    def log(self, message):
        if self.publisher:
            print(message)
            msg = '[{}] '.format(message)
            self.publisher.publish(msg)

    

    # for charging PCB
    def dis_charge(self):
        self.mixrpc.rpc_call("mixdevice.relay", "CURRENT_SOURCE_TO_DISCHARGE", "CONNECT")
        self.mixrpc.rpc_call("mixdevice.relay", "DMM_CH1_DIV2", "CONNECT")
        time.sleep(0.1)
        self.mixrpc.rpc_call("mixdevice.relay", "CURRENT_SOURCE_TO_DISCHARGE", "DISCONNECT")
        self.mixrpc.rpc_call("mixdevice.relay", "DMM_CH1_DIV2", "DISCONNECT")
        time.sleep(0.1)

    def set_dac_output(self, *args, **kwargs):
        curr, volt = args[0].split(":")
        curr_gain = int(args[1])
        curr = float(curr)
        volt = float(volt)
        volt_a = 2500 - curr * curr_gain
        volt_b = 2500 - volt / 5
        self.mixrpc.rpc_call("baseboard.set_dac_output",0,volt_a)
        self.mixrpc.rpc_call("baseboard.set_dac_output",1,volt_b)

    def check_hall(self, *args, **kwargs):
        mode = str(args[0])
        self.common.relay("CURRENT_SOURCE_TO_DUT_TP21_VMCU")
        self.common.relay("CURRENT_SOURCE_OUTPUT_RANGE_2P5MA")
        self.common.relay("CURRENT_SOURCE_OUTPUT_POSITIVE_POLARITY")
        self.set_dac_output("1:3000", 100)
        #open MAG
        if mode == "ON":
            bRet = self.fixture_ctrl.magnet_enable()
            if bRet != ReturnDef.PASS_STRING:
                return "--FAILL--magnet_enable fail"
        else:
            bRet = self.fixture_ctrl.magnet_disable()
            if bRet != ReturnDef.PASS_STRING:
                return "--FAILL--magnet_disable fail"
        self.common.relay("DMM_TO_DUT_TP4_HALL_INT")
        time.sleep(0.5)
        bRet = self.mixrpc.rpc_call("mixdevice.dmm_measure", "7000mv")
        self.dis_charge()
        self.mixrpc.rpc_call("mixdevice.reset")
        if bRet and isinstance(bRet, list):
            volt = float(bRet[0])
            final_unit = kwargs.get("unit")
            if not final_unit:
                final_unit = 'mV'
            return Unit.convert_unit(volt,"mV",final_unit)
        return ReturnDef.FAIL_STRING

    def check_button(self, *args, **kwargs):
        mode = str(args[0])
        self.common.relay("DMM_TO_DUT_TP22_BUTTON")
        if mode == "ON":
            bRet = self.fixture_ctrl.cylinder_enable()
            if bRet != ReturnDef.PASS_STRING:
                return "--FAILL--cylinder_enable fail"
        else:
            bRet = self.fixture_ctrl.cylinder_disable()
            if bRet != ReturnDef.PASS_STRING:
                return "--FAILL--cylinder_disable fail"
        time.sleep(0.5)
        bRet = self.mixrpc.rpc_call("mixdevice.dmm_measure", "7000mv")
        self.common.relay("DMM_TO_DUT_TP22_BUTTON","DISCONNECT")
        self.dis_charge()
        self.mixrpc.rpc_call("mixdevice.reset")
        if bRet and isinstance(bRet, list):
            volt = abs(float(bRet[0]))
            final_unit = kwargs.get("unit")
            if not final_unit:
                final_unit = 'mV'
            return Unit.convert_unit(volt, "mV", final_unit)
        return ReturnDef.FAIL_STRING

    def check_led(self, *args, **kwargs):
        netName = str(args[0])
        netName2 = str(args[1])
        self.mixrpc.rpc_call("mixdevice.reset")
        self.common.relay(netName)
        self.common.relay("CURRENT_SOURCE_OUTPUT_RANGE_25MA")
        self.common.relay("CURRENT_SOURCE_OUTPUT_POSITIVE_POLARITY")
        self.common.relay("CURRENT_SOURCE_MEASURE_RANGE_50MA")
        self.common.relay("CURRENT_SOURCE_TO_DUT_TP23_VLED")
        self.common.relay(netName2)
        if "LED_RHI_R" in netName or "LED_LHI_R" in netName:
            self.set_dac_output("20:3600", 100)
        else:
            self.set_dac_output("5:3600", 100)
        self.common.relay("DMM_TO_CCS_V_M")
        time.sleep(0.5)
        bRet = self.mixrpc.rpc_call("mixdevice.dmm_measure", "7000mv")
        if bRet and isinstance(bRet, list):
            volt = float(bRet[0])
        else:
            return "--FAIL--measure voltage fail"
        self.common.relay(netName, "DISCONNECT")
        self.common.relay(netName2, "DISCONNECT")
        self.dis_charge()
        self.mixrpc.rpc_call("mixdevice.reset")
        final_unit = kwargs.get("unit")
        if not final_unit:
            final_unit = 'mV'
        return Unit.convert_unit(volt, "mV", final_unit)

    def check_esd(self, *args, **kwargs):
        netName = str(args[0])
        self.common.relay(netName)
        self.common.relay("DMM_DIV2")
        self.common.relay("CURRENT_SOURCE_OUTPUT_RANGE_2P5MA")
        self.common.relay("CURRENT_SOURCE_OUTPUT_POSITIVE_POLARITY")
        # 3000 volt 300 = 2500 -10000/5
        self.set_dac_output("1:10000", 100)  #current 1mA , Voltage 10V
        self.common.relay("DMM_TO_CCS_V_M")
        time.sleep(0.5)
        bRet = self.mixrpc.rpc_call("mixdevice.dmm_measure", "7000mv")
        self.common.relay(netName, "DISCONNECT")
        self.dis_charge()
        self.mixrpc.rpc_call("mixdevice.reset")
        print(bRet)
        if bRet and isinstance(bRet, list):
            volt = float(bRet[0]) * 2
            final_unit = kwargs.get("unit")
            if not final_unit:
                final_unit = 'mV'
            return Unit.convert_unit(volt, "mV", final_unit)
        return ReturnDef.FAIL_STRING

    def check_esd_specific(self, *args, **kwargs):
        netName = str(args[0])
        self.common.relay(netName)
        self.common.relay("DMM_DIV2")
        self.common.relay("CURRENT_SOURCE_OUTPUT_RANGE_250UA")
        self.common.relay("CURRENT_SOURCE_OUTPUT_POSITIVE_POLARITY")
        # 3000 volt 300 = 2500 -10000/5
        self.set_dac_output("0.05:3000", 10000)  #current 50UA , Voltage 3V
        self.common.relay("DMM_TO_CCS_V_M")
        time.sleep(1)
        bRet = self.mixrpc.rpc_call("mixdevice.dmm_measure", "7000mv")
        self.common.relay(netName, "DISCONNECT")
        self.dis_charge()
        self.mixrpc.rpc_call("mixdevice.reset")
        print(bRet)
        if bRet and isinstance(bRet, list):
            volt = float(bRet[0]) * 2
            final_unit = kwargs.get("unit")
            if not final_unit:
                final_unit = 'mV'
            return Unit.convert_unit(volt, "mV", final_unit)
        return ReturnDef.FAIL_STRING
