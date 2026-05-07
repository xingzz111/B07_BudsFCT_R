import rp2
import gc
import time
from rp2 import PIO
from machine import Pin, PWM

class PIO_widthMeasure:

    def __init__(self, slot, pin_num=15):
        """
        初始化 PIO 硬件定时器

        :param period_us: 定时周期，单位为微秒
        :param freq: PIO 状态机频率，默认为 10 MHz
        """
        self.slot = slot

        # 创建 PIO 状态机
        self.sm = None
        self.in_base = Pin(pin_num, Pin.IN)
        # self.sm = rp2.StateMachine(self.slot, self.high_low_detect, freq=100_000_000, in_base=self.in_base)


    # 定义 PIO 先低电平，后高电平
    @rp2.asm_pio(in_shiftdir=PIO.SHIFT_LEFT)
    def low_high_detect():
        wrap_target()
        pull()
        mov(x, osr) #pull x form txfifo
        wait(1, pin, 0)
        wait(0, pin, 0) #等待一个完整的下降沿，接下来就开始低电平的计时
        label("detect_low")
        in_(pins, 1)
        in_(null, 31)
        mov(y, isr)
        jmp(y_dec, "next") #如果Pin是否是0， 是0则继续执行，否则跳转到next
        jmp(x_dec, "detect_low") #检测计数器有没有到0，如果到了0则继续执行，否则跳转到detect_low
        jmp("end")
        label("next")
        mov(isr, x)
        push()

        mov(x, osr) #pull x form txfifo
        # wait(0, pin, 0)
        # wait(1, pin, 0) #等待一个完整的上升沿，接下来就开始高电平的计时
        label("detect_high")
        in_(pins, 1)
        in_(null, 31)
        mov(y, isr)
        jmp(not_y, "end") #如果Pin是否是1， 是1则继续执行，否则跳转到end
        jmp(x_dec, "detect_high")
        label("end")
        mov(isr, x)
        push()
        wrap()

    @rp2.asm_pio(in_shiftdir=PIO.SHIFT_LEFT)
    def high_low_detect():
        wrap_target()
        pull()
        mov(x, osr) #pull x form txfifo
        wait(0, pin, 0)
        wait(1, pin, 0) #等待一个完整的上升沿，接下来就开始高电平的计时
        label("detect_high")
        in_(pins, 1)
        in_(null, 31)
        mov(y, isr)
        jmp(not_y, "next") #如果Pin是否是0， 是0则继续执行，否则跳转到next
        jmp(x_dec, "detect_high") #检测计数器有没有到0，如果到了0则继续执行，否则跳转到detect_low
        jmp("end")
        label("next")
        mov(isr, x)
        push()

        # 5个周期为1个单位时间，即1个单位时间有5个周期
        mov(x, osr) #pull x form txfifo
        # wait(0, pin, 0)
        # wait(1, pin, 0) #等待一个完整的下降沿，接下来就开始高电平的计时
        label("detect_low")
        in_(pins, 1)
        in_(null, 31)
        mov(y, isr)
        jmp(y_dec, "end") #如果Pin是否是0， 是0则继续执行，否则跳转到end
        jmp(x_dec, "detect_low")
        label("end")
        mov(isr, x)
        push()
        wrap()


    def _measure(self, mode, freq, timeout_s):
        assert mode in ("low_high", "high_low")
        if mode == "low_high":
            # self.sm.init(self.low_high_detect, freq=freq, in_base=self.in_base)
            self.sm = rp2.StateMachine(self.slot, self.low_high_detect, freq=freq, in_base=self.in_base)
        else:
            self.sm = rp2.StateMachine(self.slot, self.high_low_detect, freq=freq, in_base=self.in_base)
            # self.sm.init(self.high_low_detect, freq=freq, in_base=self.in_base)
        # 清空 TX FIFO
        while self.sm.tx_fifo() > 0:
            self.sm.get()
        # 清空 RX FIFO
        while self.sm.rx_fifo() > 0:
            self.sm.get()
        self.sm.active(1)
        # timeout_s * 1_000_000_000
        counts = 1000000000
        self.sm.put(counts)
        time.sleep(timeout_s)
        value = list()
        for item in range(self.sm.rx_fifo()):
            value.append(self.sm.get())
        if not value:
            return False
        if len(value) == 1:
            return False
        self.sm.active(0)
        del self.sm
        gc.collect()
        period = 1_000_000_000.0 / freq * 5.0
        low = (counts - int(value[0])) * period
        high = (counts - int(value[1])) * period
        dt = dict()
        dt["low"] = low
        dt["high"] = high
        dt["freq"] = 1_000_000_000.0/(low+high)
        dt["duty"] = high/(high+low)
        return dt
    
    def measure_lf(self, mode="low_high", timeout_s=1):
        return self._measure(mode, 10_000, timeout_s)
    
    def measure_hf(self, mode="low_high", timeout_s=1):
        return self._measure(mode, 100_000_000, timeout_s)