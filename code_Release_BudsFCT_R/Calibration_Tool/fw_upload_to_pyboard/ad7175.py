# -*- coding: utf-8 -*-
import rp2
from rp2 import PIO, StateMachine
import gc
from machine import Pin
import time
import binascii
import array
import rp2_util

__author__ = 'Ming'
__version__ = '0.1'


class AD717XDef:
    '''
    AD717XDef shows the registers address of AD717X
    '''

    DEFAULT_TIMEOUT = 1
    DEFAULT_TIMEOUT_MS = 400
    DEFAULT_DELAY = 0.001
    ADC_MODE_REG_ADDR = 0x01
    INTERFACE_MODE_REG_ADDR = 0x02
    ID_REG_ADDR = 0x7
    CH0_REG_ADDR = 0x10
    CH1_REG_ADDR = 0x11
    CH2_REG_ADDR = 0x12
    CH3_REG_ADDR = 0x13
    WAIT_STEADY_COUNT = 12
    DATA_REG_ADDR = 0x04
    SETUPCON0_REG_ADDR = 0x20
    SETUPCON1_REG_ADDR = 0x21
    FILTER0_REG_ADDR = 0x28
    FILTER1_REG_ADDR = 0x29
    FILTER2_REG_ADDR = 0x2A
    FILTER3_REG_ADDR = 0x2B
    DEFAULT_TIMEOUT_MS = 2000
    DEFAULT_COUNT = 1024

    CHANNELS = {"ch0", "ch1", "ch2", "ch3", "all", 0, 1, 2, 3}

    CHAN_REG_ADDR = {
        "ch0": CH0_REG_ADDR, "ch1": CH1_REG_ADDR,
        "ch2": CH2_REG_ADDR, "ch3": CH3_REG_ADDR}

    POLARS = {"bipolar": 0x01, "unipolar": 0x00}
    BUFFERS = {"enable": 0x0f, "disable": 0x00}
    REFERENCES = {"extern": 0x00, "internal": 0x02, "AVDD-AVSS": 0x03}
    SETUP_REG_ADDR = {"ch0": 0x20, "ch1": 0x21, "ch2": 0x22, "ch3": 0x23}

    SETUPS = {"ch0": 0x00, "ch1": 0x01, "ch2": 0x02, "ch3": 0x03}

    AINS = {"AIN0": 0x0, "AIN1": 0x01, "AIN2": 0x02,
            "AIN3": 0x03, "AIN4": 0x04, "Temp+": 0x11,
            "Temp-": 0x12, "AVDD1": 0x13, "AVSS": 0x14,
            "REF+": 0x15, "REF-": 0x16}

    CLOCKSEL = {
        "internal": 0x00,
        "output": 0x04,
        "external": 0X08,
        "crystal": 0x0c
    }
    CLOCKSEL_MASK = 0x0c

    SAMPLING_CONFIG_TABLE_AD7175 = {5: 0x14,
                                    10: 0x13, 16.66: 0x12,
                                    20: 0x11, 49.96: 0x10,
                                    59.92: 0x0f, 100: 0x0e,
                                    200: 0x0d, 397.5: 0x0c,
                                    500: 0x0b, 1000: 0x0a,
                                    2500: 0x09, 5000: 0x08,
                                    10000: 0x07, 15625: 0x06,
                                    25000: 0x05, 31250: 0x04,
                                    50000: 0x03, 62500: 0x02,
                                    125000: 0x01, 250000: 0x00}

    SAMPLING_CONFIG_TABLE_AD7177 = {5: 0x14,
                                    10: 0x13, 16.66: 0x12,
                                    20: 0x11, 49.96: 0x10,
                                    59.92: 0x0f, 100: 0x0e,
                                    200: 0x0d, 397.5: 0x0c,
                                    500: 0x0b, 1000: 0x0a,
                                    2500: 0x09, 5000: 0x08,
                                    10000: 0x07}

    SAMPLING_CONFIG_TABLE_AD7172 = {1.25: 0x16, 2.5: 0x15,
                                    5: 0x14,
                                    10: 0x13, 16.63: 0x12,
                                    20.01: 0x11, 49.68: 0x10,
                                    59.52: 0x0f, 100.2: 0x0e,
                                    200.3: 0x0d, 381: 0x0c,
                                    503.8: 0x0b, 1007: 0x0a,
                                    2597: 0x09, 5208: 0x08,
                                    10417: 0x07, 15625: 0x06,
                                    31250: 0x05}

    AD7175_CHIP_ID = 0x0cd0
    AD7177_CHIP_ID = 0x4fd0
    AD7172_CHIP_ID = 0x00d0


