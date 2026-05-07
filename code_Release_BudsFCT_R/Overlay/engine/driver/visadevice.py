import time, os,json
from datetime import datetime
from pyvisa import ResourceManager


class Visa(object):

    def __init__(self, port_name, publisher=None):
        self.__port_name = port_name
        self.publisher = publisher
        self.__rm = None
        self.__session = None
        self.__isOpen = False

    def open(self):
        # assert self.__port_name in self.list_resources()
        try:
            self.__rm = ResourceManager()
            self.__session = self.__rm.open_resource(self.__port_name)
            self.__session.read_termination = "\r"
            #self.set_termination("\r\n")
            self.__isOpen = True
            print ("open success")
        except Exception as e:
            raise e


    def close(self):
        try:
            if self.__session:
                self.__session.close()
                del self.__session
                del self.__rm
                print ("close success")
            self.__isOpen = False
        except Exception as e:
            raise e

    def log(self, msg):
        if self.publisher:
            self.publisher.publish(str(datetime.now()) + ' ' * 3 + msg)

    @classmethod
    def list_resources(self):
        rm = ResourceManager()
        return rm.list_resources()

    def send(self, cmd):
        if self.__isOpen:
            self.__session.write(cmd)
            self.log("send: {}".format(cmd))
            return True
        else:
            self.log("{} Is Not Open".format(self.__port_name))
            return False

    def read(self):
        if self.__isOpen:
            reply = self.__session.read()
            self.log("recv: {}".format(reply))
            return reply
        else:
            self.log("{} Is Not Open".format(self.__port_name))
            return False


    def query(self, cmd):
        if self.__isOpen:
            self.log("send: {}".format(cmd))
            reply = self.__session.query(cmd)
            self.log("recv: {}".format(reply))
            return reply
        else:
            self.log("{} Is Not Open".format(self.__port_name))
            return False

    def set_termination(self, termination="\r\n"):
        if self.__session:
            self.__session.read_termination = termination
            return True
        else:
            return False



class KeithleyDriver(Visa):

    def __init__(self, port_name, publisher=None):
        super(KeithleyDriver, self).__init__(port_name, publisher)
        self.open()

    def get_local_info(self):
        """
        KEITHLEY INSTRUMENTS,MODEL nnnn,xxxxxxx,yyyyy
        nnnn = the model number
        xxxxxxx = the serial number
        yyyyy = the firmware revision level
        :return:
        """
        try:
            info = dict()
            reply = str(self.query("*IDN?"))
            reply = reply.strip()
            vendor, model, sn, fw_v = reply.split(",")
            info.setdefault("vendor code", vendor)
            info.setdefault("model number", model)
            info.setdefault("serial number", sn)
            info.setdefault("fw version", fw_v)
            return info
        except Exception as e:
            return e

    def reset(self):
        """
        Returns the instrument to default settings
        :return:
        """
        self.send("*RST")
        return True

    def cls(self):
        """
        Returns the instrument to default settings
        :return:
        """
        self.send("*CLS")
        return True

