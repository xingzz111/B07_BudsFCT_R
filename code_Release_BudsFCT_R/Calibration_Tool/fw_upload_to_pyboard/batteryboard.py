# -*- coding: utf-8 -*-

import time
from mix.driver.module.mix_board import MIXBoard


class BatteryBoard(MIXBoard):
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
        "i2cWrite", "i2cRead"
        ] + MIXBoard.rpc_public_api

    def __init__(self, base_iic):
        super(BatteryBoard, self).__init__()
        self.i2c = base_iic

    def i2cWrite(self, slave, data):
        if not isinstance(data, list):
            data = [data]
        msg = 'Slave:0x{:02x} write_data:{} '.format(slave, ' '.join('0x{:02x}'.format(d) for d in data))
        print('i2cWrite', msg)
        return self.i2c.write(slave, data)

    def i2cRead(self):
        # msg = 'Slave:0x{:02x} rd_len:{} '.format(slave, rd_len)
        print('i2cRead', self.i2c.read(0x55, 0x0072, 20))
        return 'done'
    
    def write_and_read(self):
        print('i2cWriteAndRead', self.i2c.write_and_read(0x55, [0x3e, 0x72, 0x00], 36))
        return 'done'
