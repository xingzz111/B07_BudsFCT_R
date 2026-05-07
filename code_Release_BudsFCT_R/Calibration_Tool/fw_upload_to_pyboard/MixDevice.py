import time
import json
import ospath
from machine import UART, Pin
from collections import OrderedDict
import array


class CoreDef:
    RETURN_DONE = True
    RETURN_ERROR = False
    DEFAULT_DELAY_S = 0.01
    IO_MAP_PATH = "io_map.json"
    DEFAULT_HW_FOLDER = "hw_profile.json"
    SAMPLING_AD7175 = [
        5, 10, 16.66, 20, 49.96, 59.92, 100, 200, 397.5,
        500, 1000, 2500, 5000, 10000, 15625, 25000, 31250,
        50000, 62500, 125000, 250000
    ]
    CHARGER="charger"
    BATTERY="battery"
    CURRENT = "curr"
    VOLTAGE = "volt"
    CH0 = "ch0"
    CH1 = "ch1"

    CURRENT_MEASURE_RANGE_CONFIG = [
        {
            'CCS_CURRENT_MEASURE_RANG_100UA': {
                'max_current_ma': 0.1,  # 100uA
                'r_kom': 24.9,  # Kohm
                'index': 0
            }
        },
        {
            'CCS_CURRENT_MEASURE_RANG_100MA': {
                'max_current_ma': 100.0,  # 100mA
                'r_kom': 0.02495,  # Kohm
                'index': 1
            }
        }
    ]

    CURRENT_OUTPUT_RANGE_CONFIG = [
        {
            'CCS_CURRENT_OUTPUT_RANG_100UA': {
            'max_current_ma': 0.1,  # 100uA
            'r_kom': 24.9,  # Kohm
            'index': 2,
            }
        },
        {
            'CCS_CURRENT_OUTPUT_RANG_100MA': {
            'max_current_ma': 100.0,  # 100mA
            'r_kom': 0.02495,  # Kohm
            'index': 3
            }
        }
    ]

    ADC_CAL_TABLE = {
        0 : 4, # ch0 index 4
        3 : 5  # ch3 index 5

    }

    SYSTEM_CAL_INDEX= {
        "charger_volt_cal": 10,
        "battery_volt_cal": 11,
        "charger_curr_cal_1": 12,
        "charger_curr_cal_2": 13,
        "battery_curr_cal_1": 14,
        "battery_curr_cal_2": 15,
        "battery_curr_cal_3": 16,
        "battery_curr_cal_4": 17,
        "charger_measure": 18,
        "battery_measure": 19,
        "dmm_cal_1": 20,
        "dmm_cal_2": 21,
        "dac_cal": 22,
        "pwm_cal": 23,
    }


