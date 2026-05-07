import rp2
import gc
import time
from rp2 import PIO
from machine import Pin, PWM

class PIO_pulsMeasure:

    def __init__(self, slot, pin_num=28):
        """
        初始化 PIO 硬件定时器

        :param period_us: 定时周期，单位为微秒
        :param freq: PIO 状态机频率，默认为 10 MHz
        """
        self.slot = slot

        # 创建 PIO 状态机
        self.sm = None
        self.in_base = Pin(pin_num, Pin.IN)
        self.freq = 1_000_000
        self.sm = rp2.StateMachine(self.slot, self.detect_3_times_pusle, freq=self.freq, in_base=self.in_base)

    # 定义 PIO 先低电平，后高电平
    @rp2.asm_pio(in_shiftdir=PIO.SHIFT_LEFT)
    def detect_3_times_pusle():
        wrap_target()
        pull()
        # wait(1, pin, 0)
        wait(0, pin, 0) #等待一个完整的下降沿，接下来就开始低电平的计时
        label("init")
        mov(isr, x)
        push()
        label("first")
        in_(pins, 1)
        in_(null, 31)
        mov(y, isr)
        jmp(y_dec, "second") #如果Pin是否是0， 是0则继续执行，否则跳转到second
        jmp(x_dec, "first") #检测计数器有没有到0，如果到了0则继续执行，否则跳转到detect_low
        jmp(x_dec, "end") #检测计数器有没有到0，如果到了0则继续执行，否则跳转到detect_low

        label("second")

        in_(pins, 1)
        in_(null, 31)
        mov(y, isr)
        jmp(not_y, "init") #如果Pin是否是1， 是1则继续执行，否则跳转到init
        jmp(x_dec, "second") #检测计数器有没有到0，如果到了0则继续执行，否则跳转到sedond
        jmp(x_dec, "end") #检测计数器有没有到0，如果到了0则继续执行，否则跳转到detect_low

        label("end")
        mov(x, osr) #pull x form txfifo
        push()
        wrap()

    def measure(self, timeout_s, nums=3):
        dt = dict()
        # 清空 TX FIFO
        while self.sm.tx_fifo() > 0:
            self.sm.get()
        # 清空 RX FIFO
        while self.sm.rx_fifo() > 0:
            self.sm.get()
        counts = timeout_s * 1_000_000_000
        value = list()
        self.sm.active(0)
        self.sm.active(1)
        # counts = 1000000000
        self.sm.put(counts)
        start_time = time.time()
        while True:
            if self.sm.rx_fifo() > 0:
                value.append(self.sm.get())
                if len(value) == nums:
                    break
            if time.time() - start_time > timeout_s:
                break
        if len(value) < nums:
            self.sm.active(0)
            self.sm.restart()
            # self.sm.active(0)
            return dt
        self.sm.active(0)
        self.sm.restart()
        # self.sm.active(0)
         # 清空 TX FIFO
        while self.sm.tx_fifo() > 0:
            self.sm.get()
        # 清空 RX FIFO
        while self.sm.rx_fifo() > 0:
            self.sm.get()
        # del self.sm
        period = 1_000_000_000.0 / self.freq * 5.0
        for i in range(len(value) - 1):
            dt[i] = (int(value[i]) - int(value[i+1])) * period / 1000_000.0
        return dt
    
# def enable_pwm(pin_num, freq, duty_pecent):
#     # 检查pin_num是否在0到20之间，确保引脚编号有效
#     assert 0<= pin_num <= 20
#     # assert 0<= freq <= 10000
#     assert 0<= duty_pecent <=1
#     _pwm = PWM(Pin(pin_num))
#     _pwm.freq(freq)
#     _pwm.duty_u16(int(65536.0*duty_pecent))

# # enable_pwm(13, 10, 0.1)

# a = PIO_widthMeasure(4)
# def test(freq=10, duration_s=1, num=3):
#     _pwm = PWM(Pin(13, Pin.OUT, Pin.PULL_UP))
#     time.sleep(0.1)
#     _pwm.freq(freq)
#     _pwm.duty_u16(int(65536.0/2))
#     t= a.measure(duration_s, num)
#     _pwm.deinit()
#     return t

    
