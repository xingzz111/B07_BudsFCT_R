import asyncio
import time
from cgitb import reset

from driver.rp2Device import Rp2Device
from addon.driver.hardware import HardWare
from rtlib.taskScheduler import ConcurrencyAwareAsyncMonitor, SequentialTaskScheduler, InterActiveMonitor





async def program1(program_cmd, a):
    # client = Rp2Device("COM101", 115200)
    # a = HardWare(client)
    a.reset()
    a.disconnect8300Power()
    await asyncio.sleep(2)
    a.jlinkPowerOn()
    await asyncio.sleep(2)

    monitor = InterActiveMonitor(program_cmd, None, 100)
    return await monitor.run()

async def program2(program_cmd):
    client = Rp2Device("COM102", 115200)
    a = HardWare(client)
    # a.reset()
    a.disconnect8300Power()
    await asyncio.sleep(2)
    a.jlinkPowerOn()
    await asyncio.sleep(2)

    monitor = InterActiveMonitor(program_cmd, None, 100)
    return await monitor.run()


program_cmd1 = ["C:/Program Files/SEGGER/JLink/JFlash.exe", "-usb603000192"
               "-jlinkdevicesxmlpathC:/Program Files/SEGGER/JLink/JLinkDevices",
               "-openprjC:/Program Files/SEGGER/JLink/barista_bringup.jflash",
               "-openD:/RestorePackage/JlinkTools/PanamaManufacturing_3.2.7.hex", "-auto", "-exit"]

program_cmd2 = ["C:/Program Files/SEGGER/JLink/JFlash.exe", "-usb602010928"
               "-jlinkdevicesxmlpathC:/Program Files/SEGGER/JLink/JLinkDevices",
               "-openprjC:/Program Files/SEGGER/JLink/barista_bringup.jflash",
               "-openD:/RestorePackage/JlinkTools/PanamaManufacturing_3.2.7.hex", "-auto", "-exit"]



rp2_device1 = Rp2Device("COM101", 115200)
hardware1 = HardWare(rp2_device1)


rp2_device2 = Rp2Device("COM102", 115200)
hardware2 = HardWare(rp2_device2)


# a.setStateByName("DUT_TP5_JRESET","JRESET_1V7",1)

# a.chargerShutDownAndUartSwitch()
# input("wait 5v:")
# a.chargerPowerOn(5000,500,3)



# async def aaaaa():
#     await asyncio.gather(program1(program_cmd1,hardware))
# asyncio.run(aaaaa())

hardware1.reset()
# hardware2.reset()
time.sleep(2)
for i in range(100):
    with open("C:/Users/CTOS/Desktop/cal_time.txt","a+") as f:

        hardware1.disconnect8300Power()
        hardware1.cal8300PowerOn()


        # hardware2.disconnect8300Power()
        # hardware2.cal8300PowerOn()

        time.sleep(1)
        rp2_device1.rpc_call("mixdevice.measure_pulse", 1, 3)
        # time.sleep(40)
        r1 = rp2_device1.rpc_call("mixdevice.measure_pulse", 50, 5)

        # rp2_device2.rpc_call("mixdevice.measure_pulse", 1, 3)
        # # time.sleep(40)
        # r2 = rp2_device2.rpc_call("mixdevice.measure_pulse", 50, 5)

        # print(f"====== test :{i+1} result:{r}")
        f.write(f"===slot1=== test :{i+1} result:{r1}\n")
        # f.write(f"===slot2=== test :{i + 1} result:{r2}\n")
        time.sleep(1)