class MixDevice:

    def __init__(self, baseboard, dmm, psu, eload, wct, data_I, data_F):
        self._odinMeasurePath = None
        self._odinCurrentLimit = None
        self._dmmMeasurePath = None
        self.autoAujust = True
        self.baseboard = baseboard
        self.dmm = dmm
        self.psu = psu 
        self.eload = eload
        self.wct = wct
        self.data_I = data_I
        self.data_F = data_F
        self._dictIOMap = self.loadIoMap()

    def _get_para_from_list(self, curr_ma, config_list):
        for c in config_list:
            for range_name, config in dict(c).items():
                if curr_ma <= config['max_current_ma']:
                    return range_name, config['r_kom'], config['index']
        return None, None, None

    def _get_cal_by_index(self, index):
        assert 0<= index <=100
        if self.baseboard.is_use_cal_data():
            r = self.baseboard.read_calibration_cell(index)
            return r["is_use"], r["gain"], r["offset"]
        return False, 1.0, 0.0

    def reset(self):
        """
        reset the module, the same function like  post_power_on_init
        :return: done
        """
        self._odinMeasurePath = None
        self._odinCurrentLimit = None
        self._dmmMeasurePath = None
        self.baseboard.reset()
        self.dmm.reset()
        self.psu.reset()
        self.wct.reset()
        self.dmm.set_measure_path("ch1","7000mV")
        self.eload.reset()
        self.eload.ocp_reset(0)
        self.eload.ocp_reset(1)
        self.baseboard.set_calibration_mode("cal")
        print(CoreDef.RETURN_DONE)
        return CoreDef.RETURN_DONE

    def loadIoMap(self, path=CoreDef.IO_MAP_PATH):
        load_json = {}
        assert ospath.exists(path)
        with open(path, 'r') as f:
            load_json = json.load(f)
        return load_json

    def fw_version(self):
        """
        return: dict "MIX_FW_PACKAGE":"xxx",
        """
        ver = self._dictIOMap.get("Version", "v0.0.1")
        print(ver)
        return ver

    def relay(self, net, switch='CONNECT', duration=25):
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
        ioList = self._dictIOMap.get(net, {}).get(switch, None)
        if not ioList:
            return "%s@%s <-<< %s" % (net, switch, False)
        try:
            ret = self.baseboard.set_io_switch(ioList)
        except:
            print("retry 1x")
            time.sleep(100 / 1000.0)
            ret = self.baseboard.set_io_switch(ioList)
        time.sleep(duration / 1000.0)
        print("%s <-<< %s" % (ioList, ret))
        print(CoreDef.RETURN_DONE)
        return ioList

    def fixture_eeprom_write(self):
        print("Not implement")

    def fixture_eeprom_read(self):
        print("Not implement")

    def set_system_calibration_mode(self, mode):
        """
        """
        self.baseboard.set_calibration_mode(mode)
        print(CoreDef.RETURN_DONE)
        return CoreDef.RETURN_DONE
    
    def chargeEnable(self, voltage, currentLimit, duration=0.2):
        """
        Odin module enable change output

        Args:
            voltage (int): range [0～7500]  unit is mV
            currentLimit (int): range [0~1000]  unit is mA
            duration (float): delay after setting currentLimit
        Returns:
            True/False
        Example:
        >>> chargeEnable(5000, 1000)
        True
        """
        assert 0 <= voltage <= 7500
        assert 0 <= currentLimit <= 1000
        module = 'charger'
        self.setCurrentLimitByOdin(module, currentLimit)
        time.sleep(duration)
        if self.baseboard.is_use_cal_data():
            is_use, gain, offset = self._get_cal_by_index(CoreDef.SYSTEM_CAL_INDEX["charger_volt_cal"])
            if is_use:
                voltage = voltage * gain + offset
        r = self.psu.enable_charger_output(voltage)
        print(r)
        return r

    def chargeDisable(self):
        """
        Odin module disable change output

        Returns:
            True/False
        Example:
        >>> chargeDisable()
        True
        """
        r = self.psu.disable_charger_output()
        print(r)
        return r

    def batteryEnable(self, voltage, currentLimit=None, duration=0.2):
        """
        Odin module enable battery output

        Args:
            voltage (int): range [0～4990]  unit is mV
            currentLimit (int): range [0~1000]  unit is mA
            sense (bool): True is enable sense, else disable sense
            duration (float): delay after setting currentLimit
        Returns:
            True/False
        Example:
        >>> batteryEnable(5000, 1000)
        True
        """
        assert 0 <= voltage <= 5000
        # assert 0 <= currentLimit <= 1000
        module = 'battery'
        if currentLimit:
            self.setCurrentLimitByOdin(module, currentLimit)
            time.sleep(duration)
        if self.baseboard.is_use_cal_data():
            is_use, gain, offset = self._get_cal_by_index(CoreDef.SYSTEM_CAL_INDEX["battery_volt_cal"])
            if is_use:
                voltage = voltage * gain + offset
        r = self.psu.enable_battery_output(voltage, True)
        print(r)
        return r

    def batteryDisable(self):
        """
        Odin module disable battery output

        Returns:
            True/False
        Example:
        >>> batteryDisable()
        True
        """
        r = self.psu.disable_battery_output()
        print(r)
        return r

    def setBatteryMeasurePath(self, ch, scope):
        """
        Seting odin module battery channel measure path

        Args:
            ch (str): ch0/ch1, ch0 for voltage, ch1 for current
            scope (str): ch0: 500/2500/5000 mv
                         ch1:1ua/100ua/1ma/5ma/50ma/500ma/650ma
        Returns:
            True/False
        Example:
        >>> setBatteryMeasurePath("ch1", "5ma")
        True
        """
        module = 'battery'
        if self._odinMeasurePath != (ch, scope):
            self.psu.set_measure_path(module, ch, scope)
            self._odinMeasurePath = ch, scope
        time.sleep(CoreDef.DEFAULT_DELAY_S)
        print(CoreDef.RETURN_DONE)
        return CoreDef.RETURN_DONE

    def setCurrentLimitByOdin(self, module, currentLimit):
        """
        Seting odin module current limit

        Args:
            module(str): charger/battery
            currentLimit (int): range [0~1000]  unit is mA
                         ch1:1ua/100ua/1ma/5ma/50ma/500ma/650ma
        Returns:
            True/False
        Example:
        >>> setCurrentLimitByOdin("battery", "5ma")
        True
        """
        if self._odinCurrentLimit != (module, currentLimit):
            self.psu.set_current_limit(module, currentLimit)
            self._odinCurrentLimit = module, currentLimit
            time.sleep(CoreDef.DEFAULT_DELAY_S)
        print(CoreDef.RETURN_DONE)
        return CoreDef.RETURN_DONE

    def measureByDMM(self, channel="ch1", scope='7000mv', netName=None, duration=0.2, count=1):
        """
        Seting DMM module channel measure path
        Args:
            ch (str): ch0/ch1
            scope (str): ch0:20ua/200ua/500ua/2ma/5ma/50ma/10mv/100mv/1000mv/7000mv
                         ch1:0mv/100mv/1000mv/7000mv
            netName (str): IO NetName
            duration(float): delay after switch io
        :return
        Returns:
            float
        Example:
        >>> measureByDMM("ch1", "7000mv")
        5000.0
        """
        retList = []
        for i in range(count):
            if netName:
                try:
                    self.relay(netName, "CONNECT")
                except:
                    time.sleep(0.5)
                    self.relay(netName, "CONNECT")
            self.setMeausrePathByDMM(channel, scope)
            time.sleep(duration)
            if channel == 'ch0':
                retVal = self.dmm.measure()[0]
            else:
                retVal = self.dmm.voltage_measure_mv()[0]
            if netName:
                self.relay(netName, "DISCONNECT")
            if self.baseboard.is_use_cal_data() and channel == 'ch1':
                if retVal <= 10:
                    index = CoreDef.SYSTEM_CAL_INDEX["dmm_cal_1"]
                else:
                    index = CoreDef.SYSTEM_CAL_INDEX["dmm_cal_2"]
                is_use, gain, offset = self._get_cal_by_index(index)
                if is_use:
                    retVal = retVal * gain + offset
            retList.append(retVal)
            retList.sort()
        print(retList[int(count / 2)])
        return retList[int(count / 2)]
    
    def setMeausrePathByDMM(self, channel, scope):
        """
        Seting DMM module channel measure path

        Args:
            ch (str): ch0/ch1
            scope (str): ch0:20ua/200ua/500ua/2ma/5ma/50ma/10mv/100mv/1000mv/7000mv
                         ch1:0mv/100mv/1000mv/7000mv
        :return
        Returns:
            True/False
        Example:
        >>> setMeausrePathByDMM("ch1", "7000mv")
        True
        """
        assert channel in ('ch0', 'ch1')
        if self._dmmMeasurePath != (channel, scope):
            self.dmm.set_measure_path(channel, scope)
            self._dmmMeasurePath = (channel, scope)
            time.sleep(CoreDef.DEFAULT_DELAY_S)
        print(CoreDef.RETURN_DONE)
        return CoreDef.RETURN_DONE

    def measureVoltageByOdin(self, module, scope='5000mv'):
        """
        Measure voltage with odin module

        Args:
            module(str): charger/battery
            scope (str): only battery need set scope: 500mv/2500mv/5000mv
        Returns:
            float
        Example:
        >>> measureVoltageByOdin("battery", "5000mv")
        3800.0
        """
        assert module in ('charger', 'battery')
        if module == 'battery':
            self.setBatteryMeasurePath('ch0', scope)
        retVal = self.psu.voltage_measure(module)[0]
        if self.baseboard.is_use_cal_data():
            if module == 'battery':
                index = CoreDef.SYSTEM_CAL_INDEX["battery_measure"]
            else:
                index = CoreDef.SYSTEM_CAL_INDEX["charger_measure"]
            is_use, gain, offset = self._get_cal_by_index(index)
            if is_use:
                retVal = retVal * gain + offset
        print(retVal) 
        return retVal

    def measureCurrentByOdin(self, module, scope='500ma'):
        """
        Measure current with odin module

        Args:
            module(str): charger/battery
            scope (str): only battery need set scope: 1ua/100ua/1ma/5ma/50ma/500ma/650ma
        Returns:
            float
        Example:
        >>> measureCurrentByOdin("battery", "5ma")
        1.23
        """
        assert module in ('charger', 'battery')
        if module == 'battery':
            self.setBatteryMeasurePath('ch1', scope)
        retVal = self.psu.current_measure(module)[0]
        if self.autoAujust and module == 'battery':
            self.setBatteryMeasurePath('ch1', '500ma')
        
        if -10 <= retVal <= 10 and self.baseboard.is_use_cal_data(): 
            if module == 'charger':
                index = CoreDef.SYSTEM_CAL_INDEX["charger_curr_cal_1"]
            else:
                if 0 <= retVal <= 10:
                    index = CoreDef.SYSTEM_CAL_INDEX["battery_curr_cal_1"]
                else:
                    index = CoreDef.SYSTEM_CAL_INDEX["battery_curr_cal_3"]
            is_use, gain, offset = self._get_cal_by_index(index)
            if is_use:
                print("gain", gain)
                print("offset", offset)
                retVal = retVal * gain + offset
        print(retVal)
        return retVal
    
    def scan_iic(self):
        return_str = ""
        dict_hw_profile = self.loadIoMap(CoreDef.DEFAULT_HW_FOLDER)
        if not dict_hw_profile:
            msg = 'Hardware profile {} not found!!!'.format(CoreDef.DEFAULT_HW_FOLDER)
            raise RuntimeError(msg)
        shared_devices = dict_hw_profile.get("shared_devices")
        shared_devices = OrderedDict(sorted(shared_devices.items()))
        for k,v in shared_devices.items():
            if v.get("scl") and v.get("sda"):
                dev = PRMSoftI2CBus(Pin(v.get("scl")), Pin(v.get("sda")))
                return_str += "*"*20
                return_str += "\n"
                return_str += "---> {}: sclk({}) sda({})\n".format(k, v.get("scl"), v.get("sda"))
                return_str += "<<<- response: {}\r\n".format(dev.scan())
        print(return_str)

    def dmm_datalogger(self, channel, counts, sample_rate):
        # print(dmm.get_raw_samples(channel, counts, sample_rate))
        for i in self.data_F:
            i = 0.0
        for i in self.data_I:
            i = 0
        print(self.dmm.get_raw_samples2(channel, self.data_I[:counts], self.data_F[:counts], sample_rate))

    def odin_datalogger(self, channel, counts, sample_rate):
        print(self.psu.multi_bat_measure(channel, counts, sample_rate))
       

    def odin_datalogger2(self, channel, counts, sample_rate):
        for i in self.data_F:
            i = 0.0
        for i in self.data_I:
            i = 0
        print(self.psu.multi_bat_measure2(channel, self.data_I[:counts], self.data_F[:counts], sample_rate))

    def measure_pwm(self):
        dt = self.baseboard.mes_freq()
        print(dt)

    def enableEload(self, channel, current, duration=25):
        """
        enable eload module

        Args:
            channel:         string|int, ["0", "1", 0, 1]
            current:         int         [0~1000]  unit mA
            duration:        int         unit mS.

        Returns:
            boolean type,    True|False

        Examples:
            result = mixdevice.enableEload(0, 50)

        """
        assert channel in ("0", "1", 0, 1)
        assert 0 <= current <= 1000
        self.eload.volt_measure_enable(channel)
        self.eload.enable(channel)
        time.sleep(duration / 1000.0)
        self.eload.set_eload_current_ma(channel, current)
        print(CoreDef.RETURN_DONE)

    def disableEload(self, channel):
        """
        disable eload module

        Args:
            channel:         string|int, ["0", "1", 0, 1]

        Returns:
            boolean type,    True|False

        Examples:
            result = mixdevice.disableEload(0)

        """
        assert channel in ("0", "1", 0, 1)
        self.eload.disable(channel)
        print(CoreDef.RETURN_DONE)

    def measureByEload(self, channel, types, duration=25, count=1):
        """
        measure eload current|voltage by channel

        Args:
            channel:   string|int, ["0", "1", 0, 1]
            types:     string, current|voltage
            duration:  int         unit mS.

        Returns:
            float type,   currnet|voltage  unit:mA|mV

        Examples:
            result = mixdevice.measureByEload(0, "current")

        """
        assert channel in ("0", "1", 0, 1)
        assert types in ("current", "voltage")
        retList = []
        for i in range(count):
            if types == "current":
                retVal = self.eload.get_eload_current_ma(channel)
            else:
                self.eload.volt_measure_enable(channel)
                time.sleep(duration / 1000.0)
                retVal = self.eload.get_eload_volt_mv(channel)
                self.eload.volt_measure_disable(channel)
            if retVal and retVal[0]:
                retList.append(retVal[0])
                retList.sort()
            else:
                print(CoreDef.RETURN_ERROR)
        print(retList[int(count / 2)])
    def ccs_svs_setup(self, curr_ma, volt_mv):
        assert 0 <= curr_ma <= 100
        assert 0 <= volt_mv <= 5000
        voltageLimit = volt_mv / 2.0
        current_measure_range, r1_kom, index1 = self._get_para_from_list(curr_ma, CoreDef.CURRENT_MEASURE_RANGE_CONFIG)
        
        if not current_measure_range:
            print(CoreDef.RETURN_ERROR)
            return CoreDef.RETURN_ERROR
        self.r1_kom = r1_kom
        # 1.set current sampling scope
        self.relay(current_measure_range, "CONNECT")
        print("1.set current sampling scope: {} CONNECT".format(current_measure_range))

        #2. set voltage limit
        is_used,gain,offset = self._get_cal_by_index(index1)
        if is_used:
            voltageLimit = voltageLimit*gain+offset

        self.baseboard.setDac(1, voltageLimit)
        print("2. setDac(0x61, {})".format(voltageLimit))
        time.sleep(0.1)
        #3. set current output scope
        current_output_range, r2_kom, index2 = self._get_para_from_list(curr_ma, CoreDef.CURRENT_MEASURE_RANGE_CONFIG)
        if not current_output_range:
            print(CoreDef.RETURN_ERROR)
            return CoreDef.RETURN_ERROR

        self.relay(current_output_range, "CONNECT")
        print("3.set current output scope: {} CONNECT".format(current_output_range))

        #4. set current value
        is_used,gain,offset = self._get_cal_by_index(index2)
        if is_used:
            curr_ma = (curr_ma * 1000 * r2_kom)*gain+offset

        self.baseboard.setDac(0, 2500 - curr_ma)
        print("4. setDac(0x60, {})".format(2500 - curr_ma))
        time.sleep(0.1)
        print(CoreDef.RETURN_DONE)
        return CoreDef.RETURN_DONE

    def open_short_test(self, netName, delay_ms=200):
        if not self.r1_kom:
            print(CoreDef.RETURN_ERROR)
            return CoreDef.RETURN_ERROR

        self.relay(netName, "CONNECT")
        time.sleep(delay_ms/1000.0)
        curr_ch = 3
        #6. readback current by adc
        read_back_ma = self.baseboard.readVolt(curr_ch)
        curr_index = CoreDef.ADC_CAL_TABLE[curr_ch]
        is_used,gain,offset = self._get_cal_by_index(curr_index)
        if is_used:
            read_back_ma = read_back_ma*gain + offset

        read_back_ma = (read_back_ma - 2500) / self.r1_kom * 1000
        print("6. readback current by adc: {}".format(read_back_ma))

        #7. read volt
        volt_ch = 0
        read_back_mv = self.baseboard.readVolt(volt_ch)
        volt_index = CoreDef.ADC_CAL_TABLE[volt_ch]
        is_used,gain,offset = self._get_cal_by_index(volt_index)
        if is_used:
            read_back_mv = read_back_mv*gain + offset
        read_back_mv = read_back_mv - 2500
        resistance = float(read_back_mv / read_back_ma)
        print(resistance)
        return resistance

    def current_measure(self):
        if not self.r1_kom:
            print(CoreDef.RETURN_ERROR)
            return CoreDef.RETURN_ERROR
        curr_ma = (self.baseboard.readVolt(3) - 2500)/self.r1_kom*1000
        print(curr_ma)
        return curr_ma
    
    def voltage_measure(self):
        volt_mv = self.baseboard.readVolt(0) - 2500
        print(volt_mv)
        return volt_mv

    def wctDacOutput(self, voltage):
        is_used, gain, offset = self._get_cal_by_index(CoreDef.SYSTEM_CAL_INDEX["dac_cal"])
        print('dac set gain: {} offset:{}'.format(gain, offset))
        print('dac set voltage: {}'.format(voltage))
        if is_used:
            voltage = voltage * gain + offset
        result = self.wct.set_vrail_output_voltage(voltage)
        print("wct setDac: {}".format(result))
        return result

    def wctPWMOutput(self, frequency, duty):
        is_used,gain,offset = self._get_cal_by_index(CoreDef.SYSTEM_CAL_INDEX["pwm_cal"])
        print('pwm set gain: {} offset:{}'.format(gain, offset))
        print('pwm set frequency: {}'.format(frequency))
        if is_used:
            frequency = frequency*gain + offset
        result = self.wct.pwm_output(int(frequency), duty)
        print("wct set pwm: {}".format(result))
        return result
        

