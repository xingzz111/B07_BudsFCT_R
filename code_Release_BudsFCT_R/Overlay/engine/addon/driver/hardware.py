import time

class HardWare(object):
    rpc_public_api = ['reset', 'relay', 'setStateByName', 'uartSwitch', 'chargerPowerOn', 'chargerShutDownAndUartSwitch',
                      'jlinkPowerOn1V2','jlinkPowerOn','dutKeyPressAndrelease', 'disconnect8300Power', 'cal8300PowerOn',
                      'dutPowerOn'
                      ]
    def __init__(self, rp2_device, publisher=None):
        self.rp2_device = rp2_device
        self.publisher = publisher


    def init(self, rp2_device, publisher=None):
        self.rp2_device.init()

    def reset(self):
        return self.rp2_device.rpc_call("mixdevice.reset")

    def relay(self, netName, switch="CONNECT"):
        assert switch in("CONNECT", "DISCONNECT")
        return self.rp2_device.rpc_call("mixdevice.relay", netName, switch)
    
    def setStateByName(self, x_name, y_name, state=1):
        assert state in (0, 1)
        return self.rp2_device.rpc_call("mixdevice.setStateByName", x_name, y_name, state)

    def batteryEnable(self, volt, curr_limit):
        return self.rp2_device.rpc_call("mixdevice.batteryEnable", volt, curr_limit)

    def chargeEnable(self, volt, curr_limit):
        return self.rp2_device.rpc_call("mixdevice.chargeEnable", volt, curr_limit)

    def measureVoltageByOdin(self, module, scope='5000mv'):
        assert module in ('charger', 'battery')
        return self.rp2_device.rpc_call("mixdevice.measureVoltageByOdin", module, scope)

    def measureCurrentByOdin(self, module, scope='500ma'):
        assert module in ('charger', 'battery')
        return self.rp2_device.rpc_call("mixdevice.measureCurrentByOdin", module, scope)

    def measureByDMM_Matrix(self, channel="ch1", scope='7000mv', x_name=None):
        return self.rp2_device.rpc_call("mixdevice.measureByDMM_Matrix", channel, scope, x_name)

    def uartSwitch(self, isSingle="FULL", isConnect=1):
        assert isSingle in ("FULL", "HALF")
        assert isConnect in (0, 1)
        CONNECT = "CONNECT"
        if isConnect == 0:
            CONNECT = "DISCONNECT"
        if isSingle == "HALF":
            self.relay("UART_FT232_TO_DUT_HALF_DUPLEX", CONNECT)
        else:
            self.relay("UART_FT232_TO_DUT_FULL_DUPLEX", CONNECT)
        self.setStateByName("DUT_TP38_FW_RX", "UART_FT232_TO_DUT_1V7", isConnect)
        self.setStateByName("DUT_TP39_FW_TX", "UART_DUT_TO_FT232_1V7", isConnect)
        return True

    def chargerPowerOn(self, volt, curr_limit, delay_s=1):
        self.relay("ODIN_VCHG_TO_DUT_TP40_POGO5V")
        self.chargeEnable(volt, curr_limit)
        time.sleep(delay_s)
        # chargerVolt = self.measureVoltageByOdin("charger")
        chargerVolt = self.measureByDMM_Matrix("ch1", "7000mV", "DUT_TP40_POGO5V")
        chargerCurr = self.measureCurrentByOdin("charger")
        return {"chargerVolt":chargerVolt, "chargerCurr":chargerCurr}

    def chargerShutDownAndUartSwitch(self):
        self.rp2_device.rpc_call("mixdevice.chargeDisable")
        # self.reset()
        # self.relay("BES_BOARD_POWER_ON")
        self.uartSwitch("FULL", 1)
        time.sleep(3)
        return True

    def jlinkPowerOn1V2(self):
        self.relay("ODIN_BATT_TO_DUT_TP10_1P05V")
        self.batteryEnable(1200, 500)
        time.sleep(1)
        self.setStateByName("DUT_TP5_JRESET","JRESET_1V7")
        self.setStateByName("DUT_TP3_JTDI","JTDI_1V7")
        self.setStateByName("DUT_TP2_SW_TMS","SW_TMS_1V7")
        self.setStateByName("DUT_TP1_SW_TCK","SW_TCK_1V7")
        self.setStateByName("DUT_TP4_JTDO","JTDO_1V7")
        self.relay("PP1V7_LDO_EN")
        time.sleep(3)
        batVolt = self.measureVoltageByOdin("battery", "5000mv")
        batCurr = self.measureCurrentByOdin("battery", "50ma")
        return {"batVolt": batVolt, "batCurr": batCurr}


    def jlinkPowerOn(self):
        self.relay("ODIN_BATT_TO_DUT_TP10_1P05V")
        self.batteryEnable(1200, 500)
        self.relay("PP1V7_LDO_EN")
        self.setStateByName("DUT_TP31_B00TMODE_ON","GPIO_1V7")
        time.sleep(0.1)
        self.batteryEnable(0, 500)
        time.sleep(0.1)
        self.batteryEnable(1200, 500)
        time.sleep(0.1)
        self.relay("PP1V7_VDDO_TO_DUT_TP41_VDDO")

        self.setStateByName("DUT_TP5_JRESET", "JRESET_1V7")
        self.setStateByName("DUT_TP3_JTDI", "JTDI_1V7")
        self.setStateByName("DUT_TP2_SW_TMS", "SW_TMS_1V7")
        self.setStateByName("DUT_TP1_SW_TCK", "SW_TCK_1V7")
        self.setStateByName("DUT_TP4_JTDO", "JTDO_1V7")

        TP10Volt = self.measureVoltageByOdin("battery", "5000mv")
        TP10Curr = self.measureCurrentByOdin("battery", "50ma")
        TP31Volt = self.measureByDMM_Matrix("ch1", '7000mv',"DUT_TP31_B00TMODE_ON")
        TP41Volt = self.measureByDMM_Matrix("ch1", '7000mv', "DUT_TP41_VDDO")
        return {"TP10Volt": TP10Volt, "TP10Curr": TP10Curr,"TP31Volt": TP31Volt, "TP41Volt": TP41Volt}


    def disconnect8300Power(self):
        self.batteryEnable(0, 500)
        self.relay("ODIN_BATT_TO_DUT_TP10_1P05V","DISCONNECT")
        self.setStateByName("DUT_TP31_B00TMODE_ON", "GPIO_1V7",0)
        self.relay("PP1V7_VDDO_TO_DUT_TP41_VDDO", "DISCONNECT")
        time.sleep(1)

    def cal8300PowerOn(self):
        self.relay("ODIN_BATT_TO_DUT_TP10_1P05V")
        self.batteryEnable(1200, 500)
        self.relay("PP1V7_LDO_EN")
        self.setStateByName("DUT_TP31_B00TMODE_ON", "GPIO_1V7")
        time.sleep(0.1)
        self.batteryEnable(0, 500)
        time.sleep(0.1)
        self.batteryEnable(1200, 500)
        time.sleep(0.1)
        self.relay("PP1V7_VDDO_TO_DUT_TP41_VDDO")

        TP10Volt = self.measureVoltageByOdin("battery", "5000mv")
        TP10Curr = self.measureCurrentByOdin("battery", "50ma")
        TP31Volt = self.measureByDMM_Matrix("ch1", '7000mv', "DUT_TP31_B00TMODE_ON")
        TP41Volt = self.measureByDMM_Matrix("ch1", '7000mv', "DUT_TP41_VDDO")

        self.setStateByName("DUT_TP15_CAL_SQUWAV", "SIGNAL_GENERATOR", 1)
        self.setStateByName("DUT_TP42_CAL_STATUS", "EDGE_TRIGGER", 1)


    def dutKeyPressAndrelease(self, delay_s=0.5):
        self.relay("PP1V7_LDO_EN")
        self.setStateByName("DUT_TP6_KEY","GPIO_1V7")
        time.sleep(delay_s)
        self.relay("PP1V7_LDO_EN","DISCONNECT")
        self.setStateByName("DUT_TP6_KEY","GPIO_1V7", 0)
        return True


    def dutPowerOn(self,volt,):
        self.reset()
        time.sleep(0.5)
        self.uartSwitch("HALF",1)
        time.sleep(0.5)
        self.chargerPowerOn(5000, 500, 5)
