# -*- coding: UTF-8 -*-
import time
# from mix.driver.ic.ad56x7r import PRMAD5667R
from mix.driver.ic.mcp472x import MCP4725
from machine import PWM, Pin

class MagmaDef:
    WCT001_REG_SIZE = 65536
    AD5667_ADDR = 0X0C
    CAT24C32_ADDR = 0X50
    TIME_OUT = 6
    VOLTAGE_OUTPUT_MIN = 0
    VOLTAGE_OUTPUT_MAX = 20470
    MAXIMUM_POWER = 30000000
    PWM_FREQUENCY_MIN = 80000
    PWM_FREQUENCY_MAX = 500000
    PWM_DUTY_MIN = 0.05
    PWM_DUTY_MAX = 0.5
    SIGNAL_TIME = 0xFFFFFFFF
    SPS = 125000000
    VPP_SCALE = 0.5
    OFFSET_VOLT = 0

class MagmaException(Exception):
    def __init__(self, err_str):
        self._err_reason = err_str

    def __str__(self):
        return self._err_reason


class Magma(object):
    '''
    The Magma is Wireless charging module, it has voltage and current output function and
    also has the function of voltage and current measurement, pwm output, io set, frequency function.

    Args:
        i2c:              instance(I2C)/None,  If not given, I2CBus emulator will be created.
        ipcore:           instance(MIXWCT001), MIXWCT001 IP driver instance, provide signalsource, signalmeter_p
                                                 and signalmeter_n function.

    Examples:
        i2c = I2C('/dev/i2c-0')
        magma = Magma(i2c,ipcore)
    '''
    rpc_public_api = ['reset', 'dac_init', 'set_vrail_output_voltage','pwm_disable', 'pwm_output']

    def __init__(self, i2c=None, pwm=None):
        self.signalsource = PWM(Pin(pwm))
        self.dac = MCP4725(0x60, i2c)


        # self.ad5667 = PRMAD5667R(i2c, MagmaDef.AD5667_ADDR)
       

    def reset(self, timeout=MagmaDef.TIME_OUT):
        '''
        Reset the instrument module to a know hardware state.

        Args:
            timeout:      float, (>=0), default 6, unit Second, execute timeout.

        Returns:
            string, "done", api execution successful.
        '''
        start_time = time.time()
        while True:
            try:
                self.signalsource.deinit()
                self.dac_init()
                return 'done'
            except Exception as e:
                if time.time() - start_time > timeout:
                    raise MagmaException("Timeout: {}".format(e.message))

    def dac_init(self):
        self.dac.reset()
        self.dac.set_output(0)
        # self.ad5667.reset()
        # self.ad5667.select_work_mode(2)
        # self.ad5667.set_reference('INTERNAL')
        # self.ad5667.output_volt_dc(2, 0)
        # self.set_vrail_output_voltage(0, 5000)

    def set_vrail_output_voltage(self, voltage):
        '''
        mp8859 output voltage, range 0 V ~ 20 V.

        Args:
            voltage:    int, [0~20470], unit mV.

        Examples:
            set_vrail_output_voltage(5000)

        '''
        assert isinstance(voltage, (int, float))
        assert MagmaDef.VOLTAGE_OUTPUT_MIN <= voltage and voltage <= MagmaDef.VOLTAGE_OUTPUT_MAX

        self.dac.set_output(voltage)
        print(True)
        return "done"

    def pwm_disable(self):
        '''
        Disable pwm output function

        Examples:
            pwm_disable()
        '''

        self.signalsource.deinit()
        print(True)
        return "done"

    def pwm_output(self, frequency, duty):
        '''
        pwm output function

        Args:
            frequency:  int, [80000~500000]output signal frequency.
            duty:       float, [0.05~0.5], duty of square

        Examples:
            pwm_output(80000, 0.5)

        '''
        assert MagmaDef.PWM_FREQUENCY_MIN <= frequency <= MagmaDef.PWM_FREQUENCY_MAX
        assert MagmaDef.PWM_DUTY_MIN <= duty <= MagmaDef.PWM_DUTY_MAX
        self.signalsource.freq(frequency)
        self.signalsource.duty_u16(int(duty * 65535))
        print(True)
        return "done"