import array
data_I = array.array("I", [0]* 1024)
data_F = array.array("f", [0.0]* 1024)
# if __name__ == '__main__':
from mix.driver.ic.tca9548 import TCA9548
from mix.driver.bus.soft_i2c import rtSoftI2CBus
from mix.driver.bus.soft_spi import rtSoftSPI
from mix.driver.ic.cat24cxx import CAT24C256
from mix.driver.module.dmmV20 import DMMV20
from mix.driver.module.odin import Odin
from mix.driver.module.eloadlite import ELoad
from baseboard import BaseBoard
from wct import Magma
from batteryboard import BatteryBoard
from pio_program import PIOProgram



base_i2c_ch0 = rtSoftI2CBus(1, 0, 100000)
dmm_iic_ch0 = rtSoftI2CBus(7, 6, 100000)
psu_iic_ch0 = rtSoftI2CBus(9, 8, 100000)
sib_iic_ch0 = rtSoftI2CBus(15, 14, 100000)
eload_iic_ch0 = rtSoftI2CBus(17, 16, 100000)


iic_hub_ch0 = TCA9548(0x70, sib_iic_ch0)
dmm_eeprom_iic_ch0 = rtSoftI2CBus(7, 6, 100000)
psu_eeprom_iic_ch0 = rtSoftI2CBus(9, 8, 100000)


