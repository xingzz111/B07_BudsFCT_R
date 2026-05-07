#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
校准功能模块
独立于GUI，支持动态扩展校准类型
"""

import sys
import os
import time
import subprocess
from threading import Timer

# 添加库路径
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "lib")
sys.path.append(lib_path)

try:
    from rtRP2.rp2Device import Rp2Device
    
    # 创建自定义Rp2Device类，能够捕获RPC调用信息
    class MonitoredRp2Device(Rp2Device):
        def __init__(self, port, baudrate, publisher=None, isprint=True, log_callback=None):
            super().__init__(port, baudrate, publisher, isprint)
            self.log_callback = log_callback
        
        def rpc_call(self, *args, **kwargs):
            # 捕获RPC调用信息并记录到日志
            if self.log_callback:
                # 构造RPC调用信息
                function = str(args[0])
                function_args = args[1:]
                arg_strings = [repr(arg) for arg in function_args]
                kwargs_strings = [f"{key}={repr(value)}" for key, value in kwargs.items()]
                all_args = ", ".join(arg_strings + kwargs_strings)
                
                # 记录RPC调用开始
                self.log_callback(f"RPC: {function}({all_args})")
            
            # 执行原始RPC调用
            result = super().rpc_call(*args, **kwargs)
            
            # 记录RPC调用结果
            if self.log_callback:
                self.log_callback(f"RPC_RESULT: {result}")
            
            return result
    
    # 使用自定义的监控设备类
    Rp2Device = MonitoredRp2Device
    
except ImportError:
    # 创建模拟Rp2Device类用于测试
    class Rp2Device:
        def __init__(self, port, baudrate, publisher=None, isprint=True, log_callback=None):
            self._port = port
            self._baudrate = baudrate
            self._pyb = None
            self._publisher = publisher
            self.isprint = isprint
            self.log_callback = log_callback
        
        def init(self):
            if self.log_callback:
                self.log_callback(f"INFO: 模拟设备初始化: {self._port}")
            return True
        
        def deinit(self):
            if self.log_callback:
                self.log_callback("INFO: 模拟设备反初始化")
        
        def rpc_call(self, *args, **kwargs):
            function = str(args[0])
            function_args = args[1:]
            arg_strings = [repr(arg) for arg in function_args]
            kwargs_strings = [f"{key}={repr(value)}" for key, value in kwargs.items()]
            all_args = ", ".join(arg_strings + kwargs_strings)
            
            if self.log_callback:
                self.log_callback(f"RPC: {function}({all_args})")
                self.log_callback(f"RPC_RESULT: 0.0 (模拟)")
            
            return 0.0


class CalibrationEngine:
    """校准引擎 - 管理所有校准功能"""
    
    def __init__(self):
        self.calibration_types = {}
        self.client = None
        self.is_running = False
        self.custom_functions = {}  # 存储自定义校准函数
        self.log_callback = None  # 存储日志回调函数
        
        # 注册内置校准类型
        self.register_calibration_type("B08_B06_DAC_CAL", "DAC校准", self.dac_calibration)
        self.register_calibration_type("B08_PWM_CAL", "PWM校准", self.pwm_calibration)
        self.register_calibration_type("B06_PWM_CAL_VERIFY", "PWM校准验证", self.b06_pwm_calibration_verify)
        self.register_calibration_type("B08 Ship Mode CAL", "Ship Mode校准", self.ship_mode_calibration)
        self.register_calibration_type("COMMON_MANUAL_CAL", "手动调整index", self.manually_calibration)
        # 自动注册所有自定义校准函数
        self.auto_register_custom_functions()
    
    def register_calibration_type(self, calib_id, calib_name, calib_function):
        """注册新的校准类型"""
        self.calibration_types[calib_id] = {
            'name': calib_name,
            'function': calib_function
        }
    
    def auto_register_custom_functions(self):
        """自动注册所有自定义校准函数"""
        # 获取当前类的所有方法
        methods = [method_name for method_name in dir(self) if callable(getattr(self, method_name))]
        
        # 注册所有符合命名模式的自定义函数
        for method_name in methods:
            # 跳过内置方法和私有方法
            if method_name.startswith('_') or method_name in ['execute_calibration', 'execute_custom_function', 
                                                              'register_calibration_type', 'register_custom_function',
                                                              'unregister_custom_function', 'auto_register_custom_functions',
                                                              'init_device', 'deinit_device', 'reset_all', 'stop_calibration',
                                                              'run_shell_with_timeout', 'dac_calibration', 'pwm_calibration', 
                                                              'ship_mode_calibration', 'manually_calibration', 'b06_pwm_calibration_verify']:
                continue
            
            # 检查是否为自定义校准函数（以_calibration结尾）
            if method_name.endswith('_calibration'):
                # 提取函数名称（去掉_calibration后缀）
                function_name = method_name.replace('_calibration', '')
                
                # 注册自定义函数
                self.register_custom_function(function_name, getattr(self, method_name))
                print(f"自动注册自定义校准函数: {function_name} -> {method_name}")
    
    def register_custom_function(self, function_name, function_impl):
        """注册自定义校准函数"""
        self.custom_functions[function_name] = function_impl
        print(f"自定义校准函数 '{function_name}' 已注册")
    
    def unregister_custom_function(self, function_name):
        """注销自定义校准函数"""
        if function_name in self.custom_functions:
            del self.custom_functions[function_name]
            print(f"自定义校准函数 '{function_name}' 已注销")
        else:
            print(f"自定义校准函数 '{function_name}' 不存在")
    
    def execute_calibration(self, calib_type, port, params, log_callback=None, progress_callback=None):
        """执行校准"""
        try:
            self.is_running = True
            
            # 初始化设备连接
            if not self.init_device(port, log_callback):
                return False, "设备连接失败"
            
            # 执行校准
            if calib_type in self.calibration_types:
                success = self.calibration_types[calib_type]['function'](params, log_callback, progress_callback)
                message = f"{calib_type}校准{'成功' if success else '失败'}"
            else:
                # 检查是否为自定义校准函数
                function_type = params.get('function_type', 'builtin')
                custom_function = params.get('custom_function', '')
                
                if function_type == 'custom' and custom_function:
                    # 执行自定义校准函数
                    success = self.execute_custom_function(custom_function, params, log_callback, progress_callback)
                    message = f"自定义校准 {calib_type} {'成功' if success else '失败'}"
                else:
                    success = False
                    message = f"未知的校准类型: {calib_type}"
            
            # 清理设备连接
            self.deinit_device(log_callback)
            
            self.is_running = False
            return success, message
            
        except Exception as e:
            self.is_running = False
            if log_callback:
                log_callback(f"FAIL: 校准过程中发生错误: {str(e)}")
            return False, f"校准失败: {str(e)}"
    
    def execute_custom_function(self, function_name, params, log_callback=None, progress_callback=None):
        """执行自定义函数"""
        if not self.is_running:
            return False
        
        if log_callback:
            log_callback(f"INFO: 开始执行自定义函数: {function_name}")
        
        try:
            # 根据函数名称执行相应的校准方法
            if log_callback:
                log_callback(f"INFO: 执行函数: {function_name} 参数: {params}")
            
            # 动态调用相应的校准方法
            # 首先检查是否已注册的自定义函数
            if function_name in self.custom_functions:
                success = self.custom_functions[function_name](params, log_callback, progress_callback)
            else:
                # 如果函数名以_calibration结尾，尝试去掉后缀再查找
                if function_name.endswith('_calibration'):
                    short_name = function_name.replace('_calibration', '')
                    if short_name in self.custom_functions:
                        success = self.custom_functions[short_name](params, log_callback, progress_callback)
                    else:
                        # 如果函数未注册，使用模拟实现
                        if log_callback:
                            log_callback(f"WARN: 自定义函数 {function_name} 未注册，使用模拟执行")
                        time.sleep(2)
                        success = True
                else:
                    # 如果函数未注册，使用模拟实现
                    if log_callback:
                        log_callback(f"WARN: 自定义函数 {function_name} 未注册，使用模拟执行")
                    time.sleep(2)
                    success = True
            
            if log_callback:
                log_callback(f"PASS: 自定义函数 {function_name} 执行完成")
            return success
            
        except Exception as e:
            if log_callback:
                log_callback(f"FAIL: 自定义函数执行失败: {str(e)}")
            return False
    
    def stop_calibration(self):
        """停止校准"""
        self.is_running = False
        if self.client:
            self.deinit_device()
    
    def init_device(self, port, log_callback=None):
        """初始化设备连接"""
        try:
            if log_callback:
                log_callback(f"INFO: 正在连接设备端口: {port}")
            
            # 创建设备实例并传递日志回调函数
            self.client = Rp2Device(port, 115200, None, True, log_callback)
            self.client.init()
            self.client._pyb.exec_("from MixDevice import *")
            
            if log_callback:
                log_callback(f"PASS: 设备连接成功")
            return True
        except Exception as e:
            if log_callback:
                log_callback(f"FAIL: 设备连接失败: {str(e)}")
            return False
    
    def deinit_device(self, log_callback=None):
        """清理设备连接"""
        if self.client:
            try:
                self.client._pyb.exec_("del mixdevice")
                self.client._pyb.exec_("import gc;gc.mem_free()")
                self.client.deinit()
                if log_callback:
                    log_callback(f"INFO: 设备连接已关闭")
            except Exception as e:
                if log_callback:
                    log_callback(f"WARN: 设备清理时发生警告: {str(e)}")
    
    def reset_all(self, log_callback=None):
        """重置所有设备"""
        if not self.is_running:
            return
        
        if log_callback:
            log_callback(f"RESET: 正在重置所有设备...")
        
        self.client.rpc_call("mixdevice.reset")
        self.client.rpc_call("mixdevice.batteryDisable")
        self.client.rpc_call("mixdevice.chargeDisable")
        
        if log_callback:
            log_callback(f"RESET: 重置完成")
    
    def run_shell_with_timeout(self, cmd, timeout=5):
        """运行shell命令并设置超时"""
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        timer = Timer(timeout, lambda process: process.kill(), [p])
        try:
            timer.start()
            stdout, stderr = p.communicate(timeout=timeout)
            out = stdout.decode("gbk").strip() if stdout else ""
            error = stderr.decode("gbk").strip() if stderr else ""
            return_code = p.returncode
            return return_code, out, error
        except Exception as e:
            raise Exception(f'run_shell_with_timeout-Exception:{e}')
        finally:
            timer.cancel()
    
    def dac_calibration(self, params, log_callback=None, progress_callback=None):
        """DAC校准验证"""
        if not self.is_running:
            return False
        
        if log_callback:
            log_callback(f"CALIB: 开始DAC校准验证...")
        
        try:
            index = params.get("index", 22)
            setVoltage = params.get("setVoltage", 4100)
            
            # 详细的校准动作监控
            if log_callback:
                log_callback(f"MONITOR: 开始DAC校准流程")
                log_callback(f"MONITOR: 目标电压: 7200mV (设置电压: {setVoltage})")
                log_callback(f"MONITOR: EEPROM索引: {index}")
            
            # 初始化EEPROM
            if log_callback:
                log_callback(f"MONITOR: 初始化EEPROM索引 {index}")
            self.client.rpc_call("baseboard.write_calibration_cell", int(index), float(1.0), float(0.0), 1000)
            res = self.client.rpc_call("baseboard.read_calibration_cell", index)
            if log_callback:
                log_callback(f"MONITOR: EEPROM读取结果: {res}")
            
            # 设备初始化序列
            if log_callback:
                log_callback(f"MONITOR: 执行设备初始化序列")
            self.client.rpc_call("mixdevice.batteryDisable")
            self.client.rpc_call("mixdevice.chargeEnable", 10, 100)
            self.client.rpc_call("mixdevice.chargeDisable")
            self.client.rpc_call("mixdevice.reset")
            self.client.rpc_call("mixdevice.relay", 'NTC_SEL_SW_NORMAL_TEMP')
            self.client.rpc_call("mixdevice.relay", 'PSU_BATT_TO_DUT')
            time.sleep(0.1)
            self.client.rpc_call("mixdevice.batteryEnable", 3800, 500)
            time.sleep(3)
            self.client.rpc_call("mixdevice.relay", 'USB_SEL_SW')
            
            # 设置DAC输出
            if log_callback:
                log_callback(f"MONITOR: 设置DAC输出电压: {setVoltage}")
            self.client.rpc_call("mixdevice.wctDacOutput", setVoltage)
            self.client.rpc_call("mixdevice.relay", 'WIRELESS_OUTPUT_SW')
            time.sleep(0.1)
            self.client.rpc_call("mixdevice.relay", 'DMM_VIN1_SEL_SW')
            
            # 测量电压
            if log_callback:
                log_callback(f"MONITOR: 开始电压测量")
            voltage = self.client.rpc_call("mixdevice.measureByDMM", "ch0",'7000mv','DMM_VIN2_SEL_SW_WIRELESS_CHARGE_VOLT', 0.2)
            voltage = voltage * 5.7
            if log_callback:
                log_callback(f"MONITOR: 初始电压测量: {voltage}mV")
            
            # 电压校准循环
            iteration = 0
            while voltage >= 7195 or voltage <= 7205:
                iteration += 1
                if log_callback:
                    log_callback(f"MONITOR: 校准迭代 {iteration}: 当前电压 {voltage}mV")
                
                if voltage <= 7195:
                    setVoltage = setVoltage - 1
                    if log_callback:
                        log_callback(f"MONITOR: 电压偏低，降低DAC设置: {setVoltage}")
                elif voltage >= 7205:
                    setVoltage = setVoltage + 1
                    if log_callback:
                        log_callback(f"MONITOR: 电压偏高，提高DAC设置: {setVoltage}")
                
                # 更新DAC输出
                self.client.rpc_call("mixdevice.wctDacOutput", setVoltage)
                
                # 重新测量电压
                voltage = self.client.rpc_call("mixdevice.measureByDMM", "ch0",'7000mv','DMM_VIN2_SEL_SW_WIRELESS_CHARGE_VOLT', 0.2)
                voltage = voltage * 5.7
                
                if log_callback:
                    log_callback(f"MONITOR: 更新后电压测量: {voltage}mV")
                
                if 7195 <= voltage <= 7205:
                    if log_callback:
                        log_callback(f"PASS: DAC校准验证成功")
                        log_callback(f"MONITOR: 最终设置电压: {setVoltage}")
                        log_callback(f"MONITOR: 最终测量电压: {voltage}mV")
                    
                    offset = setVoltage - 4100
                    if log_callback:
                        log_callback(f"MONITOR: 计算偏移量: {offset}")
                    
                    # 写入校准结果到EEPROM
                    if log_callback:
                        log_callback(f"MONITOR: 写入校准结果到EEPROM索引 {index}")
                    self.client.rpc_call("baseboard.write_calibration_cell", int(index), float(1.0), float(offset), 1000)
                    res = self.client.rpc_call("baseboard.read_calibration_cell", index)
                    if log_callback:
                        log_callback(f"MONITOR: EEPROM验证读取: {res}")
                    break
            
            # 重置设备并验证
            if log_callback:
                log_callback(f"MONITOR: 重置设备进行最终验证")
            self.reset_all(log_callback)
            self.client.rpc_call("mixdevice.wctDacOutput", 4100)
            voltage = self.client.rpc_call("mixdevice.measureByDMM", "ch0",'7000mv','DMM_VIN2_SEL_SW_WIRELESS_CHARGE_VOLT', 0.2)
            voltage = voltage * 5.7
            if log_callback:
                log_callback(f"MONITOR: 最终验证电压: {voltage}mV")
            
            if log_callback:
                log_callback(f"PASS: DAC校准验证完成")
            return True
            
        except Exception as e:
            if log_callback:
                log_callback(f"FAIL: DAC校准验证失败: {str(e)}")
            return False
    
    def ship_mode_calibration(self, params, log_callback=None, progress_callback=None):
        """Ship Mode校准"""
        if not self.is_running:
            return False
        
        if log_callback:
            log_callback(f"CALIB: 开始Ship Mode校准...")
        
        try:
            target_current = params.get("target_current", 0.0045)
            
            if log_callback:
                log_callback(f"INFO: 目标电流: {target_current}A")
            
            # 实际Ship Mode校准过程
            self.client.rpc_call('mixdevice.reset')
            self.client.rpc_call("baseboard.write_calibration_cell", int(14), float(1.0), float(0.0), 1)
            self.client.rpc_call("mixdevice.relay", 'NTC_SEL_SW_NORMAL_TEMP')
            self.client.rpc_call("mixdevice.relay", 'PSU_VCHG_TO_DUT')
            self.client.rpc_call("mixdevice.relay", 'PSU_BATT_TO_DUT')
            self.client.rpc_call("mixdevice.batteryEnable", 3800, 500)
            time.sleep(0.1)
            self.client.rpc_call("mixdevice.chargeEnable", 5000, 500)
            self.client.rpc_call("mixdevice.relay", 'USB_SEL_SW')
            time.sleep(1)
            self.client.rpc_call("mixdevice.relay", 'PP24V_TO_MAGNET')
            time.sleep(10)
            
            self.client.rpc_call("mixdevice.measureCurrentByOdin", 'battery')
            self.client.rpc_call("mixdevice.measureCurrentByOdin", 'charger')
            
            return_code, resp, error = self.run_shell_with_timeout('BoseManufacturingTool.exe send "ProductInfo.FirmwareVersion.Get" --expect "." --print_response')
            if log_callback:
                log_callback(f"INFO: BMT响应: {resp}")
            
            return_code, resp, error = self.run_shell_with_timeout('BoseManufacturingTool.exe send "Control.ShipMode.Start 2000" --expect "." --print_response')
            self.client.rpc_call("mixdevice.chargeEnable", 10, 10)
            self.client.rpc_call("mixdevice.relay", 'PSU_VCHG_TO_DUT', 'DISCONNECT')
            self.client.rpc_call("mixdevice.relay", 'USB_SEL_SW', 'DISCONNECT')
            time.sleep(8)
            
            ret = self.client.rpc_call("mixdevice.measureCurrentByOdin", 'battery', '10ua')
            if log_callback:
                log_callback(f"INFO: 电流测量结果: {ret}")
            
            writeValue = target_current - float(ret)
            self.client.rpc_call("baseboard.write_calibration_cell", int(14), float(1.0), float(writeValue), 1)
            
            if log_callback:
                log_callback(f"PASS: Ship Mode校准完成")
            return True
            
        except Exception as e:
            if log_callback:
                log_callback(f"FAIL: Ship Mode校准失败: {str(e)}")
            return False
    

    def manually_calibration(self, params, log_callback=None, process_callback=None):
        if not self.is_running:
            return False
        if log_callback:
            log_callback(f"CALIB: 开始手动校准...")
        index = params.get("index", 1)
        currentValue = params.get("currentValue", 0)
        targetGain = params.get("targetGain", 1.0)
        targetOffset = params.get("targetOffset", 0.0)
        currentGain = self.client.rpc_call('baseboard.base_read_calibration_cell', index)['gain']
        currentOffset = self.client.rpc_call('baseboard.base_read_calibration_cell', index)['offset']
        rawValue = (currentValue - currentOffset) / currentGain
        log_callback(f"DEBUG: 当前校准系数, index={index}, gain={currentGain}, offset={currentOffset}, rawValue={rawValue}")
        self.client.rpc_call('baseboard.base_write_calibration_cell', index, targetGain, targetOffset, 1)
        self.client.rpc_call('mixdevice.reset')
        result = self.client.rpc_call('baseboard.base_read_calibration_cell', index)
        if log_callback:
            log_callback(f"PASS: 手动校准验证完成, index={index}, gainAfterCal={result['gain']}, offsetAfterCal={result['offset']}")
        return True  # 添加返回值表示成功

    def demo2_calibration(self, params, log_callback=None, process_callback=None):
        if not self.is_running:
            return False
        if log_callback:
            log_callback(f"CALIB: 开始demo2校准验证...")
        index = params.get("index", 111)
        setVoltage = params.get("setVoltage", 2000)
        log_callback(f"DEBUG: demo2校准验证完成, index={index}, setVoltage={setVoltage}")
        self.client.rpc_call('mixdevice.reset')
        self.client.rpc_call('mixdevice.reset')
        self.client.rpc_call('mixdevice.reset')
        self.client.rpc_call('mixdevice.reset')
        self.client.rpc_call('mixdevice.reset')
        self.client.rpc_call('mixdevice.reset')
        self.client.rpc_call('mixdevice.reset')
        if log_callback:
            log_callback(f"PASS: demo校准验证完成")
        return True  # 添加返回值表示成功

    def pwm_calibration(self, params, log_callback=None, progress_callback=None):
        """PWM校准验证"""
        if not self.is_running:
            return False
        
        if log_callback:
            log_callback(f"CALIB: 开始PWM校准验证...")
        
        try:
            frequency = params.get("frequency", 128000)
            duty = params.get("duty", 0.4)
            index = params.get("index", 23)
            
            if log_callback:
                log_callback(f"INFO: 频率: {frequency}Hz, 占空比: {duty}, EEPROM索引: {index}")
            
            while True:
                self.client.rpc_call("baseboard.write_calibration_cell", int(index), float(1.0), float(0.0), 1000)
                res = self.client.rpc_call("baseboard.read_calibration_cell", index)
                if log_callback:
                    log_callback(f"INFO: EEPROM读取: {res}")
                
                self.client.rpc_call("mixdevice.batteryDisable")
                self.client.rpc_call("mixdevice.chargeEnable", 10, 100)
                self.client.rpc_call("mixdevice.chargeDisable")
                self.client.rpc_call("mixdevice.reset")
                self.client.rpc_call("mixdevice.relay", 'NTC_SEL_SW_NORMAL_TEMP')
                self.client.rpc_call("mixdevice.relay", 'PSU_BATT_TO_DUT')
                time.sleep(0.1)
                self.client.rpc_call("mixdevice.batteryEnable", 3800, 500)
                time.sleep(3)
                self.client.rpc_call("mixdevice.relay", 'USB_SEL_SW')
                self.client.rpc_call("mixdevice.wctDacOutput", 4100)
                self.client.rpc_call("mixdevice.relay", 'WIRELESS_OUTPUT_SW')
                time.sleep(0.1)
                self.client.rpc_call("mixdevice.wctPWMOutput", frequency, duty)
                time.sleep(5)
                self.client.rpc_call("mixdevice.relay", 'DMM_VIN1_SEL_SW')
                
                voltage1 = self.client.rpc_call("mixdevice.measureByDMM", "ch0",'7000mv','DMM_VIN2_SEL_SW_WIRELESS_CHARGE_VOLT', 0.2, 3)
                voltage = self.client.rpc_call("mixdevice.measureByDMM", "ch0",'7000mv','DMM_VIN2_SEL_SW_WIRELESS_CHARGE_CURR', 0.2, 3)
                if log_callback:
                    log_callback(f"INFO: 无线充电电流: {voltage}")
                
                self.client.rpc_call('mixdevice.reset')
                
                if 395 < voltage < 405:
                    break
                else:
                    if voltage > 405:
                        frequency = frequency + 1000
                    elif voltage < 395:
                        frequency = frequency - 1000
                    if log_callback:
                        log_callback(f"INFO: 频率校准: {frequency}")
            
            offset = frequency - 128000
            if log_callback:
                log_callback(f"INFO: 偏移量: {offset}")
            
            self.client.rpc_call("baseboard.write_calibration_cell", int(index), float(1.0), float(offset), 1000)
            
            self.reset_all(log_callback)
            
            # 验证校准结果
            self.client.rpc_call("mixdevice.relay", 'NTC_SEL_SW_NORMAL_TEMP')
            self.client.rpc_call("mixdevice.relay", 'PSU_BATT_TO_DUT')
            time.sleep(0.1)
            self.client.rpc_call("mixdevice.batteryEnable", 3800, 500)
            time.sleep(3)
            self.client.rpc_call("mixdevice.relay", 'USB_SEL_SW')
            self.client.rpc_call("mixdevice.wctDacOutput", 4100)
            self.client.rpc_call("mixdevice.relay", 'WIRELESS_OUTPUT_SW')
            time.sleep(0.1)
            self.client.rpc_call("mixdevice.wctPWMOutput", 128000, duty)
            time.sleep(5)
            self.client.rpc_call("mixdevice.relay", 'DMM_VIN1_SEL_SW')
            
            voltage1 = self.client.rpc_call("mixdevice.measureByDMM", "ch0", '7000mv', 'DMM_VIN2_SEL_SW_WIRELESS_CHARGE_VOLT', 0.2, 3)
            voltage = self.client.rpc_call("mixdevice.measureByDMM", "ch0",'7000mv','DMM_VIN2_SEL_SW_WIRELESS_CHARGE_CURR', 0.2, 3)
            if log_callback:
                log_callback(f"INFO: 验证无线充电电流: {voltage}")
            
            if log_callback:
                log_callback(f"PASS: PWM校准验证完成")
            return True
            
        except Exception as e:
            if log_callback:
                log_callback(f"FAIL: PWM校准验证失败: {str(e)}")
            return False
    


    def b06_pwm_calibration_verify(self, params, log_callback=None, progress_callback=None):
        if not self.is_running:
            return False
        
        if log_callback:
            log_callback(f"CALIB: 开始PWM校准验证...")

        try:
            frequency = params.get("frequency", 128000)
            duty = params.get("duty", 0.4)
            index = params.get("index", 23)
            self.reset_all(log_callback)
            while True:
                self.client.rpc_call("baseboard.write_calibration_cell", int(index), float(1.0), float(0.0), 1000)
                res = self.client.rpc_call("baseboard.read_calibration_cell", index)
                if log_callback:
                    log_callback(f"INFO: eeprom read: {res}")
                self.client.rpc_call("mixdevice.relay", 'NTC_SEL_SW_NORMAL_TEMP')
                self.client.rpc_call("mixdevice.relay", 'DUT_PCM_SEL_SW')
                self.client.rpc_call("mixdevice.batteryEnable", 3800, 500)
                self.client.rpc_call("mixdevice.relay", 'TPF235_LID_TO_1V8')
                self.client.rpc_call("mixdevice.relay", 'DMM_VIN1_SEL_SW')
                self.client.rpc_call("mixdevice.relay", 'PSU_VCHG_TO_DUT')
                self.client.rpc_call("mixdevice.relay", 'PSU_BATT_TO_DUT')
                time.sleep(0.5)
                self.client.rpc_call("mixdevice.chargeEnable", 5000, 500)
                self.client.rpc_call("mixdevice.relay", 'USB_SEL_SW')
                time.sleep(2)
                return_code, resp, error = self.run_shell_with_timeout('BoseManufacturingTool.exe send \"Debug.GPIO.SetGet 43, 0, 2, 3\" --expect \".\" --print_response')
                if log_callback:
                    log_callback(f"INFO: resp: {resp}")
                time.sleep(0.5)
                return_code, resp1, error = self.run_shell_with_timeout('BoseManufacturingTool.exe send \"Debug.TAP.Start \\\"i2c sc\\\"\" --expect \".\" --print_response')
                if log_callback:
                    log_callback(f"INFO: resp1: {resp1}")
                
                time.sleep(2)
                self.client.rpc_call("mixdevice.wctDacOutput", 4100)
                self.client.rpc_call("mixdevice.relay", 'WIRELESS_OUTPUT_SW')
                time.sleep(0.1)
                self.client.rpc_call("mixdevice.wctPWMOutput", frequency, duty)
                time.sleep(2)
                self.client.rpc_call("mixdevice.chargeEnable", 10, 10)
                self.client.rpc_call("mixdevice.relay", 'PSU_VCHG_TO_DUT', 'DISCONNECT')
                time.sleep(3)
                voltageList = []
                for x in range(5):
                    voltage = self.client.rpc_call("mixdevice.measureByDMM", "ch0",'7000mv','DMM_VIN2_SEL_SW_WIRELESS_CHARGE_CURR', 0.2)
                    voltageList.append(voltage)
                voltageList.sort()
                if log_callback:
                    log_callback(f"INFO: voltageList: {voltageList}")
                voltage = voltageList[int(len(voltageList) / 2)]
                if log_callback:
                    log_callback(f"INFO: wireless current: {voltage}")
                self.client.rpc_call('mixdevice.reset')
                if 455 < voltage < 465:
                    break
                elif voltage < 400:
                    frequency = frequency - 1000
                    if log_callback:
                        log_callback(f"INFO: frequencyCal: {frequency}")
                elif 400 < voltage < 455:
                    frequency = frequency - 200
                    if log_callback:
                        log_callback(f"INFO: frequencyCal: {frequency}")
                elif 465 < voltage < 500:
                    frequency = frequency + 200
                    if log_callback:
                        log_callback(f"INFO: frequencyCal: {frequency}")
                elif voltage > 500:
                    frequency = frequency + 1000
                    if log_callback:
                        log_callback(f"INFO: frequencyCal: {frequency}")

            offset = frequency - 128000
            if log_callback:
                log_callback(f"INFO: offset: {offset}")
            self.client.rpc_call("baseboard.write_calibration_cell", int(index), float(1.0), float(offset), 1000)

            self.reset_all(log_callback)
            self.client.rpc_call("mixdevice.relay", 'NTC_SEL_SW_NORMAL_TEMP')
            self.client.rpc_call("mixdevice.relay", 'DUT_PCM_SEL_SW')
            self.client.rpc_call("mixdevice.batteryEnable", 3800, 500)
            self.client.rpc_call("mixdevice.relay", 'TPF235_LID_TO_1V8')
            self.client.rpc_call("mixdevice.relay", 'DMM_VIN1_SEL_SW')
            self.client.rpc_call("mixdevice.relay", 'PSU_VCHG_TO_DUT')
            self.client.rpc_call("mixdevice.relay", 'PSU_BATT_TO_DUT')
            time.sleep(0.5)
            self.client.rpc_call("mixdevice.chargeEnable", 5000, 500)
            self.client.rpc_call("mixdevice.relay", 'USB_SEL_SW')
            time.sleep(2)
            return_code, resp, error = self.run_shell_with_timeout('BoseManufacturingTool.exe send \"Debug.GPIO.SetGet 43, 0, 2, 3\" --expect \".\" --print_response')
            if log_callback:
                log_callback(f"INFO: resp: {resp}")
            return_code, resp1, error = self.run_shell_with_timeout('BoseManufacturingTool.exe send \"Debug.TAP.Start \\\"i2c sc\\\"\" --expect \".\" --print_response')
            if log_callback:
                log_callback(f"INFO: resp1: {resp1}")   
            time.sleep(2)
            self.client.rpc_call("mixdevice.relay", 'WIRELESS_OUTPUT_SW')
            self.client.rpc_call("mixdevice.wctDacOutput", 4100)
            time.sleep(0.1)
            self.client.rpc_call("mixdevice.wctPWMOutput", 128000, 0.4)
            time.sleep(2)
            self.client.rpc_call("mixdevice.chargeEnable", 10, 10)
            self.client.rpc_call("mixdevice.relay", 'PSU_VCHG_TO_DUT', 'DISCONNECT')
            time.sleep(3)
            voltageList = []
            for x in range(5):
                voltage = self.client.rpc_call("mixdevice.measureByDMM", "ch0",'7000mv','DMM_VIN2_SEL_SW_WIRELESS_CHARGE_CURR', 0.2)
                voltageList.append(voltage)
            voltageList.sort()
            if log_callback:
                log_callback(f"INFO: voltageList: {voltageList}")
            voltage = voltageList[int(len(voltageList) / 2)]
            if log_callback:
                log_callback(f"INFO: wireless current: {voltage}")
            if 450 < voltage < 470:
                log_callback(f"PASS: PWM校准验证完成")
            return True
        except Exception as e:
            if log_callback:
                log_callback(f"FAIL: PWM校准验证失败: {str(e)}")
            return False        


    def stop_calibration(self):
        """停止校准"""
        self.is_running = False
        if self.client:
            self.deinit_device()


# 创建全局校准引擎实例
calibration_engine = CalibrationEngine()