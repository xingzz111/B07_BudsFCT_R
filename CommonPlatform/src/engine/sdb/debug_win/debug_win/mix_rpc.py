

import time
from rpcClient import MixRpc



if __name__ == "__main__":
    # tasklist /FI "IMAGENAME eq python.exe"
    # taskkill /PID 11796 /F

    mix_rpc_client = MixRpc({"requester": "tcp://169.254.1.32:7801", "type": "rpc"})
    # mix_rpc_client = MixRpc({"requester": "tcp://169.254.1.33:7801", "type": "rpc"})

    # # ##### PSoC Programmer Power On
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "WIB_DUT_GND_TO_FIX_GND")
    # print("baseboard.relay = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "WIB_DUT_SWD_SW_EN")
    # print("baseboard.relay = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "WIB_DUT_VDD_UI_SWD_VTARG_EN")
    # print("baseboard.relay = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "WIB_DUT_VDD_UI_SWD_VTARG_EN")
    # print("baseboard.relay = ", ret)
    # time.sleep(1)
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "WIB_DUT_VDD_UI_MMSWD_VTARG_EN")
    # print("baseboard.relay = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "WIB_DUT_MMSWD_SW_EN")
    # print("baseboard.relay = ", ret)
    # time.sleep(1)


    # ##### i2c scan
    # # [base, wib, pdm, dut, tmp1, tm2]
    # ret = mix_rpc_client.rpc_call("baseboard.scan_slave_addr", 2)
    # print("baseboard.scan_slave_addr = ", ret)
    # for addr in ret:
    #     print(hex(addr))

    # # ##### touch
    # print("=" * 50, "power on")
    # ret = mix_rpc_client.rpc_call("baseboard.reset")
    # print("baseboard.reset = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "WIB_DUT_GND_TO_FIX_GND")
    # print("baseboard.relay = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "BASE_PP1V8_OUT_EN")
    # print("baseboard.relay = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "BASE_PP4V5_OUT_EN")
    # print("baseboard.relay = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "BASE_FIX_I2C_SEL@NO")
    # print("baseboard.relay = ", ret)
    #
    # print("="*50, "reset")
    # ret = mix_rpc_client.rpc_call("fix_dut_iic.scan")
    # print("fix_dut_iic.scan = ", ret)
    # ret = mix_rpc_client.rpc_call("fix_dut_iic.read", 0x08, 0x00, 8)
    # print("fix_dut_iic.read = ", ret)
    # ret = mix_rpc_client.rpc_call("fix_dut_iic.write", 0x08, [0x70, 0xca])
    # print("fix_dut_iic.write = ", ret)
    # ret = mix_rpc_client.rpc_call("fix_dut_iic.read", 0x08, 0x00, 8)
    # print("fix_dut_iic.read = ", ret)
    # ret = mix_rpc_client.rpc_call("fix_dut_iic.read", 0x08, 0x30, 8)
    # print("fix_dut_iic.read = ", ret)
    #
    # print("=" * 50, "function 0x01")
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "WIB_DUT_CAP_BTN_0_EN")
    # print("baseboard.relay = ", ret)
    # time.sleep(1)
    # ret = mix_rpc_client.rpc_call("fix_dut_iic.read", 0x08, 0x30, 8)
    # print("fix_dut_iic.read = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "WIB_DUT_CAP_BTN_0_EN", "DISCONNECT")
    # print("baseboard.relay = ", ret)
    #
    # print("=" * 50, "bluetooth 0x02")
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "WIB_DUT_CAP_BTN_1_EN")
    # print("baseboard.relay = ", ret)
    # time.sleep(1)
    # ret = mix_rpc_client.rpc_call("fix_dut_iic.read", 0x08, 0x30, 8)
    # print("fix_dut_iic.read = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "WIB_DUT_CAP_BTN_1_EN", "DISCONNECT")
    # print("baseboard.relay = ", ret)
    #
    # print("=" * 50, "action 0x04")
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "WIB_DUT_CAP_BTN_2_EN")
    # print("baseboard.relay = ", ret)
    # time.sleep(1)
    # ret = mix_rpc_client.rpc_call("fix_dut_iic.read", 0x08, 0x30, 8)
    # print("fix_dut_iic.read = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "WIB_DUT_CAP_BTN_2_EN", "DISCONNECT")
    # print("baseboard.relay = ", ret)
    #
    # print("=" * 50, "rotary 00")
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "WIB_DUT_RAD_SET_00")
    # print("baseboard.relay = ", ret)
    # time.sleep(1)
    # ret = mix_rpc_client.rpc_call("fix_dut_iic.read", 0x08, 0x30, 8)
    # print("fix_dut_iic.read = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "WIB_DUT_RAD_SET_00", "DISCONNECT")
    # print("baseboard.relay = ", ret)
    #
    # print("=" * 50, "rotary 01")
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "WIB_DUT_RAD_SET_01")
    # print("baseboard.relay = ", ret)
    # time.sleep(1)
    # ret = mix_rpc_client.rpc_call("fix_dut_iic.read", 0x08, 0x30, 8)
    # print("fix_dut_iic.read = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "WIB_DUT_RAD_SET_01", "DISCONNECT")
    # print("baseboard.relay = ", ret)


    # # ##### pdm
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "BASE_SPK_OUT_SEL@FL_J3800")
    # print("baseboard.relay = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "BASE_PDM_RX_SW_EN")
    # print("baseboard.relay = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "WIB_PDM_RX_MUX_SEL@DUT_PDM_DIN0")
    # print("baseboard.relay = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.sine_waveform_enable", 1000, "200mV", 15000)
    # print("baseboard.sine_waveform_enable = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.get_fft", timeout_ms=10000)
    # print("baseboard.get_fft = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.sine_waveform_disable")
    # print("baseboard.sine_waveform_disable = ", ret)


    # # ##### mic cal
    # # ret = mix_rpc_client.rpc_call("baseboard.relay", "BASE_SPK_OUT_SEL@FL_J3800")   # 2V, 9000, 93.9; 2V, 9000, 93.9
    # # ret = mix_rpc_client.rpc_call("baseboard.relay", "BASE_SPK_OUT_SEL@FR_J3801")   # 2V, 13000, 94.1; 2V, 13000, 93.9
    # ret = mix_rpc_client.rpc_call("baseboard.relay", "BASE_SPK_OUT_SEL@BL_J3802")   # 400mV, 11000, 94.0; 400mV, 5000, 93.9
    # # ret = mix_rpc_client.rpc_call("baseboard.relay", "BASE_SPK_OUT_SEL@BR_J3803")   # 2V, 9000, 94.0; 2V, 8000, 94.0
    # print("baseboard.relay = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.sine_waveform_enable", 1000, "400mV", 5000)
    # print("baseboard.sine_waveform_enable = ", ret)


    # # ##### write cal
    # index = 103
    # # ret = mix_rpc_client.rpc_call("baseboard.write_calibration_cell", index, 3, 9000, 3800)   # 100
    # # ret = mix_rpc_client.rpc_call("baseboard.write_calibration_cell", index, 3, 13000, 3801)   # 101
    # # ret = mix_rpc_client.rpc_call("baseboard.write_calibration_cell", index, 3, 11000, 3802)   # 102
    # ret = mix_rpc_client.rpc_call("baseboard.write_calibration_cell", index, 3, 8000, 3803)   # 103
    # print("baseboard.write_calibration_cell = ", ret)
    # ret = mix_rpc_client.rpc_call("baseboard.read_calibration_cell", index)
    # print("baseboard.read_calibration_cell = ", ret)


    # # ##### dmm
    # ret = mix_rpc_client.rpc_call("dmm.reset")
    # print("dmm.reset = ", ret)
    # ret = mix_rpc_client.rpc_call("dmm.set_measure_path", "ch0", "1000mv")
    # print("dmm.set_measure_path = ", ret)
    # ret = mix_rpc_client.rpc_call("dmm.measure")
    # print("dmm.measure = ", ret)

    pass