psu_eeprom_ch0 = CAT24C256(80, psu_eeprom_iic_ch0)
dmm_eeprom_ch0 = CAT24C256(80, dmm_eeprom_iic_ch0)
eload_eeprom_ch0 = CAT24C256(80, iic_hub_ch0[2])


base_eeprom_ch0 = CAT24C256(80, base_i2c_ch0)
_soft_spi_psu = rtSoftSPI(10, 11, 12, polarity=1, phase=1, baudrate=1000000)
_soft_spi_dmm = rtSoftSPI(2, 3, 4, polarity=1, phase=1, baudrate=1000000)
psu = Odin(psu_iic_ch0, psu_eeprom_ch0, 13, _soft_spi_psu)
dmm = DMMV20(dmm_iic_ch0, dmm_eeprom_ch0, 5, _soft_spi_dmm)
eload = ELoad(eload_iic_ch0, eload_eeprom_ch0)
wct = Magma(base_i2c_ch0, 28)
batteryboard =BatteryBoard(base_i2c_ch0)
baseboard = BaseBoard(base_i2c_ch0, base_eeprom_ch0)
mixdevice = MixDevice(baseboard, dmm, psu, eload, wct, data_I, data_F)
pio = PIOProgram(0, 26)
pio2 = PIOProgram(1, 27)