class AD717XException(Exception):
    '''
    AD717XException shows the exception of AD717X
    '''

    def __init__(self, err_str):
        self.err_reason = '%s.' % (err_str)

    def __str__(self):
        return self.err_reason

def CHAN(chan):
    if isinstance(chan, int):
        return "ch{}".format(chan)
    # default channel type is string
    return chan

class PLAD7175(object):
    '''
    PLAD717X ADC function class. This is a base class of AD717X IP core.

    :param axi4_bus: instance/string/None instance or dev path of AXI4 bus,
                                       If None, will create Emulator
    :param mvref:     float        reference voltage, unit is mV
    :param code_polar:  string('bipolar'/'unipolar'), Input channel polar/unipolar config
    :param reference:   string('extern'/'internal') reference voltage select.
    :param buffer_flag: string('enable'/'disable'), buffer function enable or disable
    :param clock:       string('internal'/'output'/'external'/'crystal'), select AD717x chip clock.

    .. code-block:: python

               ad717x = PLAD717X('/dev/MIX_AD717X_x', 2500)

    AD7172, AD7175 and AD7177's sample rate range is different, details as below:

    +--------+------------+---------+----------+
    |AD7172  | AD7175     |  AD7177 |   unit   |
    +========+============+=========+==========+
    |1       |  5         |  5      |   'sps'  |
    +--------+------------+---------+----------+
    |2       |  10        |  10     |   'sps'  |
    +--------+------------+---------+----------+
    |5       |  16        |  16     |   'sps'  |
    +--------+------------+---------+----------+
    |10      |  20        |  20     |   'sps'  |
    +--------+------------+---------+----------+
    |16      |  49        |  49     |   'sps'  |
    +--------+------------+---------+----------+
    |20      |  59        |  59     |   'sps'  |
    +--------+------------+---------+----------+
    |49      |  100       |  100    |   'sps'  |
    +--------+------------+---------+----------+
    |59      |  200       |  200    |   'sps'  |
    +--------+------------+---------+----------+
    |100     |  397       |  397    |   'sps'  |
    +--------+------------+---------+----------+
    |200     |  500       |  500    |   'sps'  |
    +--------+------------+---------+----------+
    |381     |  1000      |  1000   |   'sps'  |
    +--------+------------+---------+----------+
    |503     |  2500      |  2500   |   'sps'  |
    +--------+------------+---------+----------+
    |1007    |  5000      |  5000   |   'sps'  |
    +--------+------------+---------+----------+
    |2597    |  10000     |  10000  |   'sps'  |
    +--------+------------+---------+----------+
    |5208    |  15625     |    /    |   'sps'  |
    +--------+------------+---------+----------+
    |10417   |  25000     |    /    |   'sps'  |
    +--------+------------+---------+----------+
    |15625   |  31250     |    /    |   'sps'  |
    +--------+------------+---------+----------+
    |31250   |  50000     |    /    |   'sps'  |
    +--------+------------+---------+----------+
    |   /    |  62500     |    /    |   'sps'  |
    +--------+------------+---------+----------+
    |   /    |  125000    |    /    |   'sps'  |
    +--------+------------+---------+----------+
    |   /    |  250000    |    /    |   'sps'  |
    +--------+------------+---------+----------+

    AD717X Clock source

    +----------------+---------------------------------+
    |  clock         |  description                    |
    +----------------+---------------------------------+
    | 'internal'     |  Internal oscillator            |
    +----------------+---------------------------------+
    | 'output'       |  Internal oscillator and output |
    +----------------+---------------------------------+
    | 'external'     |  External clock source          |
    +----------------+---------------------------------+
    | 'crystal'      |  External crystal               |
    +----------------+---------------------------------+

    '''
    rpc_public_api = ["reset", "ic_init", "read_volt", "set_sampling_rate", "get_sampling_rate", "is_communication_ok", "get_raw_samples"]

    def __init__(self, cs, spi_bus=None, mvref=5000, code_polar="bipolar",
                 reference="extern", buffer_flag="enable", clock="internal", slot=0):
        self.cs = cs
        self.spi = spi_bus
        self.mvref = mvref
        self.clock = AD717XDef.CLOCKSEL[clock]
        self.sample_rate_table = AD717XDef.SAMPLING_CONFIG_TABLE_AD7175
        self.resolution = 24
        self.samples = 1
        self.channel_dict = {"ch0": 0, "ch1": 1, "ch2": 2, "ch3": 3}

        self.config = {
            "ch0": {"P": "AIN0", "N": "AIN1"},
            "ch1": {"P": "AIN2", "N": "AIN3"}
        }
        self.continue_sampling_mode_ch_state = "all"
        self.chip_id = AD717XDef.AD7175_CHIP_ID
        self.sampling_rates = {}
        self.reference = reference
        self.buffer_flag = buffer_flag
        self.code_polar = code_polar
        if reference == "internal":
            self.d = 0x8000
        else:
            self.d = 0x0000
        self.slot = slot
        self.sm = rp2.StateMachine(self.slot, self.output, freq=32_000_000, sideset_base=self.spi.clk, in_base=self.spi.miso)

    @rp2.asm_pio(sideset_init=(PIO.OUT_HIGH,),in_shiftdir=PIO.SHIFT_LEFT)
    def output():
        label("start")
        # wait(0,pin,0)
        wait(1,pin,0)
        wait(0,pin,0)[5]
        # nop()[5]
        # nop()[5]
        set(x,30).side(0) [3]
        label('read')
        nop().side(1) [2]
        in_(pins,1)
        jmp(x_dec,'read').side(0)[3]
        nop().side(1)
        in_(pins,1)
        push()

    def ic_init(self):
        self.spi.spi.init()
        self.is_communication_ok()
        self.cs.value(1)
        self.cs.value(0)
        self.reset()
        for key, value in self.config.items():
            assert self.set_setup_register(key, self.code_polar, self.reference, self.buffer_flag)
        self.set_sampling_rate("ch0",1000)
        self.set_sampling_rate("ch1",1000)
        self.cs.value(1)

    def reset(self):
        self.spi.write([0xFF for i in range(12)])

    def set_setup_register(self, channel, code_polar="bipolar", reference="extern", buffer_flag="enable"):
        '''
        AD717x setup register set, code polar,refrence, buffer

        :param channel:    string("ch0"/"ch1"/"ch2"/"ch3"),            The channel to config setup_register
        :param code_polar: string("unipolar"/"bipolar"),               "unipolar" for unipolar input,
                                                                       "bipolar" for bipolar input
        :param reference:  string("extern"/"internal"/"AVDD-AVSS"),    Select voltage reference
        :param buffer:     string("enable"/"disable"),                 Enable or disable input buffer
        :example:
                ad717x.set_setup_register("ch0", "bipolar", "extern", "enable")
        '''
        bFlag = False
        self.code_polar = code_polar
        value = 0x0
        value |= AD717XDef.POLARS[code_polar] << 12 | AD717XDef.BUFFERS[buffer_flag] << 8 |\
            AD717XDef.REFERENCES[reference] << 4

        # print("SETUP_REG_ADDR[{}]: {}".format(channel, [hex(i) for i in [value>>8, value&0x00FF]]))
        for i in range(3):
            self.write_register(AD717XDef.SETUP_REG_ADDR[channel], [value>>8, value&0xff])
            result = self.read_register(AD717XDef.SETUP_REG_ADDR[channel], 2)
            if result[0] == (value>>8) and result[1] == (value&0xff):
                bFlag = True
                break
        # print("SETUP_REG_ADDR[{}]: {}".format(channel, [hex(i) for i in result]))
        return bFlag

    def set_sampling_rate(self, channel, rate):
        '''
        PLAD717X set sample rate of channel

        :param channel: str("ch0"~"ch3")/int(0-3)
        :param rate:    float
        :example:
                   ad717x.set_sampling_rate("ch0", 3000)
        '''
        assert channel in ["ch" + str(i) for i in range(4)] or channel in [i for i in range(4)]

        channel = CHAN(channel)
        filter_reg = (eval("AD717XDef.FILTER" + channel[-1] + "_REG_ADDR"))
        value = self.read_register(filter_reg, 2)

        if rate not in self.sample_rate_table:
            raise AD717XException("Sample rate is out of range of PLAD717X capable.")

        for sample_rate, reg_value in self.sample_rate_table.items():
            if sample_rate == rate:
                sampling_code = reg_value
        value = (value[0] << 8) | value[1]
        # bit operation, clear first, then set 1
        value = value & (~0x1f)
        value = (value | sampling_code)
        self.write_register(filter_reg, [value>>8, value&0xff])
        self.sampling_rates[channel] = rate

    def get_sampling_rate(self, channel):
        '''
        PLAD717X get sample rate

        :param channel:    str("ch0"~"ch3")/int(0-3)
        :returns:  int         unit is sps
        :example:
                   print(ad717x.get_sampling_rate("ch0"))
        '''

        assert channel in ["ch" + str(i) for i in range(4)] or channel in range(4)

        channel = CHAN(channel)
        filter_reg = eval("AD717XDef.FILTER" + channel[-1] + "_REG_ADDR")
        result = self.read_register(filter_reg, 2)
        data = result[0]<<8|result[1]

        # get the rate operation bit, low five bits
        data = data & (0x1f)
        result = None
        for sample_rate, reg_value in self.sample_rate_table.items():
            if reg_value == data:
                result = sample_rate

        if result is None:
            raise AD717XException("Register value invalid:0x%x" % (data))

        return result

    def set_channel_state(self, channel, state):
        '''
        PLAD717X set_channel_state

        :param channel:         str("ch0"~"ch3")/int(0-3)
        :param state:           str("enable", "disable")
        :example:
                   ad717x.set_channel_state("ch0", "enable")
        '''
        channel = CHAN(channel)
        # r = False
        reg_value = 0x0
        if state == "enable":
            reg_value |= 0x1 << 15
        reg_value |= AD717XDef.SETUPS[channel] << 12
        reg_value |= AD717XDef.AINS[self.config[channel]["P"]] << 5
        reg_value |= AD717XDef.AINS[self.config[channel]["N"]]
        self.write_register(AD717XDef.CHAN_REG_ADDR[channel], [reg_value>>8, reg_value&0xff])

    def select_single_channel(self, channel):
        '''
        PLAD717X select_single_channel

        :param channel:         str("ch0","ch1","ch2","ch3")/int(0-3)
        :example:
                   ad717x.select_single_channel("ch0")
        '''
        assert channel in AD717XDef.CHANNELS

        channel = CHAN(channel)
        # close all channeal
        for chan in self.config:
            self.set_channel_state(chan, "disable")

        # open one channel
        self.set_channel_state(channel, "enable")

    def _value_2_mvolt(self, code, mvref, bits, gain=0x555555, offset=0x800000):
        '''
        translate the value to voltage value

        :param code:    int
        :param mvref:   float       unit is mV
        :param bits:    bits(16,24,32)
        :param gain:    int gain register value, nominal value 0x555555
        :param offset:  int offset register value, default value 0x800000
        :returns:       float    unit is mV
        '''
        tmp = float(code - (1 << bits - 1)) * 0x400000 / gain
        volt = float(tmp + (offset - 0x800000)) / (1 << bits - 1) * mvref / 0.75
        return volt

    def read_register(self, reg_addr, lenth=1):
        '''
        PLAD717X read the register value

        :param reg_addr:    hex(0x00~0x3F)
        :returns:           type of int
        :raises keyError:   raises an AD717XException
        :example:
                            print(ad717x.read_register(0x00))
        '''
        self.cs.value(0)
        self.spi.write([(0x3F & reg_addr) | (0x1 << 6)])
        result = self.spi.read(lenth)
        self.cs.value(1)
        return result

    def write_register(self, reg_addr, reg_data):
        '''
        PLAD717X write the register value

        :param reg_addr:    hex(0x00~0x3F)
        :param reg_data:    int
        :raises keyError:   raises an AD717XException
        :example:
                            ad717x.write_register(0x10, 30)
        '''
        self.cs.value(0)
        self.spi.write([0x3F & reg_addr]+reg_data)
        self.cs.value(1)
        return True

    def read_volt(self, channel):
        '''
        PLAD717X read voltage at single conversion mode

        :param channel:    str("ch0", "ch1", "ch2", "ch3")/int(0-3)
        :returns:           int         unit is mV
        :raises keyError:   raises an AD717XException
        :example:
                   print(ad717x.get_voltage("ch0"))
        '''
        assert channel in AD717XDef.CHANNELS
        channel = CHAN(channel)
        self.ic_init()
        self.is_communication_ok()
        self.select_single_channel(channel)
        self.write_register(AD717XDef.INTERFACE_MODE_REG_ADDR, [0x00, 0x40])
        rd_data = self.d
        wr_data = rd_data & 0xFF0F | 0x0010
        wr_data &= ~AD717XDef.CLOCKSEL_MASK
        wr_data |= self.clock
        self.write_register(AD717XDef.ADC_MODE_REG_ADDR, [wr_data>>8, wr_data&0xff])
        lasttime = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(),lasttime) < AD717XDef.DEFAULT_TIMEOUT_MS:
            result = self.read_register(0x00, 1)
            # print ("STATUS REG: {} is {}".format(0x00, [hex(i) for i in result]))
            if result[0]&0x80 == 0:
                break
            time.sleep_ms(5)
        if time.ticks_diff(time.ticks_ms(),lasttime) - lasttime > AD717XDef.DEFAULT_TIMEOUT_MS:
            raise AD717XException('Wait ADS1115 conversion completed timeout.')
        data = self.read_register(AD717XDef.DATA_REG_ADDR, 4)
        # print("DATA_REG_ADDR: {}".format([hex(i) for i in data]))
        # reg_data is 32 bit width. But for AD7175, only 24 bit is valid
        if self.resolution == 24:
            # high 24 bit is valid
            reg_data=data[0]<< 16| data[1]<<8| data[2]
            # print("Status: {}\n".format(hex(data[3])))
            # print("currnet Channel: {}\n".format(data[3]&0x03))
        volt = self._value_2_mvolt(reg_data, self.mvref, self.resolution)
        return volt

    def is_communication_ok(self):
        '''
        PLAD717X read the id of PLAD717X and then confirm
        whether the communication of SPI bus is OK

        :returns:           bool
        :raises keyError:   raises an AD717XException
        :example:
                            print(ad717x.is_communication_ok())
        '''
        self.cs.value(1)
        self.cs.value(0)
        read_times = 5
        ret = False
        while read_times > 0:
            ret = self.read_register(AD717XDef.ID_REG_ADDR, 2)
            # read ad7175 ID(0x0CDX) or AD7177 ID(0x4FDX)
            if ((ret[0]<<8|ret[1]) & 0xFFF0) != self.chip_id:
                self.reset()
                read_times -= 1
                time.sleep_ms(1)
            else:
                self.cs.value(1)
                return True
        self.cs.value(1)
        return False

    def get_raw_samples(self, channel, count=100, sample_rate=1000):
        assert 1 <= count <= AD717XDef.DEFAULT_COUNT
        assert channel in AD717XDef.CHANNELS
        dma_ch = 0
        self.ic_init()
        self.is_communication_ok()
        data = array.array('I', [0] * count)
        channel = CHAN(channel)
        self.select_single_channel(channel)
        self.set_sampling_rate(channel, sample_rate)
        rd_data = self.d
        wr_data = rd_data & 0xFF0F | 0x0000
        wr_data &= ~AD717XDef.CLOCKSEL_MASK
        wr_data |= self.clock
        self.write_register(AD717XDef.ADC_MODE_REG_ADDR, [wr_data>>8, wr_data&0xff])
        self.write_register(AD717XDef.INTERFACE_MODE_REG_ADDR, [0x00, 0xC0])
        self.sm.init(self.output, freq=32_000_000, sideset_base=self.spi.clk, in_base=self.spi.miso)
        self.cs.value(0)
        rp2_util.sm_restart(self.slot, self.output)
        self.sm.active(1)
        rp2_util.sm_dma_get(dma_ch, self.slot, data, count)
        for i in range(1000):
            if rp2_util.dma_transfer_count(dma_ch) == 0:
                break
            else:
                time.sleep_ms(5)
        else:
            print("Acquistion error")
        self.sm.active(0)
        self.cs.value(1)
        # return data if not isTimeout else []
        return array.array("f", [self._value_2_mvolt(i >>8, self.mvref, self.resolution) for i in data])

    def get_raw_samples2(self, channel, data_I, data_F, sample_rate=1000):
        assert channel in AD717XDef.CHANNELS
        dma_ch = 0
        self.ic_init()
        self.is_communication_ok()
        count = len(data_I)
        channel = CHAN(channel)
        self.select_single_channel(channel)
        self.set_sampling_rate(channel, sample_rate)
        rd_data = self.d
        wr_data = rd_data & 0xFF0F | 0x0000
        wr_data &= ~AD717XDef.CLOCKSEL_MASK
        wr_data |= self.clock
        self.write_register(AD717XDef.ADC_MODE_REG_ADDR, [wr_data>>8, wr_data&0xff])
        self.write_register(AD717XDef.INTERFACE_MODE_REG_ADDR, [0x00, 0xC0])
        self.sm.init(self.output, freq=32_000_000, sideset_base=self.spi.clk, in_base=self.spi.miso)
        self.cs.value(0)
        rp2_util.sm_restart(self.slot, self.output)
        self.sm.active(1)
        rp2_util.sm_dma_get(dma_ch, self.slot, data_I, count)
        for i in range(1000):
            if rp2_util.dma_transfer_count(dma_ch) == 0:
                break
            else:
                time.sleep_ms(5)
        else:
            print("Acquistion error")
        self.sm.active(0)
        self.cs.value(1)
        # return data if not isTimeout else []
        for index, value in enumerate(data_I):
            data_F[index] = self._value_2_mvolt(value >>8, self.mvref, self.resolution)
        return data_F

    # def _irq_handler(self, sm):
    #     pass


# from soft_spi import rtSoftSPI
# ad7175 = PLAD7175(rtSoftSPI((10, 11, 12, 13), 1, 1, baudrate=500000))
# def test(rate=1000, time_ms=100):
# # from mix.driver.bus.soft_spi import rtSoftSPI
    
#     print(ad7175.datalogger("ch0", rate, time_ms))
#     # ad7175 = PLAD7175(rtSoftSPI((2, 3, 4, 5), 1, 1, baudrate=500000))