# -*- coding: utf-8 -*-

import time
from mix.driver.ic.mcp472x import MCP4725
from mix.driver.ic.cat9555 import CAT9555
from mix.driver.ic.ads1115 import ADS1115
from widthMeasure import PIO_widthMeasure
from mix.driver.module.mix_board import MIXBoard

class BaseDef:
    IO_OFFSET = 0
    IO_PINS = 16
    EMULATOR_REG_SIZE = 256
    CAT9555_INIT_DIR_STATUS = [0x00, 0x00]
    CAT9555_INIT_PIN_STATUS = [0x00, 0x00]
    RETURN_DONE = True
    RETURN_ERROR = False

    I2C_ADDR = {
        "cat9555": [0x20, 0x21, 0x22, 0x23, 0x24],
    }
    DEFAULT_DELAY_S = 0.005
    map_path = "mix/addon/test_function/io_map.json"

class BoardArgCheckError(Exception):
    """
    Check parameter results do not conform to the function afferent specification, use this raise
    """
    def __init__(self, err):
        Exception.__init__(
            self, "[BASEBoard arg check exception] %s" % (err))


class BaseBoardError(Exception):
    def __init__(self, err_str):
        self.err_reason = str(err_str)

    def __str__(self):
        return self.err_reason


class BaseBoard(MIXBoard):
    """
    BaseBoard function class
    :param      tca9548:       instance/None,  Class instance of TCA9548, if not using this parameter, will create emulator
    :param      io_exp0:       instance/None,  Class instance of CAT9555, if not using this parameter, will create emulator

    :example:
            axi = AXI4LiteBus('/dev/MIX_I2C_4', 256)
            i2c = PLI2CBus(axi)
            tca9548 = TCA9548(0x70,i2c)
            ad5627 = AD5627(0x50, i2c)
            io_exp0 = CAT9555(0x20,i2c)

    """
    rpc_public_api = [
        "reset", "fw_version", "set_io_switch", "get_io_dir", "set_iolist_dir", "get_iolist_status","fixtureID"
        ] + MIXBoard.rpc_public_api

    def __init__(self, base_iic, eeprom=None):
        super(BaseBoard, self).__init__(eeprom)
        self.io_chips = []
        for i in BaseDef.I2C_ADDR.get('cat9555'):
            io_exp = CAT9555(i, base_iic)
            self.io_chips.append(io_exp)
        # self.ch446q = CH446Q(PRMCAT9555(0x20, base_iic))
        self.dac = MCP4725(0x60, base_iic)
        # self.adc = PRMADS1115(0x48, base_iic, "fs1")
        self.meas = PIO_widthMeasure(7, pin_num=22)

    def reset(self):
        """
        reset the module, the same function like  post_power_on_init
            int 0
        :return:
        """
        return self._module_init()

    def fw_version(self, key=None):
        """
        :return:
        """
        verTab = {'MIX_FW_PACKAGE': 'Coreboard_v0.0.1'}
        return verTab.get(key, False) if key else verTab

    def post_power_on_init(self):
        """
        init module after power on
        :param timeout:
            int 0
        :return:
        """
        self._module_init()

    def _module_init(self):
        """
        Translation Board Init cat9555 output mode
        :return: str "done"/"error";
        :example:
                self.init_baseboard_device()
        """
        # Init Dac and set 0
        for cat9555 in self.io_chips:
            cat9555.set_pins_dir(BaseDef.CAT9555_INIT_DIR_STATUS)
            reply = cat9555.get_pins_dir()
            if reply != BaseDef.CAT9555_INIT_DIR_STATUS:
                raise BaseBoardError("Cat9555 init failed!")
            cat9555.set_ports(BaseDef.CAT9555_INIT_PIN_STATUS)
            reply = cat9555.get_ports_state()
            if reply != BaseDef.CAT9555_INIT_PIN_STATUS:
                raise BaseBoardError("Cat9555 init failed!")
        # self.ch446q.reset()
        self.dac.reset()
        # self.adc.set_sampling_rate(0, 128)
        return BaseDef.RETURN_DONE

    def set_io_switch(self, io_list):
        """
        switch 3 cat9555 io;check i2c_channel is 0
        set io switch
        :param io_list:     list,[[9,1],[10,0],[12,1]]
        :return: str "done"/"error";
        :example:
                self.set_io_switch([[9,1],[10,1],[11,0],[12,1]])
                self.set_io_switch([[9,0]])
        """
        result = True
        for item in io_list:
            assert isinstance(item, list)
            io, level = item
            assert io >= BaseDef.IO_OFFSET
            assert level in (0, 1)
            index, pin = divmod(io - BaseDef.IO_OFFSET, BaseDef.IO_PINS)
            cat9555 = self.io_chips[index]
            cat9555.set_pin(pin, level)
            bit_level = cat9555.get_pin_state(pin)
            if bit_level != level:
                result = False
        return result

    def get_io_dir(self, io):
        """
        get cat9555 io input/output mode
        :param io:   int, 9
        :return: str,  input/output
        """
        assert isinstance(io, int) and io >= 0
        index, pin = divmod(io - BaseDef.IO_OFFSET, BaseDef.IO_PINS)
        cat9555 = self.io_chips[index]
        return cat9555.get_pin_dir(pin)

    def set_iolist_dir(self, io_list, dir):
        """
        switch cat9555 io input/output mode
        :param io_list:     list, [9,10,11]
        :param dir: input/output
        :return: str,  done
        """
        assert isinstance(io_list, list)
        assert dir in ("input", "output")
        for io in io_list:
            index, pin = divmod(io - BaseDef.IO_OFFSET, BaseDef.IO_PINS)
            cat9555 = self.io_chips[index]
            cat9555.set_pin_dir(pin, dir)
        return BaseDef.RETURN_DONE

    def get_iolist_status(self, io_list):
        """
        get cat9555 io high/low status
        :param io_list:     list,  [9,10,11]
        :return: dict {9:0,10:1,11:1}
        :example:
                self.get_iolist_status([9,10,11])
                self.get_iolist_status([9])
        """
        assert isinstance(io_list, list)
        result = dict()
        for io in io_list:
            index, pin = divmod(io - BaseDef.IO_OFFSET, BaseDef.IO_PINS)
            cat9555 = self.io_chips[index]
            result.setdefault(io, cat9555.get_pin_state(pin))
        return result

    def fixtureID(self, info=None):
        if info:
            assert(len(info) > 17, "Length must be less then 17")
            self.write_serialnumber(info)
        return self.read_serialnumber()
    def setDac(self, volt):
        return self.dac.set_output(volt)

    # def readVolt(self, channel):
    #     return self.adc.read_volt(channel)

    def mes_freq(self, duration_s=0.1):
        return self.meas.measure_hf(timeout_s=duration_s)