class SignalGenerator_bk(KeithleyDriver):

    rpc_public_api = ["open_device","close_device", "reset_device", "output_wave", "diable_wave"]

    def __init__(self, portName, publisher=None):
        super(SignalGenerator, self).__init__(portName, publisher)
        self.open_device()
        # self.reset_device()
        self.is_open = True
        for i in range(2):
            self.output_wave(1, 128, 1.8, 0.9, "SQUARE")
            time.sleep(1)
            self.output_wave(2, 128, 1.8, 0.9, "SQUARE")

    def log(self, msg):
        if self.publisher:
            self.publisher.publish(msg)
            self.publisher.publish('\n')

    def open_device(self):
        self.open()
        self.is_open = True
        return True

    def close_device(self):
        self.close()
        self.is_open = False
        return True

    def reset_device(self):            
        self.reset()
        self.cls()
        return True

    # def output_wave(self, channel, frequency=1000, amplitude=1.0, offset=0.0, waveform="SIN"):
    #     self.send(f"INST:SEL CH{channel}")           # Select the channel
    #     self.send(f"FUNC {waveform}")                # Setting waveform type (SIN/SQUARE/SAW/)
    #     self.send(f"FREQ {frequency}")               # Setting frequency (Hz)
    #     self.send(f"VOLT {amplitude}")               # Setting amplitude (Vpp)
    #     self.send(f"VOLT:OFFS {offset}")             # Setting shift volage (V)
    #     self.send("OUTP ON")                         # Ouput ON
    #     self.log(f"Signal generator configured: {frequency} Hz, {amplitude} V, {offset} V offset, {waveform}")


    # def diable_wave(self):
    #     """Close signal generator"""
    #     self.send("OUTP OFF")
    #     self.log("Signal generator:OUTP OFF")



    def output_wave(self, ch, frequency=128, amplitude=1.8, offset=0.9, wave="SQUARE", duty_cycle=50):

        # ch = 1
        self.send(f":SOUR{ch}:FUNC SQUARE")          # 设置通道1为方波
        self.send(f":SOUR{ch}:FREQ {frequency}")     # 设置频率
        self.send(f":SOUR{ch}:VOLT {amplitude}")     # 设置幅度
        self.send(f":SOUR{ch}:VOLT:OFFS {offset}")   # 设置偏移
        self.send(f":SOUR{ch}:SQU:DCYC {duty_cycle}")# 设置占空比
        # # ch = 2
        # self.send(f":SOUR{ch}:FUNC SQUARE")          # 设置通道1为方波
        # self.send(f":SOUR{ch}:FREQ {frequency}")     # 设置频率
        # self.send(f":SOUR{ch}:VOLT {amplitude}")     # 设置幅度
        # self.send(f":SOUR{ch}:VOLT:OFFS {offset}")   # 设置偏移
        # self.send(f":SOUR{ch}:SQU:DCYC {duty_cycle}")# 设置占空比

        # ch = 1
        self.send(f":OUTP{ch} ON")
        # ch = 2 
        # self.send(f":OUTP{ch} ON")   

       

    def diable_wave(self,ch):
        """Close signal generator"""
        self.send(f":OUTP{ch} OFF")  

    
class SignalGenerator(object):

    def __init__(self,publisher=None):
        self.publisher = publisher
        # self.__rm = ResourceManager()
        # self.open_device()

    def port_name_from_cfg(self):
        user_home = os.path.expanduser('~')
        _path = f"{user_home}/testerconfig/fixture_config.json"

        with open(_path, 'r') as f:
            file = f.read()
            device = json.loads(file)
        port_name = device.get("sg")
        return port_name

    def open_device(self):
        # 选择 Rigol DG 8200 Pro
        self.__rm = ResourceManager()
        port_name = self.port_name_from_cfg()
        instrument = self.__rm.open_resource(port_name)  # 替换为实际地址
        # 设置方波参数
        frequency = 128  # 1 kHz
        amplitude = 1.8  # 1 Vpp
        offset = 0.9      # 0 V DC offset
        duty_cycle = 50   # 50% 占空比
        for ch in range(1,3):
            instrument.write(f":SOUR{ch}:FUNC SQUARE")          # 设置通道1为方波
            instrument.write(f":SOUR{ch}:FREQ {frequency}")     # 设置频率
            instrument.write(f":SOUR{ch}:VOLT {amplitude}")     # 设置幅度
            instrument.write(f":SOUR{ch}:VOLT:OFFS {offset}")   # 设置偏移
            instrument.write(f":SOUR{ch}:SQU:DCYC {duty_cycle}")# 设置占空比
            instrument.write(f":OUTP{ch} ON")






if __name__ == '__main__':
    visa = Visa("USB0")
    print(visa.list_resources())
    visa = SignalGenerator()
    # visa.output_wave(1, 128, 1.8, 0.9, "SQUARE")
    # time.sleep(1)
    # visa.output_wave(2, 128, 1.8, 0.9, "SQUARE")
    # visa.configure_signal_generator(1, 128, 1.8, 0.9, "SQUARE")
    # time.sleep(10)
    # visa.close_signal_generator()

