import rp2
import time
import machine

PIO2 = rp2.PIO(2)

@rp2.asm_pio()
def pio_measure_high_low():
    wrap_target()
    wait(1, pin, 0)                       # 0
    mov(x, invert(null))                  # 1
    label("2")
    jmp(x_dec, "3")                       # 2
    label("3")
    jmp(pin, "2")                         # 3
    mov(isr, x)                           # 4
    push(noblock)                         # 5
    wrap()

# -------------------- #
# pio_measure_low_high #
# -------------------- #

@rp2.asm_pio()
def pio_measure_low_high():
    wrap_target()
    wait(0, pin, 0)                       # 0
    mov(x, invert(null))                  # 1
    label("2")
    jmp(x_dec, "3")                       # 2
    label("3")
    jmp(pin, "5")                         # 3
    jmp("2")                              # 4
    label("5")
    mov(isr, x)                           # 5
    push(noblock)                         # 6
    wrap()

# @rp2.asm_pio(
#     # autopush=True,
#     autopull=True,
#     # push_thresh=32,
#     pull_thresh=32,
#     # fifo_join=rp2.PIO.JOIN_NONE,
#     sideset_init=rp2.PIO.OUT_LOW,
#     out_init=rp2.PIO.OUT_HIGH, 
#     out_shiftdir=rp2.PIO.SHIFT_LEFT
# )
# def i2s_trx():
#     wait(1, pin, 0)             .side(0)
#     mov(x, y)                   .side(0)
#     label("low_loop")
#     wait(0, pin, 0)             .side(0)
#     out(pins , 1)               .side(0)
#     wait(1, pin, 0)             .side(0)
#     in_(null , 1)               .side(0)
#     in_(pins , 1)               .side(0)
#     # wait(0, pin, 0)             .side(0)
#     jmp(x_dec, "low_loop")      .side(0)
#     wait(0, pin, 0)             .side(1)
#     mov(x, y)                   .side(1)
#     wait(1, pin, 0)             .side(1)
#     label("high_loop")
#     wait(0, pin, 0)             .side(1)
#     out(pins , 1)                .side(1)
#     wait(1, pin, 0)             .side(1)
#     in_(null , 1)               .side(1)
#     in_(pins , 1)               .side(1)
#     # wait(0, pin, 0)             .side(1)
#     jmp(x_dec, "high_loop")     .side(1)
#     wait(0, pin, 0)             .side(1)

class PIOProgram:

    def __init__(self, num, pin):
        self.pin = machine.Pin(pin)
        self.sm = PIO2.state_machine(num)
        self.systemFreq = 0
        self.mode = 2

    def _init(self, program, freq):
        PIO2.remove_program()
        self.systemFreq = freq
        self.sm.init(program, freq=freq, in_base=self.pin, jmp_pin=self.pin)
        return True

    def deinit(self):
        self.sm.deinit()

    def load_program_high_low(self):
        self._init(pio_measure_high_low, 150_000_000)
        self.mode = 2
        return True

    def load_program_low_high(self):
        self._init(pio_measure_low_high, 150_000_000)
        self.mode = 3
        return True

    def measure_pulse_block(self, timeout_ms=5000):
        count_value = 0
        self.sm.active(1)
        start_time = time.ticks_ms()
        while (time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms):
            if self.sm.rx_fifo() > 0:
                count_value = self.sm.get()
                break
        self.sm.active(0)
        pulse_cycles = self.mode * (0xFFFFFFFF - count_value) + 2
        pulse_width_us = pulse_cycles * (1e6 / self.systemFreq)
        print(pulse_width_us)
        return pulse_width_us

    def measure_start(self):
        self.sm.active(1)
        return True

    def measure_stop(self):
        self.sm.active(0)
        if self.sm.rx_fifo() > 0:
            count_value = self.sm.get()
            pulse_cycles = self.mode * (0xFFFFFFFF - count_value) + 2
            pulse_width_us = pulse_cycles * (1e6 / self.systemFreq)
            print(pulse_width_us)
            return pulse_width_us
        return None

# def test(mode=0, delay_us=10):
#     if mode == 0:
#         pull = machine.Pin.PULL_DOWN
#     else:
#         pull = machine.Pin.PULL_UP
#     v = machine.Pin(11, machine.Pin.OUT)
#     if mode==0:
#         v.value(1)
#         time.sleep_us(delay_us)
#         v.value(0)
#     else:
#         v.value(0)
#         time.sleep_us(delay_us)
#         v.value(1)